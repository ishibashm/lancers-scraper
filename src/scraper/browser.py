from playwright.sync_api import sync_playwright, Browser, Page
from typing import Optional, List, Dict, Any
import logging
import time

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

    def start(self) -> None:
        """ブラウザを起動し、新しいページを開く"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            self.logger.info("ブラウザを起動しました")
        except Exception as e:
            self.logger.error(f"ブラウザの起動に失敗しました: {str(e)}")
            raise

    def close(self) -> None:
        """ブラウザを終了する"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("ブラウザを終了しました")
        except Exception as e:
            self.logger.error(f"ブラウザの終了に失敗しました: {str(e)}")
            raise

    def _extract_work_info(self, card) -> Optional[Dict[str, str]]:
        """
        案件カードから情報を抽出する
        Args:
            card: 案件カード要素
        Returns:
            Optional[Dict[str, str]]: 抽出された案件情報
        """
        try:
            title_elem = card.query_selector('.c-media__title')
            title = title_elem.text_content() if title_elem else "タイトルなし"
            
            url_elem = card.query_selector('a.c-media__title')
            url = url_elem.get_attribute('href') if url_elem else ""
            
            deadline_elem = card.query_selector('span.p-work-detail-schedule__item__title')
            deadline = deadline_elem.text_content() if deadline_elem else "期限なし"
            
            delivery_date_elem = card.query_selector('span.p-work-detail-schedule__text')
            delivery_date = delivery_date_elem.text_content() if delivery_date_elem else "納期未設定"
            
            people_elem = card.query_selector('p.c-text.u-text-center.u-color-grey-60')
            people = people_elem.text_content() if people_elem else "人数未設定"

            return {
                'title': title.strip(),
                'url': f"https://www.lancers.jp{url}" if url else "",
                'deadline': deadline.strip(),
                'delivery_date': delivery_date.strip(),
                'people': people.strip()
            }
        except Exception as e:
            self.logger.warning(f"案件情報の抽出に失敗しました: {str(e)}")
            return None

    def _has_next_page(self) -> bool:
        """
        次のページが存在するかを確認
        Returns:
            bool: 次のページが存在するかどうか
        """
        next_button = self.page.query_selector('a.c-pagination__next:not(.is-disabled)')
        return next_button is not None

    def _go_to_next_page(self) -> bool:
        """
        次のページに移動
        Returns:
            bool: 移動が成功したかどうか
        """
        try:
            next_button = self.page.query_selector('a.c-pagination__next:not(.is-disabled)')
            if next_button:
                next_button.click()
                self.page.wait_for_load_state('networkidle')
                time.sleep(2)  # 追加の待機時間
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
            url = f"{base_url}?page={start_page}&keyword={search_query}"
            self.page.goto(url)
            self.logger.info(f"検索ページにアクセスしました: {search_query} (ページ {start_page})")

            results = []
            current_page = start_page

            while current_page <= self.max_pages:
                # ページの読み込みを待機
                self.page.wait_for_load_state('networkidle')
                time.sleep(2)  # 追加の待機時間

                # 検索結果から必要な情報を抽出
                work_cards = self.page.query_selector_all('.c-media-list__item')
                
                for card in work_cards:
                    work_info = self._extract_work_info(card)
                    if work_info:
                        results.append(work_info)

                self.logger.info(f"ページ {current_page} から{len(work_cards)}件の案件情報を取得しました")

                # 次のページが存在し、最大ページ数に達していない場合は次のページへ
                if current_page < self.max_pages and self._has_next_page():
                    if not self._go_to_next_page():
                        break
                    current_page += 1
                else:
                    break

            self.logger.info(f"合計 {len(results)} 件の案件情報を取得しました")
            return results

        except Exception as e:
            self.logger.error(f"検索処理中にエラーが発生しました: {str(e)}")
            raise

    def __enter__(self):
        """コンテキストマネージャーのエントリーポイント"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了処理"""
        self.close() 