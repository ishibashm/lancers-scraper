from playwright.sync_api import sync_playwright, Browser, Page
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, List, Dict, Any
import logging
import time
import asyncio

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

    async def _extract_work_info(self, card) -> Optional[Dict[str, str]]:
        """
        案件カードから情報を抽出する
        Args:
            card: 案件カード要素
        Returns:
            Optional[Dict[str, str]]: 抽出された案件情報
        """
        try:
            # デバッグのためにより詳細なカードHTMLを取得
            card_html = await card.inner_html()
            self.logger.info(f"カードHTML（一部）: {card_html[:300]}...")
            
            # すべてのテキスト要素を列挙してデバッグ
            all_texts = await card.evaluate('el => Array.from(el.querySelectorAll("*")).map(node => node.textContent.trim()).filter(text => text.length > 0)')
            self.logger.info(f"全テキスト要素: {all_texts[:10]}...")
            
            # すべてのspanタグを列挙
            all_spans = await card.query_selector_all('span')
            span_texts = []
            for span in all_spans:
                span_text = await span.text_content()
                span_class = await span.get_attribute('class')
                if span_text.strip():
                    span_texts.append(f"[{span_class}] {span_text.strip()}")
            
            self.logger.info(f"すべてのspan: {span_texts[:5]}...")
            
            # タイトルと URL
            title_elem = await card.query_selector('.c-media__title, h3.c-heading')
            title = await title_elem.text_content() if title_elem else "タイトルなし"
            
            url_elem = await card.query_selector('a.c-media__title, a[href*="/work/detail/"]')
            url = await url_elem.get_attribute('href') if url_elem else ""
            
            # 募集情報を含むすべての要素をチェック
            deadline = "期限なし"
            delivery_date = "納期未設定"
            people = "人数未設定"
            
            # 締切日時と希望納期を探す
            schedule_items = await card.query_selector_all('.p-work-detail-schedule__item')
            for item in schedule_items:
                item_text = await item.text_content()
                item_html = await item.inner_html()
                self.logger.info(f"スケジュールアイテム: {item_text.strip()} - HTML: {item_html[:50]}...")
                
                if "締切" in item_text:
                    deadline = item_text.strip()
                if "納期" in item_text or "希望" in item_text:
                    delivery_date = item_text.strip()
            
            # 募集人数を探す - さまざまなセレクタを試す
            recruit_selectors = [
                '.c-media__start-recruit-number',
                '[class*="recruit-number"]',
                'p.u-text-center',
                '.p-work-detail-reward'
            ]
            
            for selector in recruit_selectors:
                elements = await card.query_selector_all(selector)
                for elem in elements:
                    elem_text = await elem.text_content()
                    if "人" in elem_text:
                        people = elem_text.strip()
                        break
                if people != "人数未設定":
                    break
            
            # URL処理（相対パスか絶対パスかを判定）
            full_url = url if url.startswith("http") else f"https://www.lancers.jp{url}"
            
            # 案件IDを抽出
            import re
            work_id = ""
            match = re.search(r'/work/detail/(\d+)', full_url)
            if match:
                work_id = match.group(1)
            
            return {
                'title': title.strip(),
                'url': full_url,
                'work_id': work_id,
                'deadline': deadline,
                'delivery_date': delivery_date,
                'people': people
            }
        except Exception as e:
            self.logger.warning(f"案件情報の抽出に失敗しました: {str(e)}")
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
            next_button = await self.page.query_selector('a.c-pagination__next:not(.is-disabled)')
            if next_button:
                await next_button.click()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)  # 追加の待機時間
                return True
            return False
        except Exception as e:
            self.logger.error(f"次のページへの移動に失敗しました: {str(e)}")
            return False

    async def search_short_videos(self, search_query: str, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        ショート動画で検索を実行し、結果を取得する
        Args:
            search_query (str): 検索クエリ
            start_page (int): 開始ページ番号
        Returns:
            List[Dict[str, Any]]: 検索結果のリスト
        """
        try:
            # Lancersの検索ページにアクセス
            base_url = "https://www.lancers.jp/work/search"
            url = f"{base_url}?keyword={search_query}&show_description=1&sort=started&work_rank[]=0&work_rank[]=2&work_rank[]=3"
            if start_page > 1:
                url += f"&page={start_page}"
            await self.page.goto(url)
            self.logger.info(f"検索ページにアクセスしました: {search_query} (ページ {start_page})")

            results = []
            current_page = start_page

            while current_page <= self.max_pages:
                # ページの読み込みを待機
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)  # 追加の待機時間

                # ページのHTMLを確認（デバッグ用）
                html_content = await self.page.content()
                self.logger.info(f"ページのHTML長さ: {len(html_content)}文字")
                self.logger.info(f"URLを確認: {self.page.url}")

                # より一般的なセレクタで要素を探す
                all_links = await self.page.query_selector_all('a')
                self.logger.info(f"ページ内のリンク数: {len(all_links)}")
                
                # 案件リストを探す（複数のセレクタで試す）
                selectors_to_try = [
                    '.c-media-list__item',  # 元のセレクタ
                    '.c-media',             # もう少し一般的なセレクタ
                    '.p-work-list',         # 仕事リスト
                    '.p-work-card',         # 仕事カード
                    'article',              # 一般的な記事要素
                    '.c-card'               # カード要素
                ]
                
                work_cards = []  # デフォルトは空リスト
                
                for selector in selectors_to_try:
                    elements = await self.page.query_selector_all(selector)
                    self.logger.info(f"セレクタ '{selector}' の要素数: {len(elements)}")
                    
                    if len(elements) > 0:
                        self.logger.info(f"有効なセレクタを発見: {selector}")
                        # 最初のセレクタで見つかった要素で処理を続行
                        work_cards = elements
                        break
                
                for card in work_cards:
                    work_info = await self._extract_work_info(card)
                    if work_info:
                        results.append(work_info)

                self.logger.info(f"ページ {current_page} から{len(work_cards)}件の案件情報を取得しました")

                # 次のページが存在し、最大ページ数に達していない場合は次のページへ
                if current_page < self.max_pages and await self._has_next_page():
                    if not await self._go_to_next_page():
                        break
                    current_page += 1
                else:
                    break

            self.logger.info(f"合計 {len(results)} 件の案件情報を取得しました")
            return results

        except Exception as e:
            self.logger.error(f"検索処理中にエラーが発生しました: {str(e)}")
            raise

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        await self.close() 