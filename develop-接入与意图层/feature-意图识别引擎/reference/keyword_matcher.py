"""
关键词匹配器 - 基于Trie树和正则表达式
参考LangChain设计模式和开发技术落地文档

核心特性:
1. Trie树前缀匹配 - O(m)复杂度
2. 正则表达式模式匹配
3. 同义词扩展支持
4. AC自动机多模式匹配

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-02
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import re
from collections import deque


@dataclass
class TrieNode:
    """
    Trie树节点
    
    支持中文字符的Unicode编码存储
    """
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    is_end: bool = False
    intent: Optional[str] = None
    priority: int = 1
    # 存储完整关键词（用于输出）
    full_keyword: str = ""


@dataclass
class KeywordMatch:
    """关键词匹配结果"""
    intent: str
    keyword: str
    position: Tuple[int, int]  # (start, end)
    priority: int


class TrieKeywordMatcher:
    """
    基于Trie树的关键词匹配器
    
    时间复杂度:
        - 插入: O(m)，m为关键词长度
        - 查找: O(m)
        - 前缀匹配: O(m + n)，n为结果数量
    
    空间复杂度: O(N * M)，N为关键词数量，M为平均长度
    """
    
    def __init__(self):
        self.root = TrieNode()
        self.keyword_count = 0
    
    def add_keyword(self, keyword: str, intent: str, priority: int = 1) -> None:
        """
        添加关键词到Trie树
        
        Args:
            keyword: 关键词（支持中文）
            intent: 对应的意图
            priority: 优先级，数值越小优先级越高
        """
        node = self.root
        for char in keyword:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        node.intent = intent
        node.priority = priority
        node.full_keyword = keyword
        self.keyword_count += 1
    
    def search(self, text: str) -> Optional[KeywordMatch]:
        """
        搜索文本中的关键词（精确匹配）
        
        Args:
            text: 输入文本
            
        Returns:
            最佳匹配结果或None
        """
        matches = self.search_all(text)
        if matches:
            # 按优先级排序，返回最高优先级的
            return min(matches, key=lambda x: x.priority)
        return None
    
    def search_all(self, text: str) -> List[KeywordMatch]:
        """
        搜索文本中的所有关键词匹配
        
        Args:
            text: 输入文本
            
        Returns:
            所有匹配结果列表
        """
        matches = []
        
        for i in range(len(text)):
            node = self.root
            for j in range(i, len(text)):
                char = text[j]
                if char not in node.children:
                    break
                node = node.children[char]
                if node.is_end:
                    matches.append(KeywordMatch(
                        intent=node.intent,
                        keyword=node.full_keyword,
                        position=(i, j + 1),
                        priority=node.priority
                    ))
        
        return matches
    
    def starts_with(self, prefix: str) -> List[str]:
        """
        前缀匹配 - 返回所有以prefix开头的关键词
        
        Args:
            prefix: 前缀
            
        Returns:
            匹配的关键词列表
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # BFS遍历所有子节点
        results = []
        queue = deque([(node, prefix)])
        
        while queue:
            current, current_prefix = queue.popleft()
            if current.is_end:
                results.append(current_prefix)
            
            for char, child in current.children.items():
                queue.append((child, current_prefix + char))
        
        return results


class AhoCorasickMatcher:
    """
    AC自动机多模式匹配器
    
    用于同时匹配多个关键词，时间复杂度为O(n + m + z)
    n为文本长度，m为所有模式长度之和，z为匹配数量
    
    适用场景:
        - 大量关键词匹配
        - 需要同时找出所有匹配
        - 实时文本过滤
    """
    
    def __init__(self):
        self.root = TrieNode()
        self.fail_links: Dict[TrieNode, TrieNode] = {}
        self.is_built = False
    
    def add_pattern(self, pattern: str, intent: str, priority: int = 1) -> None:
        """添加模式（关键词）"""
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        node.intent = intent
        node.priority = priority
        node.full_keyword = pattern
        self.is_built = False
    
    def build(self) -> None:
        """
        构建失败指针（AC自动机核心）
        
        使用BFS构建失败链接，确保匹配失败时能快速跳转
        """
        if self.is_built:
            return
        
        queue = deque()
        
        # 第一层节点的失败指针指向root
        for char, node in self.root.children.items():
            self.fail_links[node] = self.root
            queue.append(node)
        
        # BFS构建失败指针
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                # 计算失败指针
                fail = self.fail_links.get(current, self.root)
                while fail and char not in fail.children:
                    fail = self.fail_links.get(fail, self.root)
                
                if fail and char in fail.children:
                    self.fail_links[child] = fail.children[char]
                else:
                    self.fail_links[child] = self.root
                
                queue.append(child)
        
        self.is_built = True
    
    def search(self, text: str) -> List[KeywordMatch]:
        """
        在文本中搜索所有模式匹配
        
        Args:
            text: 输入文本
            
        Returns:
            所有匹配结果
        """
        if not self.is_built:
            self.build()
        
        matches = []
        node = self.root
        
        for i, char in enumerate(text):
            # 沿着失败指针跳转，直到找到匹配或回到根
            while node and char not in node.children:
                node = self.fail_links.get(node, self.root)
            
            if not node:
                node = self.root
                continue
            
            node = node.children[char]
            
            # 检查当前节点及失败链上的所有匹配
            temp = node
            while temp and temp != self.root:
                if temp.is_end:
                    matches.append(KeywordMatch(
                        intent=temp.intent,
                        keyword=temp.full_keyword,
                        position=(i - len(temp.full_keyword) + 1, i + 1),
                        priority=temp.priority
                    ))
                temp = self.fail_links.get(temp)
        
        return matches


class RegexPatternMatcher:
    """
    正则表达式模式匹配器
    
    特性:
        - 模式预编译缓存
        - 命名分组支持
        - 实体提取
    """
    
    def __init__(self):
        self.patterns: Dict[str, Tuple[re.Pattern, str, int]] = {}
        # pattern_id -> (compiled_pattern, intent, priority)
    
    def add_pattern(self, pattern_id: str, pattern: str, intent: str, priority: int = 1) -> None:
        """
        添加正则模式
        
        Args:
            pattern_id: 模式唯一标识
            pattern: 正则表达式字符串
            intent: 对应意图
            priority: 优先级
        """
        compiled = re.compile(pattern, re.IGNORECASE | re.UNICODE)
        self.patterns[pattern_id] = (compiled, intent, priority)
    
    def match(self, text: str) -> Optional[KeywordMatch]:
        """
        匹配文本
        
        Args:
            text: 输入文本
            
        Returns:
            最佳匹配结果或None
        """
        matches = self.match_all(text)
        if matches:
            return min(matches, key=lambda x: x.priority)
        return None
    
    def match_all(self, text: str) -> List[KeywordMatch]:
        """匹配所有模式"""
        matches = []
        
        for pattern_id, (compiled, intent, priority) in self.patterns.items():
            match = compiled.search(text)
            if match:
                matches.append(KeywordMatch(
                    intent=intent,
                    keyword=match.group(0),
                    position=(match.start(), match.end()),
                    priority=priority
                ))
        
        return matches
    
    def extract_entities(self, text: str, pattern_id: str) -> Dict[str, str]:
        """
        使用命名分组提取实体
        
        Args:
            text: 输入文本
            pattern_id: 模式ID
            
        Returns:
            实体字典
        """
        if pattern_id not in self.patterns:
            return {}
        
        compiled, _, _ = self.patterns[pattern_id]
        match = compiled.search(text)
        
        if match:
            return match.groupdict()
        return {}


class SynonymExpander:
    """
    同义词扩展器
    
    支持:
        - 同义词词典加载
        - 双向映射
        - 递归扩展
        - 输入文本扩展
    """
    
    def __init__(self):
        self.synonyms: Dict[str, Set[str]] = {}  # word -> synonyms
        self._built = False
    
    def add_synonym_group(self, words: List[str]) -> None:
        """
        添加同义词组
        
        Args:
            words: 同义词列表
        """
        word_set = set(words)
        for word in words:
            if word not in self.synonyms:
                self.synonyms[word] = set()
            self.synonyms[word].update(word_set - {word})
        self._built = False
    
    def expand(self, text: str, recursive: bool = False, max_depth: int = 2) -> Set[str]:
        """
        扩展文本中的同义词
        
        Args:
            text: 输入文本
            recursive: 是否递归扩展
            max_depth: 最大递归深度
            
        Returns:
            扩展后的文本集合
        """
        words = text.split()
        expanded_sets = []
        
        for word in words:
            synonyms = self._get_synonyms(word, recursive, max_depth, 0)
            expanded_sets.append(synonyms | {word})
        
        # 笛卡尔积组合
        from itertools import product
        results = set()
        for combination in product(*expanded_sets):
            results.add(" ".join(combination))
        
        return results
    
    def _get_synonyms(self, word: str, recursive: bool, max_depth: int, current_depth: int) -> Set[str]:
        """获取同义词"""
        if word not in self.synonyms:
            return set()
        
        result = self.synonyms[word].copy()
        
        if recursive and current_depth < max_depth:
            for syn in list(result):
                result.update(self._get_synonyms(syn, recursive, max_depth, current_depth + 1))
        
        return result


class KeywordMatcher:
    """
    关键词匹配器（主类）
    
    整合Trie树、AC自动机、正则表达式三种匹配方式
    支持同义词扩展
    
    使用示例:
        matcher = KeywordMatcher()
        matcher.add_keyword("写代码", "code_generation", priority=1)
        matcher.add_pattern("code_pattern", r".*写.*代码.*", "code_generation")
        matcher.add_synonyms(["写", "编写", "创建"])
        
        result = matcher.match("帮我编写代码")
    """
    
    def __init__(self):
        self.trie_matcher = TrieKeywordMatcher()
        self.ac_matcher = AhoCorasickMatcher()
        self.regex_matcher = RegexPatternMatcher()
        self.synonym_expander = SynonymExpander()
        self.use_synonym_expansion = True
    
    def add_keyword(self, keyword: str, intent: str, priority: int = 1) -> None:
        """添加关键词"""
        self.trie_matcher.add_keyword(keyword, intent, priority)
        self.ac_matcher.add_pattern(keyword, intent, priority)
    
    def add_pattern(self, pattern_id: str, pattern: str, intent: str, priority: int = 1) -> None:
        """添加正则模式"""
        self.regex_matcher.add_pattern(pattern_id, pattern, intent, priority)
    
    def add_synonyms(self, words: List[str]) -> None:
        """添加同义词组"""
        self.synonym_expander.add_synonym_group(words)
    
    def match(self, text: str, expand_synonyms: bool = True) -> Optional[Dict]:
        """
        执行关键词匹配
        
        Args:
            text: 输入文本
            expand_synonyms: 是否进行同义词扩展
            
        Returns:
            匹配结果字典或None
        """
        all_matches = []
        
        # 1. Trie树匹配
        trie_match = self.trie_matcher.search(text)
        if trie_match:
            all_matches.append(trie_match)
        
        # 2. AC自动机匹配（找出所有匹配）
        ac_matches = self.ac_matcher.search(text)
        all_matches.extend(ac_matches)
        
        # 3. 正则匹配
        regex_match = self.regex_matcher.match(text)
        if regex_match:
            all_matches.append(regex_match)
        
        # 4. 同义词扩展后匹配
        if expand_synonyms and self.use_synonym_expansion:
            expanded_texts = self.synonym_expander.expand(text)
            for expanded in expanded_texts:
                if expanded != text:
                    match = self.trie_matcher.search(expanded)
                    if match:
                        all_matches.append(match)
        
        if not all_matches:
            return None
        
        # 选择最佳匹配（按优先级）
        best = min(all_matches, key=lambda x: x.priority)
        
        return {
            "intent": best.intent,
            "confidence": 0.9 if best.priority == 1 else 0.8,
            "matched_keyword": best.keyword,
            "position": best.position,
            "strategy": "keyword"
        }
    
    def match_all(self, text: str) -> List[Dict]:
        """返回所有匹配结果"""
        matches = self.ac_matcher.search(text)
        regex_matches = self.regex_matcher.match_all(text)
        matches.extend(regex_matches)
        
        results = []
        for match in matches:
            results.append({
                "intent": match.intent,
                "confidence": 0.9 if match.priority == 1 else 0.8,
                "matched_keyword": match.keyword,
                "position": match.position
            })
        
        return results


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    
    # 创建匹配器
    matcher = KeywordMatcher()
    
    # 添加关键词
    matcher.add_keyword("写代码", "code_generation", priority=1)
    matcher.add_keyword("编程", "code_generation", priority=2)
    matcher.add_keyword("搜索", "search", priority=1)
    matcher.add_keyword("查找", "search", priority=2)
    
    # 添加正则模式
    matcher.add_pattern(
        "code_pattern",
        r".*写.*(代码|程序|函数).*",
        "code_generation"
    )
    
    # 添加同义词
    matcher.add_synonyms(["写", "编写", "创建", "实现"])
    matcher.add_synonyms(["搜索", "查找", "查询", "检索"])
    
    # 测试匹配
    test_texts = [
        "帮我写代码",
        "编写一个程序",
        "搜索文档",
        "查找资料"
    ]
    
    for text in test_texts:
        result = matcher.match(text)
        if result:
            print(f"'{text}' -> {result['intent']} (置信度: {result['confidence']:.2f})")
        else:
            print(f"'{text}' -> 未匹配")


if __name__ == "__main__":
    example_usage()
