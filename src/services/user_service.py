"""
Service layer for user-related business logic.
"""

from typing import List
from domain.models import User
from data.user_repository import UserRepository


class UserService:
    """Service for user operations."""

    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or UserRepository()

    def get_all_users(self) -> List[User]:
        """
        Retrieve all users from the repository.
        Returns:
            List[User]: List of user domain models.
        """
        return self.user_repository.fetch_all_users()