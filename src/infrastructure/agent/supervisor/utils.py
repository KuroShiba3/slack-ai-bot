"""Supervisor agent utility functions"""

from langchain_core.messages import ToolMessage, filter_messages


def normalize_ai_messages(messages: list) -> list:
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
