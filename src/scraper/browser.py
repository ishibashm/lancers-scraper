from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, List, Dict, Any
import logging
import time
import asyncio
import re
import urllib.parse

class LancersBrowser:
    def __init__(self, headless: bool = True, max_pages: int = 5):
        """
        LancersBrowserクラスのコンストラクタ
        Args:
            headless (bool): ヘッドレスモードで実行するかどうか
            max_pages (int): 取得する最大ページ数 (検索モード用)
        """
        self.headless = headless
        self.max_pages = max_pages
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None # コンテキストを保持する変数を追加
        self.playwright = None
        self.base_url = "https://www.lancers.jp/work/search"

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """ブラウザを起動し、新しいコンテキストとページを開く"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            # 新しいブラウザコンテキストを作成
            self.context = await self.browser.new_context()
            self.logger.info("ブラウザコンテキストを作成しました")
            # コンテキストから新しいページを作成
            self.page = await self.context.new_page()
            self.logger.info("ブラウザを起動し、新しいページを開きました")
        except Exception as e:
            self.logger.error(f"ブラウザの起動に失敗しました: {str(e)}")
            raise

    async def close(self) -> None:
        """ブラウザとコンテキストを終了する"""
        self.logger.info("ブラウザ終了処理を開始します...")
        try:
            if self.page:
                self.logger.info("ページを閉じます...")
                await self.page.close()
                self.logger.info("ページを閉じました。")
            else:
                self.logger.info("ページは存在しないか、既に閉じられています。")

            if self.context:
                self.logger.info("ブラウザコンテキストを閉じます...")
                await self.context.close()
                self.logger.info("ブラウザコンテキストを閉じました。")
            else:
                self.logger.info("ブラウザコンテキストは存在しないか、既に閉じられています。")

            if self.browser:
                self.logger.info("ブラウザを閉じます...")
                await self.browser.close()
                self.logger.info("ブラウザを閉じました。")
            else:
                self.logger.info("ブラウザは存在しないか、既に閉じられています。")

            if self.playwright:
                self.logger.info("Playwrightインスタンスを停止します...")
                await self.playwright.stop()
                self.logger.info("Playwrightインスタンスを停止しました。")
            else:
                self.logger.info("Playwrightインスタンスは存在しないか、既に停止されています。")

            self.logger.info("ブラウザとコンテキストの終了処理が正常に完了しました。")
        except Exception as e:
            self.logger.error(f"ブラウザまたはPlaywrightの終了処理中にエラーが発生しました: {str(e)}", exc_info=True)
            # raise # ここで再raiseすると、上位のexceptブロックで二重にログが出る可能性があるので、一旦コメントアウトして様子を見る
            # もし上位でこの例外を処理する必要がある場合は、raiseを戻すか、カスタム例外をraiseする

    async def _extract_work_info(self, card) -> Optional[Dict[str, Any]]:
        """案件カードから情報を抽出する"""
        try:
            title_elem = await card.query_selector('.p-search-job-media__title')
            url_elem = await card.query_selector('a.p-search-job-media__title')
            price_elem = await card.query_selector('.p-search-job-media__price')
            type_elem = await card.query_selector('.c-badge__text')
            deadline_elem = await card.query_selector('.p-search-job-media__time-remaining')
            status_elem = await card.query_selector('.p-search-job-media__time-text')

            title = (await title_elem.text_content() if title_elem else "タイトルなし").strip()
            url = await url_elem.get_attribute('href') if url_elem else ""
            price = (await price_elem.text_content() if price_elem else "報酬未設定").strip()
            work_type = (await type_elem.text_content() if type_elem else "種別不明").strip()
            deadline = (await deadline_elem.text_content() if deadline_elem else "期限なし").strip()
            status = (await status_elem.text_content() if status_elem else "状態不明").strip()

            full_url = url if url.startswith("http") else f"https://www.lancers.jp{url}"

            return {'title': title, 'url': full_url, 'price': price,
                    'type': work_type, 'deadline': deadline, 'status': status}
        except Exception as e:
            self.logger.error(f"案件情報の抽出中にエラーが発生しました: {str(e)}")
            return None

    async def _get_work_cards(self) -> List:
        """現在のページから案件カード要素のリストを取得する"""
        try:
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            selectors = ['div.p-search-job-media', 'div[data-external-modal]']
            work_cards = []
            for selector in selectors:
                cards = await self.page.query_selector_all(selector)
                work_cards.extend(cards)
            if not work_cards: self.logger.warning("案件カードが見つかりませんでした")
            return work_cards
        except Exception as e:
            self.logger.error(f"案件カードの取得中にエラーが発生しました: {str(e)}")
            return []

    async def _go_to_page(self, url: str, page_num: int):
        """指定されたURL（必要ならページ番号付き）に遷移する"""
        target_url = url
        if page_num > 1:
            separator = '&' if '?' in url else '?'
            target_url += f"{separator}page={page_num}"
        self.logger.info(f"ページ {page_num} にアクセス: {target_url}")
        await self.page.goto(target_url)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

    async def search_short_videos(self, search_query: str, page_num: int = 1) -> List[Dict[str, Any]]:
        """キーワード検索結果の指定されたページを取得"""
        try:
            base_url = "https://www.lancers.jp/work/search"
            url = (f"{base_url}?"
                  f"sort=started&open=1&show_description=1&"
                  f"work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=0&"
                  f"budget_from=&budget_to=&"
                  f"keyword={urllib.parse.quote(search_query)}&not=")
            await self._go_to_page(url, page_num)
            work_cards = await self._get_work_cards()
            results = [await self._extract_work_info(card) for card in work_cards]
            return [res for res in results if res]
        except Exception as e:
            self.logger.error(f"キーワード検索 (ページ{page_num}) 処理中にエラー: {str(e)}")
            raise

    async def search_with_data_url(self, page_num: int = 1) -> List[Dict[str, Any]]:
        """データ検索（タスク）結果の指定されたページを取得"""
        try:
            url = "https://www.lancers.jp/work/search/task/data?open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not="
            await self._go_to_page(url, page_num)
            work_cards = await self._get_work_cards()
            results = [await self._extract_work_info(card) for card in work_cards]
            return [res for res in results if res]
        except Exception as e:
            self.logger.error(f"データ検索(タスク, ページ{page_num}) 処理中にエラー: {str(e)}")
            raise

    async def search_with_data_project_url(self, page_num: int = 1) -> List[Dict[str, Any]]:
        """データ検索（プロジェクト）結果の指定されたページを取得"""
        try:
            url = "https://www.lancers.jp/work/search/task/data?type%5B%5D=project&open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not="
            await self._go_to_page(url, page_num)
            work_cards = await self._get_work_cards()
            results = [await self._extract_work_info(card) for card in work_cards]
            return [res for res in results if res]
        except Exception as e:
            self.logger.error(f"データ検索(プロジェクト, ページ{page_num}) 処理中にエラー: {str(e)}")
            raise

    async def go_to_next_search_page(self) -> bool:
        """検索結果ページの「次へ」ボタンをクリックして次のページに移動する"""
        next_button_selector = 'span.c-pager__item--next > a'
        try:
            next_button = await self.page.query_selector(next_button_selector)
            if next_button:
                is_disabled = await next_button.evaluate('(element) => element.closest("span").classList.contains("is-disabled")')
                if not is_disabled:
                    next_page_url = await next_button.get_attribute('href')
                    self.logger.info(f"「次へ」ボタンをクリックしてページ遷移: {next_page_url}")
                    await next_button.click()
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    self.logger.info(f"ページ遷移完了。現在のURL: {self.page.url}")
                    return True
                else:
                    self.logger.info("「次へ」ボタンは無効化されています。")
                    return False
            else:
                self.logger.info("「次へ」ボタンが見つかりません。")
                return False
        except Exception as e:
            self.logger.error(f"次の検索結果ページへの遷移に失敗しました: {str(e)}")
            return False

    async def get_work_detail(self, work_id: str) -> Optional[Dict[str, Any]]:
        """案件IDから詳細情報を取得（現在は未使用の可能性）"""
        url = f"https://www.lancers.jp/work/detail/{work_id}"
        return await self.get_work_detail_by_url(url)

    async def get_work_detail_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URLから案件の詳細情報を取得する"""
        try:
            self.logger.info(f"案件詳細ページにアクセス: {url}")
            await self.page.goto(url)
            # 詳細ページの主要コンテンツが表示されるまで待機（セレクタは実際のページに合わせて調整）
            await self.page.wait_for_selector('h1.c-heading--lv1', timeout=10000)
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(1) # 念のため追加待機

            if "閲覧制限" in await self.page.title():
                self.logger.warning(f"案件 {url} は閲覧制限があります")
                return None

            title = await self._get_text('h1') or await self._get_text('.p-work-detail-header__title')

            # スケジュール情報の取得
            deadline_raw, delivery_date_raw = "", ""
            schedule_section_selector = 'p.p-work-detail-schedule'
            try:
                # スケジュールセクションが表示されるまで待つ
                await self.page.wait_for_selector(schedule_section_selector, state='visible', timeout=5000)
                schedule_items = await self.page.query_selector_all(f'{schedule_section_selector} span.p-work-detail-schedule__item')
                self.logger.info(f"Found {len(schedule_items)} schedule items for {url}") # デバッグログ
                for item in schedule_items:
                    title_elem = await item.query_selector('span.p-work-detail-schedule__item__title')
                    text_elem = await item.query_selector('span.p-work-detail-schedule__text')
                    if title_elem and text_elem:
                        item_title = (await title_elem.text_content() or "").strip()
                        item_text = (await text_elem.text_content() or "").strip()
                        self.logger.info(f"  - Schedule item found: '{item_title}' '{item_text}'") # デバッグログ
                        if '締切' in item_title:
                            deadline_raw = item_text
                            self.logger.info(f"    -> Deadline found: {deadline_raw}") # デバッグログ
                        elif '希望納期' in item_title:
                            delivery_date_raw = item_text
                            self.logger.info(f"    -> Delivery date found: {delivery_date_raw}") # デバッグログ
                    else:
                         self.logger.warning(f"  - Schedule item title or text element not found within item.") # デバッグログ
            except Exception as e:
                self.logger.warning(f"スケジュール情報の取得中にエラーまたはタイムアウト ({url}): {e}")

            # 募集人数の取得
            people = ""
            people_selectors = [
                'p:has-text("(募集人数")', # 例: <p>(募集人数2人)</p>
                '.c-definitionList__description:has-text("募集人数")' # 古い形式？
            ]
            for selector in people_selectors:
                try:
                    people_elem = await self.page.query_selector(selector)
                    if people_elem:
                        people_text = await people_elem.text_content()
                        self.logger.info(f"People text found with selector '{selector}': '{people_text}'") # デバッグログ
                        match = re.search(r'(\d+)\s*人', people_text or "")
                        if match:
                            people = match.group(1) # 数字のみ取得に変更 (parserで'人'をつける)
                            self.logger.info(f"  -> Parsed people count: {people}") # デバッグログ
                            break # 見つかったらループを抜ける
                        else:
                            # セレクタは見つかったが正規表現がマッチしない場合
                            people = (people_text or "").strip() # とりあえずそのまま格納
                            self.logger.warning(f"  -> Could not parse number from people text: '{people_text}'")
                            # break するかは状況によるが、ここでは他のセレクタも試すため break しない
                    # else:
                    #     self.logger.info(f"People selector '{selector}' not found.") # デバッグログ（多すぎる可能性）
                except Exception as e_sel:
                     self.logger.warning(f"募集人数セレクタ '{selector}' の処理中にエラー: {e_sel}")
            if not people:
                 self.logger.warning(f"募集人数が見つかりませんでした ({url})")


            work_id_match = re.search(r'/work/detail/(\d+)', url)
            work_id = work_id_match.group(1) if work_id_match else "不明"

            # parser.py が raw データを受け取るように変更
            return {
                'title': title.strip() if title else "",
                'url': url, 'work_id': work_id,
                'deadline_raw': deadline_raw, # 生データを渡す
                'people': people, # parser.pyで整形されることを期待 (数字or元のテキスト)
                'delivery_date_raw': delivery_date_raw # 生データを渡す
            }
        except Exception as e:
            self.logger.error(f"案件詳細の取得処理全体でエラーが発生しました ({url}): {str(e)}")
            return None

    async def _get_text(self, selector: str) -> str:
        """指定されたセレクタの要素からテキストを取得する"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else ""
            return ""
        except Exception: return ""

    async def login(self, email: str, password: str) -> bool:
        """Lancersにログインする"""
        try:
            if not self.page: self.logger.error("ページ未初期化"); return False

            login_url = "https://www.lancers.jp/user/login"
            self.logger.info(f"ログインページにアクセス: {login_url}")
            await self.page.goto(login_url)
            await self.page.wait_for_selector('input#UserEmail', state='visible')
            await self.page.wait_for_function("document.readyState === 'complete'")
            await asyncio.sleep(1)

            try:
                await self.page.wait_for_selector('input#UserEmail:not([disabled])')
                await self.page.fill('input#UserEmail', email)
            except Exception as e:
                self.logger.error(f"メールアドレス入力失敗: {e}")
                await self.page.screenshot(path='error_screenshot_email_fill.png')
                return False
            try:
                await self.page.wait_for_selector('input#UserPassword:not([disabled])')
                await self.page.fill('input#UserPassword', password)
                await self.page.screenshot(path='debug_screenshot_after_fill.png')
            except Exception as e:
                self.logger.error(f"パスワード入力失敗: {e}")
                await self.page.screenshot(path='error_screenshot_password_fill.png')
                return False
            try:
                await self.page.wait_for_selector('button#form_submit:not([disabled])', state='visible')
                await self.page.click('button#form_submit')
                await self.page.screenshot(path='debug_screenshot_after_click.png')
            except Exception as e:
                 self.logger.error(f"ログインボタンクリック失敗: {e}")
                 await self.page.screenshot(path='error_screenshot_button_click.png')
                 return False

            self.logger.info("ログインボタンクリック後、状態変化待機中...")
            # try:
            #      # Playwright のバージョンによっては wait_for_navigation が存在しないためコメントアウト
            #      # await self.page.wait_for_navigation(timeout=15000, wait_until='networkidle')
            #      pass # 代わりに下の sleep と要素確認で待機
            # except Exception as nav_error:
            #      self.logger.warning(f"ナビゲーション待機処理中にエラー ({nav_error})。要素での確認を試みます。")
            #      pass
            await asyncio.sleep(5)

            current_url = self.page.url
            self.logger.info(f"ログイン試行後のURL: {current_url}")
            logged_in_selectors = ['.c-header-user-dropdown__user-name', '.p-mypage-sidebar__profile__name', '#header_mypage_button', 'a[href="/mypage"]']

            # --- TypeError 修正: 正しい非同期ループを使用 ---
            logged_in_indicator_found = False
            for selector in logged_in_selectors:
                indicator = await self.page.query_selector(selector)
                if indicator:
                    self.logger.info(f"ログイン成功の兆候を発見 (要素: {selector})")
                    logged_in_indicator_found = True
                    break # 一つでも見つかればOK
            # --- 修正ここまで ---

            if "mypage" in current_url or logged_in_indicator_found:
                self.logger.info("ログインに成功しました")
                await self.page.screenshot(path='debug_screenshot_login_success.png')
                return True
            else:
                await self.page.screenshot(path='error_screenshot_login_fail.png')
                error_message = await self.page.query_selector('.c-form-error__message, .error_message, .alert-danger, #js-error')
                if error_message: self.logger.error(f"ログイン失敗: {(await error_message.text_content() or '').strip()}")
                else: self.logger.error(f"ログイン失敗。ログイン後ページ遷移せず。URL: {current_url}")
                return False
        except Exception as e:
            self.logger.error(f"ログイン処理中に予期せぬエラー: {str(e)}")
            return False

    async def __aenter__(self): await self.start(); return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): await self.close()
