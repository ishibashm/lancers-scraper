import argparse
import logging
import sys
import os # osモジュールをインポート
from typing import Optional, List, Dict, Any # List, Dict, Any をインポート
from dotenv import load_dotenv # dotenvをインポート
from scraper.browser import LancersBrowser
from scraper.parser import LancersParser
from utils.csv_handler import CSVHandler

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
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
                      help='案件詳細情報も取得する（デフォルト：無効）')
    parser.add_argument('--data-search', action='store_true', default=False,
                      help='データ検索URLを使用してスクレイピングを行う（デフォルト：無効）')
    parser.add_argument('--data-search-project', action='store_true', default=False,
                      help='プロジェクトデータ検索URLを使用してスクレイピングを行う（デフォルト：無効）')
    parser.add_argument('--extract-urls', type=str, default=None,
                       help='CSVファイルからURLを抽出する（CSVファイルのパスを指定）')
    parser.add_argument('--url-output', type=str, default=None,
                       help='抽出したURLの出力ファイル名（指定しない場合はコンソールに出力）')
    parser.add_argument('--scrape-urls', type=str, default=None,
                       help='CSVファイルからURLを抽出し、スクレイピングする（CSVファイルのパスを指定）')
    parser.add_argument('--chunk-size', type=int, default=10,
                       help='--scrape-urls 実行時のチャンクサイズ (デフォルト: 10)')
    return parser.parse_args()

async def scrape_lancers(search_query: Optional[str] = None, output_file: Optional[str] = None, headless: bool = True, with_details: bool = False, data_search: bool = False, data_search_project: bool = False):
    """
    Lancersのスクレイピングを実行する (現在は --scrape-urls に統合されているため未使用部分あり)
    """
    logger = setup_logging()
    # (略: この関数は現状 --scrape-urls モードでは直接使用されない)
    pass # Keep function definition for potential future use

async def main():
    """メイン関数"""
    logger = setup_logging() # Setup logging once at the beginning
    try:
        # コマンドライン引数の解析
        args = parse_arguments()

        if args.extract_urls:
            # URL抽出の実行
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
            # --- CSVからURLを読み込み、詳細情報を取得して新しいファイルに保存 ---
            csv_filepath = args.scrape_urls
            logger.info(f"CSVファイルからURLを読み込み、詳細情報を取得して新しいファイルに保存します: {csv_filepath}")
            logger.info(f"チャンクサイズ: {args.chunk_size}")

            csv_handler = CSVHandler()
            original_data: List[Dict[str, Any]] = csv_handler.read_csv(csv_filepath)

            if not original_data:
                logger.warning(f"CSVファイルが空か、読み込みに失敗しました: {csv_filepath}")
                return

            # 環境変数からログイン情報を読み込む
            load_dotenv()
            email = os.getenv("LANCERS_EMAIL")
            password = os.getenv("LANCERS_PASSWORD")

            processed_data = [] # 結果を格納する新しいリスト
            processed_count = 0
            total_count = len(original_data)
            processed_rows_count = 0 # 実際に処理した行数 (中断考慮)

            try:
                browser = LancersBrowser(headless=not args.no_headless)
                parser = LancersParser()

                async with browser:
                    # ログイン試行
                    if email and password:
                        logger.info("ログインを試行します...")
                        login_successful = await browser.login(email, password)
                        if not login_successful:
                            logger.error("ログインに失敗しました。処理を中断します。")
                            return
                        logger.info("ログイン成功。詳細情報の取得を開始します。")
                    else:
                        logger.warning("ログイン情報が環境変数に設定されていません。ログインせずに続行します。")

                    # チャンク処理と続行確認
                    chunk_size = args.chunk_size
                    should_continue = True
                    for i in range(0, total_count, chunk_size):
                        if not should_continue:
                            break

                        chunk_start = i
                        chunk_end = min(i + chunk_size, total_count)
                        current_chunk_data = original_data[chunk_start:chunk_end] # 処理対象のチャンクデータ
                        logger.info(f"--- チャンク {chunk_start + 1}-{chunk_end}/{total_count} を処理開始 ---")

                        chunk_results = [] # このチャンクの結果を一時格納
                        for j, row in enumerate(current_chunk_data, start=chunk_start):
                            url = row.get('url')
                            current_row_data = row.copy() # 元の行データをコピー

                            if not url:
                                logger.warning(f"行 {j+1}: URLが見つかりません。スキップします。")
                            else:
                                logger.info(f"処理中 ({j+1}/{total_count}): {url}")
                                try:
                                    detail = await browser.get_work_detail_by_url(url)
                                    if detail:
                                        parsed_detail = parser.parse_work_detail(detail)
                                        # 元の行データに詳細情報をマージ
                                        current_row_data.update(parsed_detail)
                                        processed_count += 1
                                    else:
                                        logger.warning(f"URL {url} の詳細情報を取得できませんでした。")
                                except Exception as detail_error:
                                    logger.error(f"URL {url} の処理中にエラーが発生しました: {detail_error}")

                            chunk_results.append(current_row_data) # 処理結果（詳細情報がマージされているか、元のままか）を追加

                            # チャンク内の進捗表示
                            processed_in_chunk = j + 1 - chunk_start
                            if processed_in_chunk % 5 == 0 or (j + 1) == chunk_end:
                                logger.info(f"チャンク内 {processed_in_chunk}/{len(current_chunk_data)} 件処理完了 (全体 {j+1}/{total_count})")

                        processed_data.extend(chunk_results) # チャンクの結果を全体のリストに追加
                        processed_rows_count = chunk_end # 処理が完了した行数を更新

                        # --- チャンク処理後の続行確認 ---
                        if chunk_end < total_count:
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
                 # processed_rows_count はエラー発生前の最後のチャンク終了時点になっているはず

            # 結果を新しいCSVファイルに保存
            if processed_data:
                 # 保存対象は実際に処理された行 (中断した場合も考慮)
                 final_data_to_save = processed_data[:processed_rows_count]

                 if final_data_to_save:
                    # 希望の列順序を指定
                    desired_fieldnames = [
                        'scraped_at', 'title', 'url', 'deadline_raw',
                        'delivery_date_raw', 'people'
                    ]
                    # Note: 'deadline', 'delivery_date', 'period', 'price', 'status', 'type', 'work_id' は除外

                    try:
                        # 新しいファイル名を作成 (例: input.csv -> input_details.csv)
                        base, ext = os.path.splitext(os.path.basename(csv_filepath))
                        new_filename = f"{base}_details{ext}" # 拡張子を維持
                        # save_to_csvを呼び出して新しいファイルに保存 (指定したヘッダーを使用)
                        output_path = csv_handler.save_to_csv(final_data_to_save, new_filename, fieldnames=desired_fieldnames)
                        if output_path:
                            logger.info(f"詳細情報をマージした結果を新しいCSVファイル ({new_filename}) に保存しました: {output_path}")
                            logger.info(f"CSVに保存した総行数: {len(final_data_to_save)}")
                            logger.info(f"うち、詳細情報を取得・マージできた件数: {processed_count}")
                    except Exception as save_error:
                         logger.error(f"新しいCSVファイルの保存中にエラーが発生しました: {save_error}")
                 else:
                      logger.warning("保存するデータがありませんでした（中断または全行スキップ）。")
            else:
                 logger.warning("更新するデータがありませんでした。")

        else:
            # 通常のスクレイピングの実行 (引数が指定されなかった場合など)
            if args.search_query:
                 await scrape_lancers(
                     search_query=args.search_query,
                     output_file=args.output,
                     headless=not args.no_headless,
                     with_details=args.with_details,
                     data_search=args.data_search,
                     data_search_project=args.data_search_project
                 )
            else:
                 logger.warning("実行するタスクが指定されていません (--search-query, --extract-urls, --scrape-urls のいずれかが必要です)。")


    except KeyboardInterrupt:
        logger.info("\n処理を中断しました (KeyboardInterrupt)")
        # 必要であれば、ここでも途中経過を保存する処理を追加できる
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}", exc_info=True) # トレースバックも出力
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
