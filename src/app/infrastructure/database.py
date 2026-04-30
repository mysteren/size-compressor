from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

import aiosqlite


@runtime_checkable
class IMigrator(Protocol):
    """Интерфейс для применения миграций к соединению с БД."""

    async def apply(self, conn: aiosqlite.Connection) -> None:
        """Применить все необходимые миграции."""
        ...


class Database:
    """Асинхронная обёртка над SQLite с WAL-режимом и автоматическими миграциями."""

    def __init__(self, db_path: str | Path, migrator: IMigrator) -> None:
        self._path: Path = Path(db_path)
        self._migrator: IMigrator = migrator
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> Database:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        """Устанавливает соединение, настраивает прагмы и применяет миграции."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self._path))
        self._conn.row_factory = aiosqlite.Row
        await self._configure_pragmas()
        if not await self._verify_wal():
            raise RuntimeError("Failed to enable WAL journal mode")
        # Делегируем миграции внедрённому объекту
        await self._migrator.apply(self._conn)

    async def disconnect(self) -> None:
        """Безопасно закрывает соединение с финальным checkpoint'ом WAL."""
        if self._conn is None:
            return
        _ = await self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        await self._conn.close()
        self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """Возвращает активное соединение или бросает ошибку."""
        if self._conn is None:
            raise RuntimeError("Database is not connected")
        return self._conn

    @asynccontextmanager
    async def transaction(self):
        """Контекстный менеджер для транзакций с автоматическим откатом."""
        if self._conn is None:
            raise RuntimeError("Cannot start transaction: database not connected")
        _ = await self._conn.execute("BEGIN")
        try:
            yield self._conn
            await self._conn.commit()
        except BaseException:
            await self._conn.rollback()
            raise

    # ------------------------------------------------------------------ private
    async def _configure_pragmas(self) -> None:
        """Однократная настройка производительных прагм после каждого connect()."""
        assert self._conn is not None
        pragmas = (
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA journal_size_limit = 6291456",  # ~6 МБ
            "PRAGMA cache_size = -8000",  # 8 МБ
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",  # 256 МБ
        )
        for pragma in pragmas:
            _ = await self._conn.execute(pragma)
        # не делаем commit – прагмы вступают в силу сразу

    async def _verify_wal(self) -> bool:
        """Возвращает True, если WAL-режим активирован."""
        assert self._conn is not None
        cursor = await self._conn.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        if row:
            mode = cast(str, row[0])
            return str(mode).lower() == "wal"
        return False
