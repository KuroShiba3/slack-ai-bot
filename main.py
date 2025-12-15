"""Main entry point with environment-based execution"""
import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI

from src.infrastructure.slack.app import create_slack_app
from src.infrastructure.slack.handlers import SlackHandlerFactory, setup_fastapi_routes


ENV = os.getenv("ENV", "local").lower()


async def run_socket_mode():
    """Run in Socket Mode for local development"""
    print("Starting in Socket Mode (local environment)...")
    app = create_slack_app()
    handler = await SlackHandlerFactory.create_socket_mode_handler(app)
    await handler.start_async()


def run_webhook_mode():
    """Run in Webhook Mode for dev/production"""
    print(f"Starting in Webhook Mode ({ENV} environment)...")

    # Create FastAPI app and setup Slack routes
    fastapi_app = FastAPI()
    slack_app = create_slack_app()
    setup_fastapi_routes(fastapi_app, slack_app)

    # Store as global for uvicorn
    globals()['app'] = fastapi_app

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=(ENV == "dev"))


def main():
    """Main entry point"""
    if ENV == "local":
        asyncio.run(run_socket_mode())
    elif ENV in ["dev", "prod"]:
        run_webhook_mode()
    else:
        print(f"Error: Unknown environment '{ENV}'. Use 'local', 'dev', or 'prod'.")
        sys.exit(1)


if __name__ == "__main__":
    main()