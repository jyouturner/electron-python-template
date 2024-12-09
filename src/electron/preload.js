// src/electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    quickTask: () => ipcRenderer.invoke('quick-task'),
    
    startLongTask: (taskId) => ipcRenderer.invoke('start-long-task', taskId),
    
    connectWebSocket: (onMessage, onError) => {
        const ws = new WebSocket('ws://127.0.0.1:8000/ws');
        let taskToStart = null;
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            // If we have a pending task, send it now
            if (taskToStart) {
                ws.send(JSON.stringify({ type: 'start_task', task_id: taskToStart }));
                taskToStart = null;
            }
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (error) {
                onError(error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            onError(error);
        };
        
        return {
            startTask: (taskId) => {
                if (ws.readyState === WebSocket.OPEN) {
                    // If connection is open, send immediately
                    ws.send(JSON.stringify({ type: 'start_task', task_id: taskId }));
                } else {
                    // Otherwise, store the task to send when connection opens
                    taskToStart = taskId;
                }
            },
            close: () => ws.close()
        };
    }
});