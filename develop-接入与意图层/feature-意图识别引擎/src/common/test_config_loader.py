"""
测试配置加载器

验证 ConfigLoader 类和 get_setting 函数的功能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

from config_loader import ConfigLoader, get_setting, ConfigError


def test_config_loader():
    """
    测试配置加载器
    """
    print("=" * 60)
    print("测试配置加载器")
    print("=" * 60)
    print()
    
    # 测试 1: 单例模式
    print("1. 测试单例模式")
    config1 = ConfigLoader()
    config2 = ConfigLoader()
    print(f"   单例模式验证: {config1 is config2}")
    print()
    
    # 测试 2: 加载配置
    print("2. 测试加载配置")
    try:
        config = ConfigLoader()
        all_config = config.get_all()
        print(f"   配置加载成功，配置项数量: {len(all_config)}")
        print(f"   引擎配置: {all_config.get('engine', {})}")
    except ConfigError as e:
        print(f"   配置加载失败: {e}")
    print()
    
    # 测试 3: 嵌套键访问
    print("3. 测试嵌套键访问")
    try:
        plugins_dir = get_setting("plugins.directory")
        auto_load = get_setting("plugins.auto_load")
        keyword_threshold = get_setting("strategies.keyword.threshold")
        
        print(f"   plugins.directory: {plugins_dir}")
        print(f"   plugins.auto_load: {auto_load}")
        print(f"   strategies.keyword.threshold: {keyword_threshold}")
    except Exception as e:
        print(f"   嵌套键访问失败: {e}")
    print()
    
    # 测试 4: 默认值
    print("4. 测试默认值")
    try:
        non_existent = get_setting("non.existent.key", "default_value")
        print(f"   不存在的键（使用默认值）: {non_existent}")
    except Exception as e:
        print(f"   默认值测试失败: {e}")
    print()
    
    # 测试 5: 重新加载
    print("5. 测试重新加载")
    try:
        config = ConfigLoader()
        before_reload = config.get("engine.name")
        config.reload()
        after_reload = config.get("engine.name")
        print(f"   重新加载前: {before_reload}")
        print(f"   重新加载后: {after_reload}")
    except Exception as e:
        print(f"   重新加载测试失败: {e}")
    print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_config_loader()
