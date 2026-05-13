from voice_engine import _sanitize_for_tts

def test_sanitize_degree_symbols():
    # Test standalone degree
    assert _sanitize_for_tts("It is 20° outside.") == "It is 20 degrees outside."
    # Test Celsius
    assert _sanitize_for_tts("Temperature is 30°C") == "Temperature is 30 degrees Celsius"
    # Test Fahrenheit
    assert _sanitize_for_tts("Water boils at 212°F") == "Water boils at 212 degrees Fahrenheit"

def test_sanitize_garbled_utf8():
    # Test garbled degree
    assert _sanitize_for_tts("The temp is 25Â°") == "The temp is 25 degrees"
    # Test garbled arrow (â -> →, but note → is stripped later by ascii encoding)
    # The string "Go â there" becomes "Go → there" which becomes "Go  there" -> "Go there"
    assert _sanitize_for_tts("Go â there") == "Go there"

def test_sanitize_non_ascii():
    # Test emojis
    assert _sanitize_for_tts("Hello 🌍! 😊") == "Hello !"
    # Test weird unicode quotes or dashes
    assert _sanitize_for_tts("This is a “quote” — indeed") == "This is a quote indeed"

def test_sanitize_whitespace():
    # Test multiple spaces, tabs, and newlines
    assert _sanitize_for_tts("This   has\ttoo \n much \r\n whitespace") == "This has too much whitespace"
    # Test stripping leading and trailing whitespace
    assert _sanitize_for_tts("  Trim me  ") == "Trim me"

def test_sanitize_normal_text():
    assert _sanitize_for_tts("Hello world.") == "Hello world."
    assert _sanitize_for_tts("Just normal text 123!") == "Just normal text 123!"
