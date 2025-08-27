from her.parser.intent import parse_intent


def test_parse_click() -> None:
    intent = parse_intent("Click the login button")
    assert intent.action == "click"
    assert intent.target_phrase == "the login button"


def test_parse_type() -> None:
    intent = parse_intent("Type 'hello' into the message box")
    assert intent.action == "type"
    assert intent.args == "hello"
    assert "message box" in intent.target_phrase