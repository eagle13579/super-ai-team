"""
语义检索器 - 基于Embedding和向量索引
参考LangChain设计模式和开发技术落地文档

核心特性:
1. Embedding模型封装
2. FAISS向量索引
3. 相似度计算
4. 语义缓存

作者: AI架构团队
版本: 1.0.0
日期: 2026-04-02
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from pydantic import BaseModel, Field


@dataclass
class RetrievalResult:
    """检索结果"""
    intent: str
    similarity: float
    text: str
    metadata: Dict[str, Any] = None


class EmbeddingModel(ABC):
    """
    Embedding模型抽象基类
    
    参考LangChain的Embeddings接口设计
    支持多种Embedding模型（BERT、SentenceTransformer等）
    """
    
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        将文本列表编码为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量数组 (N, D)，N为文本数量，D为向量维度
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """
        将单个查询文本编码为向量
        
        Args:
            text: 查询文本
            
        Returns:
            向量 (D,)
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class MockEmbeddingModel(EmbeddingModel):
    """
    Mock Embedding模型（用于测试）
    
    实际项目中应替换为:
        - SentenceTransformer
        - OpenAI Embeddings
        - 或其他Embedding模型
    """
    
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._cache: Dict[str, np.ndarray] = {}
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Mock编码 - 使用哈希生成确定性向量"""
        vectors = []
        for text in texts:
            if text in self._cache:
                vectors.append(self._cache[text])
            else:
                # 使用文本哈希生成确定性向量
                np.random.seed(hash(text) % (2**32))
                vec = np.random.randn(self._dimension).astype(np.float32)
                vec = vec / np.linalg.norm(vec)  # 归一化
                self._cache[text] = vec
                vectors.append(vec)
        return np.array(vectors)
    
    def embed_query(self, text: str) -> np.ndarray:
        """编码单个查询"""
        return self.embed([text])[0]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class VectorIndex(ABC):
    """
    向量索引抽象基类
    
    参考LangChain的VectorStore设计
    支持多种索引实现（FAISS、Annoy、HNSW等）
    """
    
    @abstractmethod
    def add(self, vectors: np.ndarray, texts: List[str], intents: List[str]) -> None:
        """
        添加向量到索引
        
        Args:
            vectors: 向量数组 (N, D)
            texts: 文本列表
            intents: 意图列表
        """
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """
        搜索最相似的向量
        
        Args:
            query_vector: 查询向量 (D,)
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """保存索引到文件"""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """从文件加载索引"""
        pass


class SimpleVectorIndex(VectorIndex):
    """
    简单向量索引实现（基于numpy）
    
    适用于小规模数据，大规模数据应使用FAISS
    
    时间复杂度:
        - 添加: O(1)
        - 搜索: O(N * D)，N为向量数量，D为维度
    
    空间复杂度: O(N * D)
    """
    
    def __init__(self):
        self.vectors: Optional[np.ndarray] = None
        self.texts: List[str] = []
        self.intents: List[str] = []
        self.metadata: List[Dict] = []
    
    def add(self, vectors: np.ndarray, texts: List[str], intents: List[str]) -> None:
        """添加向量到索引"""
        if self.vectors is None:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])
        
        self.texts.extend(texts)
        self.intents.extend(intents)
        self.metadata.extend([{} for _ in texts])
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """
        余弦相似度搜索
        
        使用点积计算（假设向量已归一化）
        """
        if self.vectors is None or len(self.vectors) == 0:
            return []
        
        # 计算余弦相似度
        similarities = np.dot(self.vectors, query_vector)
        
        # 获取top_k索引
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append(RetrievalResult(
                intent=self.intents[idx],
                similarity=float(similarities[idx]),
                text=self.texts[idx],
                metadata=self.metadata[idx] if idx < len(self.metadata) else {}
            ))
        
        return results
    
    def save(self, path: str) -> None:
        """保存索引"""
        import json
        data = {
            "vectors": self.vectors.tolist() if self.vectors is not None else [],
            "texts": self.texts,
            "intents": self.intents,
            "metadata": self.metadata
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def load(self, path: str) -> None:
        """加载索引"""
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vectors = np.array(data["vectors"]) if data["vectors"] else None
        self.texts = data["texts"]
        self.intents = data["intents"]
        self.metadata = data.get("metadata", [{} for _ in self.texts])


class FaissVectorIndex(VectorIndex):
    """
    FAISS向量索引实现
    
    适用于大规模数据，支持多种索引类型:
        - IndexFlatIP: 精确内积（适合小数据集）
        - IndexIVFFlat: 倒排文件索引（适合大数据集）
        - IndexHNSW: 分层导航小世界图（适合高维数据）
    
    需要先安装faiss: pip install faiss-cpu 或 faiss-gpu
    """
    
    def __init__(self, index_type: str = "flat", dimension: int = 384):
        self.index_type = index_type
        self.dimension = dimension
        self.index = None
        self.texts: List[str] = []
        self.intents: List[str] = []
        self._faiss = None
        
        try:
            import faiss
            self._faiss = faiss
        except ImportError:
            print("Warning: faiss not installed, falling back to SimpleVectorIndex")
    
    def _create_index(self):
        """创建FAISS索引"""
        if self._faiss is None:
            return
        
        if self.index_type == "flat":
            # 精确内积搜索（向量需归一化）
            self.index = self._faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "ivf":
            # IVF索引
            quantizer = self._faiss.IndexFlatIP(self.dimension)
            self.index = self._faiss.IndexIVFFlat(
                quantizer, self.dimension, 100, self._faiss.METRIC_INNER_PRODUCT
            )
        elif self.index_type == "hnsw":
            # HNSW索引
            self.index = self._faiss.IndexHNSWFlat(self.dimension, 32)
            self.index.hnsw.efConstruction = 200
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
    
    def add(self, vectors: np.ndarray, texts: List[str], intents: List[str]) -> None:
        """添加向量到索引"""
        if self._faiss is None:
            return
        
        if self.index is None:
            self._create_index()
        
        # 确保向量是float32类型
        vectors = vectors.astype(np.float32)
        
        # 如果是IVF索引，需要先训练
        if self.index_type == "ivf" and not self.index.is_trained:
            self.index.train(vectors)
        
        self.index.add(vectors)
        self.texts.extend(texts)
        self.intents.extend(intents)
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """搜索最相似的向量"""
        if self._faiss is None or self.index is None:
            return []
        
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.intents):
                continue
            results.append(RetrievalResult(
                intent=self.intents[idx],
                similarity=float(dist),
                text=self.texts[idx]
            ))
        
        return results
    
    def save(self, path: str) -> None:
        """保存索引"""
        if self._faiss is None or self.index is None:
            return
        
        self._faiss.write_index(self.index, f"{path}.faiss")
        import json
        with open(f"{path}.meta", 'w', encoding='utf-8') as f:
            json.dump({"texts": self.texts, "intents": self.intents}, f, ensure_ascii=False)
    
    def load(self, path: str) -> None:
        """加载索引"""
        if self._faiss is None:
            return
        
        self.index = self._faiss.read_index(f"{path}.faiss")
        import json
        with open(f"{path}.meta", 'r', encoding='utf-8') as f:
            meta = json.load(f)
        self.texts = meta["texts"]
        self.intents = meta["intents"]


class SemanticCache:
    """
    语义缓存
    
    缓存查询向量及其结果，避免重复计算
    使用相似度阈值判断是否命中缓存
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.cache: Dict[str, Any] = {}  # text -> result
        self.vectors: List[np.ndarray] = []
        self.texts: List[str] = []
        self.results: List[Any] = []
        self.similarity_threshold = similarity_threshold
    
    def get(self, text: str, vector: np.ndarray) -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            text: 查询文本
            vector: 查询向量
            
        Returns:
            缓存结果或None
        """
        # 精确匹配
        if text in self.cache:
            return self.cache[text]
        
        # 语义相似匹配
        for cached_vec, cached_text, cached_result in zip(self.vectors, self.texts, self.results):
            similarity = np.dot(vector, cached_vec)
            if similarity >= self.similarity_threshold:
                return cached_result
        
        return None
    
    def put(self, text: str, vector: np.ndarray, result: Any) -> None:
        """添加缓存"""
        self.cache[text] = result
        self.vectors.append(vector)
        self.texts.append(text)
        self.results.append(result)
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.vectors.clear()
        self.texts.clear()
        self.results.clear()


class SemanticRetriever:
    """
    语义检索器（主类）
    
    整合Embedding模型、向量索引和语义缓存
    提供统一的语义检索接口
    
    使用示例:
        retriever = SemanticRetriever(
            embedding_model=MockEmbeddingModel(),
            vector_index=SimpleVectorIndex()
        )
        
        # 构建索引
        examples = {
            "code": ["帮我写代码", "实现一个函数"],
            "search": ["搜索资料", "查找文档"]
        }
        retriever.build_index(examples)
        
        # 检索
        result = retriever.search("帮我编写程序")
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_index: Optional[VectorIndex] = None,
        cache_enabled: bool = True,
        similarity_threshold: float = 0.75
    ):
        self.embedding_model = embedding_model or MockEmbeddingModel()
        self.vector_index = vector_index or SimpleVectorIndex()
        self.cache = SemanticCache() if cache_enabled else None
        self.similarity_threshold = similarity_threshold
        self.intent_examples: Dict[str, List[str]] = {}
    
    def build_index(self, intent_examples: Dict[str, List[str]]) -> None:
        """
        构建意图向量索引
        
        Args:
            intent_examples: 意图示例字典 {intent: [example1, example2, ...]}
        """
        self.intent_examples = intent_examples
        
        all_texts = []
        all_intents = []
        
        for intent, examples in intent_examples.items():
            all_texts.extend(examples)
            all_intents.extend([intent] * len(examples))
        
        if not all_texts:
            return
        
        # 编码所有示例
        vectors = self.embedding_model.embed(all_texts)
        
        # 添加到索引
        self.vector_index.add(vectors, all_texts, all_intents)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> Optional[Dict]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值（覆盖默认值）
            
        Returns:
            检索结果或None
        """
        threshold = threshold or self.similarity_threshold
        
        # 编码查询
        query_vector = self.embedding_model.embed_query(query)
        
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(query, query_vector)
            if cached_result:
                return cached_result
        
        # 执行检索
        results = self.vector_index.search(query_vector, top_k)
        
        if not results:
            return None
        
        # 过滤并选择最佳结果
        best = None
        for result in results:
            if result.similarity >= threshold:
                best = result
                break
        
        if best is None:
            best = results[0]  # 返回最相似的结果，即使低于阈值
        
        output = {
            "intent": best.intent,
            "confidence": min(best.similarity, 1.0),
            "matched_text": best.text,
            "similarity": best.similarity,
            "strategy": "semantic",
            "alternatives": [
                {"intent": r.intent, "similarity": r.similarity}
                for r in results[1:3]  # 返回2个备选
            ]
        }
        
        # 更新缓存
        if self.cache:
            self.cache.put(query, query_vector, output)
        
        return output
    
    async def asearch(self, query: str, top_k: int = 5) -> Optional[Dict]:
        """异步语义检索"""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self.search, query, top_k
        )
    
    def add_intent_examples(self, intent: str, examples: List[str]) -> None:
        """动态添加意图示例"""
        vectors = self.embedding_model.embed(examples)
        intents = [intent] * len(examples)
        self.vector_index.add(vectors, examples, intents)
        
        if intent not in self.intent_examples:
            self.intent_examples[intent] = []
        self.intent_examples[intent].extend(examples)
    
    def save(self, path: str) -> None:
        """保存索引"""
        self.vector_index.save(path)
    
    def load(self, path: str) -> None:
        """加载索引"""
        self.vector_index.load(path)


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    
    # 创建语义检索器
    retriever = SemanticRetriever()
    
    # 准备意图示例
    intent_examples = {
        "code_generation": [
            "帮我写一个Python函数",
            "实现一个排序算法",
            "编写代码实现功能",
            "写一个计算斐波那契数列的程序"
        ],
        "code_review": [
            "帮我review这段代码",
            "检查一下这个函数",
            "这段代码有什么问题",
            "优化一下这个实现"
        ],
        "search": [
            "搜索Python文档",
            "查找相关资料",
            "查询API用法",
            "搜索最佳实践"
        ],
        "question": [
            "什么是装饰器",
            "怎么实现单例模式",
            "为什么需要类型提示",
            "如何提高代码质量"
        ]
    }
    
    # 构建索引
    retriever.build_index(intent_examples)
    
    # 测试检索
    test_queries = [
        "帮我写个Python程序",
        "检查一下这段代码",
        "搜索一下文档",
        "什么是元类"
    ]
    
    for query in test_queries:
        result = retriever.search(query)
        if result:
            print(f"'{query}' -> {result['intent']} (置信度: {result['confidence']:.2f})")
        else:
            print(f"'{query}' -> 未匹配")


if __name__ == "__main__":
    example_usage()
