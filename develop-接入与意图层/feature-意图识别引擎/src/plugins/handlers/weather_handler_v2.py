"""
意图识别引擎 - 天气处理器 V2

处理天气查询相关的意图，提供城市天气信息

作者: AI架构团队
版本: 2.0.0
日期: 2026-04-04
"""

import asyncio
from typing import Dict, Optional, Any

from interfaces.base_handler import BaseHandler, HandlerResult


class WeatherHandler(BaseHandler):
    """
    天气意图处理器
    
    处理天气查询相关的意图，根据城市返回对应的天气信息。
    目前支持模拟数据，可扩展为调用真实天气 API。
    
    Attributes:
        intent_name: 处理的意图名称，固定为 "weather_query"
        name: 处理器名称
        
    Example:
        >>> handler = WeatherHandler()
        >>> result = handler.handle_sync("北京天气", {"city": "北京"})
        >>> print(result.message)
        '北京今日晴，15-25度'
    """
    
    @property
    def intent_name(self) -> str:
        """
        处理的意图名称
        
        Returns:
            意图名称字符串，固定返回 "weather_query"
        """
        return "weather_query"
    
    async def handle(
        self, 
        query: str, 
        entities: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> HandlerResult:
        """
        异步处理天气查询意图
        
        将同步处理逻辑委托给 handle_sync 方法执行
        
        Args:
            query: 用户输入文本，例如 "北京天气怎么样"
            entities: 提取的实体信息，应包含 "city" 键
            context: 上下文信息，可选
            
        Returns:
            HandlerResult: 处理结果，包含天气信息或错误提示
            
        Example:
            >>> result = await handler.handle("北京天气", {"city": "北京"})
            >>> result.success
            True
            >>> result.message
            '北京今日晴，15-25度'
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.handle_sync, query, entities, context)
    
    def handle_sync(
        self, 
        query: str, 
        entities: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> HandlerResult:
        """
        同步处理天气查询意图
        
        从 entities 中提取城市信息，返回对应的天气数据。
        目前仅支持北京的模拟数据，其他城市返回未获取提示。
        
        Args:
            query: 用户输入文本，例如 "北京天气怎么样"
            entities: 提取的实体信息，应包含 "city" 键
            context: 上下文信息，可选
            
        Returns:
            HandlerResult: 处理结果
                - success: 是否成功处理
                - message: 天气信息或提示语
                - data: 包含城市、天气等详细信息
                - intent: 意图名称
                
        Example:
            >>> result = handler.handle_sync("北京天气", {"city": "北京"})
            >>> result.success
            True
            >>> result.message
            '北京今日晴，15-25度'
            >>> result.data
            {'city': '北京', 'weather': '晴', 'temperature': '15-25度'}
            
            >>> result = handler.handle_sync("上海天气", {"city": "上海"})
            >>> result.success
            False
            >>> result.message
            '暂未获取该城市天气'
        """
        try:
            # 从 entities 中提取城市信息
            city: Optional[str] = entities.get("city")
            
            # 如果没有城市信息，尝试从 query 中提取（简单实现）
            if not city and query:
                # 简单的城市提取逻辑
                cities = ["北京", "上海", "广州", "深圳", "杭州"]
                for c in cities:
                    if c in query:
                        city = c
                        break
            
            # 如果仍然没有城市信息，返回错误
            if not city:
                return HandlerResult(
                    success=False,
                    message="请提供城市信息",
                    data={"query": query, "entities": entities},
                    intent=self.intent_name
                )
            
            # 模拟天气数据查询
            weather_data = self._get_weather_data(city)
            
            if weather_data:
                return HandlerResult(
                    success=True,
                    message=f"{city}今日{weather_data['weather']}，{weather_data['temperature']}",
                    data={
                        "city": city,
                        "weather": weather_data["weather"],
                        "temperature": weather_data["temperature"],
                        "query": query
                    },
                    intent=self.intent_name
                )
            else:
                return HandlerResult(
                    success=False,
                    message="暂未获取该城市天气",
                    data={"city": city, "query": query},
                    intent=self.intent_name
                )
                
        except Exception as e:
            return HandlerResult(
                success=False,
                message=f"处理天气查询时发生错误: {str(e)}",
                error=str(e),
                intent=self.intent_name
            )
    
    def _get_weather_data(self, city: str) -> Optional[Dict[str, str]]:
        """
        获取城市天气数据（模拟实现）
        
        Args:
            city: 城市名称
            
        Returns:
            天气数据字典，包含 weather 和 temperature 键
            如果城市不支持，返回 None
            
        Example:
            >>> data = handler._get_weather_data("北京")
            >>> data
            {'weather': '晴', 'temperature': '15-25度'}
            
            >>> data = handler._get_weather_data("上海")
            >>> data
            None
        """
        # 模拟天气数据，仅支持北京
        weather_db = {
            "北京": {"weather": "晴", "temperature": "15-25度"},
        }
        
        return weather_db.get(city)
    
    def can_handle(self, intent_name: str) -> bool:
        """
        检查是否能处理指定意图
        
        重写基类方法，确保正确识别 weather_query 意图
        
        Args:
            intent_name: 意图名称
            
        Returns:
            如果 intent_name 等于 "weather_query"，返回 True，否则返回 False
            
        Example:
            >>> handler.can_handle("weather_query")
            True
            >>> handler.can_handle("code_generation")
            False
        """
        return intent_name == self.intent_name
