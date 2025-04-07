import pytest
import asyncio
from src.scraper.browser import LancersBrowser
from src.utils.config import config

@pytest.fixture
def browser():
    """テスト用のブラウザインスタンスを提供するフィクスチャ"""
    browser = LancersBrowser(headless=True, max_pages=2)
    browser.start()
    yield browser
    # テスト後のクリーンアップ
    if browser:
        browser.close()

@pytest.mark.asyncio
async def test_browser_initialization(browser):
    """ブラウザの初期化テスト"""
    try:
        assert browser.browser is not None
        assert browser.page is not None
        assert browser.headless is True
        assert browser.max_pages == 2
    finally:
        browser.close()

@pytest.mark.asyncio
async def test_browser_context_manager():
    """コンテキストマネージャーのテスト"""
    async with LancersBrowser(headless=True) as browser:
        assert browser.browser is not None
        assert browser.page is not None

@pytest.mark.asyncio
async def test_search_short_videos(browser):
    """検索機能のテスト"""
    browser.start()
    try:
        # テスト用の検索クエリ
        test_query = "Python"
        results = await browser.search_short_videos(test_query)
        
        # 検索結果の検証
        assert isinstance(results, list)
        if results:  # 検索結果がある場合
            first_result = results[0]
            assert 'title' in first_result
            assert 'url' in first_result
            assert 'deadline' in first_result
            assert 'delivery_date' in first_result
            assert 'people' in first_result
            
            # URLの形式を確認
            assert first_result['url'].startswith('https://www.lancers.jp/work/detail/')
    finally:
        browser.close()

@pytest.mark.asyncio
async def test_empty_search_results(browser):
    """検索結果が空の場合のテスト"""
    browser.start()
    try:
        # 存在しそうにない検索クエリ
        test_query = "xxxxxxxxxxxxxxxxxxx"
        results = await browser.search_short_videos(test_query)
        assert isinstance(results, list)
        assert len(results) == 0
    finally:
        browser.close()

@pytest.mark.asyncio
async def test_browser_timeout():
    """ブラウザのタイムアウト設定テスト"""
    # 短いタイムアウト時間で設定
    config.set('BROWSER_TIMEOUT', 1)
    browser = LancersBrowser(headless=True)
    
    with pytest.raises(Exception):
        browser.start()
        await browser.search_short_videos("Python")
    
    # クリーンアップ
    browser.close()
    # タイムアウト設定を元に戻す
    config.set('BROWSER_TIMEOUT', 30000)

@pytest.mark.asyncio
async def test_multiple_searches(browser):
    """複数回の検索実行テスト"""
    browser.start()
    try:
        queries = ["Python", "JavaScript", "Web開発"]
        for query in queries:
            results = await browser.search_short_videos(query)
            assert isinstance(results, list)
            if results:
                assert all(isinstance(item, dict) for item in results)
    finally:
        browser.close()

@pytest.mark.asyncio
async def test_browser_restart(browser):
    """ブラウザの再起動テスト"""
    # 1回目の起動と検索
    browser.start()
    results1 = await browser.search_short_videos("Python")
    browser.close()
    
    # 2回目の起動と検索
    browser.start()
    results2 = await browser.search_short_videos("Python")
    
    # 両方の検索で結果が取得できることを確認
    assert isinstance(results1, list)
    assert isinstance(results2, list)
    
    browser.close()

def test_headless_mode_setting():
    """ヘッドレスモード設定のテスト"""
    # ヘッドレスモード有効
    browser1 = LancersBrowser(headless=True)
    assert browser1.headless is True
    
    # ヘッドレスモード無効
    browser2 = LancersBrowser(headless=False)
    assert browser2.headless is False

@pytest.mark.asyncio
async def test_search_pagination(browser):
    """ページネーション機能のテスト"""
    # 2ページ分の検索を実行
    results = await browser.search_short_videos("Python", start_page=1)
    
    # 結果の検証
    assert len(results) > 0
    
    # 各結果の形式を確認
    for result in results:
        assert 'title' in result
        assert 'url' in result
        assert 'deadline' in result
        assert 'delivery_date' in result
        assert 'people' in result

@pytest.mark.asyncio
async def test_search_with_custom_start_page(browser):
    """カスタム開始ページでの検索テスト"""
    # 2ページ目から検索を開始
    results = await browser.search_short_videos("Python", start_page=2)
    
    # 結果の検証
    assert len(results) > 0

@pytest.mark.asyncio
async def test_search_max_pages(browser):
    """最大ページ数の制限テスト"""
    # max_pages=2に設定されているため、2ページ以上は取得されないはず
    results = await browser.search_short_videos("Python")
    
    # 結果の検証
    first_page_results = await browser.search_short_videos("Python", start_page=1)
    assert len(results) >= len(first_page_results)  # 少なくとも1ページ目の結果数以上

@pytest.mark.asyncio
async def test_pagination_navigation(browser):
    """ページ遷移の動作テスト"""
    # 1ページ目の結果を取得
    page1_results = await browser.search_short_videos("Python", start_page=1)
    
    # 2ページ目の結果を取得
    page2_results = await browser.search_short_videos("Python", start_page=2)
    
    # 異なるページの結果が取得できていることを確認
    if len(page1_results) > 0 and len(page2_results) > 0:
        assert page1_results[0]['url'] != page2_results[0]['url']

def test_browser_cleanup(browser):
    """ブラウザのクリーンアップテスト"""
    browser.close()
    assert browser.page is None or browser.page.is_closed()
    assert browser.browser is None or browser.browser.is_closed() 