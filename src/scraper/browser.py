from playwright.sync_api import sync_playwright, Browser, Page
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, List, Dict, Any
import logging
import time
import asyncio
import re  # 正規表現を使用するために追加
import urllib.parse

class LancersBrowser:
    def __init__(self, headless: bool = True, max_pages: int = 5):
        """
        LancersBrowserクラスのコンストラクタ
        Args:
            headless (bool): ヘッドレスモードで実行するかどうか
            max_pages (int): 取得する最大ページ数
        """
        self.headless = headless
        self.max_pages = max_pages
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.base_url = "https://www.lancers.jp/work/search"
        
        # ロギングの設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """ブラウザを起動し、新しいページを開く"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()
            self.logger.info("ブラウザを起動しました")
        except Exception as e:
            self.logger.error(f"ブラウザの起動に失敗しました: {str(e)}")
            raise

    async def close(self) -> None:
        """ブラウザを終了する"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("ブラウザを終了しました")
        except Exception as e:
            self.logger.error(f"ブラウザの終了に失敗しました: {str(e)}")
            raise

    async def _extract_work_info(self, card) -> Optional[Dict[str, Any]]:
        """
        案件カードから情報を抽出する
        Args:
            card: 案件カードの要素
        Returns:
            Dict[str, Any]: 抽出した情報
        """
        try:
            # タイトルとURL
            title_elem = await card.query_selector('.p-search-job-media__title')
            url_elem = await card.query_selector('a.p-search-job-media__title')
            
            # 報酬
            price_elem = await card.query_selector('.p-search-job-media__price')
            
            # 案件種別
            type_elem = await card.query_selector('.c-badge__text')
            
            # 締切
            deadline_elem = await card.query_selector('.p-search-job-media__time-remaining')
            
            # 募集状態
            status_elem = await card.query_selector('.p-search-job-media__time-text')

            # データの抽出
            title = await title_elem.text_content() if title_elem else "タイトルなし"
            url = await url_elem.get_attribute('href') if url_elem else ""
            price = await price_elem.text_content() if price_elem else "報酬未設定"
            work_type = await type_elem.text_content() if type_elem else "種別不明"
            deadline = await deadline_elem.text_content() if deadline_elem else "期限なし"
            status = await status_elem.text_content() if status_elem else "状態不明"

            # URLの処理
            full_url = url if url.startswith("http") else f"https://www.lancers.jp{url}"
            
            return {
                'title': title.strip(),
                'url': full_url,
                'price': price.strip(),
                'type': work_type.strip(),
                'deadline': deadline.strip(),
                'status': status.strip()
            }
            
        except Exception as e:
            self.logger.error(f"案件情報の抽出中にエラーが発生しました: {str(e)}")
            return None

    async def _has_next_page(self) -> bool:
        """
        次のページが存在するかを確認
        Returns:
            bool: 次のページが存在するかどうか
        """
        next_button = await self.page.query_selector('a.c-pagination__next:not(.is-disabled)')
        return next_button is not None

    async def _go_to_next_page(self) -> bool:
        """
        次のページに移動
        Returns:
            bool: 移動が成功したかどうか
        """
        try:
            current_url = self.page.url
            self.logger.info("=" * 50)
            self.logger.info(f"ページ遷移前のURL: {current_url}")
            
            # URLをパースして各パラメータを取得
            parsed_url = urllib.parse.urlparse(current_url)
            params = urllib.parse.parse_qs(parsed_url.query)
            
            # 現在のページ番号を取得
            current_page = int(params.get('page', [1])[0])
            next_page = current_page + 1
            
            # パラメータを更新
            params['page'] = [str(next_page)]
            
            # 新しいURLを構築
            new_query = urllib.parse.urlencode(params, doseq=True)
            next_url = urllib.parse.urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            self.logger.info(f"生成された次ページのURL: {next_url}")
            self.logger.info("=" * 50)
            
            # 次のページに移動
            await self.page.goto(next_url)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # 追加の待機時間
            
            # 移動後の確認
            self.logger.info("=" * 50)
            self.logger.info(f"移動後の実際のURL: {self.page.url}")
            self.logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"次のページへの移動に失敗しました: {str(e)}")
            return False

    async def search_short_videos(self, search_query: str, start_page: int = 1) -> List[Dict[str, Any]]:
        try:
            # 正しいURL形式で構築
            base_url = "https://www.lancers.jp/work/search"
            url = (f"{base_url}?"
                  f"sort=started&"
                  f"open=1&"  # 募集中のみ
                  f"show_description=1&"
                  f"work_rank%5B%5D=3&"  # work_rank[]の代わりにwork_rank%5B%5Dを使用
                  f"work_rank%5B%5D=2&"
                  f"work_rank%5B%5D=0&"
                  f"budget_from=&"
                  f"budget_to=&"
                  f"keyword={urllib.parse.quote(search_query)}&"
                  f"not=")
            
            # 初期URLをログ出力
            self.logger.info("=" * 50)
            self.logger.info(f"初期アクセスURL: {url}")
            self.logger.info("=" * 50)
            
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # 追加の待機時間

            results = []
            current_page = 1  # 常に1から開始

            while True:
                self.logger.info("=" * 50)
                self.logger.info(f"現在のページ: {current_page}")
                self.logger.info(f"現在のURL: {self.page.url}")
                self.logger.info("=" * 50)

                # 案件情報の取得
                work_cards = await self._get_work_cards()
                for card in work_cards:
                    work_info = await self._extract_work_info(card)
                    if work_info:
                        results.append(work_info)

                self.logger.info(f"ページ {current_page} から{len(work_cards)}件の案件情報を取得しました")

                if current_page >= self.max_pages:
                    break

                # 次のページへの移動
                next_page = current_page + 1
                next_url = (f"{base_url}?"
                          f"sort=started&"
                          f"open=1&"
                          f"show_description=1&"
                          f"work_rank%5B%5D=3&"
                          f"work_rank%5B%5D=2&"
                          f"work_rank%5B%5D=0&"
                          f"budget_from=&"
                          f"budget_to=&"
                          f"keyword={urllib.parse.quote(search_query)}&"
                          f"not=&"
                          f"page={next_page}")  # ページ番号を追加

                self.logger.info(f"次のページへ移動を試みます: {next_url}")
                
                try:
                    await self.page.goto(next_url)
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)  # 追加の待機時間
                    current_page = next_page
                except Exception as e:
                    self.logger.error(f"ページ遷移に失敗しました: {str(e)}")
                    break

            self.logger.info(f"合計 {len(results)} 件の案件情報を取得しました")
            return results

        except Exception as e:
            self.logger.error(f"検索処理中にエラーが発生しました: {str(e)}")
            raise

    async def _get_work_cards(self) -> List:
        """
        ページから案件カードの要素を取得する
        Returns:
            List: 案件カードの要素のリスト
        """
        try:
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)

            # 正しいセレクタを使用
            work_cards = await self.page.query_selector_all('.p-search-job-media.c-media.c-media--item')
            
            if not work_cards:
                self.logger.warning("案件カードが見つかりませんでした")
                return []
            
            self.logger.info(f"検索結果から{len(work_cards)}件の案件を取得しました")
            return work_cards

        except Exception as e:
            self.logger.error(f"案件カードの取得中にエラーが発生しました: {str(e)}")
            return []

    async def get_work_detail(self, work_id: str) -> Optional[Dict[str, Any]]:
        """
        案件の詳細情報を取得する
        Args:
            work_id (str): 案件ID
        Returns:
            Optional[Dict[str, Any]]: 案件の詳細情報
        """
        try:
            url = f"https://www.lancers.jp/work/detail/{work_id}"
            self.logger.info(f"案件詳細ページにアクセス: {url}")
            
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # 追加の待機時間

            # 案件が存在しない場合や閲覧制限がある場合
            if "閲覧制限" in await self.page.title():
                self.logger.warning(f"案件 {work_id} は閲覧制限があります")
                return None

            # 基本情報の取得
            title = await self._get_text('.p-work-detail-header__title')
            
            # 締め切り情報を取得
            deadline = await self._get_text('.c-definitionList__description:has-text("募集期間")')

            # 募集人数を取得
            people = await self._get_text('.c-definitionList__description:has-text("募集人数")')

            # 希望納期を取得
            delivery_date = await self._get_text('.c-definitionList__description:has-text("希望納期")')

            return {
                'title': title,
                'url': url,
                'work_id': work_id,
                'deadline': deadline,
                'people': people,
                'delivery_date': delivery_date
            }

        except Exception as e:
            self.logger.error(f"案件詳細の取得中にエラーが発生しました: {str(e)}")
            return None

    async def _get_text(self, selector: str) -> str:
        """
        指定されたセレクタの要素からテキストを取得する
        Args:
            selector (str): CSSセレクタ
        Returns:
            str: 取得したテキスト
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else ""
            return ""
        except Exception:
            return ""

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        await self.close() 