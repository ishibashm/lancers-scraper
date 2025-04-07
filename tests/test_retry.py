import pytest
import asyncio
from src.utils.retry_handler import RetryHandler
from typing import Any

class TestException(Exception):
    pass

@pytest.fixture
def retry_handler():
    """テスト用のリトライハンドラーを提供するフィクスチャ"""
    return RetryHandler(
        max_retries=2,
        delay=0.1,
        backoff_factor=1.5,
        exceptions=(TestException,)
    )

def test_retry_sync_success(retry_handler):
    """同期関数の成功ケースのテスト"""
    counter = 0
    
    @retry_handler.retry_sync
    def test_func():
        nonlocal counter
        counter += 1
        return "success"
    
    result = test_func()
    assert result == "success"
    assert counter == 1

def test_retry_sync_failure_and_retry(retry_handler):
    """同期関数の失敗とリトライのテスト"""
    counter = 0
    
    @retry_handler.retry_sync
    def test_func():
        nonlocal counter
        counter += 1
        if counter < 2:
            raise TestException("テストエラー")
        return "success"
    
    result = test_func()
    assert result == "success"
    assert counter == 2

def test_retry_sync_max_retries_exceeded(retry_handler):
    """同期関数の最大リトライ回数超過テスト"""
    counter = 0
    
    @retry_handler.retry_sync
    def test_func():
        nonlocal counter
        counter += 1
        raise TestException("テストエラー")
    
    with pytest.raises(TestException):
        test_func()
    assert counter == 3  # 初回 + 2回のリトライ

@pytest.mark.asyncio
async def test_retry_async_success(retry_handler):
    """非同期関数の成功ケースのテスト"""
    counter = 0
    
    @retry_handler.retry_async
    async def test_func():
        nonlocal counter
        counter += 1
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert counter == 1

@pytest.mark.asyncio
async def test_retry_async_failure_and_retry(retry_handler):
    """非同期関数の失敗とリトライのテスト"""
    counter = 0
    
    @retry_handler.retry_async
    async def test_func():
        nonlocal counter
        counter += 1
        if counter < 2:
            raise TestException("テストエラー")
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert counter == 2

@pytest.mark.asyncio
async def test_retry_async_max_retries_exceeded(retry_handler):
    """非同期関数の最大リトライ回数超過テスト"""
    counter = 0
    
    @retry_handler.retry_async
    async def test_func():
        nonlocal counter
        counter += 1
        raise TestException("テストエラー")
    
    with pytest.raises(TestException):
        await test_func()
    assert counter == 3  # 初回 + 2回のリトライ

def test_custom_retry_parameters():
    """カスタムパラメータでのリトライテスト"""
    handler = RetryHandler(max_retries=1)
    counter = 0
    
    @handler.with_retry(max_retries=3, delay=0.1)
    def test_func():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise TestException("テストエラー")
        return "success"
    
    result = test_func()
    assert result == "success"
    assert counter == 3

def test_different_exception_handling(retry_handler):
    """異なる例外の処理テスト"""
    @retry_handler.retry_sync
    def test_func():
        raise ValueError("異なる例外")
    
    with pytest.raises(ValueError):
        test_func()  # TestException以外はリトライされない

@pytest.mark.asyncio
async def test_backoff_delay(retry_handler):
    """バックオフ遅延のテスト"""
    counter = 0
    start_time = 0
    
    @retry_handler.retry_async
    async def test_func():
        nonlocal counter, start_time
        counter += 1
        if counter == 1:
            start_time = asyncio.get_event_loop().time()
        raise TestException("テストエラー")
    
    with pytest.raises(TestException):
        await test_func()
    
    end_time = asyncio.get_event_loop().time()
    expected_delay = 0.1 + (0.1 * 1.5)  # 初期遅延 + バックオフ遅延
    assert end_time - start_time >= expected_delay 