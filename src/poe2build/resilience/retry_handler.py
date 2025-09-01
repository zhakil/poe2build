"""
重试处理器 - 指数退避重试机制
"""

import time
import random
import logging
from typing import Callable, Any, Type, Union, List
from functools import wraps

logger = logging.getLogger(__name__)

class RetryConfig:
    """重试配置"""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True,
                 retry_on: Union[Type[Exception], List[Type[Exception]]] = Exception):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        
        if isinstance(retry_on, type):
            self.retry_exceptions = (retry_on,)
        else:
            self.retry_exceptions = tuple(retry_on)

def retry_with_backoff(config: RetryConfig):
    """重试装饰器"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:  # 不是最后一次尝试
                        delay = min(
                            config.base_delay * (config.backoff_factor ** attempt),
                            config.max_delay
                        )
                        
                        # 添加抖动避免雷群效应
                        if config.jitter:
                            delay *= (0.5 + random.random() * 0.5)
                            
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}"
                        )
                        
            raise last_exception
            
        return wrapper
    return decorator

class RetryHandler:
    """重试处理器类"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数调用"""
        retry_decorator = retry_with_backoff(self.config)
        retry_func = retry_decorator(func)
        return retry_func(*args, **kwargs)