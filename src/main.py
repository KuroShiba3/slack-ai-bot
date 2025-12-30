import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .config import ENV
from .di_container import DIContainer
from .infrastructure.database import DatabasePool, run_migrations
from .infrastructure.external.slack.slack_adapter import SlackAdapter
from .log import get_logger

logger = get_logger(__name__)

# グローバル変数として初期化（ライフサイクル内で設定）
slack_adapter = None
container = None
slack_message_controller = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPIのライフサイクル管理"""
    global slack_adapter, container, slack_message_controller

    logger.info(f"HTTP Mode (ENV={ENV}) で起動中...")

    logger.info("データベースマイグレーションを実行中...")
    run_migrations()
    logger.info("データベースマイグレーションが完了しました")

    logger.info("データベース接続プールを初期化中...")
    await DatabasePool.initialize()
    logger.info("データベース接続プールの初期化が完了しました")

    slack_adapter = SlackAdapter()

    container = DIContainer(slack_client=slack_adapter.app.client)

    # 依存関係を注入
    slack_message_controller = container.slack_message_controller
    slack_feedback_controller = container.slack_feedback_controller

    slack_adapter.register_handler("app_mention", slack_message_controller.execute)
    slack_adapter.register_handler("message", slack_message_controller.execute)
    slack_adapter.register_handler("action", slack_feedback_controller.execute)

    # FastAPIモードの場合、ルートを設定
    if ENV in ["dev", "prod"]:
        slack_adapter.setup_routes(app)

    logger.info("アプリケーションの起動が完了しました")

    yield

    # シャットダウン時の処理
    logger.info("アプリケーションをシャットダウン中...")
    # データベース接続プールをクローズ
    await DatabasePool.close()
    logger.info("データベース接続プールをクローズしました")


app = FastAPI(lifespan=lifespan)


async def setup_socket_mode():
    """Socket Mode用のセットアップ"""
    global slack_adapter, container, slack_message_controller

    try:
        logger.info("Socket Mode (ENV=local) で起動中...")

        # データベースマイグレーションを実行
        logger.info("データベースマイグレーションを実行中...")
        run_migrations()
        logger.info("データベースマイグレーションが完了しました")

        # データベース接続プールを初期化
        logger.info("データベース接続プールを初期化中...")
        await DatabasePool.initialize()
        logger.info("データベース接続プールの初期化が完了しました")

        # Slackアダプターを初期化
        slack_adapter = SlackAdapter()

        # DIコンテナを初期化(SlackクライアントをDIコンテナに渡す)
        container = DIContainer(slack_client=slack_adapter.app.client)

        # 依存関係を注入
        slack_message_controller = container.slack_message_controller
        slack_feedback_controller = container.slack_feedback_controller

        slack_adapter.register_handler("app_mention", slack_message_controller.execute)
        slack_adapter.register_handler("message", slack_message_controller.execute)
        slack_adapter.register_handler("action", slack_feedback_controller.execute)

        await slack_adapter.start_socket_mode()
    finally:
        # クリーンアップ処理
        await DatabasePool.close()
        logger.info("データベース接続プールをクローズしました")


def main():
    if not ENV:
        raise ValueError("ENV環境変数が設定されていません")

    if ENV == "local":
        asyncio.run(setup_socket_mode())
    elif ENV in ["dev", "prod"]:
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=(ENV == "dev"))


if __name__ == "__main__":
    main()
