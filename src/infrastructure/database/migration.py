from pathlib import Path

from yoyo import get_backend, read_migrations

from ...config import POSTGRES_URL
from ...log.logger import get_logger

logger = get_logger(__name__)


def run_migrations():
    try:
        migrations_dir = Path(__file__).parent.parent.parent.parent / "migrations"

        if not migrations_dir.exists():
            logger.warning(f"マイグレーションフォルダが存在しません: {migrations_dir}")
            return

        if not POSTGRES_URL:
            raise ValueError("POSTGRES_URL環境変数が設定されていません")

        backend = get_backend(POSTGRES_URL)

        migrations = read_migrations(str(migrations_dir))

        with backend.lock():
            to_apply = backend.to_apply(migrations)

            if to_apply:
                backend.apply_migrations(to_apply)
                logger.debug("すべてのマイグレーションが正常に適用されました")
            else:
                logger.debug("適用するマイグレーションはありません")

    except Exception as e:
        logger.error(f"マイグレーションの実行に失敗しました: {e}")
        raise
