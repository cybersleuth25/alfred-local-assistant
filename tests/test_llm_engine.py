import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Setup mocks before importing the module under test
# We use patch.dict on sys.modules to safely mock dependencies during import
@pytest.fixture(autouse=True, scope="module")
def setup_mocks():
    with patch.dict(sys.modules, {
        'ollama': MagicMock(),
        'memory_engine': MagicMock(),
        'tools': MagicMock(),
        'tools.core_tools': MagicMock(),
        'shared': MagicMock(),
        'dotenv': MagicMock()
    }):
        # This ensures that when llm_engine is imported, it uses the mocked modules
        import llm_engine
        yield llm_engine

def test_get_time_of_day_morning(setup_mocks):
    llm_engine = setup_mocks
    with patch('llm_engine.datetime') as mock_datetime:
        # Morning is 5 <= hour < 12
        # Boundary: 5:00 AM
        mock_datetime.now.return_value = datetime(2023, 1, 1, 5, 0)
        assert llm_engine._get_time_of_day() == "morning"

        # Boundary: 11:59 AM
        mock_datetime.now.return_value = datetime(2023, 1, 1, 11, 59)
        assert llm_engine._get_time_of_day() == "morning"

def test_get_time_of_day_afternoon(setup_mocks):
    llm_engine = setup_mocks
    with patch('llm_engine.datetime') as mock_datetime:
        # Afternoon is 12 <= hour < 17
        # Boundary: 12:00 PM
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0)
        assert llm_engine._get_time_of_day() == "afternoon"

        # Boundary: 4:59 PM (16:59)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 16, 59)
        assert llm_engine._get_time_of_day() == "afternoon"

def test_get_time_of_day_evening(setup_mocks):
    llm_engine = setup_mocks
    with patch('llm_engine.datetime') as mock_datetime:
        # Evening is 17 <= hour < 21
        # Boundary: 5:00 PM (17:00)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 17, 0)
        assert llm_engine._get_time_of_day() == "evening"

        # Boundary: 8:59 PM (20:59)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 20, 59)
        assert llm_engine._get_time_of_day() == "evening"

def test_get_time_of_day_night(setup_mocks):
    llm_engine = setup_mocks
    with patch('llm_engine.datetime') as mock_datetime:
        # Night is everything else (21:00 - 4:59)
        # Boundary: 9:00 PM (21:00)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 21, 0)
        assert llm_engine._get_time_of_day() == "night"

        # Boundary: 12:00 AM (0:00)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0)
        assert llm_engine._get_time_of_day() == "night"

        # Boundary: 4:59 AM (4:59)
        mock_datetime.now.return_value = datetime(2023, 1, 1, 4, 59)
        assert llm_engine._get_time_of_day() == "night"

def test_get_time_of_day_transitions(setup_mocks):
    llm_engine = setup_mocks
    with patch('llm_engine.datetime') as mock_datetime:
        # Transition night -> morning
        mock_datetime.now.return_value = datetime(2023, 1, 1, 4, 59)
        assert llm_engine._get_time_of_day() == "night"
        mock_datetime.now.return_value = datetime(2023, 1, 1, 5, 0)
        assert llm_engine._get_time_of_day() == "morning"

        # Transition morning -> afternoon
        mock_datetime.now.return_value = datetime(2023, 1, 1, 11, 59)
        assert llm_engine._get_time_of_day() == "morning"
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0)
        assert llm_engine._get_time_of_day() == "afternoon"

        # Transition afternoon -> evening
        mock_datetime.now.return_value = datetime(2023, 1, 1, 16, 59)
        assert llm_engine._get_time_of_day() == "afternoon"
        mock_datetime.now.return_value = datetime(2023, 1, 1, 17, 0)
        assert llm_engine._get_time_of_day() == "evening"

        # Transition evening -> night
        mock_datetime.now.return_value = datetime(2023, 1, 1, 20, 59)
        assert llm_engine._get_time_of_day() == "evening"
        mock_datetime.now.return_value = datetime(2023, 1, 1, 21, 0)
        assert llm_engine._get_time_of_day() == "night"
