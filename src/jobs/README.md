# Jobs Directory

This directory contains all the job scripts that can be scheduled and executed by the application.

## Structure

- `sample_job.py`: Example job showing proper structure and logging
- `utils/`: Shared utilities for jobs
  - `job_utils.py`: Common functions for logging, validation, etc.

## Creating New Jobs

1. Create a new Python file in this directory

2. Follow this template:

```python
import sys
import json
from jobs.utils.job_utils import log_progress, validate_params

def main():
    try:
        # Parse parameters
        params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        
        # Your job logic here
        # Use log_progress() to report progress
        
        # Return results as JSON
        print(json.dumps({"status": "success", "data": your_result}))
        return 0
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Best Practices

1. Always handle parameters via `sys.argv[1]` as JSON
2. Use structured logging with JSON format
3. Report progress using `log_progress()`
4. Handle errors and return appropriate exit codes
5. Return results in JSON format

## Testing Jobs

Test your job from command line:

```bash
python sample_job.py '{"param1": "value1"}'
```
