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

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from datarobot_asgi_middleware import DataRobotASGIMiddleware

@pytest.fixture
def app(request):
    app = FastAPI()


    # Add a test health endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy"}


    @app.get("/")
    async def root():
        return {"message": "hello"}


    return app


def test_kubernetes_probe_redirect(app):
    # Add our middleware
    app.add_middleware(DataRobotASGIMiddleware, health_endpoint="/health")

    # Create a test client
    client = TestClient(app)

    # Make a request that simulates the Kubernetes probe
    response = client.get(
        "/apps/67f3e8ac039772f090878752/",
        headers={
            "user-agent": "kube-probe/1.30+",
            "accept": "*/*",
            "connection": "close",
            "host": "10.190.91.26:8080"
        }
    )

    # Verify the response
    assert response.status_code == 200
    assert response.request.url.path == "/apps/67f3e8ac039772f090878752/", "It should not redirect to /health"
    assert response.json() == {"status": "healthy"}


def test_normal_request(app):
    # Add our middleware
    app.add_middleware(DataRobotASGIMiddleware)

    # Create a test client
    client = TestClient(app)

    # Make a normal request to the apps endpoint
    response = client.get("/")

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_proxy_request(app):
    # Add our middleware
    app.add_middleware(DataRobotASGIMiddleware)

    # Create a test client
    client = TestClient(app)

    # Make a normal request to the apps endpoint
    response = client.get(
        "/custom_applications/67f3e8ac039772f090878752/",
        headers={"x-forwarded-prefix": "/custom_applications/67f3e8ac039772f090878752"}
    )

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_internal_load_balancer_request(app, monkeypatch):
    # Mock the SCRIPT_NAME environment variable
    monkeypatch.setenv("SCRIPT_NAME", "/apps/67f3e8ac039772f090878752")
    app.add_middleware(DataRobotASGIMiddleware)

    # Create a test client
    client = TestClient(app)

    # Make a normal request to the apps endpoint
    response = client.get(
        "/apps/67f3e8ac039772f090878752/",
    )

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_combined_internal_and_external_prefix(app, monkeypatch):
    # Mock the SCRIPT_NAME environment variable
    monkeypatch.setenv("SCRIPT_NAME", "/apps/67f3e8ac039772f090878752")
    app.add_middleware(DataRobotASGIMiddleware)

    # Create a test client
    client = TestClient(app)

    # Request from the external load balancer with the internal prefix
    response = client.get(
        "/apps/67f3e8ac039772f090878752/",
        headers={"x-forwarded-prefix": "/custom_applications/67f3e8ac039772f090878752"}
    )

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_static_files_with_external_proxy(app, tmp_path):
    # Create a test static file
    static_dir = tmp_path / "static" / "assets"
    static_dir.mkdir(parents=True)
    test_file = static_dir / "test.txt"
    test_file.write_text("test content")

    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(static_dir)), name="static")

    # Add our middleware
    app.add_middleware(DataRobotASGIMiddleware)
    middleware = app.middleware("http")

    # Create a test client
    client = TestClient(app)

    # Direct access to static file
    response = client.get("/assets/test.txt")
    assert response.status_code == 200
    assert response.text == "test content"

    # Access through external proxy with prefix
    response = client.get(
        "/custom_applications/67f3e8ac039772f090878752/assets/test.txt",
        headers={"x-forwarded-prefix": "/custom_applications/67f3e8ac039772f090878752"}
    )
    assert response.status_code == 200
    assert response.text == "test content"

   # Access through external proxy with prefix
    response = client.get(
        "/assets/test.txt",
        headers={"x-forwarded-prefix": "/custom_applications/67f3e8ac039772f090878752"}
    )
    assert response.status_code == 200
    assert response.text == "test content"


def test_static_files_with_internal_prefix(app, tmp_path, monkeypatch):
    # Set up the internal prefix via SCRIPT_NAME
    monkeypatch.setenv("SCRIPT_NAME", "/apps/67f3e8ac039772f090878752")

    # Create a test static file
    static_dir = tmp_path / "static" / "assets"
    static_dir.mkdir(parents=True)
    test_file = static_dir / "test.txt"
    test_file.write_text("test content")

    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(static_dir)), name="static")

    # Add our middleware
    app.add_middleware(DataRobotASGIMiddleware)

    # Create a test client
    client = TestClient(app)

    # Test access through internal prefix
    response = client.get("/apps/67f3e8ac039772f090878752/assets/test.txt")
    assert response.status_code == 200
    assert response.text == "test content"

    # Test access through external load balancer proxied through the internal load balancer
    response = client.get(
        "/apps/67f3e8ac039772f090878752/assets/test.txt",
        headers={"x-forwarded-prefix": "/custom_applications/67f3e8ac039772f090878752"}
    )

    # Verify the response
    assert response.status_code == 200
    assert response.text == "test content"
