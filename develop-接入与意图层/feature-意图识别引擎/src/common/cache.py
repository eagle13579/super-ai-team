"""
意图识别引擎 - 缓存系统

提供多级缓存机制，优化性能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # 过期时间（秒）
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl
    
    def get_value(self) -> Any:
        """获取值（如果未过期）"""
        if self.is_expired():
            return None
        return self.value


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheItem] = {}
        self._access_order: List[str] = []  # 最近访问的键在末尾
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        if item.is_expired():
            self._remove(key)
            return None
        
        # 更新访问顺序
        self._update_access_order(key)
        return item.get_value()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        
        # 如果缓存已满，删除最久未使用的项
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._remove(self._access_order[0])
        
        self._cache[key] = CacheItem(value, ttl)
        self._update_access_order(key)
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        return self._remove(key)
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def _remove(self, key: str) -> bool:
        """移除缓存项"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    def _update_access_order(self, key: str) -> None:
        """更新访问顺序"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def size(self) -> int:
        """获取缓存大小"""
        # 清理过期项
        self._clean_expired()
        return len(self._cache)
    
    def _clean_expired(self) -> None:
        """清理过期项"""
        expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
        for key in expired_keys:
            self._remove(key)


class IntentCache:
    """意图识别结果缓存"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache = LRUCache(max_size, default_ttl)
    
    def get(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """获取缓存结果"""
        key = self._generate_key(query, context)
        return self.cache.get(key)
    
    def set(self, query: str, result: Any, context: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> None:
        """设置缓存结果"""
        key = self._generate_key(query, context)
        self.cache.set(key, result, ttl)
    
    def delete(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """删除缓存项"""
        key = self._generate_key(query, context)
        return self.cache.delete(key)
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return self.cache.size()
    
    def _generate_key(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        key = f"query:{query}"
        if context:
            # 简单的上下文哈希
            context_hash = hash(str(sorted(context.items())))
            key += f":context:{context_hash}"
        return key


# 全局缓存实例
_intent_cache = None


def get_cache() -> IntentCache:
    """
    获取全局缓存实例
    
    Returns:
        缓存实例
    """
    global _intent_cache
    if _intent_cache is None:
        _intent_cache = IntentCache()
    return _intent_cache
