// src/electron/renderer.js
document.addEventListener('DOMContentLoaded', () => {
    // Add this function near the top
    function updateInfoMessage(message) {
        document.getElementById('infoMessage').textContent = message;
    }

    // Tab switching functionality
    const tabs = document.querySelectorAll('.tab-button');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab-button').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const contentId = tab.getAttribute('data-tab');
            document.getElementById(contentId).classList.add('active');
            updateInfoMessage(`Viewing ${contentId} section`);
        });
    });

    // State management
    let currentReportId = null;
    let currentTaskId = null;

    // Load initial data
    loadReports();
    loadTasks();

    // Load settings information
    async function loadSettings() {
        try {
            const paths = await window.electronAPI.getAppPaths();
            document.getElementById('appRoot').textContent = paths.root;
            document.getElementById('dbLocation').textContent = paths.database;
            document.getElementById('logsLocation').textContent = paths.logs;
        } catch (error) {
            console.error('Error loading settings:', error);
            document.getElementById('appRoot').textContent = 'Error loading paths';
            document.getElementById('dbLocation').textContent = 'Error loading paths';
            document.getElementById('logsLocation').textContent = 'Error loading paths';
        }
    }

    // Load settings on startup
    loadSettings();

    // Reports functionality
    async function loadReports() {
        try {
            updateInfoMessage('Loading reports...');
            const reports = await window.electronAPI.listReports();
            const tbody = document.querySelector('#reportsTable tbody');
            tbody.innerHTML = '';
            
            reports.forEach(report => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${report.id}</td>
                    <td>${report.name}</td>
                    <td>${report.created_by}</td>
                    <td>
                        <button class="edit-report" data-id="${report.id}">Edit</button>
                        <button class="delete-report" data-id="${report.id}">Delete</button>
                    </td>
                `;
            });
            updateInfoMessage(`Loaded ${reports.length} reports`);
        } catch (error) {
            console.error('Error loading reports:', error);
            updateInfoMessage('Error loading reports');
        }
    }

    // Event delegation for edit and delete buttons
    document.querySelector('#reportsTable tbody').addEventListener('click', async (e) => {
        const reportId = e.target.dataset.id;
        
        if (e.target.classList.contains('edit-report')) {
            await editReport(reportId);
        } else if (e.target.classList.contains('delete-report')) {
            await deleteReport(reportId);
        }
    });

    // Edit report function
    async function editReport(reportId) {
        try {
            updateInfoMessage('Loading report details...');
            const report = await window.electronAPI.getReport(reportId);
            currentReportId = reportId;
            
            // Populate form with report data
            document.getElementById('reportName').value = report.name;
            document.getElementById('reportCreatedBy').value = report.created_by;
            document.getElementById('reportTemplate').value = report.template || '';
            document.getElementById('reportRecipients').value = report.recipients?.join(', ') || '';
            
            // Show the form
            document.getElementById('reportForm').style.display = 'block';
            updateInfoMessage(`Editing report: ${report.name}`);
        } catch (error) {
            console.error('Error editing report:', error);
            updateInfoMessage('Error loading report details');
        }
    }

    // Delete report function
    async function deleteReport(reportId) {
        if (confirm('Are you sure you want to delete this report?')) {
            try {
                await window.electronAPI.deleteReport(reportId);
                loadReports();
            } catch (error) {
                console.error('Error deleting report:', error);
            }
        }
    }

    // Add event listeners for report form
    document.getElementById('newReportBtn').addEventListener('click', () => {
        // Clear form
        document.getElementById('reportName').value = '';
        document.getElementById('reportCreatedBy').value = '';
        document.getElementById('reportTemplate').value = '';
        document.getElementById('reportRecipients').value = '';
        
        // Reset current report ID and show form
        currentReportId = null;
        document.getElementById('reportForm').style.display = 'block';
    });

    document.getElementById('saveReportBtn').addEventListener('click', async () => {
        try {
            updateInfoMessage('Saving report...');
            const reportData = {
                name: document.getElementById('reportName').value,
                created_by: document.getElementById('reportCreatedBy').value,
                template: document.getElementById('reportTemplate').value,
                recipients: document.getElementById('reportRecipients').value.split(',').map(r => r.trim())
            };

            if (currentReportId) {
                await window.electronAPI.updateReport(currentReportId, reportData);
                updateInfoMessage('Report updated successfully');
            } else {
                await window.electronAPI.createReport(reportData);
                updateInfoMessage('New report created successfully');
            }
            document.getElementById('reportForm').style.display = 'none';
            loadReports();
        } catch (error) {
            console.error('Error saving report:', error);
            updateInfoMessage('Error saving report');
        }
    });

    // Add cancel button handler
    document.getElementById('cancelReportBtn').addEventListener('click', () => {
        document.getElementById('reportForm').style.display = 'none';
    });

    // Tasks functionality
    async function loadTasks() {
        try {
            updateInfoMessage('Loading tasks...');
            const tasks = await window.electronAPI.listTasks();
            const tbody = document.querySelector('#tasksTable tbody');
            tbody.innerHTML = '';
            
            tasks.forEach(task => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${task.id}</td>
                    <td>${task.name}</td>
                    <td>${task.type}</td>
                    <td>${task.schedule || ''}</td>
                    <td>
                        <button class="edit-task" data-id="${task.id}">Edit</button>
                        <button class="delete-task" data-id="${task.id}">Delete</button>
                    </td>
                `;
            });
            updateInfoMessage(`Loaded ${tasks.length} tasks`);
        } catch (error) {
            console.error('Error loading tasks:', error);
            updateInfoMessage('Error loading tasks');
        }
    }

    // Event delegation for task buttons
    document.querySelector('#tasksTable tbody').addEventListener('click', async (e) => {
        const taskId = e.target.dataset.id;
        
        if (e.target.classList.contains('edit-task')) {
            await editTask(taskId);
        } else if (e.target.classList.contains('delete-task')) {
            await deleteTask(taskId);
        }
    });

    // Edit task function
    async function editTask(taskId) {
        try {
            const task = await window.electronAPI.getTask(taskId);
            currentTaskId = taskId;
            
            // Populate form with task data
            document.getElementById('taskName').value = task.name;
            document.getElementById('taskType').value = task.type;
            document.getElementById('taskSchedule').value = task.schedule || '';
            document.getElementById('taskReportId').value = task.report_id || '';
            
            // Show the form
            document.getElementById('taskForm').style.display = 'block';
        } catch (error) {
            console.error('Error editing task:', error);
        }
    }

    // Delete task function
    async function deleteTask(taskId) {
        if (confirm('Are you sure you want to delete this task?')) {
            try {
                await window.electronAPI.deleteTask(taskId);
                loadTasks();
            } catch (error) {
                console.error('Error deleting task:', error);
            }
        }
    }

    // Task form event listeners
    document.getElementById('newTaskBtn').addEventListener('click', () => {
        // Clear form
        document.getElementById('taskName').value = '';
        document.getElementById('taskType').value = '';
        document.getElementById('taskSchedule').value = '';
        document.getElementById('taskReportId').value = '';
        
        // Reset current task ID and show form
        currentTaskId = null;
        document.getElementById('taskForm').style.display = 'block';
    });

    document.getElementById('saveTaskBtn').addEventListener('click', async () => {
        const taskData = {
            name: document.getElementById('taskName').value,
            type: document.getElementById('taskType').value,
            schedule: document.getElementById('taskSchedule').value,
            report_id: document.getElementById('taskReportId').value
        };

        try {
            if (currentTaskId) {
                await window.electronAPI.updateTask(currentTaskId, taskData);
            } else {
                await window.electronAPI.createTask(taskData);
            }
            document.getElementById('taskForm').style.display = 'none';
            loadTasks();
        } catch (error) {
            console.error('Error saving task:', error);
        }
    });

    // Add cancel button handler
    document.getElementById('cancelTaskBtn').addEventListener('click', () => {
        document.getElementById('taskForm').style.display = 'none';
    });

    // Example: Add a button or menu item to show database location
    async function showDatabaseLocation() {
        const dbPath = await window.electronAPI.getDatabasePath();
        alert(`Database location: ${dbPath}`);
    }
});