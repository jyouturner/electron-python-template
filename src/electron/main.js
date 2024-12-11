const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Add this near the top to define isDev
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// Define app name and data directory
const APP_NAME = 'ReportManager';
const APP_DIR = path.join(os.homedir(), APP_NAME);

// Ensure app directory exists
if (!fs.existsSync(APP_DIR)) {
    fs.mkdirSync(APP_DIR, { recursive: true });
}

// Set up paths for different data types
const paths = {
    database: path.join(APP_DIR, 'database.sqlite'),
    logs: path.join(APP_DIR, 'logs'),
};

// Ensure logs directory exists
if (!fs.existsSync(paths.logs)) {
    fs.mkdirSync(paths.logs, { recursive: true });
}

// Set up logging
function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `${timestamp}: ${message}\n`;
    const logFile = path.join(paths.logs, 'app.log');
    fs.appendFileSync(logFile, logMessage);
    console.log(message);
}

// Function to get app paths
function getAppPaths() {
    return {
        root: APP_DIR,
        database: paths.database,
        logs: paths.logs
    };
}

// Add IPC handlers for paths
ipcMain.handle('get-app-paths', () => {
    return getAppPaths();
});

let pythonProcess = null;
let mainWindow = null;
let isStartingUp = false;

// Add this function to get the database directory
function getDatabasePath() {
    const userDataPath = app.getPath('userData');
    return path.join(userDataPath, 'database.db');
}

// Optional: Add an IPC handler to expose the path to the renderer
ipcMain.handle('get-database-path', () => {
    return getDatabasePath();
});

async function startPythonServer() {
    if (isDev) {
        // In development mode, just verify the server is running
        // Don't kill it since start.sh manages it
        log('Development mode: checking if Python server is running...');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/health');
            if (response.ok) {
                log('Development server is responding');
                return;
            }
            throw new Error('Development server is not responding');
        } catch (error) {
            log(`Development server check failed: ${error}`);
            throw new Error('Development server is not accessible');
        }
    }

    // Production mode below
    return new Promise((resolve, reject) => {
        try {
            const executablePath = process.platform === 'win32'
                ? path.join(process.resourcesPath, 'api.exe')
                : path.join(process.resourcesPath, 'api');
            
            log(`Production mode: starting Python server from ${executablePath}`);
            
            if (!fs.existsSync(executablePath)) {
                throw new Error(`Python executable not found at ${executablePath}`);
            }

            // Set executable permissions if needed
            if (process.platform !== 'win32') {
                try {
                    fs.chmodSync(executablePath, '755');
                    log('Successfully set executable permissions');
                } catch (error) {
                    log(`Warning: Could not chmod executable: ${error}`);
                }
            }

            log('Spawning Python process...');
            
            // Spawn process with working directory set to Resources
            pythonProcess = spawn(executablePath, [], {
                stdio: ['ignore', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1'
                },
                cwd: process.resourcesPath  // Set working directory to Resources folder
            });

            log(`Python process spawned with PID: ${pythonProcess.pid}`);

            pythonProcess.stdout.on('data', (data) => {
                log(`Server stdout: ${data}`);
                if (data.toString().includes('Application startup complete')) {
                    waitForHealthCheck(resolve, reject);
                }
            });

            pythonProcess.stderr.on('data', (data) => {
                log(`Server stderr: ${data}`);
                // Some servers log to stderr, so check here too
                if (data.toString().includes('Application startup complete')) {
                    waitForHealthCheck(resolve, reject);
                }
            });

            pythonProcess.on('error', (error) => {
                log(`Server process error: ${error}`);
                reject(error);
            });

            pythonProcess.on('close', (code, signal) => {
                log(`Server process closed with code ${code} and signal ${signal}`);
                if (code !== 0) {
                    reject(new Error(`Server process exited with code ${code}`));
                }
            });

            // Add timeout for initial startup
            setTimeout(() => {
                if (!pythonProcess.killed) {
                    log('Server startup timeout reached');
                    reject(new Error('Server startup timeout'));
                }
            }, 15000);

        } catch (error) {
            log(`Error in startPythonServer: ${error}`);
            reject(error);
        }
    });
}

async function waitForHealthCheck(resolve, reject) {
    let attempts = 0;
    const maxAttempts = 10;

    const check = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/health');
            if (response.ok) {
                log('Server health check passed');
                resolve();
                return;
            }
        } catch (error) {
            attempts++;
            if (attempts >= maxAttempts) {
                log(`Server health check failed after ${maxAttempts} attempts`);
                reject(new Error('Server health check failed'));
                return;
            }
            setTimeout(check, 1000);
        }
    };

    check();
}

async function createWindow() {
    if (isStartingUp) {
        log('Startup already in progress, skipping...');
        return;
    }
    
    isStartingUp = true;
    try {
        log('Starting to create window...');
        log('Attempting to start Python server...');
        await startPythonServer();
        
        log('Python server started, verifying health...');
        // Quick verification that server is responding
        try {
            const response = await fetch('http://127.0.0.1:8000/api/health');
            if (!response.ok) {
                throw new Error('Server health check failed');
            }
            log('Server health check passed');
        } catch (error) {
            log(`Server health check failed: ${error}`);
            throw error;
        }
        
        log('Creating browser window...');
        mainWindow = new BrowserWindow({
            width: 800,
            height: 600,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });

        log('Loading HTML file...');
        mainWindow.loadFile(path.join(__dirname, '../static/index.html'));
        
        if (isDev) {
            mainWindow.webContents.openDevTools();
        }

        mainWindow.on('closed', () => {
            mainWindow = null;
        });

        log('Window created successfully');
    } catch (error) {
        log(`Error creating window: ${error}`);
        if (pythonProcess) {
            pythonProcess.kill();
        }
        app.quit();
    } finally {
        isStartingUp = false;
    }
}


function cleanup() {
    if (pythonProcess) {
        log('Cleaning up Python process...');
        pythonProcess.kill();
        pythonProcess = null;
    }
}


// Handle IPC calls
ipcMain.handle('quick-task', async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/quick-task', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Quick task error:', error);
        throw error;
    }
});

ipcMain.handle('start-long-task', async (event, taskId) => {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/start-long-task/${taskId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Start long task error:', error);
        throw error;
    }
});

// Reports API handlers
ipcMain.handle('list-reports', async () => {
    const response = await fetch('http://127.0.0.1:8000/api/reports');
    return await response.json();
});

ipcMain.handle('create-report', async (event, report) => {
    const response = await fetch('http://127.0.0.1:8000/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
    });
    return await response.json();
});

ipcMain.handle('get-report', async (event, id) => {
    const response = await fetch(`http://127.0.0.1:8000/api/reports/${id}`);
    return await response.json();
});

ipcMain.handle('update-report', async (event, id, report) => {
    const response = await fetch(`http://127.0.0.1:8000/api/reports/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
    });
    return await response.json();
});

ipcMain.handle('delete-report', async (event, id) => {
    const response = await fetch(`http://127.0.0.1:8000/api/reports/${id}`, {
        method: 'DELETE'
    });
    return await response.json();
});

// Tasks API handlers
ipcMain.handle('list-tasks', async () => {
    const response = await fetch('http://127.0.0.1:8000/api/tasks');
    return await response.json();
});

ipcMain.handle('create-task', async (event, task) => {
    const response = await fetch('http://127.0.0.1:8000/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task)
    });
    return await response.json();
});

ipcMain.handle('get-task', async (event, id) => {
    const response = await fetch(`http://127.0.0.1:8000/api/tasks/${id}`);
    return await response.json();
});

ipcMain.handle('update-task', async (event, id, task) => {
    const response = await fetch(`http://127.0.0.1:8000/api/tasks/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task)
    });
    return await response.json();
});

ipcMain.handle('delete-task', async (event, id) => {
    const response = await fetch(`http://127.0.0.1:8000/api/tasks/${id}`, {
        method: 'DELETE'
    });
    return await response.json();
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    cleanup();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null && !isStartingUp) {
        createWindow();
    }
});

app.on('before-quit', cleanup);