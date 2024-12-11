import pytest
import json
from src.database import db
import time

class TestReports:
    def test_create_report(self):
        report_id = db.create_report(
            name="Another Report",
            created_by="test_user",
            template="<h1>Template</h1>",
            recipients=["test@example.com"]
        )
        assert report_id > 0

    def test_get_report(self, sample_report):
        report = db.get_report(sample_report)
        assert report is not None
        assert report['name'] == 'Test Report'
        assert report['created_by'] == 'test_user'
        assert report['recipients'] == ['test@example.com']

    def test_update_report(self, sample_report):
        success = db.update_report(sample_report, {
            'name': 'Updated Report'
        })
        assert success is True
        
        report = db.get_report(sample_report)
        assert report is not None
        assert report['name'] == 'Updated Report'

    def test_duplicate_report(self, sample_report):
        new_id = db.duplicate_report(sample_report)
        assert new_id > 0
        
        copy = db.get_report(new_id)
        assert copy is not None
        assert copy['name'] == 'Test Report (Copy)'
        assert copy['created_by'] == 'test_user'
        assert copy['recipients'] == ['test@example.com']

    def test_delete_report(self, sample_report):
        success = db.delete_report(sample_report)
        assert success is True
        
        report = db.get_report(sample_report)
        assert report is None

    def test_list_reports(self, sample_report):
        # Create another report after a small delay
        time.sleep(0.1)  # Add delay to ensure different created_at timestamps
        
        second_report_id = db.create_report(
            name="Second Report",
            created_by="test_user",
            template="<h1>Template 2</h1>",
            recipients=["other@example.com"]
        )

        reports = db.list_reports()
        assert len(reports) == 2
        
        # Get reports by ID to verify they exist
        report_names = {r['name'] for r in reports}
        assert report_names == {'Test Report', 'Second Report'}
        
        # Debug output
        for report in reports:
            print(f"Report ID: {report['id']}, Name: {report['name']}, Created At: {report['created_at']}")
        
        # Verify ordering - newest should be first
        assert reports[0]['id'] == second_report_id

    def test_invalid_report_operations(self):
        # Test invalid report retrieval
        non_existent_report = db.get_report(999)
        assert non_existent_report is None

        # Test invalid report update
        update_result = db.update_report(999, {'name': 'New Name'})
        assert update_result is False

        # Test invalid report deletion
        delete_result = db.delete_report(999)
        assert delete_result is False

        # Test invalid report duplication
        duplicate_result = db.duplicate_report(999)
        assert duplicate_result is None

class TestTasks:
    def test_create_task(self, sample_report):
        task_id = db.create_task(
            name="Test Task",
            type="report",
            report_id=sample_report,
            schedule="*/5 * * * *"
        )
        assert task_id > 0

    def test_get_task(self, sample_report):
        task_id = db.create_task(
            name="Test Task",
            type="report",
            report_id=sample_report
        )
        
        task = db.get_task(task_id)
        assert task is not None
        assert task['name'] == 'Test Task'
        assert task['type'] == 'report'
        assert task['report_id'] == sample_report

    def test_update_task(self, sample_report):
        task_id = db.create_task(
            name="Original Task",
            type="report",
            report_id=sample_report
        )
        
        success = db.update_task(task_id, {
            'name': 'Updated Task',
            'is_active': 0
        })
        assert success is True
        
        task = db.get_task(task_id)
        assert task['name'] == 'Updated Task'
        assert task['is_active'] == 0
