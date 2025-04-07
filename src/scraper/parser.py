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
            # 数字のみを抽出
            match = re.search(r'(\d+)', people)
            return match.group(1) if match else people
        except Exception as e:
            self.logger.error(f"募集人数の解析に失敗しました: {str(e)}")
            return people

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
                    'deadline': self.parse_deadline(result['deadline']),
                    'delivery_date': self.parse_delivery_date(result['delivery_date']),
                    'people': self.parse_people(result['people']),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                parsed_results.append(parsed_result)
            except Exception as e:
                self.logger.error(f"結果の解析に失敗しました: {str(e)}")
                continue

        return parsed_results 