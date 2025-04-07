import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
import gzip
import json
from typing import List, Optional

class BackupHandler:
    def __init__(self, source_dir: str, backup_dir: str, max_backups: int = 5):
        """
        バックアップハンドラーのコンストラクタ
        Args:
            source_dir (str): バックアップ元ディレクトリ
            backup_dir (str): バックアップ先ディレクトリ
            max_backups (int): 保持する最大バックアップ数
        """
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.logger = logging.getLogger(__name__)

        # バックアップディレクトリの作成
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Optional[Path]:
        """
        バックアップを作成する
        Returns:
            Optional[Path]: 作成されたバックアップファイルのパス
        """
        try:
            # バックアップファイル名の生成（タイムスタンプ付き）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename

            # バックアップの作成
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'gztar',
                self.source_dir
            )

            self.logger.info(f"バックアップを作成しました: {backup_path}")
            
            # 古いバックアップの削除
            self._cleanup_old_backups()
            
            return backup_path

        except Exception as e:
            self.logger.error(f"バックアップの作成に失敗しました: {str(e)}")
            return None

    def restore_backup(self, backup_path: Path) -> bool:
        """
        バックアップからの復元
        Args:
            backup_path (Path): 復元するバックアップファイルのパス
        Returns:
            bool: 復元が成功したかどうか
        """
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"バックアップファイルが見つかりません: {backup_path}")

            # 復元先ディレクトリの準備
            shutil.rmtree(self.source_dir, ignore_errors=True)
            self.source_dir.mkdir(parents=True, exist_ok=True)

            # バックアップの展開
            shutil.unpack_archive(
                str(backup_path),
                str(self.source_dir),
                'gztar'
            )

            self.logger.info(f"バックアップを復元しました: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"バックアップの復元に失敗しました: {str(e)}")
            return False

    def list_backups(self) -> List[Path]:
        """
        利用可能なバックアップの一覧を取得
        Returns:
            List[Path]: バックアップファイルのパスのリスト
        """
        try:
            backups = sorted(
                self.backup_dir.glob('backup_*.tar.gz'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return backups
        except Exception as e:
            self.logger.error(f"バックアップ一覧の取得に失敗しました: {str(e)}")
            return []

    def _cleanup_old_backups(self) -> None:
        """古いバックアップを削除する"""
        try:
            backups = self.list_backups()
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    backup.unlink()
                    self.logger.info(f"古いバックアップを削除しました: {backup}")
        except Exception as e:
            self.logger.error(f"古いバックアップの削除に失敗しました: {str(e)}")

    def get_backup_info(self, backup_path: Path) -> Optional[dict]:
        """
        バックアップファイルの情報を取得
        Args:
            backup_path (Path): バックアップファイルのパス
        Returns:
            Optional[dict]: バックアップ情報
        """
        try:
            stats = backup_path.stat()
            return {
                'filename': backup_path.name,
                'size': stats.st_size,
                'created_at': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'path': str(backup_path)
            }
        except Exception as e:
            self.logger.error(f"バックアップ情報の取得に失敗しました: {str(e)}")
            return None 