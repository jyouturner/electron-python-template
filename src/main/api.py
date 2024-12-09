# src/main/api.py
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
origins = [
    "file://",
    "null",
    "http://localhost:8000",
    "http://localhost:*",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:*",
    "*"  # Warning: In production, you'd want to be more specific
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url}")
    logger.debug(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

@app.get("/api/quick-task")
async def quick_task(request: Request):
    logger.debug(f"Quick task called from origin: {request.headers.get('origin')}")
    await asyncio.sleep(0.1)
    return {"message": "Quick task completed"}

@app.get("/api/start-long-task/{task_id}")
async def start_long_task(task_id: str):
    return {"task_id": task_id, "status": "started"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_closed = False
    try:
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "start_task":
                    async for progress in long_running_task(data.get("task_id")):
                        await websocket.send_json(progress)
            except RuntimeError as e:
                # Connection was closed by client
                connection_closed = True
                logger.debug("WebSocket connection closed by client")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if not connection_closed:
            try:
                await websocket.close()
            except Exception as e:
                logger.debug(f"Error while closing WebSocket: {e}")

# For long-running tasks
async def long_running_task(task_id: str):
    for i in range(5):
        await asyncio.sleep(1)
        yield {"task_id": task_id, "progress": (i + 1) * 20}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")