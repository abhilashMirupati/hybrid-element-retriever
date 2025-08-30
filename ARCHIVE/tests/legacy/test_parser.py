"""Tests for intent parser."""

import pytest
from her.parser.intent import Intent, IntentParser, parse_intent


class TestIntentParser:
    """Test intent parsing functionality."""

    def test_init(self):
        """Test parser initialization."""
        parser = IntentParser()
        assert len(parser.action_patterns) > 0

    def test_parse_click_actions(self):
        """Test parsing click actions."""
        parser = IntentParser()

        # Various click patterns
        test_cases = [
            ("Click the submit button", "click", "the submit button"),
            ("click on login link", "click", "login link"),
            ("Press the enter key", "click", "the enter key"),
            ("Tap on the menu icon", "click", "the menu icon"),
            ("Select the home button", "click", "the home"),
        ]

        for step, expected_action, expected_target in test_cases:
            intent = parser.parse(step)
            assert intent.action == expected_action
            assert expected_target in intent.target_phrase.lower()

    def test_parse_type_actions(self):
        """Test parsing type/fill actions."""
        parser = IntentParser()

        # Type with quoted text
        intent = parser.parse("Type 'hello world' into the search box")
        assert intent.action == "type"
        assert intent.args == "hello world"
        assert "search box" in intent.target_phrase

        # Enter variant
        intent = parser.parse("Enter 'test@example.com' in email field")
        assert intent.action == "type"
        assert intent.args == "test@example.com"
        assert "email field" in intent.target_phrase

        # Fill variant
        intent = parser.parse("Fill username field with 'john.doe'")
        assert intent.action == "type"
        assert intent.args == "john.doe"
        assert "username field" in intent.target_phrase

        # Type without explicit target
        intent = parser.parse("Type 'password123'")
        assert intent.action == "type"
        # Should try to infer or use whole phrase as target

    def test_parse_select_actions(self):
        """Test parsing select actions."""
        parser = IntentParser()

        intent = parser.parse("Select 'United States' from country dropdown")
        assert intent.action == "select"
        assert intent.args == "United States"
        assert "country dropdown" in intent.target_phrase

        intent = parser.parse("Choose 'Option A' in the list")
        assert intent.action == "select"
        assert intent.args == "Option A"

        intent = parser.parse("Pick 'Blue' from color selector")
        assert intent.action == "select"
        assert intent.args == "Blue"

    def test_parse_hover_actions(self):
        """Test parsing hover actions."""
        parser = IntentParser()

        intent = parser.parse("Hover over the menu")
        assert intent.action == "hover"
        assert "menu" in intent.target_phrase

        intent = parser.parse("Mouse over profile picture")
        assert intent.action == "hover"
        assert "profile picture" in intent.target_phrase

        intent = parser.parse("Move to settings icon")
        assert intent.action == "hover"
        assert "settings icon" in intent.target_phrase

    def test_parse_wait_actions(self):
        """Test parsing wait actions."""
        parser = IntentParser()

        # Wait for element
        intent = parser.parse("Wait for loading spinner")
        assert intent.action == "wait"
        assert "loading spinner" in intent.target_phrase

        # Wait until visible
        intent = parser.parse("Wait until submit button is visible")
        assert intent.action == "wait"
        assert "submit button" in intent.target_phrase
        assert intent.constraints["type"] == "visible"

        # Wait time
        intent = parser.parse("Wait 5 seconds")
        assert intent.action == "wait"
        assert intent.args == "5"
        assert intent.constraints["type"] == "time"

        intent = parser.parse("Pause for 3 secs")
        assert intent.action == "wait"
        assert intent.args == "3"

    def test_parse_navigation_actions(self):
        """Test parsing navigation actions."""
        parser = IntentParser()

        intent = parser.parse("Go to homepage")
        assert intent.action == "navigate"
        assert "homepage" in intent.target_phrase

        intent = parser.parse("Navigate to settings page")
        assert intent.action == "navigate"
        assert "settings page" in intent.target_phrase

        intent = parser.parse("Open dashboard")
        assert intent.action == "navigate"
        assert "dashboard" in intent.target_phrase

        intent = parser.parse("Refresh the page")
        assert intent.action == "refresh"

        intent = parser.parse("Go back")
        assert intent.action == "back"

    def test_parse_assertion_actions(self):
        """Test parsing assertion actions."""
        parser = IntentParser()

        intent = parser.parse("Verify error message is visible")
        assert intent.action == "assert"
        assert "error message" in intent.target_phrase
        assert intent.constraints["type"] == "visible"

        intent = parser.parse("Check that success banner exists")
        assert intent.action == "assert"
        assert "success banner" in intent.target_phrase
        assert intent.constraints["type"] == "exists"

        intent = parser.parse("Assert page loaded")
        assert intent.action == "assert"
        assert "page loaded" in intent.target_phrase

    def test_parse_clear_action(self):
        """Test parsing clear action."""
        parser = IntentParser()

        intent = parser.parse("Clear the input field")
        assert intent.action == "clear"
        assert "input field" in intent.target_phrase

    def test_parse_submit_action(self):
        """Test parsing submit action."""
        parser = IntentParser()

        intent = parser.parse("Submit the form")
        assert intent.action == "submit"
        assert "form" in intent.target_phrase

    def test_infer_intent_fallback(self):
        """Test intent inference for unmatched patterns."""
        parser = IntentParser()

        # Should infer from keywords
        intent = parser.parse("Please click somewhere on the page")
        assert intent.action == "click"

        intent = parser.parse("I want to type something")
        assert intent.action == "type"

        # Default to click if no keywords
        intent = parser.parse("Do something with the button")
        assert intent.action == "click"
        assert intent.confidence < 0.7  # Lower confidence for inferred

    def test_parse_batch(self):
        """Test batch parsing."""
        parser = IntentParser()

        steps = [
            "Click login",
            "Type 'user@example.com' into email",
            "Type 'password' into password field",
            "Click submit",
        ]

        intents = parser.parse_batch(steps)
        assert len(intents) == 4
        assert intents[0].action == "click"
        assert intents[1].action == "type"
        assert intents[1].args == "user@example.com"
        assert intents[3].action == "click"

    def test_explain_intent(self):
        """Test intent explanation generation."""
        parser = IntentParser()

        intent = Intent(action="click", target_phrase="submit button")
        explanation = parser.explain_intent(intent)
        assert "Click" in explanation
        assert "submit button" in explanation

        intent = Intent(
            action="type", target_phrase="email field", args="test@example.com"
        )
        explanation = parser.explain_intent(intent)
        assert "Type" in explanation
        assert "test@example.com" in explanation
        assert "email field" in explanation

        intent = Intent(
            action="wait", target_phrase="", args="5", constraints={"type": "time"}
        )
        explanation = parser.explain_intent(intent)
        assert "Wait" in explanation
        assert "5 seconds" in explanation

        # Low confidence warning
        intent = Intent(action="click", target_phrase="something", confidence=0.5)
        explanation = parser.explain_intent(intent)
        assert "low confidence" in explanation

    def test_backwards_compatibility(self):
        """Test backwards compatibility with original parse_intent function."""
        # Original function should still work
        intent = parse_intent("Click the button")
        assert isinstance(intent, Intent)
        assert intent.action == "click"
        assert "button" in intent.target_phrase
