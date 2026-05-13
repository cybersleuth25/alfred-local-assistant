import os
import sys
import sqlite3
import pytest
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Mock ollama module before importing memory_engine
sys.modules['ollama'] = MagicMock()

import memory_engine

@pytest.fixture(autouse=True)
def setup_db():
    # Use a temporary database file for tests
    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_fd)

    # Mock the DB path
    with patch.object(memory_engine, 'DB_PATH', temp_path):
        memory_engine.init_db()
        yield

    # Cleanup
    try:
        os.remove(temp_path)
    except OSError:
        pass


def test_add_and_get_pending_tasks():
    # Initially empty
    assert len(memory_engine.get_pending_tasks()) == 0

    # Add a task
    memory_engine.add_task("Buy groceries")
    pending = memory_engine.get_pending_tasks()

    assert len(pending) == 1
    assert pending[0]["task"] == "Buy groceries"
    assert pending[0]["deadline"] is None


def test_get_due_tasks():
    # Past deadline
    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    memory_engine.add_task("Past due task", deadline=past_date)

    # Future deadline
    future_date = (datetime.now() + timedelta(days=1)).isoformat()
    memory_engine.add_task("Future task", deadline=future_date)

    # No deadline
    memory_engine.add_task("No deadline task")

    due_tasks = memory_engine.get_due_tasks()
    assert len(due_tasks) == 1
    assert due_tasks[0]["task"] == "Past due task"


def test_complete_and_delete_task():
    memory_engine.add_task("To be completed")
    pending = memory_engine.get_pending_tasks()
    assert len(pending) == 1
    task_id = pending[0]["id"]

    # Complete task
    memory_engine.complete_task(task_id)
    assert len(memory_engine.get_pending_tasks()) == 0

    # Task should still exist in db but not pending
    conn = sqlite3.connect(memory_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None

    # Delete task
    memory_engine.delete_task(task_id)
    conn = sqlite3.connect(memory_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is None


def test_clear_all_tasks():
    memory_engine.add_task("Task 1")
    memory_engine.add_task("Task 2")
    assert len(memory_engine.get_pending_tasks()) == 2

    memory_engine.clear_all_tasks()
    assert len(memory_engine.get_pending_tasks()) == 0

    conn = sqlite3.connect(memory_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 0


def test_user_facts():
    assert len(memory_engine.get_user_facts()) == 0

    memory_engine.add_user_fact("User likes coffee")
    memory_engine.add_user_fact("User is learning Python")

    facts = memory_engine.get_user_facts()
    assert len(facts) == 2
    assert facts[0]["fact"] == "User likes coffee"
    assert facts[1]["fact"] == "User is learning Python"

    fact_id = facts[0]["id"]
    memory_engine.delete_user_fact(fact_id)

    facts = memory_engine.get_user_facts()
    assert len(facts) == 1
    assert facts[0]["fact"] == "User is learning Python"


def test_get_or_create_user():
    # Setup initially creates user 1 via init_db logic for Telegram ID

    # Create new user
    user_id_1 = memory_engine.get_or_create_user("12345", "Alice")
    assert user_id_1 > 0

    # Getting same user should return same ID
    user_id_1_again = memory_engine.get_or_create_user("12345", "Alice2")
    assert user_id_1 == user_id_1_again

    # Getting another user should return new ID
    user_id_2 = memory_engine.get_or_create_user("67890", "Bob")
    assert user_id_2 > 0
    assert user_id_2 != user_id_1


def test_log_system_event():
    # Write a log
    memory_engine.log_system_event("INFO", "Test log message")

    # Read directly from DB to verify
    conn = sqlite3.connect(memory_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_logs")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][1] == "INFO"
    assert rows[0][2] == "Test log message"


def test_conversation_history():
    assert len(memory_engine.load_recent_history()) == 0

    # Empty string should not be saved
    memory_engine.save_conversation_turn("user", "   ")
    assert len(memory_engine.load_recent_history()) == 0

    # Save a few turns
    memory_engine.save_conversation_turn("user", "Hello")
    memory_engine.save_conversation_turn("assistant", "Hi there!")
    memory_engine.save_conversation_turn("user", "How are you?")

    history = memory_engine.load_recent_history(n=2)
    assert len(history) == 2
    assert history[0]["role"] == "assistant"
    assert history[0]["content"] == "Hi there!"
    assert history[1]["role"] == "user"
    assert history[1]["content"] == "How are you?"

    history_all = memory_engine.load_recent_history()
    assert len(history_all) == 3
    assert history_all[0]["role"] == "user"
    assert history_all[0]["content"] == "Hello"


def test_clear_old_history():
    # Insert multiple records
    for i in range(10):
        memory_engine.save_conversation_turn("user", f"Message {i}")

    assert len(memory_engine.load_recent_history(n=20)) == 10

    memory_engine.clear_old_history(keep_last=5)

    history = memory_engine.load_recent_history(n=20)
    assert len(history) == 5
    # Should keep the most recent 5 (messages 5, 6, 7, 8, 9)
    assert history[0]["content"] == "Message 5"
    assert history[-1]["content"] == "Message 9"


@patch('memory_engine._generate_embedding')
def test_semantic_memory_storage(mock_embed):
    # Mock embedding function to return a deterministic vector
    mock_embed.return_value = [0.1, 0.2, 0.3]

    # Initially 0
    assert memory_engine.get_memory_count() == 0

    # Too short
    assert not memory_engine.store_memory("short")

    # Empty embedding (simulate error)
    mock_embed.return_value = []
    assert not memory_engine.store_memory("this is a longer string that should pass length check")

    # Store successfully
    mock_embed.return_value = [0.1, 0.2, 0.3]
    assert memory_engine.store_memory("User likes to code in Python", "preference")

    assert memory_engine.get_memory_count() == 1

    # Deduplication test (using same mock response)
    # search_memories will be mocked since we test just storage deduplication check
    # But wait, search_memories calls _generate_embedding itself.
    # Let's ensure deduplication blocks it by making search_memories return a high similarity match
    with patch('memory_engine.search_memories') as mock_search:
        mock_search.return_value = [{"similarity": 0.95}]
        assert not memory_engine.store_memory("User likes to code in Python", "preference")

    # Should still be 1
    assert memory_engine.get_memory_count() == 1


@patch('memory_engine._generate_embedding')
def test_semantic_memory_retrieval(mock_embed):
    # Prepare mock embedding mappings
    def mock_embed_side_effect(text):
        if "Python" in text:
            return [1.0, 0.0, 0.0]
        elif "Coffee" in text:
            return [0.0, 1.0, 0.0]
        elif "Java" in text:
            # Somewhat similar to Python
            return [0.8, 0.2, 0.0]
        else:
            return [0.0, 0.0, 1.0]

    mock_embed.side_effect = mock_embed_side_effect

    # Reset index and memory
    memory_engine._faiss_index = None # Disable FAISS for test to test raw fallback or test both
    memory_engine.FAISS_AVAILABLE = False

    # Store some memories (Mock generate embedding returns lists, which store_memory json.dumps)
    memory_engine.store_memory("User likes to code in Python", "preference")
    memory_engine.store_memory("User drinks Coffee every morning", "habit")

    recent = memory_engine.get_recent_memories(n=5)
    assert len(recent) == 2
    assert recent[0]["content"] == "User drinks Coffee every morning" # Newest first

    # Search for Python, should match Python memory closely
    results = memory_engine.search_memories("Python is a great language")
    assert len(results) == 1
    assert results[0]["content"] == "User likes to code in Python"

    # Search for Coffee, should match Coffee memory closely
    results = memory_engine.search_memories("I need Coffee")
    assert len(results) == 1
    assert results[0]["content"] == "User drinks Coffee every morning"
