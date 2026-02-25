import pytest
from unittest.mock import patch, Mock
from src.data.user_repository import UserRepository
from src.domain.models import User, Address, Company

# Helper: sample user dict as returned by API
def sample_user_dict(id=1, name="Leanne Graham", username="Bret", email="Sincere@april.biz",
                     phone="1-770-736-8031 x56442", website="hildegard.org",
                     address=None, company=None):
    address = address or {
        "street": "Kulas Light",
        "suite": "Apt. 556",
        "city": "Gwenborough",
        "zipcode": "92998-3874",
        "geo": {"lat": "-37.3159", "lng": "81.1496"}
    }
    company = company or {
        "name": "Romaguera-Crona",
        "catchPhrase": "Multi-layered client-server neural-net",
        "bs": "harness real-time e-markets"
    }
    return {
        "id": id,
        "name": name,
        "username": username,
        "email": email,
        "phone": phone,
        "website": website,
        "address": address,
        "company": company
    }

@pytest.fixture
def repo():
    return UserRepository(base_url="https://jsonplaceholder.typicode.com", users_endpoint="/users")

def make_user_model(user_dict):
    address = Address(**user_dict["address"])
    company = Company(**user_dict["company"])
    return User(
        id=user_dict["id"],
        name=user_dict["name"],
        username=user_dict["username"],
        email=user_dict["email"],
        phone=user_dict["phone"],
        website=user_dict["website"],
        address=address,
        company=company
    )

# Test Case 1: fetch_all_users_returns_all_users_successfully
def test_fetch_all_users_returns_all_users_successfully(repo):
    users_data = [sample_user_dict(id=1), sample_user_dict(id=2, name="Ervin Howell", username="Antonette")]
    expected = [make_user_model(u) for u in users_data]
    mock_response = Mock()
    mock_response.json.return_value = users_data
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get:
        result = repo.fetch_all_users()
        assert result == expected
        mock_get.assert_called_once()

# Test Case 2: fetch_all_users_handles_api_unreachable
def test_fetch_all_users_handles_api_unreachable(repo):
    with patch("requests.get", side_effect=Exception("Network error")):
        with pytest.raises(Exception) as excinfo:
            repo.fetch_all_users()
        assert "Network error" in str(excinfo.value)

# Test Case 3: fetch_all_users_handles_api_error_status
def test_fetch_all_users_handles_api_error_status(repo):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("500 Internal Server Error")
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            repo.fetch_all_users()
        assert "500 Internal Server Error" in str(excinfo.value)

# Test Case 4: fetch_all_users_handles_empty_user_list
def test_fetch_all_users_handles_empty_user_list(repo):
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    with patch("requests.get", return_value=mock_response):
        result = repo.fetch_all_users()
        assert result == []

# Test Case 5: fetch_all_users_handles_malformed_json_response
def test_fetch_all_users_handles_malformed_json_response(repo):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = Exception("Malformed JSON")
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            repo.fetch_all_users()
        assert "Malformed JSON" in str(excinfo.value)

# Test Case 6: fetch_all_users_handles_partial_user_fields
def test_fetch_all_users_handles_partial_user_fields(repo):
    # Missing 'username', 'company', 'address'
    partial_user = {
        "id": 1,
        "name": "Leanne Graham",
        "email": "Sincere@april.biz",
        "phone": "1-770-736-8031 x56442",
        "website": "hildegard.org",
        # 'address' and 'company' missing
    }
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [partial_user]
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(KeyError):
            repo.fetch_all_users()

# Test Case 7: fetch_all_users_handles_unexpected_response_type
def test_fetch_all_users_handles_unexpected_response_type(repo):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"not": "a list"}
    with patch("requests.get", return_value=mock_response):
        with pytest.raises(TypeError):
            repo.fetch_all_users()

# Test Case 8: fetch_all_users_handles_large_user_list
def test_fetch_all_users_handles_large_user_list(repo):
    users_data = [sample_user_dict(id=i) for i in range(1, 10001)]
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = users_data
    with patch("requests.get", return_value=mock_response):
        result = repo.fetch_all_users()
        assert len(result) == 10000
        # Spot check first and last
        assert result[0].id == 1
        assert result[-1].id == 10000

# Test Case 9: fetch_all_users_does_not_transform_data
def test_fetch_all_users_does_not_transform_data(repo):
    users_data = [
        sample_user_dict(id=1, name="A", username="a", email="a@a.com", phone="123", website="a.com"),
        sample_user_dict(id=2, name="B", username="b", email="b@b.com", phone="456", website="b.com")
    ]
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = users_data
    with patch("requests.get", return_value=mock_response):
        result = repo.fetch_all_users()
        # Check all fields and order
        for i, user in enumerate(result):
            assert user.id == users_data[i]["id"]
            assert user.name == users_data[i]["name"]
            assert user.username == users_data[i]["username"]
            assert user.email == users_data[i]["email"]
            assert user.phone == users_data[i]["phone"]
            assert user.website == users_data[i]["website"]
            assert user.address.street == users_data[i]["address"]["street"]
            assert user.company.name == users_data[i]["company"]["name"]