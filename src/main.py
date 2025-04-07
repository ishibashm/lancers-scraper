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
    parser.add_argument('--search-query', '-q', type=str, required=True,
                      help='検索クエリ（例：Python, Web開発）')
    parser.add_argument('--output', '-o', type=str, default=None,
                      help='出力ファイル名（指定しない場合は自動生成）')
    parser.add_argument('--headless', action='store_true', default=True,
                      help='ヘッドレスモードで実行（デフォルト：True）')
    return parser.parse_args()

async def scrape_lancers(search_query: str, output_file: Optional[str] = None, headless: bool = True):
    """
    Lancersのスクレイピングを実行する
    Args:
        search_query (str): 検索クエリ
        output_file (Optional[str]): 出力ファイル名
        headless (bool): ヘッドレスモードで実行するかどうか
    """
    logger = setup_logging()
    logger.info(f"スクレイピングを開始します。検索クエリ: {search_query}")

    try:
        # 各コンポーネントの初期化
        browser = LancersBrowser(headless=headless)
        parser = LancersParser()
        csv_handler = CSVHandler()

        # ブラウザでスクレイピングを実行
        with browser:
            # 検索実行と結果取得
            raw_results = await browser.search_short_videos(search_query)
            if not raw_results:
                logger.warning("検索結果が見つかりませんでした")
                return

            # 結果のパース
            parsed_results = parser.parse_results(raw_results)
            if not parsed_results:
                logger.warning("結果のパースに失敗しました")
                return

            # CSVファイルに保存
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
            headless=args.headless
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
