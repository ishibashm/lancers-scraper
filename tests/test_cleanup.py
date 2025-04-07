import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import os
import time
from src.utils.cleanup_handler import CleanupHandler

@pytest.fixture
def temp_data_dir(tmp_path):
    """テスト用の一時データディレクトリを作成"""
    return tmp_path

@pytest.fixture
def sample_csv(temp_data_dir):
    """テスト用のCSVファイルを作成"""
    data = {
        'id': [1, 2, 2, 3, 3],  # 重複を含むデータ
        'name': ['A', 'B', 'B', 'C', 'C'],
        'value': [100, 200, 200, 300, 300]
    }
    df = pd.DataFrame(data)
    file_path = temp_data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    return file_path

def create_old_file(dir_path: Path, days_old: int, name: str = "old.csv"):
    """指定した日数分古いファイルを作成"""
    file_path = dir_path / name
    file_path.write_text("test data")
    old_time = datetime.now() - timedelta(days=days_old)
    os.utime(file_path, (old_time.timestamp(), old_time.timestamp()))
    return file_path

def test_cleanup_old_files(temp_data_dir):
    """古いファイルの削除テスト"""
    handler = CleanupHandler(str(temp_data_dir), retention_days=7)
    
    # 古いファイルと新しいファイルを作成
    old_file = create_old_file(temp_data_dir, 10)
    new_file = create_old_file(temp_data_dir, 3, "new.csv")
    
    # クリーンアップの実行
    deleted_files = handler.cleanup_old_files()
    
    # 検証
    assert len(deleted_files) == 1
    assert old_file in deleted_files
    assert not old_file.exists()
    assert new_file.exists()

def test_remove_duplicates(temp_data_dir, sample_csv):
    """重複データの削除テスト"""
    handler = CleanupHandler(str(temp_data_dir))
    
    # 重複の削除
    cleaned_file = handler.remove_duplicates(sample_csv, ['id', 'name'])
    
    # 検証
    assert cleaned_file is not None
    df_cleaned = pd.read_csv(cleaned_file)
    assert len(df_cleaned) == 3  # 重複が削除されて3行になるはず
    assert df_cleaned['id'].tolist() == [1, 2, 3]

def test_cleanup_temp_files(temp_data_dir):
    """一時ファイルの削除テスト"""
    handler = CleanupHandler(str(temp_data_dir))
    
    # 一時ファイルの作成
    temp_files = [
        temp_data_dir / "test.tmp",
        temp_data_dir / "test.temp",
        temp_data_dir / "~temp"
    ]
    normal_file = temp_data_dir / "normal.csv"
    
    for file in temp_files + [normal_file]:
        file.write_text("test data")
    
    # クリーンアップの実行
    deleted_files = handler.cleanup_temp_files()
    
    # 検証
    assert len(deleted_files) == len(temp_files)
    for temp_file in temp_files:
        assert not temp_file.exists()
    assert normal_file.exists()

def test_get_data_stats(temp_data_dir):
    """データ統計情報の取得テスト"""
    handler = CleanupHandler(str(temp_data_dir))
    
    # テストファイルの作成
    files = [
        create_old_file(temp_data_dir, 5, "old.csv"),
        create_old_file(temp_data_dir, 1, "new.csv")
    ]
    
    # 統計情報の取得
    stats = handler.get_data_stats()
    
    # 検証
    assert stats['file_count'] == 2
    assert stats['total_size_bytes'] > 0
    assert 'old.csv' in stats['oldest_file']
    assert 'new.csv' in stats['newest_file']
    assert stats['oldest_file_date'] is not None
    assert stats['newest_file_date'] is not None

def test_error_handling(temp_data_dir):
    """エラーハンドリングのテスト"""
    handler = CleanupHandler(str(temp_data_dir))
    
    # 存在しないファイルの重複削除
    result = handler.remove_duplicates(temp_data_dir / "non_existent.csv", ['id'])
    assert result is None
    
    # 無効なディレクトリのクリーンアップ
    invalid_handler = CleanupHandler("/invalid/path")
    assert invalid_handler.cleanup_old_files() == []
    assert invalid_handler.cleanup_temp_files() == []
    assert invalid_handler.get_data_stats() == {} 