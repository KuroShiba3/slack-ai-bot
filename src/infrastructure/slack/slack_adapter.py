import os
from typing import Callable
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from fastapi import FastAPI, Request

from ...config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN

class SlackAdapter:
    def __init__(self):
        self.app = self._create_slack_app()

    async def start_socket_mode(self):
        if not SLACK_APP_TOKEN:
            raise ValueError("環境変数 SLACK_APP_TOKEN が設定されていません。Socket Mode を使用するには必要です。")

        handler = AsyncSocketModeHandler(self.app, SLACK_APP_TOKEN)
        await handler.start_async()

    def setup_webhook_routes(self, fastapi_app: FastAPI):
        handler = AsyncSlackRequestHandler(self.app)

        @fastapi_app.post("/slack/events")
        async def slack_events_endpoint(req: Request):
            return await handler.handle(req)

        @fastapi_app.get("/health")
        async def health_check():
            return {"status": "ok", "environment": os.getenv("ENV", "unknown")}

    def register_handler(self, event_type: str, handler: Callable):
        self.app.event(event_type)(handler)

    def _create_slack_app(self) -> AsyncApp:
        app = AsyncApp(
            token=SLACK_BOT_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET
        )

        return app