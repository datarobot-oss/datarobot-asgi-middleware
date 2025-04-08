# DataRobot ASGI Middleware


A middleware to simplify front-proxy handling and health checks in
[DataRobot](https://datarobot.com).


## Usage

Simply add to your FastAPI application that you expect to run in DataRobot

```python
from fastapi import FastAPI

from datarobot_asgi_middleware import DataRobotASGIMiddleWare

app = FastAPI()
app.add_middleware(DataRobotASGIMiddleWare)


@app.get("/")
async def root():
    return {"message": "hello"}

```


Doing so will enable the automatic URLs such as `docs/` and
`openapi.json` to work as expected both in DataRobot and locally.


If you'd like to do proper Kubernetes health checks to let DataRobot
know your application is healthy, the middleware adds a way to tell
DataRobot to use a `/health` endpoint to validate that your app is
working as expected using
[kube-probe](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).

So, similar to the example above, but this time with `use_health=True`:

```python
from fastapi import FastAPI

from datarobot_asgi_middleware import DataRobotASGIMiddleWare


app = FastAPI()
app.add_middleware(DataRobotASGIMiddleWare, use_health=True)


@app.get("/")
async def root():
    return {"message": "hello"}


@app.get("/health")
async def health():
    # Check on database connections, memory utilization, etc. If it returns
    # any error code like a 404 or 500, the app is marked as unhealth
    return {"status": "healthy"}
```


## Development

Development is designed to run with
[uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Taskfile/go-task](https://taskfile.dev/installation/).

You can run tests, linters, etc. by setting these two up to work together


### Testing realistically with Traefic

To test through a DataRobot-like proxy:

Install traefik by downloading from: https://github.com/traefik/traefik/releases


Configure it with `traefik.toml` like:

```toml
[entryPoints]
  [entryPoints.http]
    address = ":9999"

[providers]
  [providers.file]
    filename = "routes.toml"

[log]
  level = "DEBUG"
```

Create a `routes.toml` file like:

```toml
[http]
  [http.middlewares]
    [http.middlewares.strip-front-prefix.stripPrefix]
      prefixes = ["/front-proxy"]
    
    [http.middlewares.add-back-prefix.addPrefix]
      prefix = "/back-proxy"
    
    [http.middlewares.set-forwarded-prefix.headers]
      customRequestHeaders = { X-Forwarded-Prefix = "/front-proxy" }

  [http.routers]
    [http.routers.front-proxy]
      entryPoints = ["http"]
      service = "back-proxy"
      rule = "PathPrefix(`/front-proxy`)"
      middlewares = ["strip-front-prefix", "add-back-prefix"]

    [http.routers.back-proxy]
      entryPoints = ["http"]
      service = "app"
      rule = "PathPrefix(`/back-proxy`)"
      middlewares = ["set-forwarded-prefix"]

  [http.services]
    [http.services.back-proxy]
      [http.services.back-proxy.loadBalancer]
        [[http.services.back-proxy.loadBalancer.servers]]
          url = "http://127.0.0.1:9999"

    [http.services.app]
      [http.services.app.loadBalancer]
        [[http.services.app.loadBalancer.servers]]
          url = "http://127.0.0.1:8000"

```


And run locally with:

`traefik --configFile=traefik.toml`

With the fastapi running now accessing:

http://localhost:9999/front-proxy

will take you to a proxy compatible installation.

Technically DataRobot does a double front-proxy for applications, so
this configuration mimics the double proxy with one traefic instance.
