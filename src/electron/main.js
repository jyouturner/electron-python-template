const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fetch = require('node-fetch');
const { spawn } = require('child_process');
const fs = require('fs');

// Set up custom log path
const isDev = !app.isPackaged;
const customLogPath = isDev 
    ? path.join(__dirname, '../../logs') 
    : path.join(app.getPath('userData'), 'logs');
const logFile = path.join(customLogPath, 'main.log');

// Ensure log directory exists
if (!fs.existsSync(customLogPath)) {
    fs.mkdirSync(customLogPath, { recursive: true });
}

function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `${timestamp}: ${message}\n`;
    fs.appendFileSync(logFile, logMessage);
    console.log(message);
}

let pythonProcess = null;
let mainWindow = null;
let isStartingUp = false;

// Helper function to check if port is in use
async function isPortInUse(port) {
    try {
        const response = await fetch(`http://127.0.0.1:${port}/api/quick-task`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Helper function to kill process on port
async function killProcessOnPort(port) {
    return new Promise((resolve, reject) => {
        const command = process.platform === 'win32'
            ? `netstat -ano | findstr :${port}`
            : `lsof -i :${port} -t`;
        
        require('child_process').exec(command, (error, stdout) => {
            if (error) {
                log(`No process found on port ${port}`);
                resolve();
                return;
            }

            const pid = process.platform === 'win32'
                ? stdout.split('\n')[0].split(' ').filter(Boolean).pop()
                : stdout.trim();

            if (pid) {
                const killCommand = process.platform === 'win32'
                    ? `taskkill /F /PID ${pid}`
                    : `kill -9 ${pid}`;

                require('child_process').exec(killCommand, (error) => {
                    if (error) {
                        log(`Error killing process: ${error}`);
                        reject(error);
                    } else {
                        log(`Killed process ${pid} on port ${port}`);
                        resolve();
                    }
                });
            } else {
                resolve();
            }
        });
    });
}

async function startPythonServer() {
    if (isDev) {
        // In development mode, just verify the server is running
        // Don't kill it since start.sh manages it
        log('Development mode: checking if Python server is running...');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/quick-task');
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
            const response = await fetch('http://127.0.0.1:8000/api/quick-task');
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
            const response = await fetch('http://127.0.0.1:8000/api/quick-task');
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