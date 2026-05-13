import os
import sys

import pytest

# Ensure memory_engine can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import memory_engine


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Fixture to provide a temporary database path and override DB_PATH."""
    db_file = tmp_path / "test_alfred_memory.db"
    monkeypatch.setattr(memory_engine, "DB_PATH", str(db_file))
    memory_engine.init_db()
    yield str(db_file)


def test_get_pending_tasks_empty(test_db):
    """Test getting pending tasks when none exist."""
    tasks = memory_engine.get_pending_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) == 0


def test_get_pending_tasks_with_tasks(test_db):
    """Test getting pending tasks returns only uncompleted ones."""
    memory_engine.add_task("Test task 1")
    memory_engine.add_task("Test task 2", deadline="2025-12-31T23:59:59")

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 2

    memory_engine.complete_task(tasks[0]["id"])

    tasks_after = memory_engine.get_pending_tasks()
    assert len(tasks_after) == 1
    assert tasks_after[0]["task"] == "Test task 2"
    assert tasks_after[0]["deadline"] == "2025-12-31T23:59:59"


def test_add_task_without_deadline(test_db):
    memory_engine.add_task("Buy groceries")

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Buy groceries"
    assert tasks[0]["deadline"] is None


def test_add_task_with_deadline(test_db):
    deadline = "2024-12-31T23:59:59"
    memory_engine.add_task("Submit taxes", deadline=deadline)

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Submit taxes"
    assert tasks[0]["deadline"] == deadline


def test_add_task_multiple(test_db):
    memory_engine.add_task("Task 1")
    memory_engine.add_task("Task 2")
    memory_engine.add_task("Task 3")

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 3
    task_names = [t["task"] for t in tasks]
    assert "Task 1" in task_names
    assert "Task 2" in task_names
    assert "Task 3" in task_names
