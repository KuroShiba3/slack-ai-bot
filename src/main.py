import asyncio

import uvicorn
from fastapi import FastAPI

from .config import ENV
from .di_container import DIContainer
from .infrastructure.external.slack.slack_adapter import SlackAdapter

# Slackアダプターを初期化
slack_adapter = SlackAdapter()

# DIコンテナを初期化（SlackクライアントをDIコンテナに渡す）
container = DIContainer(slack_client=slack_adapter.app.client)

# 依存関係を注入
slack_message_controller = container.slack_message_controller

slack_adapter.register_handler("app_mention", slack_message_controller.execute)
slack_adapter.register_handler("message", slack_message_controller.execute)

fastapi_app = FastAPI()

def main():
    if not ENV:
        raise ValueError("ENV環境変数が設定されていません")

    if ENV == "local":
        asyncio.run(slack_adapter.start_socket_mode())
    elif ENV in ["dev", "prod"]:
        slack_adapter.setup_routes(fastapi_app)
        uvicorn.run("src.main:fastapi_app", host="0.0.0.0", port=8000, reload=(ENV == "dev"))

if __name__ == "__main__":
    main()
