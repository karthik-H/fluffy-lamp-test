import pytest
from unittest.mock import patch, MagicMock, call
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
    # Patch logging to capture logs for assertions
    logs = []
    class DummyLogger:
        def info(self, msg, *args):
            logs.append((logging.INFO, msg % args if args else msg))
        def error(self, msg, *args):
            logs.append((logging.ERROR, msg % args if args else msg))
    monkeypatch.setattr(logging, "getLogger", lambda name=None: DummyLogger())
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    return logs

def test_fetch_all_users_success(patch_logging):
    users = [
        make_user(id=1, name="Alice"),
        make_user(id=2, name="Bob"),
    ]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        # Check start log
        assert any("Starting user data fetch" in msg for _, msg in logs)
        # Check fetched count
        assert any("Fetched 2 users." in msg for _, msg in logs)
        # Check user summaries
        assert any("User: id=1, name=Alice" in msg for _, msg in logs)
        assert any("User: id=2, name=Bob" in msg for _, msg in logs)

def test_api_unreachable_error_handling(patch_logging):
    with patch.object(UserService, "get_all_users", side_effect=Exception("API unreachable")):
        logs = patch_logging
        try:
            main()
        except Exception:
            pass
        # Should log start, then error
        assert any("Starting user data fetch" in msg for _, msg in logs)
        # No fetched count or user summaries
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_empty_user_list(patch_logging):
    with patch.object(UserService, "get_all_users", return_value=[]):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Fetched 0 users." in msg for _, msg in logs)
        # No user summaries
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_invalid_json(monkeypatch, patch_logging):
    # Patch UserService.get_all_users to raise JSONDecodeError
    import json
    with patch.object(UserService, "get_all_users", side_effect=json.JSONDecodeError("Expecting value", "", 0)):
        logs = patch_logging
        try:
            main()
        except json.JSONDecodeError:
            pass
        # Should log start, then error
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_unexpected_status_code(monkeypatch, patch_logging):
    # Patch UserService.get_all_users to raise HTTPError
    import requests
    with patch.object(UserService, "get_all_users", side_effect=requests.HTTPError("404 Not Found")):
        logs = patch_logging
        try:
            main()
        except requests.HTTPError:
            pass
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_script_imported_as_module(monkeypatch):
    # Patch __name__ to not be "__main__"
    with patch("src.main.__name__", "not_main"):
        with patch.object(UserService, "get_all_users") as mock_get:
            # Import src.main as module, main() should not be called
            import importlib
            importlib.reload(__import__("src.main"))
            assert not mock_get.called

def test_no_filter_sort_transform(patch_logging):
    users = [
        make_user(id=1, name="First"),
        make_user(id=2, name="Second"),
        make_user(id=3, name="Third"),
    ]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        # Extract logged user names in order
        user_logs = [msg for _, msg in logs if msg.startswith("User:")]
        assert user_logs[0].find("name=First") != -1
        assert user_logs[1].find("name=Second") != -1
        assert user_logs[2].find("name=Third") != -1

def test_large_user_list(patch_logging):
    users = [make_user(id=i, name=f"User{i}") for i in range(1, 1001)]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("Fetched 1000 users." in msg for _, msg in logs)
        user_logs = [msg for _, msg in logs if msg.startswith("User:")]
        assert len(user_logs) == 1000
        # Check a few random users
        assert any("id=1, name=User1" in msg for msg in user_logs)
        assert any("id=1000, name=User1000" in msg for msg in user_logs)

def test_partial_data_in_user(patch_logging):
    # Simulate missing optional fields by passing empty strings
    user1 = make_user(id=1, name="Partial", email="", phone="", website="")
    user2 = make_user(id=2, name="MissingEmail", email=None)
    users = [user1, user2]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        # Should log user summaries without crashing
        assert any("id=1, name=Partial" in msg for _, msg in logs)
        assert any("id=2, name=MissingEmail" in msg for _, msg in logs)