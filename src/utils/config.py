import os
from pathlib import Path
from typing import Dict, Any
import logging
from dotenv import load_dotenv

class Config:
    def __init__(self):
        """
        設定クラスのコンストラクタ
        - 環境変数の読み込み
        - デフォルト値の設定
        - ロギングの設定
        """
        # ロギングの設定
        self.logger = logging.getLogger(__name__)

        # .envファイルの読み込み
        load_dotenv()

        # プロジェクトのルートディレクトリを取得
        self.root_dir = Path(__file__).parent.parent.parent.absolute()

        # 基本設定
        self.config: Dict[str, Any] = {
            # ディレクトリパス
            'OUTPUT_DIR': os.path.join(self.root_dir, 'data', 'output'),
            'LOG_DIR': os.path.join(self.root_dir, 'logs'),

            # ブラウザ設定
            'HEADLESS': os.getenv('HEADLESS', 'true').lower() == 'true',
            'BROWSER_TIMEOUT': int(os.getenv('BROWSER_TIMEOUT', '30000')),
            'RETRY_COUNT': int(os.getenv('RETRY_COUNT', '3')),
            'WAIT_TIME': float(os.getenv('WAIT_TIME', '2.0')),

            # スクレイピング設定
            'MAX_PAGES': int(os.getenv('MAX_PAGES', '5')),
            'ITEMS_PER_PAGE': int(os.getenv('ITEMS_PER_PAGE', '20')),
            'BASE_URL': 'https://www.lancers.jp',
            'SEARCH_URL': 'https://www.lancers.jp/work/search',
            'SEARCH_URL_DATA': 'https://www.lancers.jp/work/search/task/data?open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not=',
            'SEARCH_URL_DATA_PROJECT': 'https://www.lancers.jp/work/search/task/data?type%5B%5D=project&open=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=1&work_rank%5B%5D=0&budget_from=&budget_to=&keyword=&not=',

            # ファイル設定
            'CSV_ENCODING': 'utf-8',
            'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'DATE_FORMAT': '%Y-%m-%d %H:%M:%S',
            'CSV_FILENAME_PREFIX': 'lancers_jobs'
        }

        # 必要なディレクトリの作成
        self._create_directories()

    def _create_directories(self) -> None:
        """必要なディレクトリを作成する"""
        try:
            # 出力ディレクトリの作成
            os.makedirs(self.config['OUTPUT_DIR'], exist_ok=True)
            self.logger.info(f"出力ディレクトリを作成しました: {self.config['OUTPUT_DIR']}")

            # ログディレクトリの作成
            os.makedirs(self.config['LOG_DIR'], exist_ok=True)
            self.logger.info(f"ログディレクトリを作成しました: {self.config['LOG_DIR']}")

        except Exception as e:
            self.logger.error(f"ディレクトリの作成に失敗しました: {str(e)}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得する
        Args:
            key (str): 設定キー
            default (Any): デフォルト値
        Returns:
            Any: 設定値
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        設定値を設定する
        Args:
            key (str): 設定キー
            value (Any): 設定値
        """
        self.config[key] = value
        self.logger.debug(f"設定を更新しました: {key} = {value}")

    def update(self, settings: Dict[str, Any]) -> None:
        """
        複数の設定値を一括更新する
        Args:
            settings (Dict[str, Any]): 設定値の辞書
        """
        self.config.update(settings)
        self.logger.debug(f"設定を一括更新しました: {settings}")

    @property
    def output_dir(self) -> str:
        """出力ディレクトリのパスを取得する"""
        return self.config['OUTPUT_DIR']

    @property
    def log_dir(self) -> str:
        """ログディレクトリのパスを取得する"""
        return self.config['LOG_DIR']

    @property
    def headless(self) -> bool:
        """ヘッドレスモードの設定を取得する"""
        return self.config['HEADLESS']

    @property
    def browser_timeout(self) -> int:
        """ブラウザのタイムアウト時間を取得する"""
        return self.config['BROWSER_TIMEOUT']
