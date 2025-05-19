import csv
import os
import logging
from typing import List, Dict, Any, Optional # Optional をインポート
from datetime import datetime

class CSVHandler:
    def __init__(self, output_dir: str = "data/output"):
        """
        CSVHandlerクラスのコンストラクタ
        Args:
            output_dir (str): CSV出力先ディレクトリ
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

        # 出力ディレクトリの作成
        try:
            os.makedirs(output_dir, exist_ok=True)
            self.logger.info(f"出力ディレクトリを作成しました: {output_dir}")
        except Exception as e:
            self.logger.error(f"出力ディレクトリの作成に失敗しました: {str(e)}")
            raise

    def generate_filename(self, prefix: str = "lancers_jobs") -> str:
        """
        タイムスタンプ付きのファイル名を生成する
        Args:
            prefix (str): ファイル名のプレフィックス
        Returns:
            str: 生成されたファイル名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.csv"

    def clean_title(self, title: str) -> str:
        """
        タイトル文字列から余計な空白や改行を削除する
        Args:
            title (str): クリーニング対象のタイトル文字列
        Returns:
            str: クリーニング後のタイトル文字列
        """
        if title:
            # 複数の空白や改行を単一の空白に置換し、前後の空白を削除
            cleaned = " ".join(title.split())
            return cleaned
        return title

    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        データのtitle列をクリーニングする
        Args:
            data (List[Dict[str, Any]]): クリーニング対象のデータ
        Returns:
            List[Dict[str, Any]]: クリーニング後のデータ
        """
        cleaned_data = []
        for item in data:
            cleaned_item = item.copy()
            if 'title' in cleaned_item:
                cleaned_item['title'] = self.clean_title(cleaned_item['title'])
            cleaned_data.append(cleaned_item)
        return cleaned_data

    # Corrected signature and logic for fieldnames=None case
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None, fieldnames: Optional[List[str]] = None) -> str:
        """
        データをCSVファイルに保存する
        Args:
            data (List[Dict[str, Any]]): 保存するデータ
            filename (str, optional): 保存するファイル名. Defaults to None.
            fieldnames (Optional[List[str]], optional): CSVのヘッダー行（指定しない場合はデータから自動推測）. Defaults to None.
        Returns:
            str: 保存したファイルのパス
        """
        try:
            if not data:
                self.logger.warning("保存するデータがありません")
                # 空のデータでもファイルは作成する（オプション）
                # return ""
                pass # Continue to potentially create an empty file if filename is provided

            # データをクリーニング
            cleaned_data = self.clean_data(data) # Even if data is empty, this should work

            # ファイル名が指定されていない場合は生成する
            if not filename:
                filename = self.generate_filename() # これはファイル名のみを返す
                filepath = os.path.join(self.output_dir, filename)
            # filename が指定されている場合、それが既に適切なパスか、相対パスかを判断
            # os.path.normpath でパス区切り文字をOS標準に正規化
            elif os.path.isabs(filename) or \
                 os.path.normpath(filename).startswith(os.path.normpath(self.output_dir)):
                filepath = filename
            else:
                # filename がディレクトリ情報を含まない単純なファイル名の場合
                filepath = os.path.join(self.output_dir, filename)

            # --- Corrected fieldnames logic ---
            _fieldnames_to_use = fieldnames # Use provided fieldnames if available
            if _fieldnames_to_use is None: # If not provided, infer from data
                if cleaned_data: # Check if there's data to infer from
                    # 推測する場合は、全てのキーの和集合を取るのがより安全
                    all_keys = set()
                    for item in cleaned_data:
                         if isinstance(item, dict):
                              all_keys.update(item.keys())
                    _fieldnames_to_use = sorted(list(all_keys))
                else:
                    _fieldnames_to_use = [] # No data, no fieldnames
            # --- End of corrected logic ---

            # CSVファイルの書き込み
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not _fieldnames_to_use:
                     self.logger.warning("ヘッダーが決定できませんでした（データも空の可能性があります）。空のファイルを保存します。")
                     f.write("") # Create an empty file
                else:
                    # extrasaction='ignore' で data に含まれる fieldnames 以外のキーを無視
                    writer = csv.DictWriter(f, fieldnames=_fieldnames_to_use, extrasaction='ignore')
                    writer.writeheader()
                    if cleaned_data: # Write rows only if data exists
                         writer.writerows(cleaned_data)

            self.logger.info(f"CSVファイルを保存しました: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"CSVファイルの保存に失敗しました: {str(e)}")
            raise # Re-raise the exception after logging

    def append_to_csv(self, data: List[Dict[str, Any]], filepath: str) -> None:
        """
        既存のCSVファイルにデータを追記する (現在は未使用の可能性あり)
        """
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
                     # 追記の場合、fieldnamesは既存ファイルに合わせるべきだが、
                     # ここでは簡略化のため、追記データから推測（キーが不足/超過する可能性あり）
                     fieldnames = sorted(list(data[0].keys()))
                     writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                     # ヘッダーは追記しない
                     writer.writerows(data)

            self.logger.info(f"CSVファイルにデータを追記しました: {filepath}")

        except Exception as e:
            self.logger.error(f"CSVファイルへの追記に失敗しました: {str(e)}")
            raise

    def read_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """
        CSVファイルからデータを読み込む
        """
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
        """
        CSVファイルから指定した列のURLを抽出する
        """
        try:
            data = self.read_csv(filepath)
            urls = [row[url_column] for row in data if url_column in row and row[url_column]]
            self.logger.info(f"CSVファイルからURLを抽出しました: {filepath}, 件数: {len(urls)}")
            return urls
        except Exception as e:
            self.logger.error(f"URLの抽出に失敗しました: {str(e)}")
            return []

    def save_scraped_data(self, data: List[Dict[str, Any]], original_filepath: str) -> str:
        """
        スクレイピングしたデータを新しいCSVファイルに保存する (main.py から直接 save_to_csv を使う方が推奨)
        """
        try:
            if not data:
                self.logger.warning("保存するデータがありません")
                return ""
            base_name = os.path.splitext(os.path.basename(original_filepath))[0]
            filename = f"{base_name}_details.csv"
            return self.save_to_csv(data, filename) # Infer fieldnames automatically
        except Exception as e:
            self.logger.error(f"スクレイピングデータの保存に失敗しました: {str(e)}")
            raise
