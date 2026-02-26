import pytest
from unittest.mock import patch
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
            logs.append((logging.INFO, msg % args if args else msg))
        def error(self, msg, *args):
            logs.append((logging.ERROR, msg % args if args else msg))
    monkeypatch.setattr(logging, "getLogger", lambda name=None: DummyLogger())
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    return logs

def test_successful_fetch_all_users(patch_logging):
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

def test_api_unreachable_scenario(patch_logging):
    with patch.object(UserService, "get_all_users", side_effect=Exception("API unreachable")):
        logs = patch_logging
        try:
            main()
        except Exception:
            pass
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

def test_internal_error_in_user_service(patch_logging):
    with patch.object(UserService, "get_all_users", side_effect=RuntimeError("Internal error")):
        logs = patch_logging
        try:
            main()
        except RuntimeError:
            pass
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("Internal error" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_invalid_json(patch_logging):
    import json
    with patch.object(UserService, "get_all_users", side_effect=json.JSONDecodeError("Expecting value", "", 0)):
        logs = patch_logging
        try:
            main()
        except json.JSONDecodeError:
            pass
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("JSON parsing failure" in msg for _, msg in logs) or any("Expecting value" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_script_imported_as_module(monkeypatch):
    with patch("src.main.__name__", "not_main"):
        with patch.object(UserService, "get_all_users") as mock_get:
            import importlib
            importlib.reload(__import__("src.main"))
            assert not mock_get.called

def test_api_returns_large_number_of_users(patch_logging):
    users = [make_user(id=i, name=f"User{i}") for i in range(1, 1001)]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("Fetched 1000 users." in msg for _, msg in logs)
        user_logs = [msg for _, msg in logs if msg.startswith("User:")]
        assert len(user_logs) == 1000
        assert any("id=1, name=User1" in msg for msg in user_logs)
        assert any("id=1000, name=User1000" in msg for msg in user_logs)

def test_api_returns_users_with_missing_or_null_fields(patch_logging):
    user1 = make_user(id=1, name="Partial", email="", phone="", website="")
    user2 = make_user(id=2, name="MissingEmail", email=None)
    users = [user1, user2]
    with patch.object(UserService, "get_all_users", return_value=users):
        logs = patch_logging
        main()
        assert any("id=1, name=Partial" in msg for _, msg in logs)
        assert any("id=2, name=MissingEmail" in msg for _, msg in logs)

def test_api_returns_http_error(patch_logging):
    import requests
    with patch.object(UserService, "get_all_users", side_effect=requests.HTTPError("500 Internal Server Error")):
        logs = patch_logging
        try:
            main()
        except requests.HTTPError:
            pass
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("HTTP error" in msg for _, msg in logs) or any("500" in msg for _, msg in logs)
        assert not any("Fetched" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)

def test_api_returns_valid_json_not_list(patch_logging):
    with patch.object(UserService, "get_all_users", return_value={"foo": "bar"}):
        logs = patch_logging
        main()
        assert any("Starting user data fetch" in msg for _, msg in logs)
        assert any("unexpected response format" in msg for _, msg in logs) or any("not a list" in msg for _, msg in logs)
        assert not any("User:" in msg for _, msg in logs)