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
- Tabbed interface for Reports, Tasks, and Settings management
- Centralized data storage in user's home directory
- Integrated logging system

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
│   │   ├── preload.js     # Preload script for IPC
│   │   └── renderer.js    # UI interaction logic
│   ├── main/             # Python backend files
│   │   └── api.py        # FastAPI server
│   └── static/           # Static frontend files
│       └── index.html    # Main application UI
├── scripts/
│   ├── start.sh          # Development startup script
│   └── build.sh          # Production build script
├── package.json          # Node.js dependencies and scripts
└── poetry.lock          # Python dependencies lock file
```

## Application Data

The application stores all data in the user's home directory:
```
~/ReportManager/
    ├── database.sqlite    # SQLite database
    └── logs/             # Application logs
        ├── app.log       # Electron app logs
        └── api_*.log     # API server logs
```

## Setup

1.Install Node.js dependencies:

```bash
npm install
```

2.Install Python dependencies using Poetry:

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
- Features a tabbed interface for different functionalities

## Features

### Reports Management

- Create, read, update, and delete reports
- Custom report templates
- Report scheduling

### Tasks Management

- Create and manage scheduled tasks
- Task status monitoring
- Task execution history

### Settings

- View application data locations
- System information
- Configuration options

## API Endpoints

- `GET /api/reports`: List all reports
- `POST /api/reports`: Create a new report
- `GET /api/reports/{id}`: Get report details
- `PUT /api/reports/{id}`: Update a report
- `DELETE /api/reports/{id}`: Delete a report
- `GET /api/tasks`: List all tasks
- `POST /api/tasks`: Create a new task
- `GET /api/tasks/{id}`: Get task details
- `PUT /api/tasks/{id}`: Update a task
- `DELETE /api/tasks/{id}`: Delete a task

## Troubleshooting

### Common Issues

1. Port 8000 already in use:
   - You can manually kill the process: `lsof -ti:8000 | xargs kill -9`

2. Server Connection Issues:
   - Check the logs in `~/ReportManager/logs/`
   - Verify the Python server is running using the system task manager

### Development Tips

1. Logs can be found in:
   - Development: `~/ReportManager/logs/`
   - Production: Same location as development

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.