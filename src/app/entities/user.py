from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class UserCreateDTO:
    """Данные, необходимые для создания пользователя."""

    max_id: int
    username: str | None = None
    phone: str | None = None
    options: dict[str, object] | None = None


@dataclass(slots=True)
class UserUpdateDTO:
    """Поля, которые можно частично обновить (None – не трогать)."""

    username: str | None = None
    phone: str | None = None
    options: dict[str, object] | None = None


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class User:
    """Представление строки таблицы users."""

    id: int
    max_id: int
    username: str | None
    phone: str | None
    options: dict[str, object] | None
    created_at: datetime
    updated_at: datetime
