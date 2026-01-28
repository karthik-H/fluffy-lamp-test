"""
Repository for fetching user data from the JSONPlaceholder API.
"""

import requests
from typing import List
from domain.models import User, Address, Company
from config.config import Config



class UserRepository:
    """Handles API communication for user data."""

    def __init__(self, base_url: str = None, users_endpoint: str = None):
        self.base_url = base_url or Config.JSONPLACEHOLDER_BASE_URL
        self.users_endpoint = users_endpoint or Config.JSONPLACEHOLDER_USERS_ENDPOINT

    def fetch_all_users(self) -> List[User]:
        """Fetch all users from the API and return as domain models."""
        url = f"{self.base_url.rstrip('/')}{self.users_endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        users_json = response.json()
        return [self._parse_user(user) for user in users_json]

    def _parse_user(self, data: dict) -> User:
        """Parse a user dict into a User domain model."""
        address = Address(
            street=data["address"]["street"],
            suite=data["address"]["suite"],
            city=data["address"]["city"],
            zipcode=data["address"]["zipcode"],
            geo=data["address"]["geo"],
        )
        company = Company(
            name=data["company"]["name"],
            catchPhrase=data["company"]["catchPhrase"],
            bs=data["company"]["bs"],
        )
        return User(
            id=data["id"],
            name=data["name"],
            username=data["username"],
            email=data["email"],
            phone=data["phone"],
            website=data["website"],
            address=address,
            company=company,
        )
