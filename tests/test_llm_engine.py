import sys
from unittest.mock import MagicMock

# Mock required modules before importing llm_engine to prevent side effects
sys.modules['ollama'] = MagicMock()
sys.modules['memory_engine'] = MagicMock()
sys.modules['shared'] = MagicMock()
sys.modules['tools'] = MagicMock()
core_tools_mock = MagicMock()
core_tools_mock.TOOL_REGISTRY = {}
sys.modules['tools.core_tools'] = core_tools_mock

from llm_engine import _needs_tools

def test_needs_tools_with_tool_keywords():
    # Happy paths: prompts containing keywords that should trigger tool usage
    assert _needs_tools("what is the weather like today?") is True
    assert _needs_tools("can you set a reminder for me?") is True
    assert _needs_tools("please play some spotify music") is True
    assert _needs_tools("can you launch the browser?") is True
    assert _needs_tools("open a new file") is True
    assert _needs_tools("check the battery status") is True

def test_needs_tools_negative_cases():
    # Negative cases: conversational prompts that should not trigger tools
    assert _needs_tools("hello, how are you today?") is False
    assert _needs_tools("what a beautiful morning") is False
    assert _needs_tools("I am feeling great") is False
    assert _needs_tools("thank you very much") is False
    assert _needs_tools("who are you?") is False

def test_needs_tools_case_insensitivity():
    # Ensure tool detection is case-insensitive
    assert _needs_tools("WHAT IS THE WEATHER?") is True
    assert _needs_tools("pLaY SoMe MuSiC") is True
    assert _needs_tools("REMIND me to call mom") is True

def test_needs_tools_edge_cases():
    # Edge cases
    assert _needs_tools("") is False
    assert _needs_tools("   ") is False

    # Check substring matches (current behavior: "notable" matches "note")
    # This documents the current behavior, though we might want to fix it later
    # "note" is in tool_signals.
    assert _needs_tools("this is a notable achievement") is True
