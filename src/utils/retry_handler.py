import asyncio
import logging
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
import time

T = TypeVar('T')

class RetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """
        リトライハンドラーのコンストラクタ
        Args:
            max_retries (int): 最大リトライ回数
            delay (float): 初期待機時間（秒）
            backoff_factor (float): バックオフ係数
            exceptions (tuple): リトライ対象の例外タプル
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.logger = logging.getLogger(__name__)

    def retry_sync(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        同期関数用のリトライデコレータ
        Args:
            func (Callable): リトライ対象の関数
        Returns:
            Callable: デコレートされた関数
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = self.delay

            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        self.logger.warning(
                            f"試行 {attempt + 1}/{self.max_retries + 1} が失敗しました: {str(e)}"
                            f" - {current_delay}秒後に再試行します"
                        )
                        time.sleep(current_delay)
                        current_delay *= self.backoff_factor
                    else:
                        self.logger.error(
                            f"最大試行回数（{self.max_retries + 1}回）に到達しました: {str(e)}"
                        )

            raise last_exception

        return wrapper

    def retry_async(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        非同期関数用のリトライデコレータ
        Args:
            func (Callable): リトライ対象の非同期関数
        Returns:
            Callable: デコレートされた非同期関数
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = self.delay

            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        self.logger.warning(
                            f"試行 {attempt + 1}/{self.max_retries + 1} が失敗しました: {str(e)}"
                            f" - {current_delay}秒後に再試行します"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= self.backoff_factor
                    else:
                        self.logger.error(
                            f"最大試行回数（{self.max_retries + 1}回）に到達しました: {str(e)}"
                        )

            raise last_exception

        return wrapper

    def with_retry(
        self,
        max_retries: Optional[int] = None,
        delay: Optional[float] = None,
        exceptions: Optional[tuple] = None
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        カスタムパラメータでリトライデコレータを生成
        Args:
            max_retries (Optional[int]): このデコレータ用の最大リトライ回数
            delay (Optional[float]): このデコレータ用の初期待機時間
            exceptions (Optional[tuple]): このデコレータ用のリトライ対象例外
        Returns:
            Callable: リトライデコレータ
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            handler = RetryHandler(
                max_retries=max_retries or self.max_retries,
                delay=delay or self.delay,
                backoff_factor=self.backoff_factor,
                exceptions=exceptions or self.exceptions
            )
            if asyncio.iscoroutinefunction(func):
                return handler.retry_async(func)
            return handler.retry_sync(func)
        return decorator 