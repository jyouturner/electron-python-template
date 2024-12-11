from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import os
from datetime import datetime
from src.database import db
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

def setup_logging(log_dir):
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file path with timestamp
    log_file = os.path.join(log_dir, f'api_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Setup logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # This will still print to console
        ]
    )
    return logging.getLogger(__name__)

# Get log directory from environment variable or use default
log_dir = os.getenv('APP_LOG_DIR', os.path.expanduser('~/ReportManager/logs'))
logger = setup_logging(log_dir)

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

# Pydantic models for request validation
class ReportCreate(BaseModel):
    name: str
    created_by: str
    meta: Optional[Dict[str, Any]] = None
    template: Optional[str] = ""
    recipients: Optional[List[str]] = []

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    recipients: Optional[List[str]] = None

class TaskCreate(BaseModel):
    name: str
    type: str
    report_id: Optional[int] = None
    schedule: Optional[str] = None
    is_active: Optional[int] = 1
    meta: Optional[Dict[str, Any]] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url}")
    logger.debug(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Example task endpoints (from your original code)
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

async def long_running_task(task_id: str):
    for i in range(5):
        await asyncio.sleep(1)
        yield {"task_id": task_id, "progress": (i + 1) * 20}

# Report endpoints
@app.get("/api/reports")
async def list_reports():
    try:
        reports = db.list_reports()
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports")
async def create_report(report: ReportCreate):
    try:
        report_id = db.create_report(**report.model_dump())
        return {"id": report_id}
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}")
async def get_report(report_id: int):
    try:
        report = db.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/reports/{report_id}")
async def update_report(report_id: int, report: ReportUpdate):
    try:
        updates = report.model_dump(exclude_unset=True)
        success = db.update_report(report_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: int):
    try:
        success = db.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task endpoints
@app.get("/api/tasks")
async def list_tasks():
    try:
        tasks = db.get_tasks_for_scheduling()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    try:
        task_data = task.model_dump()
        task_id = db.create_task(**task_data)
        return {"id": task_id}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    try:
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    try:
        updates = task.model_dump(exclude_unset=True)
        success = db.update_task(task_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    try:
        success = db.deactivate_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints
@app.get("/api/reports/{report_id}/tasks")
async def get_report_tasks(report_id: int):
    try:
        tasks = db.get_tasks_by_report_id(report_id)
        if not tasks:
            return []  # Return empty list if no tasks found
        return tasks
    except Exception as e:
        logger.error(f"Error getting report tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/{report_id}/duplicate")
async def duplicate_report(report_id: int):
    try:
        new_id = db.duplicate_report(report_id)
        if not new_id:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/scheduled")
async def get_scheduled_tasks():
    try:
        tasks = db.get_tasks_for_scheduling()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        logger.info("Initializing database connection...")
        db.initialize()
        logger.info(f"Database initialized at: {db.db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        if db.db:
            logger.info("Closing database connection...")
            db.db.close()
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")