from typing import List, Dict, Any
import re
import logging
from datetime import datetime

class LancersParser:
    def __init__(self):
        """
        LancersParserクラスのコンストラクタ
        """
        # ロギングの設定
        self.logger = logging.getLogger(__name__)

    def parse_work_id(self, url: str) -> str:
        """
        案件URLから案件IDを抽出する
        Args:
            url (str): 案件のURL
        Returns:
            str: 案件ID
        """
        try:
            if not url:
                return ""
            match = re.search(r'/work/detail/(\d+)', url)
            return match.group(1) if match else ""
        except Exception as e:
            self.logger.error(f"案件IDの抽出に失敗しました: {str(e)}")
            return ""

    def parse_deadline(self, deadline: str) -> str:
        """
        締切日時を整形する
        Args:
            deadline (str): 締切日時の文字列
        Returns:
            str: 整形された締切日時
        """
        try:
            if not deadline or deadline == "期限なし":
                return deadline
            # 不要な文字を削除し、日時形式を整形
            deadline = re.sub(r'締切|：|\s+', '', deadline)
            return deadline
        except Exception as e:
            self.logger.error(f"締切日時の解析に失敗しました: {str(e)}")
            return deadline

    def parse_delivery_date(self, delivery_date: str) -> str:
        """
        希望納期を整形する
        Args:
            delivery_date (str): 希望納期の文字列
        Returns:
            str: 整形された希望納期
        """
        try:
            if not delivery_date or delivery_date == "納期未設定":
                return delivery_date
            # 不要な文字を削除し、日時形式を整形
            delivery_date = re.sub(r'希望納期|：|\s+', '', delivery_date)
            return delivery_date
        except Exception as e:
            self.logger.error(f"希望納期の解析に失敗しました: {str(e)}")
            return delivery_date

    def parse_people(self, people: str) -> str:
        """
        募集人数を整形する
        Args:
            people (str): 募集人数の文字列
        Returns:
            str: 整形された募集人数
        """
        try:
            if not people or people == "人数未設定":
                return people
                
            # 数字のみを抽出（様々なパターンに対応）
            # パターン1: 募集人数X人
            people_match = re.search(r'募集人数\s*(\d+)\s*人', people)
            if people_match:
                return people_match.group(1)
                
            # パターン2: (募集人数X人)
            paren_match = re.search(r'\(募集人数\s*(\d+)\s*人\)', people)
            if paren_match:
                return paren_match.group(1)
                
            # パターン3: 単に数字が含まれている
            num_match = re.search(r'(\d+)', people)
            if num_match:
                return num_match.group(1)
                
            return people
        except Exception as e:
            self.logger.error(f"募集人数の解析に失敗しました: {str(e)}")
            return people

    def format_date(self, date_str: str) -> str:
        """
        日本語の日付形式を標準形式（YYYY-MM-DD）に変換
        Args:
            date_str (str): 変換する日付文字列（例：2025年04月21日 18:17）
        Returns:
            str: 変換後の日付文字列（例：2025-04-21 18:17）
        """
        try:
            if not date_str:
                return ""
                
            # 年月日の抽出
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if not date_match:
                return date_str
                
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)  # 1桁の場合は0埋め
            day = date_match.group(3).zfill(2)    # 1桁の場合は0埋め
            
            # 時刻がある場合は取得
            time_match = re.search(r'(\d{1,2}):(\d{1,2})', date_str)
            if time_match:
                hour = time_match.group(1).zfill(2)
                minute = time_match.group(2).zfill(2)
                return f"{year}-{month}-{day} {hour}:{minute}"
            
            return f"{year}-{month}-{day}"
        except Exception as e:
            self.logger.error(f"日付形式の変換に失敗しました: {str(e)}")
            return date_str

    def parse_work_detail(self, detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        案件詳細情報をパースする
        Args:
            detail (Dict[str, Any]): 案件詳細情報
        Returns:
            Dict[str, Any]: パース済みの案件詳細情報
        """
        try:
            # 締切日時のパース (正しいキー名を使用)
            deadline_raw = detail.get('deadline_raw', '') # 'deadline' -> 'deadline_raw'
            deadline = self.parse_deadline(deadline_raw) # parse_deadline は _raw 無しの整形用なのでそのまま
            # 標準形式に変換
            deadline_formatted = self.format_date(deadline)
            
            # 募集人数のパース
            people = self.parse_people(detail.get('people', '')) # people はキー名が一致している
            
            # 希望納期のパース (正しいキー名を使用)
            delivery_date_raw = detail.get('delivery_date_raw', '') # 'delivery_date' -> 'delivery_date_raw'
            delivery_date = self.parse_delivery_date(delivery_date_raw) # parse_delivery_date は _raw 無しの整形用なのでそのまま
            # 標準形式に変換
            delivery_date_formatted = self.format_date(delivery_date)
            
            # 募集期間のパース
            period = detail.get('period', '') # period は現在CSV出力から除外されている

            # --- deadline_raw から日付部分を抽出し、YYYY-MM-DD 形式に変換 ---
            deadline_yyyy_mm_dd = ""
            if deadline_raw:
                try:
                    # まず時間部分があれば削除
                    date_part = deadline_raw.split(' ', 1)[0]
                    # 年月日を正規表現で抽出
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_part)
                    if date_match:
                        year = date_match.group(1)
                        month = date_match.group(2).zfill(2) # 0埋め
                        day = date_match.group(3).zfill(2)   # 0埋め
                        deadline_yyyy_mm_dd = f"{year}-{month}-{day}"
                        self.logger.debug(f"Formatted deadline_raw to YYYY-MM-DD: '{deadline_yyyy_mm_dd}'")
                    else:
                        # マッチしない場合は元の（時間削除後の）日付部分を使用
                        deadline_yyyy_mm_dd = date_part
                        self.logger.warning(f"Could not parse YYYY年MM月DD日 from '{date_part}'. Using it as is.")
                except Exception as format_error:
                    self.logger.error(f"Error formatting deadline_raw '{deadline_raw}' to YYYY-MM-DD: {format_error}. Using original raw value.")
                    deadline_yyyy_mm_dd = deadline_raw # エラー時は元の値に戻す
            # --- 変換ここまで ---

            # デバッグログ: 返す直前の値を確認 (YYYY-MM-DD形式の値を出力)
            self.logger.info(f"Parser returning: deadline_raw(YYYY-MM-DD)='{deadline_yyyy_mm_dd}', delivery_date_raw='{delivery_date_raw}', people='{people}'")

            return_dict = {
                'title': detail.get('title', ''),
                'url': detail.get('url', ''),
                'work_id': detail.get('work_id', ''), # CSV出力からは除外されている
                'deadline': deadline_formatted, # CSV出力からは除外されている
                'deadline_raw': deadline_yyyy_mm_dd,   # ★YYYY-MM-DD形式で出力するように変更
                'people': people,               # ★CSVに出力されるべき値 (整形後)
                'delivery_date': delivery_date_formatted, # CSV出力からは除外されている
                'delivery_date_raw': delivery_date_raw, # ★CSVに出力されるべき値
                'period': period,               # CSV出力からは除外されている
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.logger.debug(f"Parser return dict: {return_dict}") # より詳細なデバッグログ
            return return_dict

        except Exception as e:
            self.logger.error(f"案件詳細情報のパースに失敗しました: {str(e)}")
            return detail

    def parse_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        スクレイピング結果を解析・整形する
        Args:
            results (List[Dict[str, Any]]): スクレイピング結果のリスト
        Returns:
            List[Dict[str, Any]]: 整形された結果のリスト
        """
        parsed_results = []
        for result in results:
            try:
                parsed_result = {
                    'title': result['title'],
                    'url': result['url'],
                    'work_id': self.parse_work_id(result['url']),
                    'price': result.get('price', '報酬未設定'),
                    'type': result.get('type', '種別不明'),
                    'deadline': self.parse_deadline(result.get('deadline', '')),
                    'status': result.get('status', '状態不明'),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                parsed_results.append(parsed_result)
            except Exception as e:
                self.logger.error(f"結果の解析に失敗しました: {str(e)}")
                continue

        return parsed_results
