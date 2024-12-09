// src/electron/renderer.js
document.addEventListener('DOMContentLoaded', () => {
    const quickTaskBtn = document.getElementById('quickTaskBtn');
    const longTaskBtn = document.getElementById('longTaskBtn');
    const outputDiv = document.getElementById('output');
    
    function appendOutput(message) {
        const p = document.createElement('p');
        p.textContent = typeof message === 'object' ? JSON.stringify(message) : message;
        outputDiv.appendChild(p);
        outputDiv.scrollTop = outputDiv.scrollHeight;
        console.log(message);
    }

    quickTaskBtn.addEventListener('click', async () => {
        appendOutput('Starting quick task...');
        try {
            const result = await window.electronAPI.quickTask();
            appendOutput(`Quick task result: ${JSON.stringify(result)}`);
        } catch (error) {
            appendOutput(`Error in quick task: ${error.message}`);
        }
    });

    longTaskBtn.addEventListener('click', async () => {
        const taskId = Date.now().toString();
        appendOutput('Starting long task...');
        
        try {
            const result = await window.electronAPI.startLongTask(taskId);
            appendOutput(`Task started: ${JSON.stringify(result)}`);
            
            // Create WebSocket connection first
            appendOutput('Establishing WebSocket connection...');
            const ws = window.electronAPI.connectWebSocket(
                (data) => {
                    appendOutput(`Progress: ${JSON.stringify(data)}`);
                    if (data.progress === 100) {
                        appendOutput('Task completed, closing WebSocket');
                        ws.close();
                    }
                },
                (error) => {
                    appendOutput(`WebSocket error: ${error.message}`);
                }
            );
            
            // Start the task (the connection will handle when to actually send)
            appendOutput('Queuing task to start...');
            ws.startTask(taskId);
            
        } catch (error) {
            appendOutput(`Error: ${error.message}`);
        }
    });
});