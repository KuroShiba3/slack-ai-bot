import asyncio
import os
import uvicorn
from fastapi import FastAPI

from .infrastructure.slack.slack_adapter import SlackAdapter
from .presentation import MentionController, MessageController


ENV = os.getenv("ENV", "local")

slack_adapter = SlackAdapter()
mention_controller = MentionController()
message_controller = MessageController()
slack_adapter.register_handler("app_mention", mention_controller.exec)
slack_adapter.register_handler("message", message_controller.exec)

fastapi_app = FastAPI()

def main():
    if ENV == "local":
        asyncio.run(slack_adapter.start_socket_mode())
    elif ENV in ["dev", "prod"]:
        slack_adapter.setup_webhook_routes(fastapi_app)
        uvicorn.run("src.main:fastapi_app", host="0.0.0.0", port=8000, reload=(ENV == "dev"))

if __name__ == "__main__":
    main()