from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import redis
import json
from datetime import datetime


@dataclass
class MemoryItem:
    """记忆项"""
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    priority: int = 0


class HotMemory:
    """热记忆（当前会话 + 工作记忆）"""
    
    def __init__(self):
        self.memories: Dict[str, List[MemoryItem]] = {}
    
    def add(self, session_id: str, item: MemoryItem):
        """添加记忆"""
        if session_id not in self.memories:
            self.memories[session_id] = []
        # 添加到列表开头
        self.memories[session_id].insert(0, item)
        # 限制记忆数量
        if len(self.memories[session_id]) > 100:
            self.memories[session_id] = self.memories[session_id][:100]
    
    def search(self, session_id: str, query: str) -> List[MemoryItem]:
        """搜索记忆"""
        if session_id not in self.memories:
            return []
        
        results = []
        for item in self.memories[session_id]:
            if query.lower() in item.content.lower():
                results.append(item)
        return results[:10]  # 返回前10个结果


class WarmMemory:
    """温记忆（近期会话摘要 + 活跃项目上下文）"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
        except:
            self.redis = None
            self.memory_store = {}
    
    async def add(self, session_id: str, item: MemoryItem):
        """添加记忆"""
        try:
            memory_data = {
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.timestamp,
                "priority": item.priority
            }
            if self.redis:
                # 使用Redis有序集合，按时间戳排序
                self.redis.zadd(
                    f"warm_memory:{session_id}",
                    {json.dumps(memory_data): float(item.timestamp.replace(":", ""))}
                )
                # 限制数量
                self.redis.zremrangebyrank(f"warm_memory:{session_id}", 0, -101)
            else:
                # 使用内存存储
                if session_id not in self.memory_store:
                    self.memory_store[session_id] = []
                self.memory_store[session_id].append(memory_data)
                if len(self.memory_store[session_id]) > 100:
                    self.memory_store[session_id] = self.memory_store[session_id][-100:]
        except Exception as e:
            print(f"Error adding to warm memory: {e}")
    
    async def search(self, session_id: str, query: str) -> List[MemoryItem]:
        """搜索记忆"""
        try:
            results = []
            if self.redis:
                # 获取所有记忆
                memory_datas = self.redis.zrange(f"warm_memory:{session_id}", 0, -1)
                for data in memory_datas:
                    memory_data = json.loads(data)
                    if query.lower() in memory_data["content"].lower():
                        results.append(MemoryItem(
                            content=memory_data["content"],
                            metadata=memory_data["metadata"],
                            timestamp=memory_data["timestamp"],
                            priority=memory_data["priority"]
                        ))
            else:
                # 使用内存存储
                if session_id in self.memory_store:
                    for memory_data in self.memory_store[session_id]:
                        if query.lower() in memory_data["content"].lower():
                            results.append(MemoryItem(
                                content=memory_data["content"],
                                metadata=memory_data["metadata"],
                                timestamp=memory_data["timestamp"],
                                priority=memory_data["priority"]
                            ))
            return results[:10]  # 返回前10个结果
        except Exception as e:
            print(f"Error searching warm memory: {e}")
            return []


class ColdMemory:
    """冷记忆（向量数据库 + 长期知识库）"""
    
    def __init__(self):
        # 简化实现，实际应该使用向量数据库
        self.memories: List[MemoryItem] = []
    
    def add(self, item: MemoryItem):
        """添加记忆"""
        self.memories.append(item)
    
    async def vector_search(self, query: str) -> List[MemoryItem]:
        """向量搜索"""
        # 简化实现，实际应该使用向量相似度搜索
        results = []
        for item in self.memories:
            if query.lower() in item.content.lower():
                results.append(item)
        return results[:10]  # 返回前10个结果


class MemoryMesh:
    """记忆网格"""
    
    def __init__(self):
        self.hot_memory = HotMemory()
        self.warm_memory = WarmMemory()
        self.cold_memory = ColdMemory()
    
    async def add_memory(self, session_id: str, content: str, metadata: Dict[str, Any], priority: int = 0):
        """添加记忆"""
        item = MemoryItem(
            content=content,
            metadata=metadata,
            timestamp=datetime.now().isoformat(),
            priority=priority
        )
        
        # 添加到热记忆
        self.hot_memory.add(session_id, item)
        
        # 添加到温记忆
        await self.warm_memory.add(session_id, item)
        
        # 添加到冷记忆（优先级高的才添加）
        if priority > 5:
            self.cold_memory.add(item)
    
    async def retrieve(self, session_id: str, query: str) -> List[MemoryItem]:
        """检索记忆"""
        # 1. 从热记忆检索
        hot_results = self.hot_memory.search(session_id, query)
        
        # 2. 从温记忆检索
        warm_results = await self.warm_memory.search(session_id, query)
        
        # 3. 从冷记忆检索
        cold_results = await self.cold_memory.vector_search(query)
        
        # 4. 融合排序
        all_results = hot_results + warm_results + cold_results
        
        # 去重
        seen = set()
        unique_results = []
        for item in all_results:
            key = (item.content, item.timestamp)
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        
        # 按优先级和时间戳排序
        unique_results.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
        
        return unique_results[:15]  # 返回前15个结果
