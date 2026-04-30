import aiosqlite


class Migrator:
    """Набор идемпотентных миграций для базы данных."""

    @staticmethod
    async def _create_users_table(conn: aiosqlite.Connection) -> None:
        """Создаёт таблицу users, если она не существует."""
        _ = await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                max_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                phone TEXT,
                options TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.commit()

    @staticmethod
    async def _add_role_column(conn: aiosqlite.Connection) -> None:
        """Добавляет колонку role, если её ещё нет."""
        cursor = await conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "role" not in columns:
            _ = await conn.execute(
                "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
            )
            await conn.commit()

    @classmethod
    async def apply(cls, conn: aiosqlite.Connection) -> None:
        """Применяет все миграции в нужном порядке."""
        await cls._create_users_table(conn)
        await cls._add_role_column(conn)
        # При добавлении новых миграций дописываем вызовы сюда
