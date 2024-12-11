import pytest
from fastapi.testclient import TestClient
from src.main.api import app
from src.database import db
import os
from pathlib import Path

client = TestClient(app)

@pytest.fixture(scope="session")
def test_db():
    """Create a test database"""
    test_db_path = str(Path(__file__).parent / "test.sqlite")
    os.environ['TEST_DB_PATH'] = test_db_path
    db.initialize()
    yield db
    
    # Cleanup
    if db.db:
        db.db.close()
        try:
            os.remove(test_db_path)
        except FileNotFoundError:
            pass

@pytest.fixture(autouse=True)
def clear_tables(test_db):
    """Clear tables before each test"""
    with test_db.db:  # Use context manager for transactions
        test_db.db.executescript("""
            DELETE FROM tasks;
            DELETE FROM reports;
        """)

@pytest.fixture
def sample_report(test_db):
    """Create a sample report for testing"""
    report_data = {
        "name": "Test Report",
        "created_by": "test_user",
        "template": "<h1>Test Template</h1>",
        "recipients": ["test@example.com"],
        "meta": {"key": "value"}
    }
    response = client.post("/api/reports", json=report_data)
    assert response.status_code == 200
    return response.json()["id"]

@pytest.fixture
def sample_task(sample_report):
    """Create a sample task for testing"""
    task_data = {
        "name": "Test Task",
        "type": "report",
        "report_id": sample_report,
        "schedule": "*/5 * * * *",
        "meta": {"key": "value"}
    }
    response = client.post("/api/tasks", json=task_data)
    assert response.status_code == 200
    return response.json()["id"]

class TestHealthCheck:
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

class TestReportEndpoints:
    def test_create_report(self):
        report_data = {
            "name": "New Report",
            "created_by": "test_user",
            "template": "<h1>Template</h1>",
            "recipients": ["user@example.com"]
        }
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_report(self, sample_report):
        response = client.get(f"/api/reports/{sample_report}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Report"
        assert data["created_by"] == "test_user"

    def test_list_reports(self, sample_report):
        response = client.get("/api/reports")
        assert response.status_code == 200
        reports = response.json()
        assert len(reports) == 1
        assert reports[0]["id"] == sample_report

    def test_update_report(self, sample_report):
        update_data = {
            "name": "Updated Report",
            "recipients": ["new@example.com"]
        }
        response = client.put(f"/api/reports/{sample_report}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = client.get(f"/api/reports/{sample_report}")
        data = response.json()
        assert data["name"] == "Updated Report"
        assert data["recipients"] == ["new@example.com"]

    def test_delete_report(self, sample_report):
        response = client.delete(f"/api/reports/{sample_report}")
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(f"/api/reports/{sample_report}")
        assert response.status_code == 404

    def test_duplicate_report(self, sample_report):
        response = client.post(f"/api/reports/{sample_report}/duplicate")
        assert response.status_code == 200
        new_id = response.json()["id"]
        
        # Verify duplication
        response = client.get(f"/api/reports/{new_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Report (Copy)"

class TestTaskEndpoints:
    def test_create_task(self, sample_report):
        task_data = {
            "name": "New Task",
            "type": "report",
            "report_id": sample_report,
            "schedule": "*/10 * * * *"
        }
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_task(self, sample_task):
        response = client.get(f"/api/tasks/{sample_task}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["type"] == "report"

    def test_update_task(self, sample_task):
        update_data = {
            "name": "Updated Task",
            "schedule": "*/15 * * * *"
        }
        response = client.put(f"/api/tasks/{sample_task}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = client.get(f"/api/tasks/{sample_task}")
        data = response.json()
        assert data["name"] == "Updated Task"
        assert data["schedule"] == "*/15 * * * *"

    def test_delete_task(self, sample_task):
        response = client.delete(f"/api/tasks/{sample_task}")
        assert response.status_code == 200
        
        # Verify deletion (should be deactivated, not deleted)
        response = client.get(f"/api/tasks/{sample_task}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == 0

    def test_get_report_tasks(self, sample_report, sample_task):
        response = client.get(f"/api/reports/{sample_report}/tasks")
        assert response.status_code == 200
        data = response.json()
        # Since we're getting a list of tasks, we need to find our task in the list
        assert len(data) > 0
        task = next((t for t in data if t["id"] == sample_task), None)
        assert task is not None
        assert task["id"] == sample_task

class TestErrorHandling:
    def test_invalid_report_id(self):
        response = client.get("/api/reports/999")
        assert response.status_code == 404

    def test_invalid_task_id(self):
        response = client.get("/api/tasks/999")
        assert response.status_code == 404

    def test_invalid_report_data(self):
        response = client.post("/api/reports", json={})
        assert response.status_code == 422  # FastAPI validation error

    def test_invalid_task_data(self):
        response = client.post("/api/tasks", json={})
        assert response.status_code == 422  # FastAPI validation error