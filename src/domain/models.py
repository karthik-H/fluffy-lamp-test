"""Domain models for User, Address, and Company."""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class Address:
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Dict[str, str]  # {'lat': str, 'lng': str}


@dataclass(frozen=True)
class Company:
    name: str
    catchPhrase: str
    bs: str


@dataclass(frozen=True)
class User:
    id: int
    name: str
    username: str
    email: str
    phone: str
    website: str
    address: Address
    company: Company