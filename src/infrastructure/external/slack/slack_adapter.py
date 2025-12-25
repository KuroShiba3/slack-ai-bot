import os
from collections.abc import Callable

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from ....config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET


class SlackAdapter:
    def __init__(self):
        self.app = self._create_slack_app()

    async def start_socket_mode(self):
        if not SLACK_APP_TOKEN:
            raise ValueError(
                "環境変数 SLACK_APP_TOKEN が設定されていません。Socket Mode を使用するには必要です。"
            )

        handler = AsyncSocketModeHandler(self.app, SLACK_APP_TOKEN)
        await handler.start_async()

    def setup_routes(self, fastapi_app: FastAPI):
        handler = AsyncSlackRequestHandler(self.app)

        @fastapi_app.post("/slack/events")
        async def slack_events_endpoint(req: Request):
            return await handler.handle(req)

        @fastapi_app.get("/health")
        async def health_check():
            return {"status": "ok", "environment": os.getenv("ENV", "unknown")}

    def register_handler(self, event_type: str, handler: Callable):
        if event_type == "action":
            self.app.action("feedback")(handler)
        else:
            self.app.event(event_type)(handler)

    def _create_slack_app(self) -> AsyncApp:
        if not SLACK_BOT_TOKEN or not SLACK_SIGNING_SECRET:
            raise ValueError(
                "環境変数 SLACK_BOT_TOKEN または SLACK_SIGNING_SECRET が設定されていません。"
            )

        return AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
