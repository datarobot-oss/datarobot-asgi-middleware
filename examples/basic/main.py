from fastapi import FastAPI

from datarobot_asgi_middleware import DataRobotASGIMiddleware


app = FastAPI()
app.add_middleware(DataRobotASGIMiddleware, health_endpoint="/probe/health")


@app.get("/")
async def root():
    return {"message": "hello"}


@app.get("/probe/health")
async def health():
    # Check on database connections, memory utilization, etc. If it returns
    # any error code like a 404 or 500, the app is marked as unhealth
    return {"status": "healthy"}
