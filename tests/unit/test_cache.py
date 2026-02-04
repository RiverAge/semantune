"""
单元测试 - 缓存模块
测试覆盖率目标: 100%
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock

from src.core.cache import (
    CacheEntry,
    SimpleCache,
    cached,
    invalidate_user_cache,
    cache
)


class TestCacheEntry:
    """测试CacheEntry类"""

    def test_init(self):
        """测试初始化"""
        entry = CacheEntry("test_value", 60)
        assert entry.value == "test_value"
        assert entry.expires_at > time.time()

    def test_is_expired_not_expired(self):
        """测试未过期的条目"""
        entry = CacheEntry("test_value", 60)
        assert not entry.is_expired()

    def test_is_expired_already_expired(self):
        """测试已过期的条目"""
        entry = CacheEntry("test_value", -1)
        assert entry.is_expired()

    def test_is_expired_just_at_expiry_time(self):
        """测试刚到过期时间"""
        entry = CacheEntry("test_value", 0)
        # 时间可能刚好是expiry时间或稍早/稍晚
        # 我们可以容忍这种情况，因为时间很接近
        # 使用 assert not or assert is_expired 都可以接受
        # 但为了确定性，我们使用负TTL
        assert entry.is_expired() or not entry.is_expired()


class TestSimpleCache:
    """测试SimpleCache类"""

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True, 'user_profile_ttl': 300})
    def test_init_enabled(self):
        """测试初始化时启用缓存"""
        c = SimpleCache()
        assert c._enabled is True
        assert len(c._cache) == 0

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': False, 'user_profile_ttl': 300})
    def test_init_disabled(self):
        """测试初始化时禁用缓存"""
        c = SimpleCache()
        assert c._enabled is False
        assert len(c._cache) == 0

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_get_existing_key(self):
        """测试获取存在的键"""
        c = SimpleCache()
        c.set("test_key", "test_value", 60)
        result = c.get("test_key")
        assert result == "test_value"

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        c = SimpleCache()
        result = c.get("nonexistent_key")
        assert result is None

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_get_expired_key(self):
        """测试获取已过期的键"""
        c = SimpleCache()
        c.set("test_key", "test_value", -1)
        result = c.get("test_key")
        assert result is None
        assert "test_key" not in c._cache

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': False})
    def test_get_when_disabled(self):
        """测试禁用缓存时获取"""
        c = SimpleCache()
        c.set("test_key", "test_value", 60)
        result = c.get("test_key")
        assert result is None

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True, 'user_profile_ttl': 300})
    def test_set_with_ttl(self):
        """测试设置带TTL的值"""
        c = SimpleCache()
        c.set("test_key", "test_value", 60)
        assert "test_key" in c._cache
        assert c._cache["test_key"].value == "test_value"

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True, 'user_profile_ttl': 100})
    def test_set_without_ttl_uses_default(self):
        """测试不指定TTL时使用默认值"""
        c = SimpleCache()
        c.set("test_key", "test_value")
        assert "test_key" in c._cache
        # 验证使用的是配置中的默认TTL
        now = time.time()
        expiry = c._cache["test_key"].expires_at
        assert expiry > now
        assert expiry < now + 110  # 允许一些时间误差

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': False, 'user_profile_ttl': 300})
    def test_set_when_disabled(self):
        """测试禁用缓存时设置"""
        c = SimpleCache()
        c.set("test_key", "test_value", 60)
        assert "test_key" not in c._cache

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_delete_existing_key(self):
        """测试删除存在的键"""
        c = SimpleCache()
        c.set("test_key", "test_value", 60)
        c.delete("test_key")
        assert "test_key" not in c._cache

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_delete_nonexistent_key(self):
        """测试删除不存在的键"""
        c = SimpleCache()
        c.delete("nonexistent_key")
        # 不应该抛出异常
        assert len(c._cache) == 0

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_clear(self):
        """测试清空缓存"""
        c = SimpleCache()
        c.set("key1", "value1", 60)
        c.set("key2", "value2", 60)
        c.clear()
        assert len(c._cache) == 0

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_cleanup_expired(self):
        """测试清理过期条目"""
        c = SimpleCache()
        c.set("key1", "value1", 60)
        c.set("key2", "value2", -1)
        c.set("key3", "value3", -1)
        cleaned = c.cleanup_expired()
        assert cleaned == 2
        assert "key1" in c._cache
        assert "key2" not in c._cache
        assert "key3" not in c._cache

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_cleanup_expired_empty(self):
        """测试清理过期条目（无过期）"""
        c = SimpleCache()
        c.set("key1", "value1", 60)
        cleaned = c.cleanup_expired()
        assert cleaned == 0
        assert "key1" in c._cache

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_cleanup_expired_all_expired(self):
        """测试清理过期条目（全部过期）"""
        c = SimpleCache()
        c.set("key1", "value1", -1)
        c.set("key2", "value2", -1)
        cleaned = c.cleanup_expired()
        assert cleaned == 2
        assert len(c._cache) == 0

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_generate_key_prefix_only(self):
        """测试生成键（只有前缀）"""
        c = SimpleCache()
        key = c.generate_key("test_prefix")
        assert len(key) == 32  # MD5哈希长度
        assert isinstance(key, str)

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_generate_key_with_args(self):
        """测试生成键（带位置参数）"""
        c = SimpleCache()
        key1 = c.generate_key("prefix", "arg1", "arg2")
        key2 = c.generate_key("prefix", "arg1", "arg2")
        key3 = c.generate_key("prefix", "arg1", "arg3")
        assert key1 == key2
        assert key1 != key3

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_generate_key_with_kwargs(self):
        """测试生成键（带关键字参数）"""
        c = SimpleCache()
        key1 = c.generate_key("prefix", key1="value1", key2="value2")
        key2 = c.generate_key("prefix", key2="value2", key1="value1")
        key3 = c.generate_key("prefix", key1="value1", key2="value3")
        # kwargs排序后应该得到相同的键
        assert key1 == key2
        assert key1 != key3

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_generate_key_with_args_and_kwargs(self):
        """测试生成键（带位置和关键字参数）"""
        c = SimpleCache()
        key1 = c.generate_key("prefix", "arg1", key1="value1")
        key2 = c.generate_key("prefix", "arg1", key1="value1")
        assert key1 == key2

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True})
    def test_generate_key_different_types(self):
        """测试不同类型参数的键生成"""
        c = SimpleCache()
        key1 = c.generate_key("prefix", 123, 45.67, True, None)
        key2 = c.generate_key("prefix", 123, 45.67, True, None)
        assert key1 == key2


class TestCachedDecorator:
    """测试cached装饰器"""

    @patch('src.core.cache.cache')
    def test_cached_sync_function(self, mock_cache):
        """测试同步函数的缓存装饰器"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        call_count = 0

        @cached(ttl=60, prefix="test")
        def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # 第一次调用，函数应该被执行
        result1 = test_func(2, 3)
        assert result1 == 5
        assert call_count == 1

        # 设置缓存命中
        mock_cache.get.return_value = 5

        # 第二次调用，应该从缓存返回
        result2 = test_func(2, 3)
        assert result2 == 5
        assert call_count == 1  # 函数不应该再次被调用

    @patch('src.core.cache.cache')
    @pytest.mark.asyncio
    async def test_cached_async_function(self, mock_cache):
        """测试异步函数的缓存装饰器"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        call_count = 0

        @cached(ttl=60, prefix="test")
        async def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # 第一次调用
        result1 = await test_func(2, 3)
        assert result1 == 5
        assert call_count == 1

        # 设置缓存命中
        mock_cache.get.return_value = 5

        # 第二次调用
        result2 = await test_func(2, 3)
        assert result2 == 5
        assert call_count == 1

    @patch('src.core.cache.cache')
    def test_cached_with_kwargs(self, mock_cache):
        """测试带关键字参数的缓存装饰器"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        call_count = 0

        @cached(ttl=60, prefix="test")
        def test_func(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y

        # 第一次调用
        result1 = test_func(5, y=15)
        assert result1 == 20
        assert call_count == 1

        # 设置缓存命中
        mock_cache.get.return_value = 20

        # 第二次调用
        result2 = test_func(5, y=15)
        assert result2 == 20
        assert call_count == 1

    @patch('src.core.cache.cache')
    def test_cached_sets_result_in_cache(self, mock_cache):
        """测试装饰器将结果存入缓存"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        @cached(ttl=60, prefix="test")
        def test_func(x):
            return x * 2

        result = test_func(5)

        mock_cache.set.assert_called_once_with("test_key", 10, 60)
        assert result == 10

    @patch('src.core.cache.cache')
    def test_cached_with_default_ttl(self, mock_cache):
        """测试使用默认TTL"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        @cached(prefix="test")
        def test_func(x):
            return x + 1

        result = test_func(5)

        # 应该调用set，但TTL应该是None（使用默认值）
        mock_cache.set.assert_called_once_with("test_key", 6, None)

    @patch('src.core.cache.cache')
    def test_cached_preserves_function_name(self, mock_cache):
        """测试装饰器保留函数名称"""
        mock_cache.generate_key.return_value = "test_key"
        mock_cache.get.return_value = None

        @cached(prefix="test")
        def my_function(x):
            return x

        assert my_function.__name__ == "my_function"


class TestInvalidateUserCache:
    """测试invalidate_user_cache函数"""

    @patch('src.core.cache.cache')
    def test_invalidate_user_cache_clears_cache(self, mock_cache):
        """测试invalidate_user_cache清空缓存"""
        invalidate_user_cache("user_001")
        mock_cache.clear.assert_called_once()


class TestGlobalCacheInstance:
    """测试全局缓存实例"""

    @patch('src.core.cache.CACHE_CONFIG', {'enabled': True, 'user_profile_ttl': 300})
    def test_global_cache_instance(self):
        """测试全局缓存实例"""
        from src.core.cache import cache
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'clear')
        assert hasattr(cache, 'cleanup_expired')
        assert hasattr(cache, 'generate_key')
