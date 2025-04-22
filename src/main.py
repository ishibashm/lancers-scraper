import argparse
import logging
import sys
from typing import Optional
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
    return parser.parse_args()

async def scrape_lancers(search_query: Optional[str] = None, output_file: Optional[str] = None, headless: bool = True, with_details: bool = False, data_search: bool = False, data_search_project: bool = False):
    """
    Lancersのスクレイピングを実行する
    Args:
        search_query (Optional[str]): 検索クエリ
        output_file (Optional[str]): 出力ファイル名
        headless (bool): ヘッドレスモードで実行するかどうか
        with_details (bool): 案件詳細情報も取得するかどうか
        data_search (bool): データ検索URLを使用するかどうか
        data_search_project (bool): プロジェクトデータ検索URLを使用するかどうか
    """
    logger = setup_logging()
    if data_search:
        logger.info("データ検索URLを使用してスクレイピングを開始します")
    elif data_search_project:
        logger.info("プロジェクトデータ検索URLを使用してスクレイピングを開始します")
    else:
        logger.info(f"スクレイピングを開始します。検索クエリ: {search_query}")

    try:
        # 各コンポーネントの初期化
        browser = LancersBrowser(headless=headless)
        parser = LancersParser()
        csv_handler = CSVHandler()

        # ブラウザでスクレイピングを実行
        async with browser:
            # 検索実行と結果取得
            if data_search:
                raw_results = await browser.search_with_data_url()
            elif data_search_project:
                raw_results = await browser.search_with_data_project_url()
            else:
                if search_query is None:
                    logger.error("検索クエリが指定されていません")
                    return
                raw_results = await browser.search_short_videos(search_query)
            if not raw_results:
                logger.warning("検索結果が見つかりませんでした")
                return

            # 案件詳細の取得
            if with_details:
                logger.info("案件詳細情報の取得を開始します")
                detailed_results = []
                for result in raw_results:
                    work_id = parser.parse_work_id(result['url'])
                    if work_id:
                        detail = await browser.get_work_detail(work_id)
                        if detail:
                            parsed_detail = parser.parse_work_detail(detail)
                            detailed_results.append(parsed_detail)
                        else:
                            logger.warning(f"案件 {work_id} の詳細情報を取得できませんでした")
                
                if detailed_results:
                    # 詳細情報をCSVファイルに保存
                    output_path = csv_handler.save_to_csv(detailed_results, output_file)
                    if output_path:
                        logger.info(f"詳細情報を保存しました: {output_path}")
                        logger.info(f"取得した案件数: {len(detailed_results)}件")
            else:
                # 基本情報のみパースしてCSVファイルに保存
                parsed_results = parser.parse_results(raw_results)
                if parsed_results:
                    output_path = csv_handler.save_to_csv(parsed_results, output_file)
                    if output_path:
                        logger.info(f"スクレイピング結果を保存しました: {output_path}")
                        logger.info(f"取得した案件数: {len(parsed_results)}件")

    except Exception as e:
        logger.error(f"スクレイピング中にエラーが発生しました: {str(e)}")
        raise

async def main():
    """メイン関数"""
    try:
        # コマンドライン引数の解析
        args = parse_arguments()
        
        # スクレイピングの実行
        await scrape_lancers(
            search_query=args.search_query,
            output_file=args.output,
            headless=not args.no_headless,
            with_details=args.with_details,
            data_search=args.data_search,
            data_search_project=args.data_search_project
        )

    except KeyboardInterrupt:
        print("\nスクレイピングを中断しました")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
