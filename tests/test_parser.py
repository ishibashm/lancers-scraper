import pytest
from datetime import datetime
from src.scraper.parser import LancersParser

@pytest.fixture
def parser():
    """テスト用のパーサーインスタンスを提供するフィクスチャ"""
    return LancersParser()

def test_parse_work_id(parser):
    """案件IDのパース処理テスト"""
    # 正常系
    url = "https://www.lancers.jp/work/detail/12345"
    assert parser.parse_work_id(url) == "12345"
    
    # 異常系
    assert parser.parse_work_id("") == ""
    assert parser.parse_work_id("https://www.lancers.jp/invalid/url") == ""
    assert parser.parse_work_id("https://www.lancers.jp/work/detail/invalid") == ""

def test_parse_deadline(parser):
    """締切日時のパース処理テスト"""
    # 正常系
    assert parser.parse_deadline("締切：2024年3月31日") == "2024年3月31日"
    assert parser.parse_deadline("期限なし") == "期限なし"
    
    # 異常系
    assert parser.parse_deadline("") == ""
    assert parser.parse_deadline(None) == None

def test_parse_delivery_date(parser):
    """希望納期のパース処理テスト"""
    # 正常系
    assert parser.parse_delivery_date("希望納期：2024年4月30日") == "2024年4月30日"
    assert parser.parse_delivery_date("納期未設定") == "納期未設定"
    
    # 異常系
    assert parser.parse_delivery_date("") == ""
    assert parser.parse_delivery_date(None) == None

def test_parse_people(parser):
    """募集人数のパース処理テスト"""
    # 正常系 - 基本パターン
    assert parser.parse_people("3人") == "3"
    assert parser.parse_people("人数未設定") == "人数未設定"
    
    # 正常系 - 新しいパターン
    assert parser.parse_people("募集人数5人") == "5"
    assert parser.parse_people("(募集人数1人)") == "1"
    assert parser.parse_people("募集人数 2 人") == "2"
    
    # 異常系
    assert parser.parse_people("") == ""
    assert parser.parse_people(None) == None
    assert parser.parse_people("複数名") == "複数名"

def test_format_date(parser):
    """日付フォーマット変換処理のテスト"""
    # 正常系 - 日付のみ
    assert parser.format_date("2025年4月21日") == "2025-04-21"
    assert parser.format_date("2025年04月21日") == "2025-04-21"
    assert parser.format_date("2025年12月1日") == "2025-12-01"
    
    # 正常系 - 日付と時刻
    assert parser.format_date("2025年4月21日 18:17") == "2025-04-21 18:17"
    assert parser.format_date("2025年04月21日 9:05") == "2025-04-21 09:05"
    
    # 異常系
    assert parser.format_date("") == ""
    assert parser.format_date(None) == None
    assert parser.format_date("無効な日付") == "無効な日付"
    assert parser.format_date("2025/04/21") == "2025/04/21"  # 変換されないパターン

def test_parse_work_detail(parser):
    """案件詳細情報のパース処理テスト"""
    # テスト用のダミーデータ
    test_detail = {
        'title': 'Webアプリ開発',
        'url': 'https://www.lancers.jp/work/detail/12345',
        'work_id': '12345',
        'deadline': '締切：2025年4月21日 18:17',
        'people': '(募集人数1人)',
        'delivery_date': '希望納期：2025年5月16日',
        'period': '5日間'
    }
    
    parsed = parser.parse_work_detail(test_detail)
    
    assert parsed['title'] == 'Webアプリ開発'
    assert parsed['url'] == 'https://www.lancers.jp/work/detail/12345'
    assert parsed['work_id'] == '12345'
    assert parsed['deadline'] == '2025-04-21 18:17'
    assert parsed['deadline_raw'] == '締切：2025年4月21日 18:17'
    assert parsed['people'] == '1'
    assert parsed['delivery_date'] == '2025-05-16'
    assert parsed['delivery_date_raw'] == '希望納期：2025年5月16日'
    assert parsed['period'] == '5日間'
    assert 'scraped_at' in parsed

def test_parse_results(parser):
    """検索結果全体のパース処理テスト"""
    # テスト用のダミーデータ
    test_results = [
        {
            'title': 'Pythonプログラミング',
            'url': 'https://www.lancers.jp/work/detail/98765',
            'deadline': '締切：2024年3月31日',
            'delivery_date': '希望納期：2024年4月30日',
            'people': '2人'
        }
    ]
    
    parsed = parser.parse_results(test_results)
    assert len(parsed) == 1
    
    result = parsed[0]
    assert result['title'] == 'Pythonプログラミング'
    assert result['work_id'] == '98765'
    assert result['deadline'] == '2024年3月31日'
    assert result['delivery_date'] == '2024年4月30日'
    assert result['people'] == '2'
    assert 'scraped_at' in result
    
    # datetime形式の検証
    scraped_at = datetime.strptime(result['scraped_at'], '%Y-%m-%d %H:%M:%S')
    assert isinstance(scraped_at, datetime)

def test_parse_results_error_handling(parser):
    """検索結果パース処理のエラーハンドリングテスト"""
    # 不正なデータ構造
    invalid_results = [
        {'invalid_key': 'value'},  # 必要なキーが存在しない
        None,  # Noneデータ
        {}  # 空辞書
    ]
    
    parsed = parser.parse_results(invalid_results)
    assert len(parsed) == 0  # エラーが発生したため、結果は空リスト

def test_parse_results_empty_input(parser):
    """空の入力に対する処理テスト"""
    assert parser.parse_results([]) == []
    assert parser.parse_results(None) == [] 