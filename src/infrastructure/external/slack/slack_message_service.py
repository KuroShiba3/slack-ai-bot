import json
from typing import Any

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from ....log.logger import get_logger

logger = get_logger(__name__)


class SlackMessageService:
    """Slackメッセージ送信とリアクション管理を行うサービス"""

    MAX_TEXT_LENGTH = 2900
    MAX_FALLBACK_LENGTH = 100

    def __init__(self, slack_client: AsyncWebClient):
        self._client = slack_client

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
        use_blocks: bool = True,
        message_id: str | None = None,
        enable_feedback: bool = True,
    ) -> None:
        """Slackにメッセージを送信する

        Args:
            channel: 送信先チャンネルID
            text: 送信するテキスト
            thread_ts: スレッドのタイムスタンプ
            use_blocks: Block Kitを使用するか
            message_id: メッセージID (フィードバック用)
            enable_feedback: フィードバックボタンを表示するか
        """
        # テキストの切り詰め処理
        text, truncated = self._truncate_text_if_needed(text)

        if not use_blocks:
            await self._client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts,
            )
            return

        blocks = self._create_message_blocks(text, message_id, enable_feedback)

        fallback_text = text[: self.MAX_FALLBACK_LENGTH] if truncated else text

        await self._client.chat_postMessage(
            channel=channel,
            text=fallback_text,
            thread_ts=thread_ts,
            blocks=blocks,
        )

    def _truncate_text_if_needed(self, text: str) -> tuple[str, bool]:
        """必要に応じてテキストを切り詰める

        Args:
            text: 元のテキスト

        Returns:
            切り詰められたテキストと切り詰めが発生したかのフラグ
        """
        if len(text) <= self.MAX_TEXT_LENGTH:
            return text, False

        original_length = len(text)

        # 適切な切断点を探す
        truncate_point = self._find_truncation_point(text)

        truncated_text = text[:truncate_point]

        logger.warning(
            f"メッセージが長すぎるため切り詰めました (元の長さ: {original_length}, 切り詰め後: {len(truncated_text)})"
        )

        return truncated_text, True

    def _find_truncation_point(self, text: str) -> int:
        """テキストの適切な切断点を見つける

        Args:
            text: 対象テキスト

        Returns:
            切断位置のインデックス
        """
        # 段落の区切りを探す
        last_paragraph = text.rfind("\n\n", 0, self.MAX_TEXT_LENGTH)
        if last_paragraph > self.MAX_TEXT_LENGTH - 500:
            return last_paragraph

        # 文の区切りを探す
        last_sentence = max(
            text.rfind("。", 0, self.MAX_TEXT_LENGTH),
            text.rfind(". ", 0, self.MAX_TEXT_LENGTH),
        )
        if last_sentence > self.MAX_TEXT_LENGTH - 200:
            return last_sentence + 1

        # 見つからない場合は最大長で切る
        return self.MAX_TEXT_LENGTH

    def _create_message_blocks(
        self,
        text: str,
        message_id: str | None,
        enable_feedback: bool,
    ) -> list[dict[str, Any]]:
        """メッセージ用のblocksを生成

        Args:
            text: メッセージテキスト
            message_id: メッセージID
            enable_feedback: フィードバックボタンを含めるか

        Returns:
            Slack blocks形式のリスト
        """
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            }
        ]

        if enable_feedback and message_id:
            blocks.append(self._create_feedback_block(message_id))

        return blocks

    def _create_feedback_block(self, message_id: str) -> dict[str, Any]:
        """フィードバックボタンのblockを生成

        Args:
            message_id: メッセージID

        Returns:
            フィードバックblock
        """
        return {
            "type": "context_actions",
            "elements": [
                {
                    "type": "feedback_buttons",
                    "action_id": "feedback",
                    "positive_button": {
                        "text": {"type": "plain_text", "text": "good"},
                        "value": json.dumps({"message_id": message_id, "type": "good"}),
                    },
                    "negative_button": {
                        "text": {"type": "plain_text", "text": "bad"},
                        "value": json.dumps({"message_id": message_id, "type": "bad"}),
                    },
                }
            ],
        }

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
    ) -> None:
        """Slackメッセージにリアクションを追加する

        Args:
            channel: チャンネルID
            timestamp: メッセージのタイムスタンプ
            emoji: 絵文字名 (コロンなし)
        """
        try:
            await self._client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji,
            )
        except SlackApiError as e:
            if e.response["error"] != "already_reacted":
                logger.error(f"リアクション追加エラー: {e.response['error']}")
            else:
                logger.debug("既にリアクションが追加されています")

    async def remove_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
    ) -> None:
        """Slackメッセージからリアクションを削除する

        Args:
            channel: チャンネルID
            timestamp: メッセージのタイムスタンプ
            emoji: 絵文字名 (コロンなし)
        """
        try:
            await self._client.reactions_remove(
                channel=channel,
                timestamp=timestamp,
                name=emoji,
            )
        except SlackApiError as e:
            if e.response["error"] != "no_reaction":
                logger.error(f"リアクション削除エラー: {e.response['error']}")
            else:
                logger.debug("リアクションが存在しません")

    async def check_reaction_exists(
        self,
        channel: str,
        timestamp: str,
        reaction_name: str,
    ) -> bool:
        """特定のリアクションがボットによって押されているかチェック

        Args:
            channel: チャンネルID
            timestamp: メッセージのタイムスタンプ
            reaction_name: リアクション名

        Returns:
            リアクションが存在する場合True
        """
        try:
            response = await self._client.reactions_get(
                channel=channel,
                timestamp=timestamp,
            )

            message: dict = response.get("message", {})
            reactions = message.get("reactions", [])

            return any(reaction["name"] == reaction_name for reaction in reactions)

        except SlackApiError as e:
            logger.error(f"リアクション取得エラー: {e.response['error']}")
            return False
