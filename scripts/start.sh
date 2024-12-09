#!/bin/bash
# scripts/start.sh

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Move to project root
cd "$PROJECT_ROOT"

echo "Starting Python server from $PROJECT_ROOT..."

# Kill any existing Python processes using port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Get the Poetry virtual environment path
VENV_PATH=$(poetry env info --path)
if [ -z "$VENV_PATH" ]; then
    echo "Poetry virtual environment not found"
    exit 1
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Export PYTHONPATH to include our project root and site-packages
export PYTHONPATH="$PROJECT_ROOT:$VENV_PATH/lib/python3.11/site-packages:$PYTHONPATH"

# Start Python server using uvicorn directly
echo "Starting FastAPI server..."
python -m uvicorn src.main.api:app --host 127.0.0.1 --port 8000 &
PYTHON_PID=$!

# Wait for Python server to start
echo "Waiting for server to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/docs >/dev/null; then
        echo "FastAPI server is running on http://localhost:8000"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "Server failed to start"
        kill $PYTHON_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start electron
echo "Starting Electron..."
if [ -f "./node_modules/.bin/electron" ]; then
    ./node_modules/.bin/electron .
else
    npx electron .
fi

# Cleanup
echo "Shutting down..."
kill $PYTHON_PID 2>/dev/null
deactivate