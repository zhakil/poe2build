"""
相似性搜索引擎 - 基于FAISS的构筑相似性搜索

提供高效的构筑相似性搜索功能，支持多维度过滤和排序。
集成向量化和索引系统，提供完整的RAG检索功能。
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

from .models import PoE2BuildData, BuildGoal, DataQuality
from .vectorizer import PoE2BuildVectorizer
from .index_builder import PoE2BuildIndexBuilder

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """搜索配置"""
    max_results: int = 20                    # 最大返回结果数
    min_similarity: float = 0.3              # 最小相似度阈值
    similarity_weight: float = 0.6           # 相似度权重
    popularity_weight: float = 0.2           # 流行度权重
    quality_weight: float = 0.2              # 数据质量权重
    
    # 过滤配置
    filter_by_class: bool = True             # 是否按职业过滤
    filter_by_budget: bool = True            # 是否按预算过滤
    filter_by_goal: bool = True              # 是否按目标过滤
    min_data_quality: DataQuality = DataQuality.MEDIUM  # 最小数据质量
    
    # 搜索行为
    enable_boost: bool = True                # 是否启用相关性提升
    diversify_results: bool = True           # 是否多样化结果
    max_similar_builds: int = 3              # 每个相似构筑类型最多返回数量

@dataclass
class SearchResult:
    """搜索结果"""
    build_hash: str                         # 构筑哈希
    similarity_score: float                 # 相似度分数
    final_score: float                      # 最终综合分数
    metadata: Dict[str, Any]               # 构筑元数据
    distance: float = 0.0                  # 向量距离
    rank: int = 0                          # 排名
    
    # 匹配信息
    matched_features: List[str] = None     # 匹配的特征
    boost_reasons: List[str] = None        # 提升原因
    filter_status: str = "passed"          # 过滤状态

@dataclass
class SearchQuery:
    """搜索查询"""
    query_text: str = ""                   # 查询文本
    character_class: Optional[str] = None   # 职业过滤
    ascendancy: Optional[str] = None       # 升华过滤
    main_skill: Optional[str] = None       # 主技能过滤
    build_goal: Optional[BuildGoal] = None # 构筑目标过滤
    budget_range: Tuple[float, float] = (0, float('inf'))  # 预算范围
    level_range: Tuple[int, int] = (1, 100)               # 等级范围
    min_dps: float = 0.0                   # 最小DPS
    tags: List[str] = None                 # 标签过滤
    exclude_hashes: Set[str] = None        # 排除的构筑哈希

class PoE2SimilarityEngine:
    """PoE2构筑相似性搜索引擎
    
    提供基于向量相似性的智能构筑推荐，支持多维度过滤和排序。
    """
    
    def __init__(self, config: Optional[SearchConfig] = None):
        """初始化相似性搜索引擎
        
        Args:
            config: 搜索配置，如果为None则使用默认配置
        """
        self.config = config or SearchConfig()
        self.vectorizer = None
        self.index_builder = None
        self._ready = False
        
        # 缓存
        self._query_cache = {}
        self._feature_cache = {}
        
    def setup(self, vectorizer: PoE2BuildVectorizer, 
             index_builder: PoE2BuildIndexBuilder):
        """设置依赖组件
        
        Args:
            vectorizer: 向量化引擎
            index_builder: 索引构建器
        """
        self.vectorizer = vectorizer
        self.index_builder = index_builder
        
        # 验证组件状态
        if not self.index_builder.index:
            raise ValueError("索引构建器未初始化索引")
        
        self._ready = True
        logger.info("相似性搜索引擎已就绪")
    
    def search_similar_builds(self, query: Union[str, SearchQuery, PoE2BuildData], 
                            config: Optional[SearchConfig] = None) -> List[SearchResult]:
        """搜索相似构筑
        
        Args:
            query: 查询输入 - 可以是文本、查询对象或构筑数据
            config: 搜索配置覆盖
            
        Returns:
            搜索结果列表，按相关性排序
        """
        if not self._ready:
            raise RuntimeError("搜索引擎未就绪，请先调用setup()方法")
        
        # 使用提供的配置或默认配置
        search_config = config or self.config
        
        # 标准化查询输入
        if isinstance(query, str):
            search_query = SearchQuery(query_text=query)
            query_vector = self.vectorizer.vectorize_text(query)
        elif isinstance(query, SearchQuery):
            search_query = query
            if query.query_text:
                query_vector = self.vectorizer.vectorize_text(query.query_text)
            else:
                # 从查询参数构建文本
                query_text = self._build_query_text(query)
                query_vector = self.vectorizer.vectorize_text(query_text)
        elif isinstance(query, PoE2BuildData):
            search_query = self._build_query_from_build(query)
            query_vector = self.vectorizer.vectorize_build(query)
        else:
            raise ValueError(f"不支持的查询类型: {type(query)}")
        
        logger.info(f"开始搜索相似构筑: {search_query}")
        
        # 1. 向量相似性搜索
        vector_results = self._vector_search(query_vector, search_config)
        
        # 2. 应用过滤器
        filtered_results = self._apply_filters(vector_results, search_query, search_config)
        
        # 3. 计算综合分数
        scored_results = self._calculate_scores(filtered_results, search_query, search_config)
        
        # 4. 应用相关性提升
        if search_config.enable_boost:
            boosted_results = self._apply_boosts(scored_results, search_query, search_config)
        else:
            boosted_results = scored_results
        
        # 5. 结果多样化
        if search_config.diversify_results:
            diversified_results = self._diversify_results(boosted_results, search_config)
        else:
            diversified_results = boosted_results
        
        # 6. 最终排序和截断
        final_results = sorted(diversified_results, key=lambda x: x.final_score, reverse=True)
        final_results = final_results[:search_config.max_results]
        
        # 设置排名
        for i, result in enumerate(final_results):
            result.rank = i + 1
        
        logger.info(f"搜索完成，返回 {len(final_results)} 个结果")
        return final_results
    
    def _vector_search(self, query_vector: np.ndarray, 
                      config: SearchConfig) -> List[Tuple[int, float]]:
        """执行向量相似性搜索
        
        Args:
            query_vector: 查询向量
            config: 搜索配置
            
        Returns:
            (索引位置, 相似度分数) 列表
        """
        # 确保查询向量格式正确
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # 标准化查询向量 (如果使用余弦相似度)
        if self.index_builder.config.similarity_metric == "cosine":
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
        
        # FAISS搜索
        k = min(config.max_results * 3, self.index_builder.index.ntotal)  # 搜索更多候选
        
        if self.index_builder.config.similarity_metric == "cosine":
            # 使用内积搜索 (已标准化向量)
            scores, indices = self.index_builder.index.search(query_vector, k)
            # 转换内积为余弦相似度 (已标准化，所以内积=余弦)
            similarities = scores[0]
        else:
            # L2距离搜索
            distances, indices = self.index_builder.index.search(query_vector, k)
            # 转换L2距离为相似度分数
            similarities = 1.0 / (1.0 + distances[0])
        
        # 过滤无效结果
        valid_results = []
        for idx, sim in zip(indices[0], similarities):
            if idx != -1 and sim >= config.min_similarity:  # FAISS用-1表示无效结果
                valid_results.append((int(idx), float(sim)))
        
        return valid_results
    
    def _apply_filters(self, vector_results: List[Tuple[int, float]], 
                      query: SearchQuery, config: SearchConfig) -> List[SearchResult]:
        """应用查询过滤器
        
        Args:
            vector_results: 向量搜索结果
            query: 搜索查询
            config: 搜索配置
            
        Returns:
            过滤后的搜索结果
        """
        filtered_results = []
        
        for idx, similarity in vector_results:
            # 获取元数据
            metadata = self.index_builder.build_metadata.get(idx, {})
            if not metadata:
                continue
            
            # 创建结果对象
            result = SearchResult(
                build_hash=metadata.get('build_hash', ''),
                similarity_score=similarity,
                final_score=similarity,  # 临时设置，后面会重新计算
                metadata=metadata,
                matched_features=[],
                boost_reasons=[]
            )
            
            # 应用过滤器
            filter_reasons = []
            
            # 职业过滤
            if (config.filter_by_class and query.character_class and 
                metadata.get('character_class', '').lower() != query.character_class.lower()):
                filter_reasons.append("职业不匹配")
            
            # 升华过滤
            if (query.ascendancy and 
                metadata.get('ascendancy', '').lower() != query.ascendancy.lower()):
                filter_reasons.append("升华不匹配")
            
            # 技能过滤
            if (query.main_skill and 
                metadata.get('main_skill', '').lower() != query.main_skill.lower()):
                filter_reasons.append("主技能不匹配")
            
            # 目标过滤
            if (config.filter_by_goal and query.build_goal and 
                metadata.get('build_goal', '') != query.build_goal.value):
                filter_reasons.append("构筑目标不匹配")
            
            # 预算过滤
            if config.filter_by_budget:
                build_cost = metadata.get('total_cost', 0)
                if not (query.budget_range[0] <= build_cost <= query.budget_range[1]):
                    filter_reasons.append("预算超出范围")
            
            # 等级过滤
            build_level = metadata.get('level', 1)
            if not (query.level_range[0] <= build_level <= query.level_range[1]):
                filter_reasons.append("等级超出范围")
            
            # 数据质量过滤
            build_quality = DataQuality(metadata.get('data_quality', DataQuality.MEDIUM.value))
            quality_order = {
                DataQuality.INVALID: 0, DataQuality.LOW: 1, 
                DataQuality.MEDIUM: 2, DataQuality.HIGH: 3
            }
            if quality_order[build_quality] < quality_order[config.min_data_quality]:
                filter_reasons.append("数据质量不足")
            
            # 排除特定构筑
            if query.exclude_hashes and result.build_hash in query.exclude_hashes:
                filter_reasons.append("已排除的构筑")
            
            # 设置过滤状态
            if filter_reasons:
                result.filter_status = f"filtered: {', '.join(filter_reasons)}"
                continue  # 跳过被过滤的结果
            else:
                result.filter_status = "passed"
                filtered_results.append(result)
        
        logger.info(f"过滤后保留 {len(filtered_results)} 个结果")
        return filtered_results
    
    def _calculate_scores(self, results: List[SearchResult], 
                         query: SearchQuery, config: SearchConfig) -> List[SearchResult]:
        """计算综合分数
        
        Args:
            results: 搜索结果列表
            query: 搜索查询
            config: 搜索配置
            
        Returns:
            更新分数的搜索结果
        """
        for result in results:
            metadata = result.metadata
            
            # 基础相似度分数
            similarity_score = result.similarity_score
            
            # 流行度分数 (基于排名，归一化到0-1)
            popularity_rank = metadata.get('popularity_rank', 0)
            if popularity_rank > 0:
                # 排名越低（数值越小），分数越高
                popularity_score = max(0, 1.0 - (popularity_rank - 1) / 10000)
            else:
                popularity_score = 0.5  # 默认中等流行度
            
            # 数据质量分数
            quality_value = metadata.get('data_quality', DataQuality.MEDIUM.value)
            quality_scores = {
                DataQuality.HIGH.value: 1.0,
                DataQuality.MEDIUM.value: 0.7,
                DataQuality.LOW.value: 0.4,
                DataQuality.INVALID.value: 0.1
            }
            quality_score = quality_scores.get(quality_value, 0.5)
            
            # 计算加权综合分数
            final_score = (
                similarity_score * config.similarity_weight +
                popularity_score * config.popularity_weight +
                quality_score * config.quality_weight
            )
            
            result.final_score = final_score
        
        return results
    
    def _apply_boosts(self, results: List[SearchResult], 
                     query: SearchQuery, config: SearchConfig) -> List[SearchResult]:
        """应用相关性提升
        
        Args:
            results: 搜索结果列表
            query: 搜索查询
            config: 搜索配置
            
        Returns:
            应用提升后的搜索结果
        """
        for result in results:
            metadata = result.metadata
            boost_factor = 1.0
            boost_reasons = []
            
            # 完全匹配职业+升华
            if (query.character_class and 
                metadata.get('character_class', '').lower() == query.character_class.lower()):
                if (query.ascendancy and 
                    metadata.get('ascendancy', '').lower() == query.ascendancy.lower()):
                    boost_factor *= 1.3
                    boost_reasons.append("完全匹配职业+升华")
                else:
                    boost_factor *= 1.15
                    boost_reasons.append("匹配职业")
            
            # 完全匹配主技能
            if (query.main_skill and 
                metadata.get('main_skill', '').lower() == query.main_skill.lower()):
                boost_factor *= 1.2
                boost_reasons.append("匹配主技能")
            
            # 匹配构筑目标
            if (query.build_goal and 
                metadata.get('build_goal', '') == query.build_goal.value):
                boost_factor *= 1.1
                boost_reasons.append("匹配构筑目标")
            
            # 高质量数据提升
            if metadata.get('data_quality', '') == DataQuality.HIGH.value:
                boost_factor *= 1.05
                boost_reasons.append("高质量数据")
            
            # 流行构筑提升
            popularity_rank = metadata.get('popularity_rank', 0)
            if 0 < popularity_rank <= 100:
                boost_factor *= 1.1
                boost_reasons.append("热门构筑")
            
            # 应用提升
            result.final_score *= boost_factor
            result.boost_reasons = boost_reasons
        
        return results
    
    def _diversify_results(self, results: List[SearchResult], 
                          config: SearchConfig) -> List[SearchResult]:
        """结果多样化处理
        
        Args:
            results: 搜索结果列表
            config: 搜索配置
            
        Returns:
            多样化后的搜索结果
        """
        if not config.diversify_results:
            return results
        
        # 按构筑类型分组 (职业+升华+主技能)
        groups = {}
        for result in results:
            metadata = result.metadata
            group_key = (
                metadata.get('character_class', ''),
                metadata.get('ascendancy', ''),
                metadata.get('main_skill', '')
            )
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(result)
        
        # 从每个组中选择最好的几个结果
        diversified = []
        for group_results in groups.values():
            # 按分数排序
            group_results.sort(key=lambda x: x.final_score, reverse=True)
            # 取前N个
            diversified.extend(group_results[:config.max_similar_builds])
        
        return diversified
    
    def _build_query_text(self, query: SearchQuery) -> str:
        """从查询对象构建查询文本"""
        parts = []
        
        if query.character_class:
            parts.append(query.character_class)
        if query.ascendancy:
            parts.append(query.ascendancy)
        if query.main_skill:
            parts.append(query.main_skill)
        if query.build_goal:
            parts.append(query.build_goal.value)
        
        # 预算描述
        budget_min, budget_max = query.budget_range
        if budget_max != float('inf'):
            if budget_min > 0:
                parts.append(f"budget {budget_min}-{budget_max} divine")
            else:
                parts.append(f"budget under {budget_max} divine")
        elif budget_min > 0:
            parts.append(f"budget over {budget_min} divine")
        
        return " ".join(parts) if parts else "general build"
    
    def _build_query_from_build(self, build: PoE2BuildData) -> SearchQuery:
        """从构筑数据创建查询对象"""
        return SearchQuery(
            character_class=build.character_class,
            ascendancy=build.ascendancy,
            main_skill=build.main_skill_setup.main_skill,
            build_goal=build.build_goal,
            budget_range=(0, build.total_cost * 2) if build.total_cost > 0 else (0, float('inf')),
            level_range=(max(1, build.level - 10), min(100, build.level + 10)),
            exclude_hashes={build.similarity_hash}  # 排除自己
        )
    
    def find_build_variants(self, base_build: PoE2BuildData, 
                           max_variants: int = 5) -> List[SearchResult]:
        """寻找构筑变种
        
        Args:
            base_build: 基础构筑
            max_variants: 最大变种数量
            
        Returns:
            构筑变种列表
        """
        # 创建宽松的搜索配置
        variant_config = SearchConfig(
            max_results=max_variants,
            min_similarity=0.6,
            filter_by_class=True,      # 保持同职业
            filter_by_budget=False,    # 允许不同预算
            filter_by_goal=False,      # 允许不同目标
            diversify_results=True,
            max_similar_builds=2       # 每种变种最多2个
        )
        
        # 创建变种查询
        query = SearchQuery(
            character_class=base_build.character_class,
            ascendancy=base_build.ascendancy,  # 可选择性保持升华
            budget_range=(0, float('inf')),
            exclude_hashes={base_build.similarity_hash}
        )
        
        variants = self.search_similar_builds(query, variant_config)
        logger.info(f"找到 {len(variants)} 个构筑变种")
        
        return variants
    
    def get_build_recommendations(self, user_preferences: Dict[str, Any], 
                                 max_recommendations: int = 10) -> List[SearchResult]:
        """获取构筑推荐
        
        Args:
            user_preferences: 用户偏好设置
            max_recommendations: 最大推荐数量
            
        Returns:
            推荐构筑列表
        """
        # 构建查询
        query = SearchQuery()
        
        if 'character_class' in user_preferences:
            query.character_class = user_preferences['character_class']
        if 'ascendancy' in user_preferences:
            query.ascendancy = user_preferences['ascendancy']
        if 'main_skill' in user_preferences:
            query.main_skill = user_preferences['main_skill']
        if 'build_goal' in user_preferences:
            query.build_goal = BuildGoal(user_preferences['build_goal'])
        if 'budget' in user_preferences:
            budget = user_preferences['budget']
            query.budget_range = (0, budget * 1.5)  # 允许稍微超预算
        
        # 构建查询文本
        query_parts = []
        if query.character_class:
            query_parts.append(query.character_class)
        if query.main_skill:
            query_parts.append(query.main_skill)
        if query.build_goal:
            query_parts.append(query.build_goal.value)
        
        query.query_text = " ".join(query_parts) if query_parts else "popular build"
        
        # 搜索配置
        recommend_config = SearchConfig(
            max_results=max_recommendations,
            min_similarity=0.2,  # 较宽松的相似度要求
            enable_boost=True,
            diversify_results=True,
            max_similar_builds=3
        )
        
        recommendations = self.search_similar_builds(query, recommend_config)
        logger.info(f"生成 {len(recommendations)} 个推荐构筑")
        
        return recommendations
    
    def clear_cache(self):
        """清理缓存"""
        self._query_cache.clear()
        self._feature_cache.clear()
        logger.info("相似性搜索缓存已清理")

# 工厂函数
def create_similarity_engine(max_results: int = 20, 
                            min_similarity: float = 0.3) -> PoE2SimilarityEngine:
    """创建相似性搜索引擎的工厂函数
    
    Args:
        max_results: 最大返回结果数
        min_similarity: 最小相似度阈值
        
    Returns:
        配置好的相似性搜索引擎实例
    """
    config = SearchConfig(
        max_results=max_results,
        min_similarity=min_similarity
    )
    return PoE2SimilarityEngine(config)

# 测试函数
def test_similarity_search():
    """测试相似性搜索功能"""
    from .models import PoE2BuildData, SkillGemSetup, BuildGoal
    from .vectorizer import create_vectorizer
    from .index_builder import create_index_builder
    
    # 创建测试数据
    test_builds = []
    skills = ["Lightning Arrow", "Fireball", "Cyclone", "Ice Nova", "Earthquake"]
    classes = ["Ranger", "Witch", "Marauder", "Templar", "Duelist"]
    
    for i in range(50):
        build = PoE2BuildData(
            character_class=classes[i % len(classes)],
            level=80 + i % 20,
            main_skill_setup=SkillGemSetup(
                main_skill=skills[i % len(skills)],
                support_gems=["Added Lightning", "Elemental Damage"][:i % 3]
            ),
            build_goal=BuildGoal.CLEAR_SPEED,
            total_cost=float(i % 30)
        )
        test_builds.append(build)
    
    # 设置系统
    vectorizer = create_vectorizer()
    index_builder = create_index_builder()
    index_builder.set_vectorizer(vectorizer)
    index_builder.build_index(test_builds)
    
    similarity_engine = create_similarity_engine()
    similarity_engine.setup(vectorizer, index_builder)
    
    # 测试搜索
    print("测试文本搜索...")
    text_results = similarity_engine.search_similar_builds("Ranger Lightning Arrow clear speed")
    for result in text_results[:3]:
        print(f"  {result.rank}. {result.metadata.get('character_class')} - {result.metadata.get('main_skill')} (分数: {result.final_score:.3f})")
    
    print("\n测试构筑相似搜索...")
    target_build = test_builds[0]
    build_results = similarity_engine.search_similar_builds(target_build)
    for result in build_results[:3]:
        print(f"  {result.rank}. {result.metadata.get('character_class')} - {result.metadata.get('main_skill')} (相似度: {result.similarity_score:.3f})")
    
    print("\n测试构筑推荐...")
    preferences = {
        'character_class': 'Witch',
        'build_goal': 'clear_speed',
        'budget': 10.0
    }
    recommendations = similarity_engine.get_build_recommendations(preferences, max_recommendations=5)
    for rec in recommendations:
        print(f"  推荐: {rec.metadata.get('character_class')} - {rec.metadata.get('main_skill')} (综合分数: {rec.final_score:.3f})")
    
    return similarity_engine, test_builds

if __name__ == "__main__":
    # 运行测试
    engine, builds = test_similarity_search()
    print("相似性搜索引擎测试完成!")