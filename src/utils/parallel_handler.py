import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from src.scraper.browser import LancersBrowser

class ParallelHandler:
    def __init__(self, max_workers: int = 4, use_processes: bool = False):
        """
        並列処理ハンドラーのコンストラクタ
        Args:
            max_workers (int): 最大ワーカー数
            use_processes (bool): プロセスベースの並列処理を使用するかどうか
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.logger = logging.getLogger(__name__)

    async def parallel_search(
        self,
        search_queries: List[str],
        max_pages: int = 5,
        headless: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数の検索クエリを並列に実行
        Args:
            search_queries (List[str]): 検索クエリのリスト
            max_pages (int): 各検索で取得する最大ページ数
            headless (bool): ヘッドレスモードで実行するかどうか
        Returns:
            Dict[str, List[Dict[str, Any]]]: クエリごとの検索結果
        """
        try:
            # 検索タスクの作成
            tasks = []
            for query in search_queries:
                browser = LancersBrowser(headless=headless, max_pages=max_pages)
                task = self._search_with_browser(browser, query)
                tasks.append(task)

            # 並列実行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果の整理
            search_results = {}
            for query, result in zip(search_queries, results):
                if isinstance(result, Exception):
                    self.logger.error(f"検索中にエラーが発生しました（{query}）: {str(result)}")
                    search_results[query] = []
                else:
                    search_results[query] = result

            return search_results

        except Exception as e:
            self.logger.error(f"並列検索処理中にエラーが発生しました: {str(e)}")
            return {query: [] for query in search_queries}

    async def _search_with_browser(
        self,
        browser: LancersBrowser,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        ブラウザインスタンスを使用して検索を実行
        Args:
            browser (LancersBrowser): ブラウザインスタンス
            query (str): 検索クエリ
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            browser.start()
            results = await browser.search_short_videos(query)
            return results
        finally:
            browser.close()

    def process_results_parallel(
        self,
        results: List[Dict[str, Any]],
        processor: Callable[[Dict[str, Any]], Any]
    ) -> List[Any]:
        """
        検索結果を並列に処理
        Args:
            results (List[Dict[str, Any]]): 処理する結果のリスト
            processor (Callable): 各結果に適用する処理関数
        Returns:
            List[Any]: 処理された結果のリスト
        """
        try:
            # プロセスまたはスレッドプールの選択
            executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
            
            with executor_class(max_workers=self.max_workers) as executor:
                processed_results = list(executor.map(processor, results))
            
            return processed_results

        except Exception as e:
            self.logger.error(f"結果の並列処理中にエラーが発生しました: {str(e)}")
            return []

    async def search_and_process(
        self,
        search_queries: List[str],
        processor: Callable[[Dict[str, Any]], Any],
        max_pages: int = 5,
        headless: bool = True
    ) -> Dict[str, List[Any]]:
        """
        検索と結果処理を組み合わせた並列処理
        Args:
            search_queries (List[str]): 検索クエリのリスト
            processor (Callable): 各結果に適用する処理関数
            max_pages (int): 各検索で取得する最大ページ数
            headless (bool): ヘッドレスモードで実行するかどうか
        Returns:
            Dict[str, List[Any]]: クエリごとの処理済み結果
        """
        try:
            # 並列検索の実行
            search_results = await self.parallel_search(
                search_queries,
                max_pages=max_pages,
                headless=headless
            )
            
            # 結果の並列処理
            processed_results = {}
            for query, results in search_results.items():
                if results:
                    processed = self.process_results_parallel(results, processor)
                    processed_results[query] = processed
                else:
                    processed_results[query] = []
            
            return processed_results

        except Exception as e:
            self.logger.error(f"検索と処理の並列実行中にエラーが発生しました: {str(e)}")
            return {query: [] for query in search_queries} 