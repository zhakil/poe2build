"""RAG相似度检索引擎

实现基于FAISS的高性能向量相似度搜索，支持语义搜索、智能过滤和个性化推荐。
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import json

from ..models.characters import PoE2CharacterClass
from ..models.build import PoE2Build


class RetrievalMode(Enum):
    """检索模式枚举"""
    SEMANTIC = "semantic"  # 语义相似搜索
    HYBRID = "hybrid"  # 混合搜索（语义+关键词）
    FILTERED = "filtered"  # 过滤搜索
    PERSONALIZED = "personalized"  # 个性化推荐


@dataclass
class SearchQuery:
    """搜索查询配置"""
    text: str  # 查询文本
    character_class: Optional[PoE2CharacterClass] = None
    ascendancy: Optional[str] = None
    main_skill: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    playstyle_tags: Optional[List[str]] = None
    exclude_tags: Optional[List[str]] = None
    mode: RetrievalMode = RetrievalMode.SEMANTIC
    top_k: int = 10
    min_similarity: float = 0.6
    boost_popular: bool = True
    boost_recent: bool = True


@dataclass
class SearchResult:
    """搜索结果"""
    build_id: str
    build_data: Dict[str, Any]
    similarity_score: float
    popularity_score: float
    final_score: float
    match_reasons: List[str]
    metadata: Dict[str, Any]


@dataclass
class RetrievalStats:
    """检索统计信息"""
    query_time_ms: float
    total_candidates: int
    filtered_candidates: int
    returned_results: int
    cache_hit: bool
    index_version: str


class MockRetrievalEngine:
    """Mock检索引擎，当依赖不可用时使用"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockRetrievalEngine")
        self.mock_builds = self._generate_mock_builds()
    
    def _generate_mock_builds(self) -> List[Dict[str, Any]]:
        """生成mock构筑数据"""
        return [
            {
                "build_id": "mock_witch_fire_1",
                "name": "Infernalist Fire Witch",
                "character_class": "Witch",
                "ascendancy": "Infernalist",
                "main_skill": "Fireball",
                "support_gems": ["Fire Penetration", "Elemental Focus"],
                "level": 85,
                "estimated_cost": 25.0,
                "description": "High damage fire-based witch build focusing on elemental damage",
                "tags": ["fire", "elemental", "ranged", "beginner-friendly"],
                "popularity": 0.85,
                "league": "Standard"
            },
            {
                "build_id": "mock_ranger_bow_1", 
                "name": "Deadeye Lightning Bow",
                "character_class": "Ranger",
                "ascendancy": "Deadeye",
                "main_skill": "Lightning Arrow",
                "support_gems": ["Chain", "Elemental Damage with Attacks"],
                "level": 90,
                "estimated_cost": 40.0,
                "description": "Fast clearing bow ranger with chain lightning attacks",
                "tags": ["lightning", "bow", "clear-speed", "projectile"],
                "popularity": 0.78,
                "league": "Standard"
            },
            {
                "build_id": "mock_monk_melee_1",
                "name": "Invoker Staff Monk",
                "character_class": "Monk",
                "ascendancy": "Invoker", 
                "main_skill": "Quarter Staff",
                "support_gems": ["Melee Physical Damage", "Multistrike"],
                "level": 87,
                "estimated_cost": 15.0,
                "description": "Balanced melee monk with staff combat and spirit skills",
                "tags": ["melee", "staff", "spirit", "balanced"],
                "popularity": 0.72,
                "league": "Standard"
            }
        ]
    
    async def search(self, query: SearchQuery) -> Tuple[List[SearchResult], RetrievalStats]:
        """执行mock搜索"""
        start_time = time.time()
        
        results = []
        for build in self.mock_builds:
            # 基础相似度计算（简单的关键词匹配）
            similarity = self._calculate_mock_similarity(query, build)
            
            if similarity < query.min_similarity:
                continue
            
            # 应用过滤器
            if not self._passes_filters(query, build):
                continue
            
            # 计算最终分数
            popularity_boost = 1.2 if query.boost_popular else 1.0
            final_score = similarity * popularity_boost * build["popularity"]
            
            results.append(SearchResult(
                build_id=build["build_id"],
                build_data=build,
                similarity_score=similarity,
                popularity_score=build["popularity"],
                final_score=final_score,
                match_reasons=self._get_match_reasons(query, build),
                metadata={"mock": True, "source": "generated"}
            ))
        
        # 排序和限制结果
        results.sort(key=lambda x: x.final_score, reverse=True)
        results = results[:query.top_k]
        
        query_time = (time.time() - start_time) * 1000
        
        stats = RetrievalStats(
            query_time_ms=query_time,
            total_candidates=len(self.mock_builds),
            filtered_candidates=len(results),
            returned_results=len(results),
            cache_hit=False,
            index_version="mock_v1.0"
        )
        
        return results, stats
    
    def _calculate_mock_similarity(self, query: SearchQuery, build: Dict[str, Any]) -> float:
        """计算mock相似度分数"""
        similarity = 0.5  # 基础分数
        
        # 职业匹配
        if query.character_class and build["character_class"] == query.character_class.value:
            similarity += 0.2
        
        # 技能匹配
        if query.main_skill and query.main_skill.lower() in build["main_skill"].lower():
            similarity += 0.2
        
        # 关键词匹配
        query_words = set(query.text.lower().split())
        build_words = set(build["description"].lower().split())
        if query_words & build_words:
            similarity += 0.1
        
        return min(similarity, 1.0)
    
    def _passes_filters(self, query: SearchQuery, build: Dict[str, Any]) -> bool:
        """检查是否通过过滤器"""
        # 预算过滤
        if query.budget_min and build["estimated_cost"] < query.budget_min:
            return False
        if query.budget_max and build["estimated_cost"] > query.budget_max:
            return False
        
        # 等级过滤
        if query.min_level and build["level"] < query.min_level:
            return False
        if query.max_level and build["level"] > query.max_level:
            return False
        
        # 标签过滤
        build_tags = set(build.get("tags", []))
        if query.playstyle_tags:
            required_tags = set(query.playstyle_tags)
            if not (required_tags & build_tags):
                return False
        
        if query.exclude_tags:
            excluded_tags = set(query.exclude_tags)
            if excluded_tags & build_tags:
                return False
        
        return True
    
    def _get_match_reasons(self, query: SearchQuery, build: Dict[str, Any]) -> List[str]:
        """获取匹配原因"""
        reasons = []
        
        if query.character_class and build["character_class"] == query.character_class.value:
            reasons.append("职业匹配")
        
        if query.main_skill and query.main_skill.lower() in build["main_skill"].lower():
            reasons.append("主技能匹配")
        
        if query.playstyle_tags:
            build_tags = set(build.get("tags", []))
            matching_tags = set(query.playstyle_tags) & build_tags
            if matching_tags:
                reasons.append(f"标签匹配: {', '.join(matching_tags)}")
        
        return reasons
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "engine_type": "mock",
            "total_builds": len(self.mock_builds),
            "index_version": "mock_v1.0",
            "last_updated": time.time()
        }


class RetrievalEngine:
    """RAG相似度检索引擎"""
    
    def __init__(self, index_path: Path, vectorizer=None):
        self.logger = logging.getLogger(f"{__name__}.RetrievalEngine")
        self.index_path = index_path
        self.vectorizer = vectorizer
        self.index = None
        self.build_metadata = {}
        self.query_cache = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必要依赖"""
        try:
            import faiss
            import numpy as np
            self.faiss = faiss
            self.np = np
            self.use_real_impl = True
        except ImportError:
            self.logger.warning("FAISS或NumPy不可用，使用Mock实现")
            self.use_real_impl = False
            self.mock_engine = MockRetrievalEngine()
    
    async def initialize(self) -> bool:
        """初始化检索引擎"""
        if not self.use_real_impl:
            return True
        
        try:
            # 加载向量索引
            await self._load_index()
            
            # 加载构筑元数据
            await self._load_metadata()
            
            self.logger.info("检索引擎初始化成功")
            return True
        
        except Exception as e:
            self.logger.error(f"检索引擎初始化失败: {e}")
            return False
    
    async def _load_index(self):
        """加载FAISS索引"""
        index_file = self.index_path / "build_vectors.index"
        
        if not index_file.exists():
            self.logger.warning("向量索引文件不存在，创建空索引")
            # 创建空的FAISS索引（假设384维向量）
            self.index = self.faiss.IndexFlatIP(384)
            return
        
        try:
            self.index = self.faiss.read_index(str(index_file))
            self.logger.info(f"加载向量索引: {self.index.ntotal} 个向量")
        except Exception as e:
            self.logger.error(f"加载向量索引失败: {e}")
            # 创建空索引作为fallback
            self.index = self.faiss.IndexFlatIP(384)
    
    async def _load_metadata(self):
        """加载构筑元数据"""
        metadata_file = self.index_path / "build_metadata.json"
        
        if not metadata_file.exists():
            self.logger.warning("构筑元数据文件不存在")
            self.build_metadata = {}
            return
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.build_metadata = json.load(f)
            self.logger.info(f"加载构筑元数据: {len(self.build_metadata)} 个构筑")
        except Exception as e:
            self.logger.error(f"加载构筑元数据失败: {e}")
            self.build_metadata = {}
    
    async def search(self, query: SearchQuery) -> Tuple[List[SearchResult], RetrievalStats]:
        """执行相似度搜索"""
        if not self.use_real_impl:
            return await self.mock_engine.search(query)
        
        start_time = time.time()
        
        # 检查缓存
        cache_key = self._generate_cache_key(query)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # 生成查询向量
            query_vector = await self._generate_query_vector(query)
            
            # 执行向量搜索
            candidate_results = await self._vector_search(query_vector, query)
            
            # 应用过滤器
            filtered_results = await self._apply_filters(candidate_results, query)
            
            # 重新排序和评分
            final_results = await self._rerank_results(filtered_results, query)
            
            # 构建结果
            search_results = await self._build_search_results(final_results, query)
            
            query_time = (time.time() - start_time) * 1000
            
            stats = RetrievalStats(
                query_time_ms=query_time,
                total_candidates=len(candidate_results),
                filtered_candidates=len(filtered_results),
                returned_results=len(search_results),
                cache_hit=False,
                index_version="v1.0"
            )
            
            # 缓存结果
            self._cache_result(cache_key, (search_results, stats))
            
            return search_results, stats
        
        except Exception as e:
            self.logger.error(f"搜索执行失败: {e}")
            # 返回空结果
            return [], RetrievalStats(
                query_time_ms=(time.time() - start_time) * 1000,
                total_candidates=0,
                filtered_candidates=0,
                returned_results=0,
                cache_hit=False,
                index_version="error"
            )
    
    async def _generate_query_vector(self, query: SearchQuery) -> 'np.ndarray':
        """生成查询向量"""
        if not self.vectorizer:
            # 生成随机向量作为fallback
            return self.np.random.rand(384).astype('float32')
        
        # 构建增强查询文本
        enhanced_query = query.text
        
        if query.character_class:
            enhanced_query += f" {query.character_class.value}"
        
        if query.ascendancy:
            enhanced_query += f" {query.ascendancy}"
        
        if query.main_skill:
            enhanced_query += f" {query.main_skill}"
        
        if query.playstyle_tags:
            enhanced_query += f" {' '.join(query.playstyle_tags)}"
        
        # 使用vectorizer生成向量
        try:
            if hasattr(self.vectorizer, 'encode_async'):
                vector = await self.vectorizer.encode_async([enhanced_query])
            else:
                vector = self.vectorizer.encode([enhanced_query])
            
            return vector[0].astype('float32')
        except Exception as e:
            self.logger.error(f"查询向量生成失败: {e}")
            return self.np.random.rand(384).astype('float32')
    
    async def _vector_search(self, query_vector: 'np.ndarray', query: SearchQuery) -> List[Tuple[int, float]]:
        """执行向量相似度搜索"""
        if self.index.ntotal == 0:
            return []
        
        # 搜索更多候选以便后续过滤
        k = min(query.top_k * 5, self.index.ntotal)
        
        # 执行搜索
        query_vector = query_vector.reshape(1, -1)
        scores, indices = self.index.search(query_vector, k)
        
        # 过滤低分结果
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx != -1 and score >= query.min_similarity:
                results.append((int(idx), float(score)))
        
        return results
    
    async def _apply_filters(self, candidates: List[Tuple[int, float]], query: SearchQuery) -> List[Tuple[int, float, Dict[str, Any]]]:
        """应用搜索过滤器"""
        filtered = []
        
        for idx, score in candidates:
            build_id = str(idx)
            build_data = self.build_metadata.get(build_id, {})
            
            if not build_data:
                continue
            
            # 应用各种过滤器
            if not self._passes_character_filter(build_data, query):
                continue
            
            if not self._passes_budget_filter(build_data, query):
                continue
            
            if not self._passes_level_filter(build_data, query):
                continue
            
            if not self._passes_tag_filter(build_data, query):
                continue
            
            filtered.append((idx, score, build_data))
        
        return filtered
    
    def _passes_character_filter(self, build_data: Dict[str, Any], query: SearchQuery) -> bool:
        """检查职业过滤器"""
        if not query.character_class:
            return True
        
        build_class = build_data.get('character_class', '')
        return build_class == query.character_class.value
    
    def _passes_budget_filter(self, build_data: Dict[str, Any], query: SearchQuery) -> bool:
        """检查预算过滤器"""
        build_cost = build_data.get('estimated_cost', 0)
        
        if query.budget_min and build_cost < query.budget_min:
            return False
        
        if query.budget_max and build_cost > query.budget_max:
            return False
        
        return True
    
    def _passes_level_filter(self, build_data: Dict[str, Any], query: SearchQuery) -> bool:
        """检查等级过滤器"""
        build_level = build_data.get('level', 1)
        
        if query.min_level and build_level < query.min_level:
            return False
        
        if query.max_level and build_level > query.max_level:
            return False
        
        return True
    
    def _passes_tag_filter(self, build_data: Dict[str, Any], query: SearchQuery) -> bool:
        """检查标签过滤器"""
        build_tags = set(build_data.get('tags', []))
        
        # 必须包含的标签
        if query.playstyle_tags:
            required_tags = set(query.playstyle_tags)
            if not (required_tags & build_tags):
                return False
        
        # 排除的标签
        if query.exclude_tags:
            excluded_tags = set(query.exclude_tags)
            if excluded_tags & build_tags:
                return False
        
        return True
    
    async def _rerank_results(self, filtered_results: List[Tuple[int, float, Dict[str, Any]]], query: SearchQuery) -> List[Tuple[int, float, Dict[str, Any]]]:
        """重新排序和评分结果"""
        reranked = []
        
        for idx, similarity_score, build_data in filtered_results:
            # 基础相似度分数
            final_score = similarity_score
            
            # 流行度加成
            if query.boost_popular:
                popularity = build_data.get('popularity', 0.5)
                final_score *= (1.0 + popularity * 0.3)
            
            # 最近更新加成
            if query.boost_recent:
                # 假设有updated_at字段
                days_old = build_data.get('days_old', 30)
                recency_boost = max(0.8, 1.0 - (days_old / 100))
                final_score *= recency_boost
            
            # 完全匹配加成
            exact_match_bonus = self._calculate_exact_match_bonus(build_data, query)
            final_score *= (1.0 + exact_match_bonus)
            
            reranked.append((idx, final_score, build_data))
        
        # 按最终分数排序
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:query.top_k]
    
    def _calculate_exact_match_bonus(self, build_data: Dict[str, Any], query: SearchQuery) -> float:
        """计算完全匹配加成"""
        bonus = 0.0
        
        # 职业完全匹配
        if query.character_class and build_data.get('character_class') == query.character_class.value:
            bonus += 0.1
        
        # 升华完全匹配
        if query.ascendancy and build_data.get('ascendancy') == query.ascendancy:
            bonus += 0.1
        
        # 主技能匹配
        if query.main_skill and query.main_skill in build_data.get('main_skill', ''):
            bonus += 0.15
        
        return bonus
    
    async def _build_search_results(self, final_results: List[Tuple[int, float, Dict[str, Any]]], query: SearchQuery) -> List[SearchResult]:
        """构建搜索结果"""
        search_results = []
        
        for idx, final_score, build_data in final_results:
            # 计算原始相似度分数（从最终分数中反推）
            similarity_score = min(final_score * 0.7, 1.0)  # 简化计算
            popularity_score = build_data.get('popularity', 0.5)
            
            # 生成匹配原因
            match_reasons = self._generate_match_reasons(build_data, query)
            
            search_results.append(SearchResult(
                build_id=build_data.get('build_id', str(idx)),
                build_data=build_data,
                similarity_score=similarity_score,
                popularity_score=popularity_score,
                final_score=final_score,
                match_reasons=match_reasons,
                metadata={
                    "index_position": idx,
                    "query_mode": query.mode.value,
                    "filters_applied": self._get_applied_filters(query)
                }
            ))
        
        return search_results
    
    def _generate_match_reasons(self, build_data: Dict[str, Any], query: SearchQuery) -> List[str]:
        """生成匹配原因说明"""
        reasons = []
        
        if query.character_class and build_data.get('character_class') == query.character_class.value:
            reasons.append("职业匹配")
        
        if query.ascendancy and build_data.get('ascendancy') == query.ascendancy:
            reasons.append("升华匹配")
        
        if query.main_skill and query.main_skill in build_data.get('main_skill', ''):
            reasons.append("主技能匹配")
        
        # 标签匹配
        if query.playstyle_tags:
            build_tags = set(build_data.get('tags', []))
            matching_tags = set(query.playstyle_tags) & build_tags
            if matching_tags:
                reasons.append(f"风格匹配: {', '.join(matching_tags)}")
        
        # 预算合适
        build_cost = build_data.get('estimated_cost', 0)
        if query.budget_min and query.budget_max:
            if query.budget_min <= build_cost <= query.budget_max:
                reasons.append("预算适合")
        
        return reasons
    
    def _get_applied_filters(self, query: SearchQuery) -> List[str]:
        """获取应用的过滤器列表"""
        filters = []
        
        if query.character_class:
            filters.append("character_class")
        if query.budget_min or query.budget_max:
            filters.append("budget")
        if query.min_level or query.max_level:
            filters.append("level")
        if query.playstyle_tags:
            filters.append("playstyle_tags")
        if query.exclude_tags:
            filters.append("exclude_tags")
        
        return filters
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """生成缓存键"""
        key_data = {
            'text': query.text,
            'character_class': query.character_class.value if query.character_class else None,
            'ascendancy': query.ascendancy,
            'main_skill': query.main_skill,
            'budget_min': query.budget_min,
            'budget_max': query.budget_max,
            'min_level': query.min_level,
            'max_level': query.max_level,
            'playstyle_tags': sorted(query.playstyle_tags) if query.playstyle_tags else None,
            'exclude_tags': sorted(query.exclude_tags) if query.exclude_tags else None,
            'mode': query.mode.value,
            'top_k': query.top_k,
            'min_similarity': query.min_similarity,
            'boost_popular': query.boost_popular,
            'boost_recent': query.boost_recent
        }
        
        return f"search_{hash(str(sorted(key_data.items())))}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Tuple[List[SearchResult], RetrievalStats]]:
        """从缓存获取结果"""
        if cache_key not in self.query_cache:
            return None
        
        cached_data, timestamp = self.query_cache[cache_key]
        
        # 检查是否过期
        if time.time() - timestamp > self.cache_ttl:
            del self.query_cache[cache_key]
            return None
        
        # 更新统计信息显示缓存命中
        results, stats = cached_data
        stats.cache_hit = True
        
        return results, stats
    
    def _cache_result(self, cache_key: str, result: Tuple[List[SearchResult], RetrievalStats]):
        """缓存搜索结果"""
        self.query_cache[cache_key] = (result, time.time())
        
        # 清理过期缓存
        current_time = time.time()
        expired_keys = [k for k, (_, timestamp) in self.query_cache.items() 
                       if current_time - timestamp > self.cache_ttl]
        
        for key in expired_keys:
            del self.query_cache[key]
    
    async def get_similar_builds(self, build_id: str, top_k: int = 5) -> List[SearchResult]:
        """获取相似构筑"""
        if not self.use_real_impl:
            # Mock实现
            mock_results, _ = await self.mock_engine.search(SearchQuery(
                text=f"similar to {build_id}",
                top_k=top_k
            ))
            return mock_results
        
        # 实际实现
        build_data = self.build_metadata.get(build_id, {})
        if not build_data:
            return []
        
        # 构建查询
        query_text = f"{build_data.get('name', '')} {build_data.get('description', '')}"
        
        query = SearchQuery(
            text=query_text,
            character_class=PoE2CharacterClass(build_data.get('character_class', 'Witch')),
            main_skill=build_data.get('main_skill'),
            playstyle_tags=build_data.get('tags', []),
            top_k=top_k + 1,  # +1因为会包含自己
            min_similarity=0.3
        )
        
        results, _ = await self.search(query)
        
        # 移除自己
        filtered_results = [r for r in results if r.build_id != build_id]
        return filtered_results[:top_k]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取检索引擎统计信息"""
        if not self.use_real_impl:
            return await self.mock_engine.get_stats()
        
        return {
            "engine_type": "faiss",
            "index_size": self.index.ntotal if self.index else 0,
            "metadata_count": len(self.build_metadata),
            "cache_size": len(self.query_cache),
            "index_dimension": self.index.d if self.index else 0,
            "last_updated": time.time()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "status": "healthy",
            "dependencies_available": self.use_real_impl,
            "index_loaded": self.index is not None,
            "metadata_loaded": len(self.build_metadata) > 0,
            "timestamp": time.time()
        }
        
        if not self.use_real_impl:
            status["status"] = "degraded"
            status["warning"] = "使用Mock实现，缺少FAISS依赖"
        
        return status
    
    async def cleanup(self):
        """清理资源"""
        self.query_cache.clear()
        self.logger.info("检索引擎资源已清理")


# 便捷函数
async def create_retrieval_engine(index_path: Path, vectorizer=None) -> RetrievalEngine:
    """创建检索引擎实例"""
    engine = RetrievalEngine(index_path, vectorizer)
    await engine.initialize()
    return engine


async def search_builds(query: SearchQuery, engine: RetrievalEngine) -> Tuple[List[SearchResult], RetrievalStats]:
    """便捷搜索函数"""
    return await engine.search(query)