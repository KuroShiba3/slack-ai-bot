import os

from dotenv import load_dotenv

load_dotenv(override=True)

# Slack関連
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Google関連
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

# Database関連
POSTGRES_URL = os.environ.get("POSTGRES_URL")

# 環境
ENV = os.environ.get("ENV")
