import os
import pytest
from pathlib import Path
from src.database import db

@pytest.fixture(scope="session")
def test_db_path():
    return str(Path(__file__).parent / "test.sqlite")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(test_db_path):
    # Set test database path
    os.environ['TEST_DB_PATH'] = test_db_path
    
    # Initialize database
    db.initialize()
    
    yield db
    
    # Cleanup after all tests
    if db.db:
        db.db.close()
        try:
            os.remove(test_db_path)
        except FileNotFoundError:
            pass

@pytest.fixture(autouse=True)
def clear_tables():
    # Clear tables before each test - delete tasks first due to foreign key constraint
    db.db.executescript("""
        DELETE FROM tasks;
        DELETE FROM reports;
    """)
    db.db.commit()

@pytest.fixture
def sample_report():
    report_id = db.create_report(
        name="Test Report",
        created_by="test_user",
        template="<h1>Test Template</h1>",
        recipients=["test@example.com"]
    )
    return report_id
