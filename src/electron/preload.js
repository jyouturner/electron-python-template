// src/electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Reports API
    listReports: () => ipcRenderer.invoke('list-reports'),
    createReport: (report) => ipcRenderer.invoke('create-report', report),
    getReport: (id) => ipcRenderer.invoke('get-report', id),
    updateReport: (id, report) => ipcRenderer.invoke('update-report', id, report),
    deleteReport: (id) => ipcRenderer.invoke('delete-report', id),
    
    // Tasks API
    listTasks: () => ipcRenderer.invoke('list-tasks'),
    createTask: (task) => ipcRenderer.invoke('create-task', task),
    getTask: (id) => ipcRenderer.invoke('get-task', id),
    updateTask: (id, task) => ipcRenderer.invoke('update-task', id, task),
    deleteTask: (id) => ipcRenderer.invoke('delete-task', id),
    
    // Keep existing WebSocket functionality
    // ... (keep existing WebSocket code)
    
    // Add this line
    getDatabasePath: () => ipcRenderer.invoke('get-database-path'),
    
    // Add this method
    getAppPaths: () => ipcRenderer.invoke('get-app-paths'),
});