class FinalAnswer:
    def __init__(self, content: str):
        self._content = content

    def to_message(self) -> str:
        """ユーザーに表示する文字列を生成"""
        return self._content
