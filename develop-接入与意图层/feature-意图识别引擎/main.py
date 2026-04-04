"""
意图识别引擎 - 主入口

统一的程序入口，支持命令行参数和交互模式

使用方式:
    python main.py                    # 运行演示模式
    python main.py --query "你好"      # 识别单个查询
    python main.py --interactive      # 交互模式
    python main.py --batch            # 批量测试模式

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加 src 到 Python 路径
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.engine import get_engine


async def demo_mode(engine):
    """演示模式 - 展示引擎功能"""
    print("=" * 60)
    print("🚀 意图识别引擎 - 演示模式")
    print("=" * 60)
    print()
    
    # 测试用例
    test_queries = [
        "你好",
        "谢谢",
        "再见",
        "帮我写代码",
        "搜索信息"
    ]
    
    print("=" * 60)
    print("测试意图识别")
    print("=" * 60)
    print()
    
    for query in test_queries:
        print(f"输入: '{query}'")
        result = await engine.process(query)
        
        recognition = result["recognition"]
        handling = result["handling"]
        
        print(f"识别意图: {recognition['intent']}")
        print(f"置信度: {recognition['confidence']:.2f}")
        print(f"策略: {recognition['strategy']}")
        print(f"处理时间: {recognition['processing_time_ms']:.2f}ms")
        print(f"处理结果: {handling['message']}")
        print()
    
    # 测试批量处理
    print("=" * 60)
    print("测试批量处理")
    print("=" * 60)
    print()
    
    batch_queries = ["你好", "谢谢", "再见"]
    batch_results = await engine.batch_process(batch_queries)
    
    for i, (query, result) in enumerate(zip(batch_queries, batch_results)):
        print(f"[{i+1}] 输入: '{query}'")
        print(f"   意图: {result['recognition']['intent']}")
        print(f"   结果: {result['handling']['message']}")
    
    print()


async def single_query_mode(engine, query):
    """单查询模式"""
    print(f"输入: '{query}'")
    result = await engine.process(query)
    
    recognition = result["recognition"]
    handling = result["handling"]
    
    print(f"识别意图: {recognition['intent']}")
    print(f"置信度: {recognition['confidence']:.2f}")
    print(f"策略: {recognition['strategy']}")
    print(f"处理时间: {recognition['processing_time_ms']:.2f}ms")
    print(f"处理结果: {handling['message']}")


async def interactive_mode(engine):
    """交互模式"""
    print("=" * 60)
    print("🚀 意图识别引擎 - 交互模式")
    print("输入 'exit' 或 'quit' 退出")
    print("=" * 60)
    print()
    
    while True:
        try:
            query = input("请输入: ").strip()
            if query.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break
            if not query:
                continue
            
            print()
            result = await engine.process(query)
            
            recognition = result["recognition"]
            handling = result["handling"]
            
            print(f"识别意图: {recognition['intent']}")
            print(f"置信度: {recognition['confidence']:.2f}")
            print(f"策略: {recognition['strategy']}")
            print(f"处理结果: {handling['message']}")
            print()
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="意图识别引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 运行演示模式
  python main.py -q "你好"           # 识别单个查询
  python main.py -i                 # 交互模式
        """
    )
    
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='要识别的查询文本'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='进入交互模式'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示模式（默认）'
    )
    
    args = parser.parse_args()
    
    # 初始化引擎
    print("正在初始化引擎...")
    engine = get_engine()
    engine.initialize()
    
    # 查看引擎状态
    status = engine.get_status()
    print(f"引擎状态: {status}")
    print()
    
    try:
        # 根据参数选择模式
        if args.query:
            await single_query_mode(engine, args.query)
        elif args.interactive:
            await interactive_mode(engine)
        else:
            await demo_mode(engine)
    finally:
        # 关闭引擎
        engine.shutdown()
        print()
        print("=" * 60)
        print("引擎运行完成")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
