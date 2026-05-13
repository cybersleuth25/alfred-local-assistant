import os
import sqlite3
import pytest
import sys

# Patch DB_PATH BEFORE memory_engine is imported so the module-level
# _init_faiss and init_db see the correct test path.

@pytest.fixture(scope="session", autouse=True)
def mock_db_path(tmp_path_factory):
    # Setup temporary database
    db_path = tmp_path_factory.mktemp("data") / "test_alfred_memory.db"

    # Pre-emptively create the DB and the tables so `import memory_engine` doesn't crash
    # when it calls _init_faiss() -> "SELECT id, embedding FROM semantic_memories"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semantic_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Now let's trick memory_engine into using this path
    # We can create a dummy module or patch os.path.join temporarily
    import os.path
    original_join = os.path.join

    def mock_join(*args, **kwargs):
        if len(args) == 2 and args[1] == "alfred_memory.db":
            return str(db_path)
        return original_join(*args, **kwargs)

    os.path.join = mock_join

    import memory_engine

    # Restore original join
    os.path.join = original_join

    # Verify DB_PATH was correctly patched
    assert memory_engine.DB_PATH == str(db_path)

    yield

    if db_path.exists():
        os.remove(db_path)

@pytest.fixture(autouse=True)
def clean_db():
    # Before each test, clear the tasks table
    import memory_engine
    conn = memory_engine._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()

def test_delete_task_success():
    """Test that delete_task successfully removes an existing task."""
    from memory_engine import add_task, get_pending_tasks, delete_task

    add_task("Test task to delete")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    delete_task(task_id)

    tasks_after = get_pending_tasks()
    assert len(tasks_after) == 0

def test_delete_task_nonexistent():
    """Test that delete_task handles non-existent task IDs without error and leaves other tasks intact."""
    from memory_engine import add_task, get_pending_tasks, delete_task

    add_task("Test task to keep")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    task_id = tasks[0]["id"]

    # Try deleting a non-existent task (e.g. ID + 999)
    delete_task(task_id + 999)

    # Ensure the original task is still there
    tasks_after = get_pending_tasks()
    assert len(tasks_after) == 1
    assert tasks_after[0]["id"] == task_id
