from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from ....domain.model import Message, Role


class MessageConverter:
    """ドメインモデルのMessageとLangChainのメッセージを相互変換するクラス"""

    @staticmethod
    def to_langchain_messages(messages: list[Message]) -> list[BaseMessage]:
        """ドメインモデルのMessageをLangChainのメッセージに変換

        Args:
            messages: ドメインモデルのMessageリスト

        Returns:
            LangChainのBaseMessageリスト
        """
        langchain_messages: list[BaseMessage] = []

        for msg in messages:
            if msg.role == Role.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == Role.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == Role.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
            else:
                raise ValueError(f"未対応のロールです: {msg.role}")

        return langchain_messages

    @staticmethod
    def to_domain_message(message: BaseMessage) -> Message:
        """LangChainのメッセージをドメインモデルのMessageに変換

        Args:
            message: LangChainのBaseMessage

        Returns:
            ドメインモデルのMessage
        """
        if isinstance(message, HumanMessage):
            return Message.create_user_message(message.content)
        elif isinstance(message, AIMessage):
            return Message.create_assistant_message(message.content)
        elif isinstance(message, SystemMessage):
            return Message.create_system_message(message.content)
        else:
            raise ValueError(f"未対応のメッセージタイプです: {type(message)}")
