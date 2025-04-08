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
