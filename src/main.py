import argparse
import logging
import sys
import os # osモジュールをインポート
from typing import Optional, List, Dict, Any # List, Dict, Any をインポート
from dotenv import load_dotenv # dotenvをインポート
import re # 正規表現モジュールをインポート
from scraper.browser import LancersBrowser
from scraper.parser import LancersParser
from utils.csv_handler import CSVHandler
from utils.gdrive_uploader import upload_to_gdrive # 追加

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.DEBUG, # INFOからDEBUGに変更
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('scraping.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description='Lancersの案件情報をスクレイピングするツール')
    parser.add_argument('--search-query', '-q', type=str, default=None,
                      help='検索クエリ（例：Python, Web開発）')
    parser.add_argument('--output', '-o', type=str, default=None,
                      help='出力ファイル名（指定しない場合は自動生成）')
    parser.add_argument('--no-headless', action='store_true', default=False,
                      help='ヘッドレスモードを無効にする（デフォルト：有効）')
    parser.add_argument('--with-details', action='store_true', default=False,
                      help='（非推奨）案件詳細情報も取得する。--scrape-urlsを使用してください。')
    parser.add_argument('--data-search', action='store_true', default=False,
                      help='データ検索URLを使用してタスク案件をスクレイピングを行う')
    parser.add_argument('--data-search-project', action='store_true', default=False,
                      help='データ検索URLを使用してプロジェクト案件をスクレイピングを行う')
    parser.add_argument('--extract-urls', type=str, default=None,
                       help='CSVファイルからURLを抽出する（CSVファイルのパスを指定）')
    parser.add_argument('--url-output', type=str, default=None,
                       help='抽出したURLの出力ファイル名（指定しない場合はコンソールに出力）')
    parser.add_argument('--scrape-urls', type=str, default=None,
                       help='CSVファイルからURLを読み込み、ログインして詳細情報を取得し、別ファイルに保存する')
    parser.add_argument('--chunk-size', type=int, default=10,
                       help='--scrape-urls 実行時のチャンクサイズ (デフォルト: 10)')
    parser.add_argument('--max-items', type=int, default=None,
                       help='取得する最大案件数 (検索モード時)')
    parser.add_argument('--skip-confirm', action='store_true', default=False,
                       help='チャンクごとの確認をスキップする')
    # Google Drive Upload Arguments
    parser.add_argument('--upload-gdrive', action='store_true', default=False,
                        help='生成されたCSVファイルをGoogle Driveにアップロードする')
    parser.add_argument('--gdrive-folder-id', type=str, default=os.getenv('GDRIVE_FOLDER_ID'),
                        help='Google Driveのアップロード先フォルダID (環境変数 GDRIVE_FOLDER_ID でも設定可)')
    parser.add_argument('--gdrive-credentials', type=str, default=os.getenv('GDRIVE_CREDENTIALS_PATH', 'service_account.json'),
                        help='Google Drive APIの認証情報ファイル(JSON)へのパス (環境変数 GDRIVE_CREDENTIALS_PATH でも設定可)')
    return parser.parse_args()

async def scrape_lancers(
    search_query: Optional[str] = None,
    output_file: Optional[str] = None,
    headless: bool = True,
    data_search: bool = False,
    data_search_project: bool = False,
    max_items: Optional[int] = None,
    # args を個別パラメータに変更
    upload_gdrive_flag: bool = False,
    gdrive_folder_id_val: Optional[str] = None,
    gdrive_credentials_val: Optional[str] = None
):
    """
    Lancersの案件リストページをスクレイピングする
    """
    logger = setup_logging()
    load_dotenv() # .envから環境変数を読み込む

    # --- DEBUG LOGGING ---
    logger.debug(f"[scrape_lancers] Received params: upload_gdrive_flag={upload_gdrive_flag}, gdrive_folder_id_val={gdrive_folder_id_val}, gdrive_credentials_val={gdrive_credentials_val}")
    # --- END DEBUG LOGGING ---

    search_type = ""
    if data_search:
        search_type = "タスク（データ検索）"
        logger.info("データ検索URL（タスク）を使用してスクレイピングを開始します")
    elif data_search_project:
        search_type = "プロジェクト（データ検索）"
        logger.info("データ検索URL（プロジェクト）を使用してスクレイピングを開始します")
    elif search_query:
        search_type = f"キーワード検索: {search_query}"
        logger.info(f"スクレイピングを開始します。検索クエリ: {search_query}")
    else:
        logger.error("検索方法が指定されていません（--search-query, --data-search, --data-search-project のいずれか）。")
        return

    if max_items is not None:
        logger.info(f"最大取得件数: {max_items}件")

    try:
        browser = LancersBrowser(headless=headless)
        parser = LancersParser()
        csv_handler = CSVHandler()

        async with browser:
            all_results = []
            current_page = 1
            items_collected = 0

            while True:
                logger.info(f"ページ {current_page} を処理中...")
                raw_results_page = []

                if data_search:
                    raw_results_page = await browser.search_with_data_url(page_num=current_page)
                elif data_search_project:
                    raw_results_page = await browser.search_with_data_project_url(page_num=current_page)
                elif search_query:
                    raw_results_page = await browser.search_short_videos(search_query, page_num=current_page)

                if not raw_results_page:
                    logger.warning(f"ページ {current_page} で検索結果が見つかりませんでした。")
                    break

                page_items_count = len(raw_results_page)
                logger.info(f"ページ {current_page} から{page_items_count}件の案件情報を取得しました")

                items_needed = (max_items - items_collected) if max_items is not None else page_items_count
                items_to_add = min(page_items_count, items_needed)

                all_results.extend(raw_results_page[:items_to_add])
                items_collected += items_to_add

                if max_items is not None and items_collected >= max_items:
                    logger.info(f"指定された最大取得件数 ({max_items}件) に達しました。")
                    break

                logger.info("次のページへの遷移を試みます...")
                has_next = await browser.go_to_next_search_page()
                if not has_next:
                    logger.info("次のページが見つかりませんでした。スクレイピングを終了します。")
                    break

                current_page += 1
                if browser.max_pages and current_page > browser.max_pages:
                    logger.warning(f"最大ページ数 ({browser.max_pages}) に達しました。")
                    break

            if all_results:
                logger.info(f"合計 {items_collected} 件の案件情報を取得しました。")
                parsed_results = parser.parse_results(all_results)
                
                if parsed_results:
                    basic_fieldnames = ['scraped_at', 'title', 'url', 'work_id']
                    
                    current_output_filename = output_file
                    # --data-search または --data-search-project で --output の指定がない場合、専用のファイル名を生成
                    if (data_search_project or data_search) and not current_output_filename:
                        prefix = "lancers_data_search_project" if data_search_project else "lancers_data_search_task"
                        current_output_filename = csv_handler.generate_filename(prefix=prefix)
                    
                    output_path = csv_handler.save_to_csv(parsed_results, current_output_filename, fieldnames=basic_fieldnames)
                    if output_path:
                        logger.info(f"スクレイピング結果を保存しました: {output_path}")
                        logger.info(f"保存した案件数: {len(parsed_results)}件")
                        # Google Driveへのアップロード処理を追加
                        # --- DEBUG LOGGING ---
                        logger.debug(f"[scrape_lancers_upload_check] upload_gdrive_flag={upload_gdrive_flag}, gdrive_folder_id_val={gdrive_folder_id_val}")
                        # --- END DEBUG LOGGING ---
                        if upload_gdrive_flag:
                            if gdrive_folder_id_val:
                                logger.info(f"Google Driveへのアップロードを開始します: {output_path}")
                                upload_to_gdrive(output_path, gdrive_folder_id_val, gdrive_credentials_val)
                            else:
                                logger.warning("Google DriveフォルダIDが指定されていないため、アップロードをスキップします。")
                                logger.warning("--gdrive-folder-id 引数または GDRIVE_FOLDER_ID 環境変数を設定してください。")
                    else:
                        logger.warning("CSVファイルの保存に失敗したため、アップロードは行いません。")
                else:
                     logger.warning("パース結果が空でした。")
            else:
                logger.warning("最終的な検索結果がありませんでした。")

    except Exception as e:
        logger.error(f"スクレイピング ({search_type}) 中にエラーが発生しました: {str(e)}", exc_info=True)

async def main():
    """メイン関数"""
    logger = setup_logging()
    load_dotenv() # main関数直下でも念のため呼び出し (parse_argumentsでos.getenvを使うため)
    try:
        args = parse_arguments()
        # --- DEBUG LOGGING ---
        logger.debug(f"[main] Parsed args: upload_gdrive={args.upload_gdrive}, folder_id={args.gdrive_folder_id}, creds_path={args.gdrive_credentials}, search_query='{args.search_query}', output='{args.output}'")
        # --- END DEBUG LOGGING ---

        if args.extract_urls:
            logger.info(f"CSVファイルからURLを抽出します: {args.extract_urls}")
            csv_handler = CSVHandler()
            urls = csv_handler.extract_urls(args.extract_urls)
            if urls:
                if args.url_output:
                    try:
                        with open(args.url_output, 'w', encoding='utf-8') as f:
                            for url in urls:
                                f.write(url + '\n')
                        logger.info(f"URLをファイルに保存しました: {args.url_output}")
                    except Exception as write_error:
                        logger.error(f"URLファイルの書き込み中にエラー: {write_error}")
                else:
                    logger.info("抽出したURL:")
                    for url in urls:
                        print(url)
                logger.info(f"抽出されたURLの数: {len(urls)}")
            else:
                logger.warning("URLが見つかりませんでした")

        elif args.scrape_urls:
            csv_filepath = args.scrape_urls
            logger.info(f"CSVファイルからURLを読み込み、詳細情報を取得して新しいファイルに保存します: {csv_filepath}")
            logger.info(f"チャンクサイズ: {args.chunk_size}")

            csv_handler = CSVHandler()
            original_data: List[Dict[str, Any]] = csv_handler.read_csv(csv_filepath)

            if not original_data:
                logger.warning(f"CSVファイルが空か、読み込みに失敗しました: {csv_filepath}")
                return

            load_dotenv()
            email = os.getenv("LANCERS_EMAIL")
            password = os.getenv("LANCERS_PASSWORD")

            processed_data = []
            processed_count = 0
            total_count = len(original_data)

            try:
                browser = LancersBrowser(headless=not args.no_headless)
                parser = LancersParser()

                async with browser:
                    if email and password:
                        logger.info("ログインを試行します...")
                        login_successful = await browser.login(email, password)
                        if not login_successful:
                            logger.error("ログインに失敗しました。ファイル保存を試みます。")
                        else:
                            logger.info("ログイン成功。詳細情報の取得を開始します。")
                    else:
                        logger.warning("ログイン情報が環境変数に設定されていません。ログインせずに続行します。")

                    chunk_size = args.chunk_size
                    should_continue = True
                    for i in range(0, total_count, chunk_size):
                        if not should_continue:
                            break

                        chunk_start = i
                        chunk_end = min(i + chunk_size, total_count)
                        current_chunk_data = original_data[chunk_start:chunk_end]
                        logger.info(f"--- チャンク {chunk_start + 1}-{chunk_end}/{total_count} を処理開始 ---")

                        chunk_results = []
                        for j, row in enumerate(current_chunk_data, start=chunk_start):
                            url = row.get('url')
                            current_row_data = row.copy()

                            if not url:
                                logger.warning(f"行 {j+1}: URLが見つかりません。スキップします。")
                            else:
                                logger.info(f"処理中 ({j+1}/{total_count}): {url}")
                                try:
                                    detail = await browser.get_work_detail_by_url(url)
                                    if detail:
                                        parsed_detail = parser.parse_work_detail(detail)
                                        current_row_data.update(parsed_detail)
                                        processed_count += 1
                                        logger.debug(f"  詳細取得・マージ後データ (行 {j+1}): {current_row_data}")
                                    else:
                                        logger.warning(f"URL {url} の詳細情報を取得できませんでした。")
                                except Exception as detail_error:
                                    logger.error(f"URL {url} の処理中にエラーが発生しました: {detail_error}")

                            chunk_results.append(current_row_data)
                            processed_in_chunk = j + 1 - chunk_start
                            if processed_in_chunk % 5 == 0 or (j + 1) == chunk_end:
                                logger.info(f"チャンク内 {processed_in_chunk}/{len(current_chunk_data)} 件処理完了 (全体 {j+1}/{total_count})")

                        processed_data.extend(chunk_results)

                        if chunk_end < total_count:
                            if args.skip_confirm:
                                logger.info("--skip-confirm オプションにより確認なしで次のチャンクに進みます。")
                                continue
                            try:
                                response = input(f"--- チャンク {chunk_start + 1}-{chunk_end} 完了。次のチャンクに進みますか？ (y/n): ")
                                if response.lower() != 'y':
                                    logger.info("ユーザーの選択により処理を中断しました。")
                                    should_continue = False
                            except EOFError:
                                logger.warning("入力が取得できなかったため、処理を中断します。")
                                should_continue = False
                        else:
                            logger.info("--- 全てのチャンク処理が完了しました ---")

            except Exception as browser_error:
                 logger.error(f"ブラウザ処理中にエラーが発生しました: {browser_error}")
                 logger.warning("エラーが発生しましたが、それまでに処理した結果で新しいCSVファイルを作成します。")

            # --- Corrected saving logic (Simplified & Final V6) ---
            if processed_data:
                 final_data_to_save = processed_data
                 logger.info(f"CSVファイルへの保存を試みます。対象行数: {len(final_data_to_save)}")
                 if len(final_data_to_save) > 0:
                     logger.debug(f"保存直前のデータサンプル (先頭1件): {final_data_to_save[0]}")

                 if final_data_to_save:
                    # 1. Define the essential columns and their desired order
                    desired_columns_ordered = [
                        'scraped_at', 'title', 'url', 'deadline_raw',
                        'delivery_date_raw', 'people'
                    ]
                    # 2. Define columns to absolutely remove
                    columns_to_remove = {'deadline', 'delivery_date', 'price', 'type', 'status', 'work_id', 'period'}

                    # 3. Construct the final fieldnames list more robustly
                    final_fieldnames = list(desired_columns_ordered) # Start with desired order

                    # 4. Get original keys (if original data exists)
                    original_keys = []
                    if original_data:
                         original_keys = list(original_data[0].keys())

                    # 5. Add original keys that are not desired and not removed
                    for key in original_keys:
                        if key not in final_fieldnames and key not in columns_to_remove:
                            final_fieldnames.append(key)
                            
                    # 6. Add any other keys from processed data if missed (e.g., new keys from scraping)
                    all_processed_keys = set()
                    for item in final_data_to_save:
                        if isinstance(item, dict):
                           all_processed_keys.update(item.keys())
                    for key in sorted(list(all_processed_keys)):
                        if key not in final_fieldnames and key not in columns_to_remove:
                             final_fieldnames.append(key)

                    logger.info(f"最終的なCSVヘッダー (保存直前、V8): {final_fieldnames}")

                    try:
                        base, ext = os.path.splitext(os.path.basename(csv_filepath))
                        new_filename = f"{base}_details{ext}"
                        output_path = csv_handler.save_to_csv(final_data_to_save, new_filename, fieldnames=final_fieldnames)
                        if output_path:
                            logger.info(f"結果を新しいCSVファイル ({new_filename}) に保存しました: {output_path}")
                            logger.info(f"CSVに保存した総行数: {len(final_data_to_save)}")
                            logger.info(f"うち、詳細情報を取得・マージできた件数: {processed_count}")
                            # Google Driveへのアップロード処理を追加
                            if args.upload_gdrive:
                                if args.gdrive_folder_id:
                                    logger.info(f"Google Driveへのアップロードを開始します: {output_path}")
                                    upload_to_gdrive(output_path, args.gdrive_folder_id, args.gdrive_credentials)
                                else:
                                    logger.warning("Google DriveフォルダIDが指定されていないため、アップロードをスキップします。")
                                    logger.warning("--gdrive-folder-id 引数または GDRIVE_FOLDER_ID 環境変数を設定してください。")
                        else:
                            logger.warning(f"新しいCSVファイル ({new_filename}) の保存に失敗したため、アップロードは行いません。")
                    except Exception as save_error:
                         logger.error(f"新しいCSVファイルの保存中にエラーが発生しました: {save_error}")
                 else:
                      logger.warning("最終的な保存対象データが空です。")
            else:
                 logger.warning("処理されたデータがありませんでした。CSVファイルは作成されません。")
            # --- End of corrected saving logic ---

        else:
            if args.search_query or args.data_search or args.data_search_project:
                 # --- DEBUG LOGGING for scrape_lancers call ---
                 logger.debug(f"[main_pre_call_scrape_lancers] Passing to scrape_lancers: "
                              f"upload_gdrive_flag={args.upload_gdrive}, "
                              f"gdrive_folder_id_val={args.gdrive_folder_id}, "
                              f"gdrive_credentials_val={args.gdrive_credentials}")
                 # --- END DEBUG LOGGING ---
                 await scrape_lancers(
                     search_query=args.search_query,
                     output_file=args.output,
                     headless=not args.no_headless,
                     data_search=args.data_search,
                     data_search_project=args.data_search_project,
                     max_items=args.max_items,
                     # 個別パラメータとして渡す
                     upload_gdrive_flag=args.upload_gdrive,
                     gdrive_folder_id_val=args.gdrive_folder_id,
                     gdrive_credentials_val=args.gdrive_credentials
                     # apply_filter_flag は削除されたので渡さない
                 )
            else:
                 logger.warning("実行するタスクが指定されていません (--search-query, --data-search, --data-search-project, --extract-urls, --scrape-urls のいずれかが必要です)。")

    except KeyboardInterrupt:
        logger.info("\n処理を中断しました (KeyboardInterrupt)。途中までのデータを保存します...")
        # --- 中断時のCSV保存処理 ---
        # processed_dataが定義されており、かつ空でない場合に保存を試みる
        if 'processed_data' in locals() and processed_data:
            try:
                final_data_to_save = processed_data
                logger.info(f"CSVファイルへの保存を試みます (中断時)。対象行数: {len(final_data_to_save)}")

                if final_data_to_save:
                    # ヘッダー決定ロジック (通常保存時と同様)
                    desired_columns_ordered = [
                        'scraped_at', 'title', 'url', 'deadline_raw',
                        'delivery_date_raw', 'people'
                    ]
                    columns_to_remove = {'deadline', 'delivery_date', 'price', 'type', 'status', 'work_id', 'period'}
                    final_fieldnames = list(desired_columns_ordered)
                    original_keys = []
                    # original_data がスコープ内に存在するか確認
                    if 'original_data' in locals() and original_data:
                         original_keys = list(original_data[0].keys())
                    for key in original_keys:
                        if key not in final_fieldnames and key not in columns_to_remove:
                            final_fieldnames.append(key)
                    all_processed_keys = set()
                    for item in final_data_to_save:
                        if isinstance(item, dict):
                           all_processed_keys.update(item.keys())
                    for key in sorted(list(all_processed_keys)):
                        if key not in final_fieldnames and key not in columns_to_remove:
                             final_fieldnames.append(key)

                    logger.info(f"最終的なCSVヘッダー (中断時): {final_fieldnames}")

                    try:
                        # csv_filepath と csv_handler がスコープ内に存在するか確認
                        if 'csv_filepath' in locals() and 'csv_handler' in locals():
                            base, ext = os.path.splitext(os.path.basename(csv_filepath))
                            # 中断したことがわかるファイル名に変更
                            new_filename = f"{base}_details_interrupted{ext}"
                            output_path = csv_handler.save_to_csv(final_data_to_save, new_filename, fieldnames=final_fieldnames)
                            if output_path:
                                logger.info(f"中断時の結果を新しいCSVファイル ({new_filename}) に保存しました: {output_path}")
                                logger.info(f"CSVに保存した総行数: {len(final_data_to_save)}")
                                # processed_count がスコープ内に存在するか確認
                                if 'processed_count' in locals():
                                    logger.info(f"うち、詳細情報を取得・マージできた件数: {processed_count}")
                            else:
                                logger.warning(f"中断時のCSVファイルの保存に失敗しました (パス未取得)。")
                        else:
                             logger.warning("中断時のCSV保存に必要な情報 (ファイルパス/ハンドラ) が不足しています。")

                    except Exception as save_error:
                         logger.error(f"中断時のCSVファイル保存中にエラーが発生しました: {save_error}")
                else:
                      logger.warning("中断時の保存対象データが空です。")
            except Exception as general_save_error:
                 logger.error(f"中断時のデータ保存処理全体でエラーが発生しました: {general_save_error}")
        else:
            logger.info("中断時に保存するデータがありませんでした。")
        # --- 中断時のCSV保存処理ここまで ---
        sys.exit(1) # 保存試行後にプログラムを終了
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        logging.getLogger(__name__).error(f"スクリプトのトップレベルで予期せぬエラーが発生: {e}", exc_info=True)
