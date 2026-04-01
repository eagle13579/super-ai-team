import pytest
from src.skill_execution.skills.registry import SkillRegistry


@pytest.fixture
def skill_registry():
    return SkillRegistry()


@pytest.mark.asyncio
async def test_list_skills(skill_registry):
    """测试列出所有技能"""
    skills = skill_registry.list_skills()
    assert isinstance(skills, list)
    assert "web_search" in skills
    assert "file_operations" in skills


@pytest.mark.asyncio
async def test_get_skill(skill_registry):
    """测试获取技能"""
    web_search_skill = skill_registry.get_skill("web_search")
    assert web_search_skill is not None
    assert web_search_skill.name == "web_search"
    
    file_ops_skill = skill_registry.get_skill("file_operations")
    assert file_ops_skill is not None
    assert file_ops_skill.name == "file_operations"


@pytest.mark.asyncio
async def test_get_skill_info(skill_registry):
    """测试获取技能信息"""
    info = skill_registry.get_skill_info("web_search")
    assert info is not None
    assert info["name"] == "web_search"
    assert info["version"] == "1.0.0"
    assert "input_schema" in info
    assert "output_schema" in info
