"""
Configuration loader for environment variables.
Reads from .env file and environment variables.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""

    JSONPLACEHOLDER_BASE_URL: str = os.getenv("JSONPLACEHOLDER_BASE_URL", "https://jsonplaceholder.typicode.com")
    JSONPLACEHOLDER_USERS_ENDPOINT: str = os.getenv("JSONPLACEHOLDER_USERS_ENDPOINT", "/users")