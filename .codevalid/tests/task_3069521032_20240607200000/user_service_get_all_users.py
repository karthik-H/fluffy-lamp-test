import pytest
from unittest.mock import MagicMock
from src.services.user_service import UserService
from src.data.user_repository import UserRepository
from src.domain.models import User, Address, Company

# Helper to create sample user data
def sample_user(id=1, name=None, username=None, email=None, phone=None, website=None, address=None, company=None):
    return User(
        id=id,
        name=name or f"User{id}",
        username=username or f"user{id}",
        email=email or f"user{id}@example.com",
        phone=phone or "123-456-7890",
        website=website or "userwebsite.com",
        address=address or Address(
            street="Street",
            suite="Suite",
            city="City",
            zipcode="12345",
            geo={"lat": "0", "lng": "0"},
        ),
        company=company or Company(
            name="Company",
            catchPhrase="CatchPhrase",
            bs="bs"
        )
    )

@pytest.fixture
def user_repository_mock():
    return MagicMock(spec=UserRepository)

@pytest.fixture
def user_service(user_repository_mock):
    return UserService(user_repository=user_repository_mock)

def test_fetch_all_users_success(user_service, user_repository_mock):
    # Given: API returns 10 users
    users = [sample_user(i) for i in range(1, 11)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 10
    assert all(isinstance(u, User) for u in result)
    assert result == users

def test_api_unreachable_error_handling(user_service, user_repository_mock):
    # Given: API unreachable (simulate network error)
    user_repository_mock.fetch_all_users.side_effect = Exception("API unreachable")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "API unreachable" in str(excinfo.value)

def test_api_returns_http_error(user_service, user_repository_mock):
    # Given: API returns HTTP 500 error (simulate HTTP error)
    user_repository_mock.fetch_all_users.side_effect = Exception("500 Internal Server Error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "500 Internal Server Error" in str(excinfo.value)

def test_api_returns_empty_user_list(user_service, user_repository_mock):
    # Given: API returns empty list
    user_repository_mock.fetch_all_users.return_value = []

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 0

def test_api_returns_malformed_json(user_service, user_repository_mock):
    # Given: API returns malformed JSON (simulate JSON decode error)
    user_repository_mock.fetch_all_users.side_effect = Exception("JSON decode error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "JSON decode error" in str(excinfo.value)

def test_api_returns_large_list_of_users(user_service, user_repository_mock):
    # Given: API returns 10000 users
    users = [sample_user(i) for i in range(1, 10001)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 10000
    assert all(isinstance(u, User) for u in result)
    assert result == users

def test_api_returns_single_user(user_service, user_repository_mock):
    # Given: API returns a single user in a list
    users = [sample_user(1)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == users[0]

def test_api_returns_incomplete_user_data(user_service, user_repository_mock):
    # Given: API returns users with missing fields
    incomplete_user = User(
        id=None,  # missing id
        name=None,  # missing name
        username="userX",
        email="userX@example.com",
        phone="123-456-7890",
        website="userwebsite.com",
        address=None,  # missing address
        company=None   # missing company
    )
    user_repository_mock.fetch_all_users.return_value = [incomplete_user]

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id is None
    assert result[0].name is None
    assert result[0].address is None
    assert result[0].company is None

def test_api_returns_non_array_json_root(user_service, user_repository_mock):
    # Given: API returns a JSON object instead of a list (simulate type error)
    user_repository_mock.fetch_all_users.side_effect = Exception("Unexpected response format: not a list")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "Unexpected response format" in str(excinfo.value)

def test_no_modification_of_fetched_user_data(user_service, user_repository_mock):
    # Given: API returns users in a specific order and with exact values
    users = [
        sample_user(5, name="Alice"),
        sample_user(2, name="Bob"),
        sample_user(9, name="Charlie")
    ]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert result == users
    assert [u.id for u in result] == [5, 2, 9]
    assert [u.name for u in result] == ["Alice", "Bob", "Charlie"]