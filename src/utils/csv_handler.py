import csv
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re # 正規表現モジュールをインポート

class CSVHandler:
    def __init__(self, output_dir: str = "data/output"):
        """
        CSVHandlerクラスのコンストラクタ
        Args:
            output_dir (str): CSV出力先ディレクトリ
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

        try:
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"出力ディレクトリを作成しました: {output_dir}")
        except Exception as e:
            self.logger.error(f"出力ディレクトリの作成に失敗しました: {str(e)}")
            raise

    def generate_filename(self, prefix: str = "lancers_jobs") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.csv"

    def clean_title(self, title: str) -> str:
        if title:
            cleaned = " ".join(title.split())
            return cleaned
        return title

    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_data = []
        for item in data:
            cleaned_item = item.copy()
            if 'title' in cleaned_item:
                cleaned_item['title'] = self.clean_title(cleaned_item['title'])
            cleaned_data.append(cleaned_item)
        return cleaned_data

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None, fieldnames: Optional[List[str]] = None) -> str:
        try:
            if not data and fieldnames is None: # データもフィールド名も無い場合は警告して空ファイル
                self.logger.warning("保存するデータもフィールド名もありません。空のファイルを作成します。")
                if not filename:
                    filename = self.generate_filename()
                filepath = os.path.join(self.output_dir, filename) if not (os.path.isabs(filename) or os.path.normpath(filename).startswith(os.path.normpath(self.output_dir))) else filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("")
                return filepath
            
            cleaned_data = self.clean_data(data)

            if not filename:
                filename = self.generate_filename()
                filepath = os.path.join(self.output_dir, filename)
            elif os.path.isabs(filename) or \
                 os.path.normpath(filename).startswith(os.path.normpath(self.output_dir)):
                filepath = filename
            else:
                filepath = os.path.join(self.output_dir, filename)

            _fieldnames_to_use = fieldnames
            if _fieldnames_to_use is None:
                if cleaned_data:
                    all_keys = set()
                    for item in cleaned_data:
                         if isinstance(item, dict):
                              all_keys.update(item.keys())
                    _fieldnames_to_use = sorted(list(all_keys))
                else: # データが空でもフィールド名が指定されていればそれを使う
                    _fieldnames_to_use = [] 
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not _fieldnames_to_use:
                     self.logger.warning("ヘッダーが決定できませんでした。空のファイルを保存します。")
                     f.write("")
                else:
                    writer = csv.DictWriter(f, fieldnames=_fieldnames_to_use, extrasaction='ignore')
                    writer.writeheader()
                    if cleaned_data:
                         writer.writerows(cleaned_data)

            self.logger.info(f"CSVファイルを保存しました: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"CSVファイルの保存に失敗しました: {str(e)}")
            raise

    def append_to_csv(self, data: List[Dict[str, Any]], filepath: str) -> None:
        try:
            if not data:
                self.logger.warning("追記するデータがありません")
                return

            file_exists = os.path.exists(filepath)
            if not file_exists:
                 self.save_to_csv(data, os.path.basename(filepath))
                 return

            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                if data:
                     fieldnames = sorted(list(data[0].keys()))
                     writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                     writer.writerows(data)

            self.logger.info(f"CSVファイルにデータを追記しました: {filepath}")

        except Exception as e:
            self.logger.error(f"CSVファイルへの追記に失敗しました: {str(e)}")
            raise

    def read_csv(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(filepath):
                self.logger.error(f"ファイルが存在しません: {filepath}")
                return []
            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = [row for row in reader]
            self.logger.info(f"CSVファイルを読み込みました: {filepath}")
            return data
        except Exception as e:
            self.logger.error(f"CSVファイルの読み込みに失敗しました: {str(e)}")
            return []

    def extract_urls(self, filepath: str, url_column: str = 'url') -> List[str]:
        try:
            data = self.read_csv(filepath)
            urls = [row[url_column] for row in data if url_column in row and row[url_column]]
            self.logger.info(f"CSVファイルからURLを抽出しました: {filepath}, 件数: {len(urls)}")
            return urls
        except Exception as e:
            self.logger.error(f"URLの抽出に失敗しました: {str(e)}")
            return []

    def save_scraped_data(self, data: List[Dict[str, Any]], original_filepath: str) -> str:
        try:
            if not data:
                self.logger.warning("保存するデータがありません")
                return ""
            base_name = os.path.splitext(os.path.basename(original_filepath))[0]
            filename = f"{base_name}_details.csv"
            return self.save_to_csv(data, filename)
        except Exception as e:
            self.logger.error(f"スクレイピングデータの保存に失敗しました: {str(e)}")
            raise
