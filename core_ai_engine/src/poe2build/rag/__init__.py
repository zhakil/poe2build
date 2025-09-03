"""
RAG智能推荐系统 - 基于PoE2构筑数据的RAG增强AI推荐

集成真实数据源如poe.ninja/poe2、poe2scout.com等构筑数据，
使用RAG技术实现智能构筑推荐和相似性搜索。

核心组件:
- PoE2BuildData: 构筑数据模型
- PoE2RAGDataCollector: 数据收集器
- PoE2BuildScraper: 构筑爬虫
- PoE2DataPreprocessor: 数据预处理器
- PoE2BuildVectorizer: 向量化引擎 (NEW)
- PoE2BuildIndexBuilder: 索引构建器 (NEW)  
- PoE2SimilarityEngine: 相似性搜索引擎 (NEW)

特性:
- 智能构筑相似性搜索
- 弹性架构(circuit breaker, retry, rate limiting)
- 向量化存储与检索
- 尊重API使用规范
- 缓存和性能优化
"""

from .models import (
    PoE2BuildData, 
    RAGDataModel, 
    SuccessMetrics,
    SkillGemSetup,
    ItemInfo,
    OffensiveStats,
    DefensiveStats,
    BuildGoal,
    DataQuality
)
from .data_collector import PoE2RAGDataCollector, PoE2NinjaRAGCollector
from .build_scraper import PoE2BuildScraper
from .data_preprocessor import PoE2DataPreprocessor

# RAG向量化组件
from .vectorizer import PoE2BuildVectorizer, VectorConfig, create_vectorizer
from .index_builder import PoE2BuildIndexBuilder, IndexConfig, create_index_builder
from .similarity_engine import (
    PoE2SimilarityEngine, 
    SearchConfig, 
    SearchQuery, 
    SearchResult,
    create_similarity_engine
)

# RAG AI引擎组件 (阶段9新增)
from .ai_engine import (
    PoE2AIEngine,
    RecommendationStrategy,
    RecommendationContext, 
    AIRecommendation,
    BuildInsight,
    ConfidenceLevel,
    create_ai_engine
)
from .knowledge_base import (
    PoE2KnowledgeBase,
    BuildPattern,
    MetaInsight,
    KnowledgeEntry,
    MetaTrend,
    KnowledgeType,
    create_knowledge_base
)
from .recommendation import (
    PoE2RecommendationEngine,
    AlgorithmType,
    RecommendationScore,
    UserProfile,
    OptimizationGoal,
    create_recommendation_engine
)

__version__ = "2.0.0"

__all__ = [
    # 数据模型
    "PoE2BuildData",
    "RAGDataModel",
    "SuccessMetrics",
    "SkillGemSetup", 
    "ItemInfo",
    "OffensiveStats",
    "DefensiveStats",
    "BuildGoal",
    "DataQuality",
    
    # 数据收集与预处理
    "PoE2RAGDataCollector",
    "PoE2NinjaRAGCollector",
    "PoE2BuildScraper",
    "PoE2DataPreprocessor",
    
    # RAG向量化系统 (阶段8)
    "PoE2BuildVectorizer",
    "VectorConfig", 
    "create_vectorizer",
    "PoE2BuildIndexBuilder",
    "IndexConfig",
    "create_index_builder",
    "PoE2SimilarityEngine",
    "SearchConfig",
    "SearchQuery", 
    "SearchResult",
    "create_similarity_engine",
    
    # RAG AI引擎系统 (阶段9)
    "PoE2AIEngine",
    "RecommendationStrategy",
    "RecommendationContext",
    "AIRecommendation",
    "BuildInsight",
    "ConfidenceLevel",
    "create_ai_engine",
    "PoE2KnowledgeBase",
    "BuildPattern",
    "MetaInsight",
    "KnowledgeEntry",
    "MetaTrend",
    "KnowledgeType", 
    "create_knowledge_base",
    "PoE2RecommendationEngine",
    "AlgorithmType",
    "RecommendationScore",
    "UserProfile",
    "OptimizationGoal",
    "create_recommendation_engine",
]