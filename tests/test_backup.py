import pytest
import os
import shutil
from pathlib import Path
from datetime import datetime
from src.utils.backup_handler import BackupHandler

@pytest.fixture
def temp_dirs(tmp_path):
    """テスト用の一時ディレクトリを作成"""
    source_dir = tmp_path / "source"
    backup_dir = tmp_path / "backup"
    source_dir.mkdir()
    return source_dir, backup_dir

@pytest.fixture
def sample_data(temp_dirs):
    """テスト用のサンプルデータを作成"""
    source_dir, _ = temp_dirs
    
    # テストファイルの作成
    test_file = source_dir / "test.txt"
    test_file.write_text("テストデータ")
    
    # テストディレクトリの作成
    test_subdir = source_dir / "subdir"
    test_subdir.mkdir()
    (test_subdir / "subfile.txt").write_text("サブディレクトリのテストデータ")
    
    return source_dir

def test_backup_creation(temp_dirs):
    """バックアップ作成のテスト"""
    source_dir, backup_dir = temp_dirs
    handler = BackupHandler(str(source_dir), str(backup_dir))
    
    # テストファイルの作成
    test_file = source_dir / "test.txt"
    test_file.write_text("テストデータ")
    
    # バックアップの作成
    backup_path = handler.create_backup()
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.suffix == '.gz'

def test_backup_restoration(temp_dirs, sample_data):
    """バックアップ復元のテスト"""
    source_dir, backup_dir = temp_dirs
    handler = BackupHandler(str(source_dir), str(backup_dir))
    
    # バックアップの作成
    backup_path = handler.create_backup()
    
    # ソースディレクトリの内容を削除
    shutil.rmtree(str(source_dir))
    source_dir.mkdir()
    
    # バックアップから復元
    success = handler.restore_backup(backup_path)
    assert success
    
    # 復元されたファイルの確認
    assert (source_dir / "test.txt").exists()
    assert (source_dir / "test.txt").read_text() == "テストデータ"
    assert (source_dir / "subdir" / "subfile.txt").exists()
    assert (source_dir / "subdir" / "subfile.txt").read_text() == "サブディレクトリのテストデータ"

def test_backup_rotation(temp_dirs, sample_data):
    """バックアップローテーションのテスト"""
    source_dir, backup_dir = temp_dirs
    max_backups = 3
    handler = BackupHandler(str(source_dir), str(backup_dir), max_backups=max_backups)
    
    # 複数のバックアップを作成
    for _ in range(5):
        handler.create_backup()
    
    # バックアップ数の確認
    backups = handler.list_backups()
    assert len(backups) == max_backups

def test_backup_info(temp_dirs, sample_data):
    """バックアップ情報取得のテスト"""
    source_dir, backup_dir = temp_dirs
    handler = BackupHandler(str(source_dir), str(backup_dir))
    
    # バックアップの作成
    backup_path = handler.create_backup()
    
    # バックアップ情報の取得
    info = handler.get_backup_info(backup_path)
    assert info is not None
    assert 'filename' in info
    assert 'size' in info
    assert 'created_at' in info
    assert 'path' in info

def test_error_handling(temp_dirs):
    """エラーハンドリングのテスト"""
    source_dir, backup_dir = temp_dirs
    handler = BackupHandler(str(source_dir), str(backup_dir))
    
    # 存在しないバックアップの復元
    non_existent_backup = backup_dir / "non_existent.tar.gz"
    success = handler.restore_backup(non_existent_backup)
    assert not success
    
    # 無効なディレクトリからのバックアップ
    invalid_handler = BackupHandler("/invalid/path", str(backup_dir))
    backup_path = invalid_handler.create_backup()
    assert backup_path is None 