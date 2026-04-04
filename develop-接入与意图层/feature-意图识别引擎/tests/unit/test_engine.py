"""
意图识别引擎 - 引擎测试

测试核心引擎功能

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import asyncio
import unittest

from core.engine import get_engine


class TestIntentEngine(unittest.TestCase):
    """
    意图引擎测试
    """
    
    def setUp(self):
        """
        测试前设置
        """
        self.engine = get_engine()
        self.engine.initialize()
    
    def tearDown(self):
        """
        测试后清理
        """
        self.engine.shutdown()
    
    async def test_recognize(self):
        """
        测试意图识别
        """
        # 测试聊天意图
        result = await self.engine.recognize("你好")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, "general_chat")
        self.assertGreater(result.confidence, 0.0)
    
    async def test_handle(self):
        """
        测试意图处理
        """
        # 测试聊天意图处理
        result = await self.engine.handle("general_chat", "你好", {})
        self.assertTrue(result.success)
        self.assertIn("你好", result.message)
    
    async def test_process(self):
        """
        测试完整处理流程
        """
        result = await self.engine.process("你好")
        self.assertIn("recognition", result)
        self.assertIn("handling", result)
        self.assertEqual(result["recognition"]["intent"], "general_chat")
        self.assertTrue(result["handling"]["success"])
    
    async def test_batch_process(self):
        """
        测试批量处理
        """
        queries = ["你好", "谢谢"]
        results = await self.engine.batch_process(queries)
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("recognition", result)
            self.assertIn("handling", result)
    
    def test_get_status(self):
        """
        测试获取状态
        """
        status = self.engine.get_status()
        self.assertTrue(status["initialized"])
        self.assertIsInstance(status["strategies"], list)
        self.assertIsInstance(status["handlers"], list)


if __name__ == '__main__':
    unittest.main()
