import os
import pytest
import sqlite3
from datetime import datetime

# We will need to set the DB_PATH to a temporary in-memory database or a test file
# to avoid modifying the real DB.
import memory_engine

@pytest.fixture
def test_db_path(tmp_path):
    test_db = tmp_path / "test_alfred_memory.db"

    # Store original DB path
    original_db_path = memory_engine.DB_PATH

    # Override DB path for testing
    memory_engine.DB_PATH = str(test_db)

    # Initialize the test database
    memory_engine.init_db()

    yield str(test_db)

    # Restore original DB path
    memory_engine.DB_PATH = original_db_path

def test_complete_task_success(test_db_path):
    # First, add a task
    memory_engine.add_task("Test task to complete")

    # Verify it is in the database as not completed
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    # Complete the task
    memory_engine.complete_task(task_id)

    # Verify the task is no longer pending
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 0

    # Verify the task is completed in the database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 1

def test_complete_task_nonexistent(test_db_path):
    # Add a task to ensure it isn't affected
    memory_engine.add_task("Existing task")
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    existing_id = tasks[0]["id"]

    # Complete a non-existent task
    nonexistent_id = 9999
    memory_engine.complete_task(nonexistent_id)

    # Verify the existing task is still pending
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == existing_id

    # Verify nothing was added
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 1

def test_complete_task_already_completed(test_db_path):
    # Add a task
    memory_engine.add_task("Task to double-complete")
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    # Complete it once
    memory_engine.complete_task(task_id)

    # Complete it again
    memory_engine.complete_task(task_id)

    # Verify it is still completed
    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 0

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 1
