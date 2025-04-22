import pytest
import asyncio
from src.scraper.browser import LancersBrowser
from src.utils.csv_handler import CSVHandler
from src.utils.retry_handler import RetryHandler
import os
import tempfile

@pytest.fixture
async def browser():
    browser = LancersBrowser(headless=True)
    await browser.start()
    yield browser
    await browser.close()

@pytest.fixture
def csv_handler():
    return CSVHandler()

@pytest.mark.asyncio
async def test_url_extraction(csv_handler):
    # テスト用のCSVファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        f.write("title,url,price\n")
        f.write("Test Job 1,https://www.lancers.jp/work/detail/123,10000\n")
        f.write("Test Job 2,https://www.lancers.jp/work/detail/456,20000\n")
        temp_file_path = f.name

    # URLを抽出
    urls = csv_handler.extract_urls(temp_file_path, url_column='url')
    
    # 結果を検証
    assert len(urls) == 2
    assert urls[0] == "https://www.lancers.jp/work/detail/123"
    assert urls[1] == "https://www.lancers.jp/work/detail/456"
    
    # 一時ファイルを削除
    os.unlink(temp_file_path)

@pytest.mark.asyncio
async def test_page_type_check(browser):
    # テスト用のURL（実際のURLに置き換える必要がある）
    test_url = "https://www.lancers.jp/work/detail/123"
    
    # ページタイプを判定
    page_type = await browser.check_page_type(test_url)
    
    # 結果を検証（実際のページに応じて調整）
    assert page_type in ['member', 'non-member', 'unknown']

@pytest.mark.asyncio
async def test_scraped_data_saving(csv_handler):
    # テスト用のデータ
    scraped_data = [
        {"url": "https://www.lancers.jp/work/detail/123", "deadline": "2025-05-01", "delivery_date": "2025-06-01", "people": "1"},
        {"url": "https://www.lancers.jp/work/detail/456", "deadline": "2025-05-02", "delivery_date": "2025-06-02", "people": "2"}
    ]
    
    # 一時的なCSVファイルパス
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        temp_file_path = f.name
    
    # データを保存
    saved_path = csv_handler.save_scraped_data(scraped_data, temp_file_path)
    
    # 結果を検証
    assert os.path.exists(saved_path)
    assert saved_path.endswith("_scraped.csv")
    
    # 保存されたデータを読み込み
    loaded_data = csv_handler.read_csv(saved_path)
    assert len(loaded_data) == 2
    assert loaded_data[0]["url"] == "https://www.lancers.jp/work/detail/123"
    assert loaded_data[1]["people"] == "2"
    
    # 一時ファイルを削除
    os.unlink(temp_file_path)
    os.unlink(saved_path)

@pytest.mark.asyncio
async def test_retry_on_failure():
    # リトライハンドラーのインスタンスを作成
    retry_handler = RetryHandler(max_retries=2, delay=1.0, exceptions=(ValueError,))
    
    # テスト用の非同期関数（失敗する）
    @retry_handler.retry_async
    async def failing_function():
        raise ValueError("Test error")
    
    # リトライが試みられることを確認
    with pytest.raises(ValueError) as exc_info:
        await failing_function()
    assert str(exc_info.value) == "Test error"
