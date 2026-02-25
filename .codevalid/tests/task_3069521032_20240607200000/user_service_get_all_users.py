import pytest
from unittest.mock import MagicMock
from src.services.user_service import UserService
from src.data.user_repository import UserRepository
from src.domain.models import User, Address, Company

@pytest.fixture
def user_repository_mock():
    return MagicMock(spec=UserRepository)

@pytest.fixture
def user_service(user_repository_mock):
    return UserService(user_repository=user_repository_mock)

def sample_user(id=1, name=None, username=None, email=None, phone=None, website=None, address=None, company=None):
    return User(
        id=id,
        name=name if name is not None else f"User{id}",
        username=username if username is not None else f"user{id}",
        email=email if email is not None else f"user{id}@example.com",
        phone=phone if phone is not None else "123-456-7890",
        website=website if website is not None else "userwebsite.com",
        address=address if address is not None else Address(
            street="Street",
            suite="Suite",
            city="City",
            zipcode="12345",
            geo={"lat": "0", "lng": "0"},
        ),
        company=company if company is not None else Company(
            name="Company",
            catchPhrase="CatchPhrase",
            bs="bs"
        )
    )

# Test Case 1: test_all_users_success
def test_all_users_success(user_service, user_repository_mock):
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

# Test Case 2: test_empty_user_list
def test_empty_user_list(user_service, user_repository_mock):
    # Given: API returns empty list
    user_repository_mock.fetch_all_users.return_value = []

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 0

# Test Case 3: test_api_unreachable
def test_api_unreachable(user_service, user_repository_mock):
    # Given: API unreachable (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("API unreachable")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "API unreachable" in str(excinfo.value)

# Test Case 4: test_api_http_error
def test_api_http_error(user_service, user_repository_mock):
    # Given: API returns HTTP error (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("500 Internal Server Error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "500 Internal Server Error" in str(excinfo.value)

# Test Case 5: test_api_invalid_json
def test_api_invalid_json(user_service, user_repository_mock):
    # Given: API returns invalid JSON (simulate exception)
    user_repository_mock.fetch_all_users.side_effect = Exception("JSON decode error")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "JSON decode error" in str(excinfo.value)

# Test Case 6: test_user_records_with_missing_fields
def test_user_records_with_missing_fields(user_service, user_repository_mock):
    # Given: API returns users with missing/null fields
    users = [
        sample_user(1, name=None, email=None),  # missing name and email
        sample_user(2, address=None),           # missing address
        sample_user(3, company=None),           # missing company
        sample_user(4, username=None),          # missing username
    ]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 4
    # Check missing/null fields are reflected
    assert result[0].name is None
    assert result[0].email is None
    assert result[1].address is None
    assert result[2].company is None
    assert result[3].username is None

# Test Case 7: test_large_user_list
def test_large_user_list(user_service, user_repository_mock):
    # Given: API returns 10,000 users
    users = [sample_user(i) for i in range(1, 10001)]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 10000
    assert result == users

# Test Case 8: test_api_returns_non_list_object
def test_api_returns_non_list_object(user_service, user_repository_mock):
    # Given: API returns a JSON object (not a list)
    user_repository_mock.fetch_all_users.side_effect = Exception("API returned non-list object")

    # When / Then
    with pytest.raises(Exception) as excinfo:
        user_service.get_all_users()
    assert "API returned non-list object" in str(excinfo.value)

# Test Case 9: test_duplicate_user_records
def test_duplicate_user_records(user_service, user_repository_mock):
    # Given: API returns duplicate user records
    user1 = sample_user(1)
    user2 = sample_user(2)
    users = [user1, user2, user1, user2]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 4
    assert result == users  # duplicates preserved

# Test Case 10: test_special_characters_in_user_data
def test_special_characters_in_user_data(user_service, user_repository_mock):
    # Given: API returns users with special/non-ASCII characters
    users = [
        sample_user(1, name="José", email="josé@example.com"),
        sample_user(2, name="Zoë", email="zoë@example.com"),
        sample_user(3, name="李雷", email="lilei@example.cn"),
        sample_user(4, name="O'Connor", email="oconnor@example.com"),
        sample_user(5, name="François", email="françois@example.fr"),
    ]
    user_repository_mock.fetch_all_users.return_value = users

    # When
    result = user_service.get_all_users()

    # Then
    assert isinstance(result, list)
    assert len(result) == 5
    for i, user in enumerate(users):
        assert result[i].name == user.name
        assert result[i].email == user.email