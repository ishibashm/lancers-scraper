import pytest
import asyncio
from src.utils.parallel_handler import ParallelHandler
from typing import Dict, Any

@pytest.fixture
def parallel_handler():
    """テスト用の並列処理ハンドラーを提供するフィクスチャ"""
    return ParallelHandler(max_workers=2)

def sample_processor(result: Dict[str, Any]) -> Dict[str, Any]:
    """テスト用の処理関数"""
    processed = result.copy()
    processed['processed'] = True
    return processed

@pytest.mark.asyncio
async def test_parallel_search(parallel_handler):
    """並列検索のテスト"""
    search_queries = ["Python", "JavaScript"]
    results = await parallel_handler.parallel_search(search_queries, max_pages=1)
    
    assert isinstance(results, dict)
    assert all(query in results for query in search_queries)
    assert all(isinstance(result_list, list) for result_list in results.values())

@pytest.mark.asyncio
async def test_process_results_parallel(parallel_handler):
    """検索結果の並列処理テスト"""
    # テスト用のダミーデータ
    test_results = [
        {"title": "Test1", "url": "http://test1.com"},
        {"title": "Test2", "url": "http://test2.com"}
    ]
    
    processed_results = parallel_handler.process_results_parallel(
        test_results,
        sample_processor
    )
    
    assert len(processed_results) == len(test_results)
    assert all(result['processed'] for result in processed_results)

@pytest.mark.asyncio
async def test_search_and_process(parallel_handler):
    """検索と処理の組み合わせテスト"""
    search_queries = ["Python"]
    results = await parallel_handler.search_and_process(
        search_queries,
        sample_processor,
        max_pages=1
    )
    
    assert isinstance(results, dict)
    assert "Python" in results
    if results["Python"]:
        assert all(result['processed'] for result in results["Python"])

@pytest.mark.asyncio
async def test_parallel_search_error_handling(parallel_handler):
    """エラーハンドリングのテスト"""
    # 無効な検索クエリ
    invalid_queries = ["", "   "]
    results = await parallel_handler.parallel_search(invalid_queries)
    
    assert isinstance(results, dict)
    assert all(query in results for query in invalid_queries)
    assert all(isinstance(result_list, list) for result_list in results.values())

@pytest.mark.asyncio
async def test_process_results_error_handling(parallel_handler):
    """結果処理のエラーハンドリングテスト"""
    def error_processor(result):
        raise Exception("処理エラー")
    
    test_results = [{"title": "Test"}]
    processed_results = parallel_handler.process_results_parallel(
        test_results,
        error_processor
    )
    
    assert isinstance(processed_results, list)
    assert len(processed_results) == 0

@pytest.mark.asyncio
async def test_multiple_queries_parallel(parallel_handler):
    """複数クエリの並列実行テスト"""
    search_queries = ["Python", "JavaScript", "TypeScript"]
    results = await parallel_handler.parallel_search(
        search_queries,
        max_pages=1
    )
    
    assert len(results) == len(search_queries)
    assert all(query in results for query in search_queries)

@pytest.mark.asyncio
async def test_process_pool_execution(parallel_handler):
    """プロセスプールでの実行テスト"""
    # プロセスプールを使用するように設定
    process_handler = ParallelHandler(max_workers=2, use_processes=True)
    
    test_results = [
        {"title": "Test1", "url": "http://test1.com"},
        {"title": "Test2", "url": "http://test2.com"}
    ]
    
    processed_results = process_handler.process_results_parallel(
        test_results,
        sample_processor
    )
    
    assert len(processed_results) == len(test_results)
    assert all(result['processed'] for result in processed_results) 