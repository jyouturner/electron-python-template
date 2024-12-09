# src/jobs/utils/job_utils.py
import json
from datetime import datetime

def log_progress(percentage: float):
    """Log job progress in a structured format."""
    progress_data = {
        "type": "progress",
        "percentage": round(percentage, 2),
        "timestamp": datetime.now().isoformat()
    }
    print(json.dumps(progress_data))

def validate_params(params: dict, required_fields: list) -> bool:
    """Validate that all required parameters are present."""
    return all(field in params for field in required_fields)

def format_result(data: dict) -> dict:
    """Format job result in a consistent structure."""
    return {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }