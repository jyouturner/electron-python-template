import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import threading

class Database:
    _lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        with self._lock:
            try:
                yield self.db
            except Exception as e:
                self.db.rollback()
                raise
            else:
                self.db.commit()

    def __init__(self):
        self.db = None
        self.db_path = None

    def log(self, message):
        if os.getenv('ENVIRONMENT') != 'test':
            print(message)

    def initialize(self):
        try:
            data_dir = os.getenv('TEST_DB_PATH') or os.path.join(os.getcwd(), 'data', 'database.sqlite')
            os.makedirs(os.path.dirname(data_dir), exist_ok=True)
            
            self.db_path = data_dir
            self.db = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.db.row_factory = sqlite3.Row
            
            print(f"Database initialized successfully at: {self.db_path}")
            self._create_tables()
            return True
        except Exception as error:
            print(f"Error initializing database: {error}")
            raise

    def check_connection(self):
        if not self.db:
            raise Exception("Database not initialized")
        
        try:
            self.db.execute("SELECT 1").fetchone()
            return True
        except Exception as error:
            print(f"Database connection check failed: {error}")
            raise 

    # Database Info Methods
    def get_database_info(self):
        if not self.db:
            raise Exception("Database not initialized")

        try:
            cursor = self.db.execute("""
                SELECT name, sql 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            stats = os.stat(self.db_path)
            
            return {
                'path': self.db_path,
                'size': stats.st_size,
                'tables': [t['name'] for t in tables],
                'last_modified': datetime.fromtimestamp(stats.st_mtime)
            }
        except Exception as error:
            print(f"Failed to get database info: {error}")
            raise

    # Report CRUD Operations
    def create_report(self, name, created_by, meta=None, template='', recipients=None):
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO reports 
                   (name, created_by, meta, template, recipients, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                [name, created_by, json.dumps(meta or {}), 
                 template, json.dumps(recipients or [])]
            )
            return cursor.lastrowid

    def get_report(self, id):
        try:
            cursor = self.db.execute('SELECT * FROM reports WHERE id = ?', [id])
            report = cursor.fetchone()
            if report:
                # Convert JSON strings back to Python objects
                report = dict(report)
                report['meta'] = json.loads(report['meta']) if report['meta'] else {}
                report['recipients'] = json.loads(report['recipients']) if report['recipients'] else []
            return report
        except Exception as error:
            print(f"Error getting report: {error}")
            raise

    def update_report(self, report_id, updates):
        try:
            with self.get_connection() as conn:
                # Convert lists and dicts to JSON strings
                if 'recipients' in updates:
                    updates['recipients'] = json.dumps(updates['recipients'])
                if 'meta' in updates:
                    updates['meta'] = json.dumps(updates['meta'])
                    
                set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values())
                
                cursor = conn.execute(
                    f"""UPDATE reports 
                        SET {set_clause}, updated_at = datetime('now')
                        WHERE id = ?""",
                    [*values, report_id]
                )
                return cursor.rowcount > 0
        except Exception as error:
            print(f"Error updating report: {error}")
            raise

    def duplicate_report(self, id):
        try:
            original = self.get_report(id)
            if not original:
                return None

            copy = {
                'name': f"{original['name']} (Copy)",
                'created_by': original['created_by'],
                'meta': original['meta'],
                'template': original['template'],
                'recipients': original['recipients']
            }

            return self.create_report(**copy)
        except Exception as error:
            print(f"Error duplicating report: {error}")
            raise

    # Task Operations
    def create_task(self, name, type, report_id=None, schedule=None, is_active=1, meta=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO tasks 
                       (name, type, report_id, schedule, is_active, meta, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                    [name, type, report_id, schedule, is_active, 
                     json.dumps(meta) if meta else '{}']
                )
                return cursor.lastrowid
        except Exception as error:
            print(f"Error creating task: {error}")
            raise

    def get_task(self, task_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM tasks WHERE id = ?', 
                    [task_id]
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert row to dictionary
                task = dict(zip([col[0] for col in cursor.description], row))
                
                # Parse JSON fields
                task['meta'] = json.loads(task['meta']) if task['meta'] else {}
                return task
        except Exception as error:
            print(f"Error getting task: {error}")
            raise

    def get_tasks_by_report_id(self, report_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM tasks WHERE report_id = ? AND is_active = 1', 
                    [report_id]
                )
                tasks = []
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    task = dict(zip(columns, row))
                    task['meta'] = json.loads(task['meta']) if task['meta'] else {}
                    tasks.append(task)
                return tasks
        except Exception as error:
            print(f"Error getting tasks by report ID: {error}")
            raise

    def update_task(self, task_id, updates):
        try:
            with self.get_connection() as conn:
                # Convert any JSON fields
                if 'meta' in updates:
                    updates['meta'] = json.dumps(updates['meta'])
                    
                set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values())
                
                cursor = conn.execute(
                    f"""UPDATE tasks 
                        SET {set_clause}, updated_at = datetime('now')
                        WHERE id = ?""",
                    [*values, task_id]
                )
                return cursor.rowcount > 0
        except Exception as error:
            print(f"Error updating task: {error}")
            raise

    def delete_task(self, task_id):
        try:
            with self.get_connection() as conn:
                # Soft delete by deactivating
                cursor = conn.execute(
                    'UPDATE tasks SET is_active = 0 WHERE id = ?',
                    [task_id]
                )
                return cursor.rowcount > 0
        except Exception as error:
            print(f"Error deleting task: {error}")
            raise

    def get_tasks_for_scheduling(self):
        try:
            cursor = self.db.execute("""
                SELECT * FROM tasks 
                WHERE is_active = 1 
                AND schedule IS NOT NULL
            """)
            return cursor.fetchall()
        except Exception as error:
            print(f"Error getting tasks for scheduling: {error}")
            raise

    def deactivate_task(self, id):
        try:
            cursor = self.db.execute(
                'UPDATE tasks SET is_active = 0 WHERE id = ?', 
                [id]
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as error:
            print(f"Error deactivating task: {error}")
            raise

    # List Operations
    def list_reports(self):
        try:
            cursor = self.db.execute(
                'SELECT * FROM reports ORDER BY created_at DESC, id DESC'
            )
            reports = cursor.fetchall()
            return [dict(report) for report in reports]
        except Exception as error:
            print(f"Error listing reports: {error}")
            raise

    def get_task_by_report_id(self, report_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM tasks WHERE report_id = ? AND is_active = 1', 
                    [report_id]
                )
                row = cursor.fetchone()
                if row:
                    task = dict(row)
                    # Parse JSON fields
                    task['meta'] = json.loads(task['meta']) if task['meta'] else {}
                    return task
                return None
        except Exception as error:
            print(f"Error getting task by report ID: {error}")
            raise

    # Delete Operations
    def delete_report(self, id):
        try:
            with self.get_connection() as conn:
                # First, deactivate any associated tasks
                conn.execute('UPDATE tasks SET is_active = 0 WHERE report_id = ?', [id])
                # Then delete the report
                cursor = conn.execute('DELETE FROM reports WHERE id = ?', [id])
                return cursor.rowcount > 0
        except Exception as error:
            print(f"Error deleting report: {error}")
            raise

    def _create_tables(self):
        """Create the necessary database tables if they don't exist"""
        try:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    meta TEXT,
                    template TEXT,
                    recipients TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    report_id INTEGER,
                    schedule TEXT,
                    is_active INTEGER DEFAULT 1,
                    meta TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_run_at TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES reports(id)
                );
            """)
            self.db.commit()
            return True
        except Exception as error:
            print(f"Error creating tables: {error}")
            raise