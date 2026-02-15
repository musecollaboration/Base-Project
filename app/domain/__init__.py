"""
Доменный слой приложения.

Содержит бизнес-логику, сущности, value objects и абстрактные интерфейсы.
"""

from app.domain.entities import User
from app.domain.interfaces import UserRepository

__all__ = [
    "User",
    "UserRepository",
]
