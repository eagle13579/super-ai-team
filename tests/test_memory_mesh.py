import pytest
from src.memory_persistence.memory.mesh import MemoryMesh


@pytest.fixture
def memory_mesh():
    return MemoryMesh()


@pytest.mark.asyncio
async def test_add_and_retrieve_memory(memory_mesh):
    """测试添加和检索记忆"""
    session_id = "test_session"
    content = "测试记忆内容"
    metadata = {"source": "test"}
    
    # 添加记忆
    await memory_mesh.add_memory(session_id, content, metadata, priority=5)
    
    # 检索记忆
    results = await memory_mesh.retrieve(session_id, "测试")
    assert len(results) > 0
    assert results[0].content == content
    assert results[0].metadata == metadata


@pytest.mark.asyncio
async def test_memory_priority(memory_mesh):
    """测试记忆优先级"""
    session_id = "test_session_2"
    
    # 添加低优先级记忆
    await memory_mesh.add_memory(session_id, "低优先级记忆", {"priority": "low"}, priority=1)
    
    # 添加高优先级记忆
    await memory_mesh.add_memory(session_id, "高优先级记忆", {"priority": "high"}, priority=10)
    
    # 检索记忆
    results = await memory_mesh.retrieve(session_id, "记忆")
    assert len(results) >= 2
    # 高优先级记忆应该排在前面
    assert results[0].content == "高优先级记忆"
    assert results[0].priority == 10
