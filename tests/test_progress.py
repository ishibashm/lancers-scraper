import pytest
import asyncio
import time
from datetime import datetime, timedelta
from src.utils.progress_handler import ProgressHandler, AsyncProgressHandler

@pytest.fixture
def progress_handler():
    """テスト用のプログレスハンドラーを提供するフィクスチャ"""
    return ProgressHandler(total=100, description="テスト処理")

def test_progress_initialization(progress_handler):
    """初期化のテスト"""
    assert progress_handler.total == 100
    assert progress_handler.current == 0
    assert progress_handler.description == "テスト処理"
    assert isinstance(progress_handler.start_time, datetime)

def test_progress_update():
    """進捗更新のテスト"""
    handler = ProgressHandler(total=10, update_interval=0)
    handler.update(2)
    assert handler.current == 2
    
    handler.update()
    assert handler.current == 3

def test_progress_stats():
    """進捗統計のテスト"""
    handler = ProgressHandler(total=100)
    handler.update(50)
    stats = handler._get_stats()
    
    assert stats.total == 100
    assert stats.current == 50
    assert stats.percentage == 50.0
    assert isinstance(stats.elapsed_time, timedelta)
    assert stats.speed >= 0

def test_progress_finish():
    """完了処理のテスト"""
    handler = ProgressHandler(total=100)
    handler.update(50)
    stats = handler.finish()
    
    assert handler.current == 100
    assert isinstance(stats, dict)
    assert 'total' in stats
    assert 'elapsed_time' in stats
    assert 'speed' in stats

def test_progress_zero_total():
    """総数0の場合のテスト"""
    handler = ProgressHandler(total=0)
    stats = handler._get_stats()
    
    assert stats.percentage == 0
    assert stats.speed == 0

def test_progress_display_format(capsys):
    """表示フォーマットのテスト"""
    handler = ProgressHandler(total=100, bar_length=20)
    handler.update(50)
    handler._display_progress()
    captured = capsys.readouterr()
    
    assert '[' in captured.out
    assert ']' in captured.out
    assert '%' in captured.out
    assert '経過:' in captured.out
    assert '残り:' in captured.out
    assert '速度:' in captured.out

@pytest.mark.asyncio
async def test_async_progress_update():
    """非同期更新のテスト"""
    handler = AsyncProgressHandler(total=10, update_interval=0)
    await handler.update_async(2)
    assert handler.current == 2
    
    await handler.update_async()
    assert handler.current == 3

@pytest.mark.asyncio
async def test_async_progress_finish():
    """非同期完了のテスト"""
    handler = AsyncProgressHandler(total=100)
    await handler.update_async(50)
    stats = await handler.finish_async()
    
    assert handler.current == 100
    assert isinstance(stats, dict)
    assert 'total' in stats
    assert 'elapsed_time' in stats
    assert 'speed' in stats

def test_progress_with_long_operation():
    """長時間処理での動作テスト"""
    handler = ProgressHandler(total=5, update_interval=0.1)
    
    for _ in range(5):
        time.sleep(0.1)  # 処理時間をシミュレート
        handler.update()
    
    stats = handler.finish()
    assert stats['elapsed_time'].total_seconds() >= 0.5

@pytest.mark.asyncio
async def test_async_progress_with_long_operation():
    """非同期の長時間処理テスト"""
    handler = AsyncProgressHandler(total=5, update_interval=0.1)
    
    for _ in range(5):
        await asyncio.sleep(0.1)  # 非同期の処理時間をシミュレート
        await handler.update_async()
    
    stats = await handler.finish_async()
    assert stats['elapsed_time'].total_seconds() >= 0.5 