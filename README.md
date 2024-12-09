# Python Electron App Template

A template for building desktop applications using Electron as the frontend and Python (FastAPI) as the backend. This template demonstrates how to package a Python server with an Electron application into a single distributable.

## Features

- Electron-based desktop application
- Python FastAPI backend server
- WebSocket support for real-time communication
- Automatic server management
- Cross-platform support (macOS, Windows, Linux)
- Development and production environment configurations
- Build system for creating distributable applications

## Prerequisites

- Node.js (v16 or later)
- Python 3.11 or later
- Poetry (Python dependency management)
- npm or yarn

## Project Structure

```
.
├── src/
│   ├── electron/          # Electron application files
│   │   ├── main.js        # Main electron process
│   │   └── preload.js     # Preload script for IPC
│   ├── main/             # Python backend files
│   │   └── api.py        # FastAPI server
│   └── static/           # Static frontend files
├── scripts/
│   ├── start.sh          # Development startup script
│   └── build.sh          # Production build script
├── package.json          # Node.js dependencies and scripts
└── poetry.lock          # Python dependencies lock file
```

## Setup

1. Install Node.js dependencies:
```bash
npm install
```

2. Install Python dependencies using Poetry:
```bash
poetry install
```

## Development

To run the application in development mode:

```bash
npm start
```

This will:
1. Start the Python FastAPI server
2. Launch the Electron application
3. Enable hot-reloading for development

## Building

To create a distributable package:

```bash
npm run build
```

This will:
1. Build the Python backend into a single executable using PyInstaller
2. Package the Electron application with electron-builder
3. Create platform-specific distributables in the `dist` folder

## Architecture

### Backend (Python)

- Uses FastAPI for the REST API and WebSocket support
- Handles both quick tasks and long-running operations
- Implements CORS for development flexibility
- Includes comprehensive logging

### Frontend (Electron)

- Implements secure IPC communication
- Manages Python server lifecycle
- Handles both development and production environments
- Provides WebSocket client implementation

## API Endpoints

- `GET /api/quick-task`: Example endpoint for quick tasks
- `GET /api/start-long-task/{task_id}`: Initiates a long-running task
- `WebSocket /ws`: WebSocket endpoint for real-time updates

## Production Considerations

When building for production:
- The Python server is packaged as a single executable
- The application handles server lifecycle management
- Proper cleanup is implemented for application shutdown
- Error handling and logging are configured for production use

## Troubleshooting

### Common Issues

1. Port 8000 already in use:
   - The application will attempt to kill existing processes on port 8000
   - You can manually kill the process: `lsof -ti:8000 | xargs kill -9`

2. Server Connection Issues:
   - Check the logs in `~/Library/Application Support/python-electron-app/logs/main.log` (macOS)
   - Verify the Python server is running using the system task manager

### Development Tips

1. Logs can be found in:
   - Development: `logs/main.log`
   - Production: 
     - macOS: `~/Library/Application Support/python-electron-app/logs/main.log`
     - Windows: `%APPDATA%\python-electron-app\logs\main.log`

2. To inspect the packaged application:
   - macOS: Right-click the .app and select "Show Package Contents"
   - Windows: Check the installation directory in Program Files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.