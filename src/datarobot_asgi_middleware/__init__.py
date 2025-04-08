# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from starlette.types import ASGIApp, Receive, Scope, Send


class DataRobotASGIMiddleware:
    """
    Middleware to augment ASGI applications run by DataRobot Custom Applications.

    It routes root URL requests from Kubernetes to the base /health URL to support
    more robust health checks than just loading the root URL.
    """

    def __init__(self, app: ASGIApp, use_health: bool = False):
        self.app = app
        self.use_health = use_health
        # Get the script name from the environment variable to know what the internal
        # load balancer is using as the prefix for the request.
        self.internal_prefix = os.getenv("SCRIPT_NAME", None)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        headers = dict(scope["headers"])
        x_forwarded_prefix = headers.get(b"x-forwarded-prefix", b"").decode("utf-8")
        user_agent = headers.get(b"user-agent", b"").decode("utf-8")

        # Send Kubernetes probe requests to /health for real health checks
        if self.use_health and user_agent.startswith("kube-probe"):
            scope["path"] = "/health"
            scope["root_path"] = ""
            return await self.app(scope, receive, send)

        if not x_forwarded_prefix and self.internal_prefix:
            # Getting a request from internal load balancer without the front-proxy.
            scope["root_path"] = self.internal_prefix + scope["root_path"]
            return await self.app(scope, receive, send)

        if x_forwarded_prefix:
            # Getting a request originating from the external load balancer.
            scope["root_path"] = x_forwarded_prefix + scope["root_path"]
            if self.internal_prefix and scope["path"].startswith(self.internal_prefix):
                # But it is getting proxied through the internal load balancer, so we need to
                # rewrite the path to match the external load balancer.
                scope["path"] = scope["path"].replace(self.internal_prefix, x_forwarded_prefix, 1)
            return await self.app(scope, receive, send)

        return await self.app(scope, receive, send)
