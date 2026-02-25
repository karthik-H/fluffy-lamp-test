import pytest
from unittest.mock import patch, MagicMock
import logging

from src.main import main
from src.services.user_service import UserService
from src.domain.models import User, Address, Company

# Helper to create a User object
def make_user(
    id=1, name="Test User", username="testuser", email="test@example.com",
    phone="123-456-7890", website="example.com",
    address=None, company=None
):
    if address is None:
        address = Address(
            street="123 Main St", suite="Apt 1", city="Testville", zipcode="12345",
            geo={"lat": "0", "lng": "0"}
        )
    if company is None:
        company = Company(
            name="TestCorp", catchPhrase="Testing!", bs="test-bs"
        )
    return User(
        id=id, name=name, username=username, email=email,
        phone=phone, website=website, address=address, company=company
    )

@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    logs = []
    class DummyLogger:
        def info(self, msg, *args):
            logs.append(("INFO", msg % args if args else msg))
        def error(self, msg, *args):
            logs.append(("ERROR", msg % args if args else msg))
        def warning(self, msg, *args):
            logs.append(("WARNING", msg % args if args else msg))
        def debug(self, msg, *args):
            logs.append(("DEBUG", msg % args if args else msg))
    monkeypatch.setattr(logging, "getLogger", lambda name=None: DummyLogger())
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    return logs

def test_successful_fetch_of_all_users(patch_logging):
    users = [
        make_user(id=1, name="Alice"),
        make_user(id=2, name="Bob"),
    ]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Fetched 2 users." in msg for _, msg in logs)
        assert any("User: id=1, name=Alice" in msg for _, msg in logs)
        assert any("User: id=2, name=Bob" in msg for _, msg in logs)

def test_api_unreachable(patch_logging):
    with patch.object(UserService, "get_all_users", side_effect=Exception("API unreachable")):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("API unreachable" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_empty_user_list(patch_logging):
    with patch.object(UserService, "get_all_users", return_value=[]):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Fetched 0 users." in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_invalid_json(patch_logging):
    import json
    with patch.object(UserService, "get_all_users", side_effect=json.JSONDecodeError("Expecting value", "", 0)):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Expecting value" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_partial_user_data(patch_logging):
    user1 = make_user(id=1, name="Partial", email="", phone="", website="")
    user2 = make_user(id=2, name="MissingEmail", email=None)
    users = [user1, user2]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Fetched 2 users." in msg for _, msg in logs)
        assert any("id=1, name=Partial" in msg for _, msg in logs)
        assert any("id=2, name=MissingEmail" in msg for _, msg in logs)

def test_api_returns_non_list_response(patch_logging):
    # Simulate get_all_users returning a dict instead of a list
    with patch.object(UserService, "get_all_users", return_value={"error": "unexpected"}):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Unexpected response type" in msg or "error" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_run_as_imported_module(monkeypatch):
    # Patch __name__ to not be "__main__"
    with patch("src.main.__name__", "not_main"):
        with patch.object(UserService, "get_all_users") as mock_get:
            import importlib
            importlib.reload(__import__("src.main"))
            assert not mock_get.called

def test_logging_initialization(monkeypatch):
    # Ensure logging.basicConfig is called at the start of main()
    called = {}
    def fake_basicConfig(**kwargs):
        called["called"] = True
        called["kwargs"] = kwargs
    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    with patch.object(UserService, "get_all_users", return_value=[]):
        main()
    assert called.get("called", False)

def test_api_slow_response_timeout(patch_logging):
    import requests
    with patch.object(UserService, "get_all_users", side_effect=requests.Timeout("Timeout")):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Timeout" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_duplicate_users(patch_logging):
    users = [
        make_user(id=1, name="Alice"),
        make_user(id=1, name="Alice"),
        make_user(id=2, name="Bob"),
    ]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Fetched 3 users." in msg for _, msg in logs)
        user_logs = [msg for _, msg in logs if msg.startswith("User:")]
        assert len(user_logs) == 3
        assert user_logs.count("User: id=1, name=Alice") == 2
        assert any("User: id=2, name=Bob" in msg for msg in user_logs)