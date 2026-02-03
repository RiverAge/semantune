"""
缓存模块 - 简单的内存缓存实现
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from functools import wraps

from config.constants import CACHE_CONFIG


class CacheEntry:
    """缓存条目"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at


class SimpleCache:
    """简单的内存缓存"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._enabled = CACHE_CONFIG.get("enabled", True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        if not self._enabled:
            return None
        
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if entry.is_expired():
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
        """
        if not self._enabled:
            return
        
        if ttl is None:
            ttl = CACHE_CONFIG.get("user_profile_ttl", 300)
        
        self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> None:
        """
        删除缓存值
        
        Args:
            key: 缓存键
        """
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目
        
        Returns:
            清理的条目数量
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        # 将参数序列化为字符串
        key_parts = [prefix]
        
        if args:
            key_parts.extend(str(arg) for arg in args)
        
        if kwargs:
            # 对 kwargs 进行排序以确保一致性
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
        
        key_string = ":".join(key_parts)
        
        # 使用 MD5 哈希来缩短键长度
        return hashlib.md5(key_string.encode()).hexdigest()


# 全局缓存实例
cache = SimpleCache()


def cached(ttl: Optional[int] = None, prefix: str = "cache"):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间（秒）
        prefix: 缓存键前缀
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache.generate_key(prefix, func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache.generate_key(prefix, func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_user_cache(user_id: str) -> None:
    """
    使指定用户的缓存失效
    
    Args:
        user_id: 用户ID
    """
    # 由于我们使用哈希键，无法直接匹配用户ID
    # 这里简化处理：清空所有缓存
    # 在生产环境中，应该使用更智能的缓存失效策略
    cache.clear()
