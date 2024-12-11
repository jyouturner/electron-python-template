# src/jobs/sample_job.py
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from src.jobs.utils.job_utils import log_progress

def main():
    try:
        # Get parameters from command line
        params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        
        # Log start
        print(f"Starting job at {datetime.now()}")
        print(f"Received parameters: {params}")
        
        # Simulate work with progress
        total_steps = 5
        for step in range(total_steps):
            time.sleep(1)  # Simulate work
            progress = (step + 1) / total_steps * 100
            log_progress(progress)
            print(f"Completed step {step + 1}/{total_steps}")
        
        # Return results
        result = {
            "status": "success",
            "completed_at": datetime.now().isoformat(),
            "processed_params": params
        }
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())