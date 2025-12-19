from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, AnyMessage, filter_messages
from ...log import get_logger

logger = get_logger(__name__)


class MessageService:

    @staticmethod
    def get_last_user_message(messages: list[AnyMessage]) -> Optional[str]:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and not getattr(msg, 'tool_calls', None):
                return msg.content
        return None

    @staticmethod
    def normalize_messages(messages: list[AnyMessage]) -> list[AnyMessage]:
        filtered_messages = filter_messages(
            messages, exclude_types=[ToolMessage], exclude_tool_calls=True
        )

        normalized_messages = []
        for msg in filtered_messages:
            if msg.type == "ai" and isinstance(msg.content, list):
                text_parts = [
                    part.get("text", "")
                    for part in msg.content
                    if isinstance(part, dict) and "text" in part
                ]
                normalized_msg = msg.copy()
                normalized_msg.content = "\n".join(text_parts)
                normalized_messages.append(normalized_msg)
            else:
                normalized_messages.append(msg)

        return normalized_messages