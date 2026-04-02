import pytest
from src.access_intent.intent.engine import IntentEngine


@pytest.fixture
def intent_engine():
    return IntentEngine()


@pytest.mark.asyncio
async def test_keyword_matching(intent_engine):
    """测试关键词匹配"""
    result = await intent_engine.recognize("帮我搜索一下Python的列表推导式")
    assert result["intent_type"] == "search"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_semantic_retrieval(intent_engine):
    """测试语义检索"""
    result = await intent_engine.recognize("我想查找关于人工智能的最新研究")
    assert result["intent_type"] == "search"
    assert result["confidence"] >= 0.7


@pytest.mark.asyncio
async def test_few_shot_classification(intent_engine):
    """测试Few-shot分类"""
    result = await intent_engine.recognize("今天天气怎么样？")
    # 应该被分类为question或chat
    assert result["intent_type"] in ["question", "chat"]
    assert result["confidence"] >= 0.5
