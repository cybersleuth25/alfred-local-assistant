import pytest
import os
import sqlite3
import datetime

import memory_engine

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    # Setup temporary database
    db_file = tmp_path / "test_memory.db"

    # Patch DB path and let pytest restore it automatically
    monkeypatch.setattr(memory_engine, "DB_PATH", str(db_file))

    # Initialize schema
    memory_engine.init_db()

    yield str(db_file)

def test_add_task_without_deadline(temp_db):
    memory_engine.add_task("Buy groceries")

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Buy groceries"
    assert tasks[0]["deadline"] is None

def test_add_task_with_deadline(temp_db):
    deadline = "2024-12-31T23:59:59"
    memory_engine.add_task("Submit taxes", deadline=deadline)

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task"] == "Submit taxes"
    assert tasks[0]["deadline"] == deadline

def test_add_task_multiple(temp_db):
    memory_engine.add_task("Task 1")
    memory_engine.add_task("Task 2")
    memory_engine.add_task("Task 3")

    tasks = memory_engine.get_pending_tasks()
    assert len(tasks) == 3
    task_names = [t["task"] for t in tasks]
    assert "Task 1" in task_names
    assert "Task 2" in task_names
    assert "Task 3" in task_names
