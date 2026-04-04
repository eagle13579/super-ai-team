"""
意图识别引擎 - 实体提取器

从查询中提取结构化信息

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-04
"""

import re
from typing import Dict, List, Optional, Any, Pattern
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Entity:
    """实体定义"""
    name: str
    value: Any
    start: int
    end: int
    confidence: float = 1.0


class EntityExtractor:
    """
    实体提取器
    
    从查询中提取结构化信息，支持多种实体类型
    """
    
    def __init__(self):
        """初始化实体提取器"""
        # 城市列表
        self.cities = [
            "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "重庆",
            "天津", "苏州", "长沙", "郑州", "沈阳", "青岛", "宁波", "东莞", "无锡", "佛山"
        ]
        
        # 日期模式
        self.date_patterns = [
            (r'(今天|明天|后天|昨天|前天)', 'relative'),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 'absolute'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'absolute'),
            (r'(\d{1,2})月(\d{1,2})日', 'absolute_month_day'),
        ]
        
        # 时间模式
        self.time_patterns = [
            (r'(上午|下午|晚上|早上|中午|凌晨)(\d{1,2})点', 'period'),
            (r'(\d{1,2})点(\d{1,2})分', 'hour_minute'),
            (r'(\d{1,2})点', 'hour'),
        ]
        
        # 数字模式
        self.number_pattern = re.compile(r'\d+')
        
        # 货币模式
        self.currency_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(元|块|美元|人民币|USD|CNY)')
        
        # 邮箱模式
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
        # 手机号模式
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        
        # URL模式
        self.url_pattern = re.compile(r'https?://[^\s]+')
    
    def extract(self, query: str, intent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        从查询中提取实体
        
        Args:
            query: 用户输入文本
            intent_name: 意图名称（可选，用于针对性提取）
            
        Returns:
            提取的实体字典
        """
        entities = {}
        
        # 提取城市
        city = self._extract_city(query)
        if city:
            entities['city'] = city
        
        # 提取日期
        date = self._extract_date(query)
        if date:
            entities['date'] = date
        
        # 提取时间
        time = self._extract_time(query)
        if time:
            entities['time'] = time
        
        # 提取数字
        numbers = self._extract_numbers(query)
        if numbers:
            entities['numbers'] = numbers
        
        # 提取货币
        currency = self._extract_currency(query)
        if currency:
            entities['currency'] = currency
        
        # 提取邮箱
        emails = self._extract_emails(query)
        if emails:
            entities['emails'] = emails
        
        # 提取手机号
        phones = self._extract_phones(query)
        if phones:
            entities['phones'] = phones
        
        # 提取URL
        urls = self._extract_urls(query)
        if urls:
            entities['urls'] = urls
        
        # 根据意图进行针对性提取
        if intent_name:
            intent_entities = self._extract_by_intent(query, intent_name)
            entities.update(intent_entities)
        
        return entities
    
    def _extract_city(self, query: str) -> Optional[str]:
        """提取城市"""
        for city in self.cities:
            if city in query:
                return city
        return None
    
    def _extract_date(self, query: str) -> Optional[str]:
        """提取日期"""
        for pattern, date_type in self.date_patterns:
            match = re.search(pattern, query)
            if match:
                if date_type == 'relative':
                    return self._parse_relative_date(match.group(1))
                elif date_type == 'absolute':
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    day = match.group(3).zfill(2)
                    return f"{year}-{month}-{day}"
                elif date_type == 'absolute_month_day':
                    month = match.group(1).zfill(2)
                    day = match.group(2).zfill(2)
                    year = datetime.now().year
                    return f"{year}-{month}-{day}"
        return None
    
    def _parse_relative_date(self, relative: str) -> str:
        """解析相对日期"""
        today = datetime.now()
        
        if relative == '今天':
            return today.strftime('%Y-%m-%d')
        elif relative == '明天':
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif relative == '后天':
            return (today + timedelta(days=2)).strftime('%Y-%m-%d')
        elif relative == '昨天':
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif relative == '前天':
            return (today - timedelta(days=2)).strftime('%Y-%m-%d')
        
        return today.strftime('%Y-%m-%d')
    
    def _extract_time(self, query: str) -> Optional[str]:
        """提取时间"""
        for pattern, time_type in self.time_patterns:
            match = re.search(pattern, query)
            if match:
                if time_type == 'period':
                    period = match.group(1)
                    hour = int(match.group(2))
                    # 转换下午时间
                    if period in ['下午', '晚上'] and hour < 12:
                        hour += 12
                    return f"{hour:02d}:00"
                elif time_type == 'hour_minute':
                    hour = match.group(1).zfill(2)
                    minute = match.group(2).zfill(2)
                    return f"{hour}:{minute}"
                elif time_type == 'hour':
                    hour = match.group(1).zfill(2)
                    return f"{hour}:00"
        return None
    
    def _extract_numbers(self, query: str) -> List[int]:
        """提取数字"""
        matches = self.number_pattern.findall(query)
        return [int(m) for m in matches]
    
    def _extract_currency(self, query: str) -> Optional[List[Dict]]:
        """提取货币"""
        matches = self.currency_pattern.findall(query)
        if matches:
            return [
                {
                    'amount': float(amount),
                    'currency': currency
                }
                for amount, currency in matches
            ]
        return None
    
    def _extract_emails(self, query: str) -> List[str]:
        """提取邮箱"""
        return self.email_pattern.findall(query)
    
    def _extract_phones(self, query: str) -> List[str]:
        """提取手机号"""
        return self.phone_pattern.findall(query)
    
    def _extract_urls(self, query: str) -> List[str]:
        """提取URL"""
        return self.url_pattern.findall(query)
    
    def _extract_by_intent(self, query: str, intent_name: str) -> Dict[str, Any]:
        """
        根据意图进行针对性提取
        
        Args:
            query: 用户输入文本
            intent_name: 意图名称
            
        Returns:
            提取的实体
        """
        entities = {}
        
        # 代码生成意图
        if intent_name == 'code_generation':
            # 提取编程语言
            languages = ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust', 'TypeScript']
            for lang in languages:
                if lang.lower() in query.lower():
                    entities['language'] = lang
                    break
            
            # 提取代码行数
            line_match = re.search(r'(\d+)\s*行', query)
            if line_match:
                entities['line_count'] = int(line_match.group(1))
        
        # 搜索意图
        elif intent_name == 'information_search':
            # 提取搜索关键词
            search_terms = re.findall(r'搜索(.+?)(?:的|信息|$)', query)
            if search_terms:
                entities['search_terms'] = search_terms
        
        # 天气查询意图
        elif intent_name == 'weather_query':
            # 提取温度单位
            if '摄氏度' in query or '°C' in query:
                entities['temperature_unit'] = 'celsius'
            elif '华氏度' in query or '°F' in query:
                entities['temperature_unit'] = 'fahrenheit'
        
        return entities
    
    def extract_all_entities(self, query: str) -> List[Entity]:
        """
        提取所有实体（带位置信息）
        
        Args:
            query: 用户输入文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 提取城市
        for city in self.cities:
            for match in re.finditer(re.escape(city), query):
                entities.append(Entity(
                    name='city',
                    value=city,
                    start=match.start(),
                    end=match.end()
                ))
        
        # 提取日期
        for pattern, date_type in self.date_patterns:
            for match in re.finditer(pattern, query):
                entities.append(Entity(
                    name='date',
                    value=match.group(0),
                    start=match.start(),
                    end=match.end()
                ))
        
        # 提取数字
        for match in re.finditer(r'\d+', query):
            entities.append(Entity(
                name='number',
                value=int(match.group(0)),
                start=match.start(),
                end=match.end()
            ))
        
        return entities


# 全局实体提取器实例
_extractor = None


def get_extractor() -> EntityExtractor:
    """
    获取全局实体提取器实例
    
    Returns:
        实体提取器实例
    """
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extract_entities(query: str, intent_name: Optional[str] = None) -> Dict[str, Any]:
    """
    提取实体的便捷函数
    
    Args:
        query: 用户输入文本
        intent_name: 意图名称
        
    Returns:
        提取的实体字典
    """
    return get_extractor().extract(query, intent_name)
