import pytest
import os
import json
import csv
import logging
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
domain_dir = os.path.join(project_root, 'src', 'domain')
if domain_dir not in sys.path:
    sys.path.insert(0, domain_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from unittest.mock import patch, MagicMock
from src.services.user_service import UserService
from src.main import main

CSV_FILE_PATH = "users.csv"

@pytest.fixture(autouse=True)
def cleanup_csv():
    yield
    if os.path.exists(CSV_FILE_PATH):
        os.remove(CSV_FILE_PATH)

def mock_users(count=10, special_chars=False, missing_fields=False):
    users = []
    for i in range(count):
        user = {
            "id": i + 1,
            "name": f"User {i + 1}" if not special_chars else f"Üser \"{i+1},\nΩ\"",
            "username": f"user{i+1}" if not special_chars else f"user,{i+1}\n",
            "email": f"user{i+1}@example.com" if not special_chars else f"user{i+1}@exämple.com",
            "phone": f"123-456-789{i}" if not special_chars else f"123,456\n789{i}",
            "website": f"website{i+1}.com" if not special_chars else f"websíte{i+1}.com",
            "address": {
                "street": f"Street {i+1}" if not special_chars else f"Stréet \"{i+1},\nΩ\"",
                "city": f"City {i+1}" if not special_chars else f"City,{i+1}\n",
            },
            "company": {
                "name": f"Company {i+1}" if not special_chars else f"Compány \"{i+1},\nΩ\"",
            }
        }
        if missing_fields:
            if i % 2 == 0:
                user.pop("address")
            if i % 3 == 0:
                user.pop("company")
        users.append(user)
    return users

def read_csv_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_logged_messages(caplog):
    return [record.getMessage() for record in caplog.records]

# Test Case 1: Successful API fetch and CSV file write
@patch("src.services.user_service.requests.get")
def test_successful_api_fetch_and_csv_file_write(mock_get, caplog):
    users = mock_users()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    caplog.set_level(logging.INFO)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    assert len(rows) == 10
    expected_columns = ["id", "name", "username", "email", "phone", "website", "address", "company"]
    assert set(rows[0].keys()) == set(expected_columns)
    for row, user in zip(rows, users):
        assert row["id"] == str(user["id"])
        assert row["name"] == user["name"]
        assert row["username"] == user["username"]
        assert row["email"] == user["email"]
        assert row["phone"] == user["phone"]
        assert row["website"] == user["website"]
        assert json.loads(row["address"]) == user["address"]
        assert json.loads(row["company"]) == user["company"]
    messages = get_logged_messages(caplog)
    for user in users:
        assert any(str(user["id"]) in msg and user["name"] in msg for msg in messages)

# Test Case 2: API network failure
@patch("src.services.user_service.requests.get")
def test_api_network_failure(mock_get):
    mock_get.side_effect = Exception("Network error")
    with pytest.raises(SystemExit):
        main()
    assert not os.path.exists(CSV_FILE_PATH)

# Test Case 3: API returns empty list of users
@patch("src.services.user_service.requests.get")
def test_api_returns_empty_list_of_users(mock_get, caplog):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
    caplog.set_level(logging.INFO)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    assert len(rows) == 0
    expected_columns = ["id", "name", "username", "email", "phone", "website", "address", "company"]
    assert set(rows[0].keys()) == set(expected_columns) if rows else True
    messages = get_logged_messages(caplog)
    assert not any("User" in msg for msg in messages)

# Test Case 4: CSV file write permission error
@patch("src.services.user_service.requests.get")
def test_csv_file_write_permission_error(mock_get):
    users = mock_users()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with pytest.raises(SystemExit):
            main()
    assert not os.path.exists(CSV_FILE_PATH)

# Test Case 5: CSV file write fails due to disk full
@patch("src.services.user_service.requests.get")
def test_csv_file_write_fails_due_to_disk_full(mock_get):
    users = mock_users()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    with patch("builtins.open", side_effect=OSError("No space left on device")):
        with pytest.raises(SystemExit):
            main()
    assert not os.path.exists(CSV_FILE_PATH)

# Test Case 6: API returns invalid response format
@patch("src.services.user_service.requests.get")
def test_api_returns_invalid_response_format(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: "not a list")
    with pytest.raises(SystemExit):
        main()
    assert not os.path.exists(CSV_FILE_PATH)

# Test Case 7: User data contains special characters
@patch("src.services.user_service.requests.get")
def test_user_data_contains_special_characters(mock_get):
    users = mock_users(special_chars=True)
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    for row, user in zip(rows, users):
        assert row["name"] == user["name"]
        assert row["username"] == user["username"]
        assert row["email"] == user["email"]
        assert row["phone"] == user["phone"]
        assert row["website"] == user["website"]
        assert json.loads(row["address"]) == user["address"]
        assert json.loads(row["company"]) == user["company"]

# Test Case 8: Logging initialization and user summary
@patch("src.services.user_service.requests.get")
def test_logging_initialization_and_user_summary(mock_get, caplog):
    users = mock_users()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    caplog.set_level(logging.INFO)
    main()
    messages = get_logged_messages(caplog)
    for user in users:
        assert any(str(user["id"]) in msg and user["name"] in msg for msg in messages)
    assert os.path.exists(CSV_FILE_PATH)

# Test Case 9: User object with missing fields
@patch("src.services.user_service.requests.get")
def test_user_object_with_missing_fields(mock_get):
    users = mock_users(missing_fields=True)
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    for row, user in zip(rows, users):
        for field in ["address", "company"]:
            if field in user:
                assert json.loads(row[field]) == user[field]
            else:
                assert row[field] == "" or row[field] is None

# Test Case 10: API returns large number of users
@patch("src.services.user_service.requests.get")
def test_api_returns_large_number_of_users(mock_get):
    users = mock_users(count=1000)
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    assert len(rows) == 1000
    expected_columns = ["id", "name", "username", "email", "phone", "website", "address", "company"]
    assert set(rows[0].keys()) == set(expected_columns)
    for row, user in zip(rows, users):
        assert row["id"] == str(user["id"])
        assert row["name"] == user["name"]

# Test Case 11: No transformation of user data
@patch("src.services.user_service.requests.get")
def test_no_transformation_of_user_data(mock_get):
    users = mock_users()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: users)
    main()
    assert os.path.exists(CSV_FILE_PATH)
    rows = read_csv_rows(CSV_FILE_PATH)
    for row, user in zip(rows, users):
        assert row["name"] == user["name"]
        assert row["username"] == user["username"]
        assert row["email"] == user["email"]
        assert row["phone"] == user["phone"]
        assert row["website"] == user["website"]
        assert json.loads(row["address"]) == user["address"]
        assert json.loads(row["company"]) == user["company"]