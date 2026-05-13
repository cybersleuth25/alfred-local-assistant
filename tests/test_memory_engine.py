import pytest
import sqlite3
import os
import sys
from unittest import mock

# Ensure memory_engine can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import memory_engine

@pytest.fixture
def test_db(tmp_path):
    """Fixture to provide a temporary database path and override DB_PATH."""
    db_file = tmp_path / "test_alfred_memory.db"

    # Store original path
    original_db_path = memory_engine.DB_PATH

    # Override path with temporary database
    memory_engine.DB_PATH = str(db_file)

    # Initialize the tables in the new temporary database
    memory_engine.init_db()

    yield str(db_file)

    # Restore original path
    memory_engine.DB_PATH = original_db_path

def test_get_pending_tasks_empty(test_db):
    """Test getting pending tasks when none exist."""
    tasks = memory_engine.get_pending_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) == 0

def test_get_pending_tasks_with_tasks(test_db):
    """Test getting pending tasks returns only uncompleted ones."""
    # Add some tasks
    memory_engine.add_task("Test task 1")
    memory_engine.add_task("Test task 2", deadline="2025-12-31T23:59:59")

    # Complete the first task to ensure it's not returned
    # But wait, we need to know its ID. We can fetch all pending, then complete one
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 2

    # Complete the first one
    memory_engine.complete_task(tasks[0]["id"])

    # Fetch again, should only be 1
    tasks_after = memory_engine.get_pending_tasks()
    assert len(tasks_after) == 1
    assert tasks_after[0]["task"] == "Test task 2"
    assert tasks_after[0]["deadline"] == "2025-12-31T23:59:59"
