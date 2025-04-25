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
            base_url = "https://www.lancers.jp/work/search"
            results = []
            current_page = 1

            # 初期URLを構築
            url = (f"{base_url}?"
                  f"sort=started&"
                  f"open=1&"
                  f"show_description=1&"
                  f"work_rank%5B%5D=3&"
                  f"work_rank%5B%5D=2&"
                  f"work_rank%5B%5D=0&"
                  f"budget_from=&"
                  f"budget_to=&"
                  f"keyword={urllib.parse.quote(search_query)}&"
                  f"not=")
            
            # 環境変数を読み込む
            from dotenv import load_dotenv
            import os
            load_dotenv()
            # Login should be handled before calling search methods if needed
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)

            # 総件数を取得
            total_count_elem = await self.page.query_selector('.p-search-job-count__number')
            total_count = 0
            if total_count_elem:
                count_text = await total_count_elem.text_content()
                try:
                    total_count = int(re.search(r'\d+', count_text).group())
                    self.logger.info(f"総件数: {total_count}件")
                except (AttributeError, ValueError):
                    self.logger.warning("総件数の取得に失敗しました")

            while True:
                self.logger.info(f"ページ {current_page} を処理中...")

                # 案件カードを取得
                work_cards = await self._get_work_cards()
                for card in work_cards:
                    work_info = await self._extract_work_info(card)
                    if work_info:
                        results.append(work_info)

                self.logger.info(f"ページ {current_page} から{len(work_cards)}件の案件情報を取得しました")

                # 次のページの有無を確認
                next_button = await self.page.query_selector('a.c-pagination__next:not(.is-disabled)')
                if not next_button or current_page >= self.max_pages:
                    break

                # 次のページへ移動
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
                    await asyncio.sleep(2)
                    current_page = next_page
                except Exception as e:
                    self.logger.error(f"ページ遷移に失敗しました: {str(e)}")
                    break

            self.logger.info(f"合計 {len(results)} 件の案件情報を取得しました（総件数: {total_count}件）")
            return results

        except Exception as e:
            self.logger.error(f"検索処理中にエラーが発生しました: {str(e)}")
            raise

    async def search_with_data_url(self, start_page: int = 1) -> List[Dict[str, Any]]:
        try:
            # データ検索URLを使用
            url = "https://www.lancers.jp/work/search/task/data?open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not="
            
            # 初期URLをログ出力
            self.logger.info("=" * 50)
            self.logger.info(f"データ検索初期アクセスURL: {url}")
            self.logger.info("=" * 50)
            
            # 環境変数を読み込む
            from dotenv import load_dotenv
            import os
            load_dotenv()
            # Login should be handled before calling search methods if needed
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
                next_url = f"{url}&page={next_page}"  # ページ番号を追加

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
            self.logger.error(f"データ検索処理中にエラーが発生しました: {str(e)}")
            raise

    async def search_with_data_project_url(self, start_page: int = 1) -> List[Dict[str, Any]]:
        try:
            # プロジェクトデータ検索URLを使用
            url = "https://www.lancers.jp/work/search/task/data?type%5B%5D=project&open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not="
            
            # 初期URLをログ出力
            self.logger.info("=" * 50)
            self.logger.info(f"プロジェクトデータ検索初期アクセスURL: {url}")
            self.logger.info("=" * 50)
            
            # 環境変数を読み込む
            from dotenv import load_dotenv
            import os
            load_dotenv()
            # Login should be handled before calling search methods if needed
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
                next_url = f"{url}&page={next_page}"  # ページ番号を追加

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
            self.logger.error(f"プロジェクトデータ検索処理中にエラーが発生しました: {str(e)}")
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

            # より包括的なセレクタを使用
            selectors = [
                'div.p-search-job-media',  # 通常の案件カード
                'div[data-external-modal]'  # 外部リンクの案件カード
            ]
            
            work_cards = []
            for selector in selectors:
                cards = await self.page.query_selector_all(selector)
                work_cards.extend(cards)

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
            
            # 特定の要素が表示されるまで待機（ページロード完了の確認）
            try:
                await self.page.wait_for_selector('h1', timeout=5000)
            except Exception:
                self.logger.warning("ページロード完了の確認に失敗しました。処理を続行します。")
            
            await asyncio.sleep(2)  # 追加の待機時間

            # 案件が存在しない場合や閲覧制限がある場合
            if "閲覧制限" in await self.page.title():
                self.logger.warning(f"案件 {work_id} は閲覧制限があります")
                return None

            # 基本情報の取得
            title = await self._get_text('h1') or await self._get_text('.p-work-detail-header__title')
            
            # ページ全体のテキストを取得して正規表現で解析
            page_text = await self.page.evaluate('document.body.innerText')
            
            # 複数の方法で情報を抽出
            detail_info = {}
            
            # 締切と希望納期をユーザー指定セレクタで抽出
            deadline = ""
            delivery_date = ""
            schedule_items = await self.page.query_selector_all('span.p-work-detail-schedule__item')
            for item in schedule_items:
                item_title_elem = await item.query_selector('span.p-work-detail-schedule__item__title')
                item_text_elem = await item.query_selector('span.p-work-detail-schedule__text')
                if item_title_elem and item_text_elem:
                    item_title = await item_title_elem.text_content()
                    item_text = await item_text_elem.text_content()
                    if item_title and item_text:
                        if '締切' in item_title:
                            deadline = item_text.strip()
                        elif '希望納期' in item_title:
                            delivery_date = item_text.strip()

            # 他の情報も抽出（既存のロジックを流用・調整）
            # 他の情報も抽出（募集人数は複数のセレクタを試す）
            people = ""
            # まず <p>(募集人数X人)</p> 形式を探す
            people_p_elem = await self.page.query_selector('p:has-text("(募集人数")')
            if people_p_elem:
                people_text = await people_p_elem.text_content()
                match = re.search(r'\(募集人数(\d+)人\)', people_text)
                if match:
                    people = match.group(1) + "人" # parser側で数字のみ抽出する想定
            
            # 上記で見つからなければ、従来の方法を試す
            if not people:
                 people_elem = await self.page.query_selector('.c-definitionList__description:has-text("募集人数")')
                 if people_elem:
                     people = await people_elem.text_content()

            period_elem = await self.page.query_selector('.c-definitionList__description:has-text("募集期間")')
            period = await period_elem.text_content() if period_elem else ""

            return {
                'title': title.strip() if title else "",
                'url': url, # Keep original URL
                'work_id': work_id, # Keep work_id extracted from URL
                'deadline': deadline, # Use newly extracted deadline
                'people': people.strip() if people else "",
                'delivery_date': delivery_date, # Use newly extracted delivery_date
                'period': period.strip() if period else ""
                # Removed detail_info for cleaner output
            }

        except Exception as e:
            self.logger.error(f"案件詳細の取得中にエラーが発生しました: {str(e)}")
            return None

    async def get_work_detail_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        URLから案件の詳細情報を取得する
        Args:
            url (str): 案件のURL
        Returns:
            Optional[Dict[str, Any]]: 案件の詳細情報
        """
        try:
            self.logger.info(f"案件詳細ページにアクセス: {url}")
            
            # 環境変数を読み込む
            from dotenv import load_dotenv
            import os
            load_dotenv()
            # Login should be handled before calling this method
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # 特定の要素が表示されるまで待機（ページロード完了の確認）
            try:
                await self.page.wait_for_selector('h1', timeout=5000)
            except Exception:
                self.logger.warning("ページロード完了の確認に失敗しました。処理を続行します。")
            
            await asyncio.sleep(2)  # 追加の待機時間

            # 案件が存在しない場合や閲覧制限がある場合
            if "閲覧制限" in await self.page.title():
                self.logger.warning(f"案件 {url} は閲覧制限があります")
                return None

            # 基本情報の取得
            title = await self._get_text('h1') or await self._get_text('.p-work-detail-header__title')
            
            # ページ全体のテキストを取得して正規表現で解析
            page_text = await self.page.evaluate('document.body.innerText')
            
            # 複数の方法で情報を抽出
            detail_info = {}
            
            # 締切と希望納期をユーザー指定セレクタで抽出
            deadline = ""
            delivery_date = ""
            schedule_items = await self.page.query_selector_all('span.p-work-detail-schedule__item')
            for item in schedule_items:
                item_title_elem = await item.query_selector('span.p-work-detail-schedule__item__title')
                item_text_elem = await item.query_selector('span.p-work-detail-schedule__text')
                if item_title_elem and item_text_elem:
                    item_title = await item_title_elem.text_content()
                    item_text = await item_text_elem.text_content()
                    if item_title and item_text:
                        if '締切' in item_title:
                            deadline = item_text.strip()
                        elif '希望納期' in item_title:
                            delivery_date = item_text.strip()

            # 他の情報も抽出（既存のロジックを流用・調整）
            # 他の情報も抽出（募集人数は複数のセレクタを試す）
            people = ""
            # まず <p>(募集人数X人)</p> 形式を探す
            people_p_elem = await self.page.query_selector('p:has-text("(募集人数")')
            if people_p_elem:
                 people_text = await people_p_elem.text_content()
                 match = re.search(r'\(募集人数(\d+)人\)', people_text)
                 if match:
                     people = match.group(1) + "人" # parser側で数字のみ抽出する想定

            # 上記で見つからなければ、従来の方法を試す
            if not people:
                 people_elem = await self.page.query_selector('.c-definitionList__description:has-text("募集人数")')
                 if people_elem:
                     people = await people_elem.text_content()

            period_elem = await self.page.query_selector('.c-definitionList__description:has-text("募集期間")')
            period = await period_elem.text_content() if period_elem else ""

            # URLからwork_idを抽出
            work_id_match = re.search(r'/work/detail/(\d+)', url)
            work_id = work_id_match.group(1) if work_id_match else "不明"

            return {
                'title': title.strip() if title else "",
                'url': url, # Keep original URL
                'work_id': work_id, # Keep work_id extracted from URL
                'deadline': deadline, # Use newly extracted deadline
                'people': people.strip() if people else "",
                'delivery_date': delivery_date, # Use newly extracted delivery_date
                'period': period.strip() if period else ""
                # Removed detail_info for cleaner output
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
    
    async def login(self, email: str, password: str) -> bool: # 引数名を email に変更
        """
        Lancersにログインする
        Args:
            email (str): ログイン用のメールアドレス
            password (str): ログイン用のパスワード
        Returns:
            bool: ログインが成功したかどうか
        """
        try:
            if not self.page:
                self.logger.error("ページが初期化されていません。ログインできません。")
                return False

            login_url = "https://www.lancers.jp/user/login"
            self.logger.info(f"ログインページにアクセス: {login_url}")
            await self.page.goto(login_url)
            # Wait for email field to be visible and stable
            await self.page.wait_for_selector('input#UserEmail', state='visible')
            await self.page.wait_for_function("document.readyState === 'complete'")
            await asyncio.sleep(1) # Small extra delay

            # ログイン情報入力
            try:
                 # Wait for the element to be editable
                await self.page.wait_for_selector('input#UserEmail:not([disabled])')
                await self.page.fill('input#UserEmail', email)
            except Exception as e:
                self.logger.error(f"メールアドレス入力フィールドが見つからないか、入力できませんでした: {e}")
                await self.page.screenshot(path='error_screenshot_email_fill.png') # Debug screenshot
                return False

            try:
                 # Wait for the element to be editable
                await self.page.wait_for_selector('input#UserPassword:not([disabled])')
                await self.page.fill('input#UserPassword', password)
                await self.page.screenshot(path='debug_screenshot_after_fill.png') # Debug screenshot after filling
            except Exception as e:
                self.logger.error(f"パスワード入力フィールドが見つからないか、入力できませんでした: {e}")
                await self.page.screenshot(path='error_screenshot_password_fill.png') # Debug screenshot
                return False
            
            # ログインボタンクリック
            try:
                # Wait for button to be enabled and visible
                await self.page.wait_for_selector('button#form_submit:not([disabled])', state='visible')
                await self.page.click('button#form_submit')
                await self.page.screenshot(path='debug_screenshot_after_click.png') # Debug screenshot immediately after click
            except Exception as e:
                 self.logger.error(f"ログインボタンが見つからないか、クリックできませんでした: {e}")
                 await self.page.screenshot(path='error_screenshot_button_click.png') # Debug screenshot
                 return False
            
            # Navigation or content change after click might take time
            self.logger.info("ログインボタンクリック後、ナビゲーション/状態変化待機中...")
            try:
                 # Wait for either navigation or a common logged-in element to appear
                 # Increased timeout to handle potentially slow redirects or checks
                 await self.page.wait_for_navigation(timeout=15000, wait_until='networkidle') 
            except Exception as nav_error:
                 self.logger.warning(f"ナビゲーション待機タイムアウト ({nav_error})。要素でのログイン成功確認を試みます。")
                 # If navigation times out, still check for logged-in indicators
                 pass
            
            await asyncio.sleep(5) # Increased wait time after potential navigation/action

            # ログイン成功確認 (複数の要素とURLで確認)
            current_url = self.page.url
            self.logger.info(f"ログイン試行後のURL: {current_url}")
            
            # Common indicators of being logged in
            logged_in_selectors = [
                '.c-header-user-dropdown__user-name', # Header user name
                '.p-mypage-sidebar__profile__name',    # Mypage sidebar name
                '#header_mypage_button',               # Mypage button in header
                'a[href="/mypage"]'                    # Direct link to mypage
            ]
            logged_in_indicator_found = False
            for selector in logged_in_selectors:
                indicator = await self.page.query_selector(selector)
                if indicator:
                    self.logger.info(f"ログイン成功の兆候を発見 (要素: {selector})")
                    logged_in_indicator_found = True
                    break # Stop checking once one indicator is found

            # Final check based on URL and indicators
            if "mypage" in current_url or logged_in_indicator_found:
                self.logger.info("ログインに成功しました")
                await self.page.screenshot(path='debug_screenshot_login_success.png') # Screenshot on success
                return True
            else:
                await self.page.screenshot(path='error_screenshot_login_fail.png') # Screenshot on failure
                # Check for explicit error messages again
                error_message = await self.page.query_selector('.c-form-error__message, .error_message, .alert-danger, #js-error') # Added generic error id
                if error_message:
                    error_text = await error_message.text_content()
                    self.logger.error(f"ログインに失敗しました: {error_text.strip()}")
                else:
                     self.logger.error(f"ログインに失敗しました。ログイン後のページに遷移しませんでした。現在のURL: {current_url}")
                return False

        except Exception as e:
            self.logger.error(f"ログイン処理中に予期せぬエラーが発生しました: {str(e)}")
            return False

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        await self.close()
