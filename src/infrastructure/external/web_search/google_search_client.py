import asyncio
import re
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_community import GoogleSearchAPIWrapper

from ....domain.model import SearchResult
from ....log import get_logger

logger = get_logger(__name__)


class GoogleSearchClient:
    """Google検索APIを使用した検索クライアント"""

    def __init__(self, google_api_key: str, google_cse_id: str):
        self._google_api_key = google_api_key
        self._google_cse_id = google_cse_id

    async def search(self, query: str, num_results: int = 3) -> list[SearchResult]:
        """Google検索を実行してWebページを取得する

        Args:
            query: 検索クエリ
            num_results: 取得する検索結果の数

        Returns:
            検索結果のリスト
        """
        try:
            search = GoogleSearchAPIWrapper(
                google_api_key=self._google_api_key,
                google_cse_id=self._google_cse_id
            )

            results = search.results(query, num_results=num_results)

            if not results:
                return []

            search_results: list[SearchResult] = []
            for result in results:
                url = result['link']
                title = result['title']
                snippet = result.get('snippet', '')

                try:
                    # Webページを取得してクリーニング
                    content = await self._fetch_and_clean_webpage(url)

                    search_results.append(SearchResult(
                        url=url,
                        title=title,
                        content=content
                    ))
                except Exception as e:
                    logger.warning(f"Webページ取得エラー ({url}): {str(e)}")
                    # エラー時はスニペットを使用
                    search_results.append(SearchResult(
                        url=url,
                        title=title,
                        content=snippet
                    ))

            return search_results

        except Exception as e:
            logger.error(f"検索実行エラー: {str(e)}", exc_info=True)
            return []

    async def _fetch_and_clean_webpage(self, url: str, timeout: float = 8.0) -> str:
        """Webページを取得してクリーニングする

        Args:
            url: WebページのURL
            timeout: タイムアウト時間（秒）

        Returns:
            クリーニングされたテキスト（最大5000文字）
        """
        loader = WebBaseLoader(url)
        load_task = asyncio.to_thread(loader.load)
        docs = await asyncio.wait_for(load_task, timeout=timeout)

        raw_content = docs[0].page_content
        cleaned_content = self._clean_text(raw_content)

        # 最大5000文字に制限
        return cleaned_content[:5000]

    def _clean_text(self, text: str) -> str:
        """テキストをクリーニングする

        Args:
            text: クリーニング対象のテキスト

        Returns:
            クリーニングされたテキスト
        """
        # 連続する改行を2つの改行に統一
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # 各行をトリムして空行を削除
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]

        return '\n'.join(lines)
