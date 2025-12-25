from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ...config import POSTGRES_URL


class DatabasePool:
    _pool: AsyncConnectionPool | None = None

    @classmethod
    async def initialize(cls, min_size: int = 2, max_size: int = 10):
        """接続プールを初期化"""
        if cls._pool is None:
            if not POSTGRES_URL:
                raise ValueError("POSTGRES_URL環境変数が設定されていません")
            cls._pool = AsyncConnectionPool(
                POSTGRES_URL,
                kwargs={"row_factory": dict_row},
                min_size=min_size,
                max_size=max_size,
                open=False,  # 自動オープンを無効化
            )
            await cls._pool.open()

    @classmethod
    async def close(cls):
        """接続プールをクローズ"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """データベース接続を取得"""
        if cls._pool is None:
            raise RuntimeError(
                "DatabasePoolが初期化されていません。initialize()を呼んでください。"
            )

        async with cls._pool.connection() as conn:
            yield conn

    @classmethod
    def get_pool(cls) -> AsyncConnectionPool:
        """接続プールを取得"""
        if cls._pool is None:
            raise RuntimeError(
                "DatabasePoolが初期化されていません。initialize()を呼んでください。"
            )
        return cls._pool
