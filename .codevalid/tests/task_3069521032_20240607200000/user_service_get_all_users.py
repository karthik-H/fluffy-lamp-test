import pytest
from unittest.mock import MagicMock, patch
from src.services.user_service import UserService
from src.data.user_repository import UserRepository
from src.domain.models import User, Address, Company

# Sample user data for mocking
def sample_user(id=1):
    return User(
        id=id,
        name=f"User{id}",
        username=f"user{id}",
        email=f"user{id}@example.com",
        phone="123-456-7890",
        website="userwebsite.com",
        address=Address(
            street="Street",
            suite="Suite",
            city="City",
            zipcode="12345",
            geo={"lat": "0", "lng": "0"},
        ),
        company=Company(
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

def test_fetch_all_users_api_unreachable(user_service, user_repository_mock):
    # Given: API unreachable (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("API unreachable")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "API unreachable" in str(excinfo.value)

def test_fetch_all_users_empty_response(user_service, user_repository_mock):
    # Given: API returns empty list
    user_repository_mock.fetch_all_users.return_value = []

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 0

def test_fetch_all_users_partial_data(user_service, user_repository_mock):
    # Given: API returns 1 user
    users = [sample_user(1)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == users[0]

def test_fetch_all_users_api_returns_error(user_service, user_repository_mock):
    # Given: API returns HTTP error (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("500 Internal Server Error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "500 Internal Server Error" in str(excinfo.value)

def test_fetch_all_users_api_returns_invalid_json(user_service, user_repository_mock):
    # Given: API returns invalid JSON (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("JSON decode error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "JSON decode error" in str(excinfo.value)

def test_fetch_all_users_data_not_transformed(user_service, user_repository_mock):
    # Given: API returns users in unsorted order
    users = [sample_user(3), sample_user(1), sample_user(2)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert result == users
    assert [u.id for u in result] == [3, 1, 2]