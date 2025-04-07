import sys
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ProgressStats:
    """進捗状況の統計情報"""
    total: int
    current: int
    start_time: datetime
    elapsed_time: timedelta
    remaining_time: Optional[timedelta]
    percentage: float
    speed: float  # items/sec

class ProgressHandler:
    def __init__(
        self,
        total: int,
        description: str = "",
        bar_length: int = 50,
        update_interval: float = 0.1
    ):
        """
        プログレスバーハンドラーのコンストラクタ
        Args:
            total (int): 処理する総アイテム数
            description (str): プログレスバーの説明
            bar_length (int): プログレスバーの長さ
            update_interval (float): 更新間隔（秒）
        """
        self.total = total
        self.current = 0
        self.description = description
        self.bar_length = bar_length
        self.update_interval = update_interval
        self.start_time = datetime.now()
        self.last_update_time = self.start_time
        self._last_line_length = 0

    def update(self, amount: int = 1) -> None:
        """
        進捗を更新
        Args:
            amount (int): 進捗増加量
        """
        self.current += amount
        current_time = datetime.now()
        
        # 更新間隔をチェック
        if (current_time - self.last_update_time).total_seconds() >= self.update_interval:
            self._display_progress()
            self.last_update_time = current_time

    def _get_stats(self) -> ProgressStats:
        """
        現在の進捗統計を取得
        Returns:
            ProgressStats: 進捗統計情報
        """
        current_time = datetime.now()
        elapsed_time = current_time - self.start_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        # 進捗率と速度を計算
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        speed = self.current / elapsed_seconds if elapsed_seconds > 0 else 0
        
        # 残り時間を推定
        remaining_items = self.total - self.current
        remaining_time = None
        if speed > 0:
            remaining_seconds = remaining_items / speed
            remaining_time = timedelta(seconds=remaining_seconds)
        
        return ProgressStats(
            total=self.total,
            current=self.current,
            start_time=self.start_time,
            elapsed_time=elapsed_time,
            remaining_time=remaining_time,
            percentage=percentage,
            speed=speed
        )

    def _display_progress(self) -> None:
        """プログレスバーを表示"""
        stats = self._get_stats()
        
        # プログレスバーの作成
        filled_length = int(self.bar_length * stats.current / self.total)
        bar = '=' * filled_length + '-' * (self.bar_length - filled_length)
        
        # 時間情報のフォーマット
        elapsed = str(stats.elapsed_time).split('.')[0]
        remaining = str(stats.remaining_time).split('.')[0] if stats.remaining_time else "不明"
        
        # 進捗情報の作成
        progress_line = (
            f"\r{self.description} "
            f"[{bar}] "
            f"{stats.percentage:.1f}% "
            f"({stats.current}/{stats.total}) "
            f"経過: {elapsed} "
            f"残り: {remaining} "
            f"速度: {stats.speed:.1f}件/秒"
        )
        
        # 前回の行を消去してから新しい行を表示
        if len(progress_line) < self._last_line_length:
            sys.stdout.write('\r' + ' ' * self._last_line_length)
        
        sys.stdout.write(progress_line)
        sys.stdout.flush()
        self._last_line_length = len(progress_line)

    def finish(self) -> Dict[str, Any]:
        """
        プログレスバーを完了状態で表示し、統計情報を返す
        Returns:
            Dict[str, Any]: 進捗の統計情報
        """
        self.current = self.total
        self._display_progress()
        sys.stdout.write('\n')
        sys.stdout.flush()
        
        stats = self._get_stats()
        return {
            'total': stats.total,
            'elapsed_time': stats.elapsed_time,
            'speed': stats.speed
        }

class AsyncProgressHandler(ProgressHandler):
    """非同期処理用のプログレスハンドラー"""
    async def update_async(self, amount: int = 1) -> None:
        """
        非同期で進捗を更新
        Args:
            amount (int): 進捗増加量
        """
        self.current += amount
        current_time = datetime.now()
        
        if (current_time - self.last_update_time).total_seconds() >= self.update_interval:
            self._display_progress()
            self.last_update_time = current_time

    async def finish_async(self) -> Dict[str, Any]:
        """
        非同期でプログレスバーを完了
        Returns:
            Dict[str, Any]: 進捗の統計情報
        """
        return self.finish() 