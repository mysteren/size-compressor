from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from app.entities.user import User, UserCreateDTO, UserUpdateDTO
from app.infrastructure.database import Database

if TYPE_CHECKING:
    from aiosqlite import Row


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------
class UserRepository:
    """Асинхронный репозиторий для работы с пользователями."""

    def __init__(self, db: Database) -> None:
        self._db: Database = db

    async def create(self, dto: UserCreateDTO) -> User:
        """Вставляет новую запись и возвращает созданного пользователя."""
        async with self._db.transaction() as conn:
            cursor = await conn.execute(
                """INSERT INTO users (max_id, username, phone, options)
                   VALUES (?, ?, ?, ?)""",
                (
                    dto.max_id,
                    dto.username,
                    dto.phone,
                    json.dumps(dto.options) if dto.options is not None else None,
                ),
            )
            row = await (
                await conn.execute(
                    "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
                )
            ).fetchone()
            if row is None:
                raise RuntimeError("Не удалось прочитать только что созданную запись")
            return self._row_to_entity(row)

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по primary key или None."""
        cursor = await self._db.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return self._row_to_entity(row) if row else None

    async def get_all(self) -> list[User]:
        """Возвращает список всех пользователей."""
        cursor = await self._db.conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [self._row_to_entity(r) for r in rows]

    async def update(self, user_id: int, dto: UserUpdateDTO) -> User | None:
        """Частично обновляет пользователя. Возвращает обновлённую запись или None."""
        async with self._db.transaction() as conn:
            sets: list[str] = []
            params: list[object] = []

            if dto.username is not None:
                sets.append("username = ?")
                params.append(dto.username)
            if dto.phone is not None:
                sets.append("phone = ?")
                params.append(dto.phone)
            if dto.options is not None:
                sets.append("options = ?")
                params.append(json.dumps(dto.options))

            if sets:
                sets.append("updated_at = datetime('now')")
                params.append(user_id)
                _ = await conn.execute(
                    f"UPDATE users SET {', '.join(sets)} WHERE id = ?",
                    params,
                )

            row = await (
                await conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            ).fetchone()
            return self._row_to_entity(row) if row else None

    async def delete(self, user_id: int) -> bool:
        """Удаляет пользователя. Возвращает True, если запись существовала."""
        async with self._db.transaction() as conn:
            cursor = await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_entity(row: Row) -> User:
        """Десериализует aiosqlite.Row в экземпляр User."""
        return User(
            id=row["id"],
            max_id=row["max_id"],
            username=row["username"],
            phone=row["phone"],
            options=json.loads(row["options"]) if row["options"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
