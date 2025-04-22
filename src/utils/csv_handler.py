import csv
import os
import logging
from typing import List, Dict, Any
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

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        データをCSVファイルに保存する
        Args:
            data (List[Dict[str, Any]]): 保存するデータ
            filename (str, optional): 保存するファイル名
        Returns:
            str: 保存したファイルのパス
        """
        try:
            if not data:
                self.logger.warning("保存するデータがありません")
                return ""

            # データをクリーニング
            cleaned_data = self.clean_data(data)

            # ファイル名が指定されていない場合は生成する
            if not filename:
                filename = self.generate_filename()

            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルの書き込み
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                # ヘッダーの取得（最初のデータのキーを使用）
                fieldnames = list(cleaned_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # ヘッダーと内容の書き込み
                writer.writeheader()
                writer.writerows(cleaned_data)

            self.logger.info(f"CSVファイルを保存しました: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"CSVファイルの保存に失敗しました: {str(e)}")
            raise

    def append_to_csv(self, data: List[Dict[str, Any]], filepath: str) -> None:
        """
        既存のCSVファイルにデータを追記する
        Args:
            data (List[Dict[str, Any]]): 追記するデータ
            filepath (str): 追記先のファイルパス
        """
        try:
            if not data:
                self.logger.warning("追記するデータがありません")
                return

            # ファイルが存在しない場合は新規作成
            if not os.path.exists(filepath):
                self.save_to_csv(data, os.path.basename(filepath))
                return

            # 既存ファイルへの追記
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                writer.writerows(data)

            self.logger.info(f"CSVファイルにデータを追記しました: {filepath}")

        except Exception as e:
            self.logger.error(f"CSVファイルへの追記に失敗しました: {str(e)}")
            raise

    def read_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """
        CSVファイルからデータを読み込む
        Args:
            filepath (str): 読み込むファイルのパス
        Returns:
            List[Dict[str, Any]]: 読み込んだデータ
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
        Args:
            filepath (str): 読み込むファイルのパス
            url_column (str): URLが記載されている列名（デフォルトは 'url'）
        Returns:
            List[str]: 抽出したURLのリスト
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
        スクレイピングしたデータを新しいCSVファイルに保存する
        Args:
            data (List[Dict[str, Any]]): 保存するスクレイピングデータ
            original_filepath (str): 元のCSVファイルのパス（ファイル名生成に使用）
        Returns:
            str: 保存したファイルのパス
        """
        try:
            if not data:
                self.logger.warning("保存するデータがありません")
                return ""

            # ファイル名を生成（元のファイル名に '_scraped' を追加）
            base_name = os.path.splitext(os.path.basename(original_filepath))[0]
            filename = f"{base_name}_scraped.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルの書き込み
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                # ヘッダーの取得（最初のデータのキーを使用）
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # ヘッダーと内容の書き込み
                writer.writeheader()
                writer.writerows(data)

            self.logger.info(f"スクレイピングデータをCSVファイルに保存しました: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"スクレイピングデータの保存に失敗しました: {str(e)}")
            raise
