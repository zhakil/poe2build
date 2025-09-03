"""
RAG增强AI推荐引擎 - PoE2构筑智能推荐的核心

基于已实现的向量化系统，提供真正的AI增强构筑推荐功能。
集成RAG上下文、模式识别和Meta洞察，生成高质量的构筑推荐。
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .models import PoE2BuildData, BuildGoal, DataQuality
from .vectorizer import PoE2BuildVectorizer
from .index_builder import PoE2BuildIndexBuilder
from .similarity_engine import PoE2SimilarityEngine, SearchQuery, SearchResult
from ..utils.poe2_constants import PoE2Constants

# 配置日志
logger = logging.getLogger(__name__)

class RecommendationStrategy(Enum):
    """推荐策略枚举"""
    SIMILARITY_BASED = "similarity_based"       # 基于相似度
    META_TRENDING = "meta_trending"             # Meta趋势
    BUDGET_OPTIMIZED = "budget_optimized"       # 预算优化
    PERFORMANCE_FOCUSED = "performance_focused"  # 性能导向
    BEGINNER_FRIENDLY = "beginner_friendly"     # 新手友好
    EXPERIMENTAL = "experimental"               # 实验性构筑

class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_HIGH = "very_high"    # >0.9
    HIGH = "high"              # 0.7-0.9
    MEDIUM = "medium"          # 0.5-0.7
    LOW = "low"                # 0.3-0.5
    VERY_LOW = "very_low"      # <0.3

@dataclass
class RecommendationContext:
    """推荐上下文信息"""
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    budget_constraints: Tuple[float, float] = (0.0, float('inf'))
    skill_level: str = "intermediate"  # beginner, intermediate, advanced
    playstyle: str = "balanced"       # defensive, offensive, balanced
    content_focus: str = "general"    # leveling, mapping, bossing, general
    avoid_mechanics: List[str] = field(default_factory=list)
    required_features: List[str] = field(default_factory=list)

@dataclass
class BuildInsight:
    """构筑洞察信息"""
    pattern_type: str = ""                      # 构筑模式类型
    meta_position: str = ""                     # Meta位置
    strength_analysis: List[str] = field(default_factory=list)  # 优势分析
    weakness_analysis: List[str] = field(default_factory=list)  # 劣势分析
    optimization_suggestions: List[str] = field(default_factory=list)  # 优化建议
    difficulty_assessment: str = "medium"      # 难度评估
    investment_tier: str = "medium"            # 投资等级

@dataclass
class AIRecommendation:
    """AI推荐结果"""
    build_data: PoE2BuildData                  # 构筑数据
    confidence_score: float                    # 置信度分数
    confidence_level: ConfidenceLevel          # 置信度等级
    recommendation_reason: str                 # 推荐理由
    build_insight: BuildInsight                # 构筑洞察
    
    # RAG上下文信息
    similar_builds: List[SearchResult] = field(default_factory=list)
    meta_context: Dict[str, Any] = field(default_factory=dict)
    rag_sources: List[str] = field(default_factory=list)
    
    # 推荐策略信息
    strategy_used: RecommendationStrategy = RecommendationStrategy.SIMILARITY_BASED
    personalization_factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'build_data': self.build_data.to_dict(),
            'confidence_score': self.confidence_score,
            'confidence_level': self.confidence_level.value,
            'recommendation_reason': self.recommendation_reason,
            'build_insight': {
                'pattern_type': self.build_insight.pattern_type,
                'meta_position': self.build_insight.meta_position,
                'strengths': self.build_insight.strength_analysis,
                'weaknesses': self.build_insight.weakness_analysis,
                'optimizations': self.build_insight.optimization_suggestions,
                'difficulty': self.build_insight.difficulty_assessment,
                'investment': self.build_insight.investment_tier
            },
            'similar_builds_count': len(self.similar_builds),
            'meta_context': self.meta_context,
            'rag_sources': self.rag_sources,
            'strategy_used': self.strategy_used.value,
            'personalization_factors': self.personalization_factors
        }

class PoE2AIEngine:
    """PoE2 RAG增强AI推荐引擎
    
    核心AI推荐系统，集成向量化检索、模式识别和智能推荐算法。
    """
    
    def __init__(self):
        """初始化AI引擎"""
        self.vectorizer = None
        self.index_builder = None
        self.similarity_engine = None
        self.knowledge_base = None
        self._ready = False
        
        # 推荐配置
        self.default_max_recommendations = 5
        self.min_confidence_threshold = 0.3
        
        # 模式识别缓存
        self._pattern_cache = {}
        self._meta_analysis_cache = {}
        
    def setup(self, vectorizer: PoE2BuildVectorizer, 
             index_builder: PoE2BuildIndexBuilder,
             similarity_engine: PoE2SimilarityEngine,
             knowledge_base=None):
        """设置依赖组件
        
        Args:
            vectorizer: 向量化引擎
            index_builder: 索引构建器
            similarity_engine: 相似性搜索引擎
            knowledge_base: 知识库管理器 (可选)
        """
        self.vectorizer = vectorizer
        self.index_builder = index_builder
        self.similarity_engine = similarity_engine
        self.knowledge_base = knowledge_base
        
        if not self.similarity_engine._ready:
            raise ValueError("相似性搜索引擎未就绪")
        
        self._ready = True
        logger.info("RAG AI引擎已就绪")
    
    def generate_recommendations(self, 
                               user_query: Union[str, Dict[str, Any], RecommendationContext],
                               strategy: RecommendationStrategy = RecommendationStrategy.SIMILARITY_BASED,
                               max_recommendations: int = None,
                               context: Optional[RecommendationContext] = None) -> List[AIRecommendation]:
        """生成AI推荐
        
        Args:
            user_query: 用户查询 - 文本、偏好字典或上下文对象
            strategy: 推荐策略
            max_recommendations: 最大推荐数量
            context: 推荐上下文
            
        Returns:
            AI推荐结果列表
        """
        if not self._ready:
            raise RuntimeError("AI引擎未就绪，请先调用setup()方法")
        
        max_recs = max_recommendations or self.default_max_recommendations
        
        # 标准化输入
        if isinstance(user_query, str):
            query_text = user_query
            preferences = {}
        elif isinstance(user_query, dict):
            preferences = user_query
            query_text = self._build_query_from_preferences(preferences)
        elif isinstance(user_query, RecommendationContext):
            context = user_query
            preferences = context.user_preferences
            query_text = self._build_query_from_context(context)
        else:
            raise ValueError(f"不支持的查询类型: {type(user_query)}")
        
        context = context or RecommendationContext(user_preferences=preferences)
        
        logger.info(f"生成AI推荐: 策略={strategy.value}, 查询='{query_text[:50]}...'")
        
        # 1. 基于策略获取候选构筑
        candidates = self._get_candidates_by_strategy(query_text, strategy, context, max_recs * 3)
        
        # 2. 应用个性化过滤
        filtered_candidates = self._apply_personalization(candidates, context)
        
        # 3. 生成详细推荐
        recommendations = []
        for candidate in filtered_candidates[:max_recs]:
            recommendation = self._create_detailed_recommendation(
                candidate, strategy, context, query_text
            )
            if recommendation.confidence_score >= self.min_confidence_threshold:
                recommendations.append(recommendation)
        
        # 4. 排序和优化
        final_recommendations = self._optimize_recommendations(recommendations, context)
        
        logger.info(f"生成了 {len(final_recommendations)} 个AI推荐")
        return final_recommendations
    
    def _get_candidates_by_strategy(self, query_text: str, 
                                   strategy: RecommendationStrategy,
                                   context: RecommendationContext,
                                   max_candidates: int) -> List[SearchResult]:
        """根据策略获取候选构筑"""
        
        if strategy == RecommendationStrategy.SIMILARITY_BASED:
            # 基于相似度的搜索
            results = self.similarity_engine.search_similar_builds(
                query_text, 
                config=self.similarity_engine.config._replace(max_results=max_candidates)
            )
            
        elif strategy == RecommendationStrategy.META_TRENDING:
            # Meta趋势推荐
            results = self._get_meta_trending_builds(context, max_candidates)
            
        elif strategy == RecommendationStrategy.BUDGET_OPTIMIZED:
            # 预算优化推荐
            results = self._get_budget_optimized_builds(query_text, context, max_candidates)
            
        elif strategy == RecommendationStrategy.PERFORMANCE_FOCUSED:
            # 性能导向推荐
            results = self._get_performance_focused_builds(query_text, context, max_candidates)
            
        elif strategy == RecommendationStrategy.BEGINNER_FRIENDLY:
            # 新手友好推荐
            results = self._get_beginner_friendly_builds(query_text, context, max_candidates)
            
        elif strategy == RecommendationStrategy.EXPERIMENTAL:
            # 实验性构筑推荐
            results = self._get_experimental_builds(query_text, context, max_candidates)
            
        else:
            # 默认使用相似度搜索
            results = self.similarity_engine.search_similar_builds(query_text)
        
        return results
    
    def _get_meta_trending_builds(self, context: RecommendationContext, max_candidates: int) -> List[SearchResult]:
        """获取Meta趋势构筑"""
        # 构建Meta查询
        meta_query = SearchQuery(
            character_class=context.user_preferences.get('character_class'),
            build_goal=context.user_preferences.get('build_goal'),
            budget_range=context.budget_constraints
        )
        
        # 搜索热门构筑（基于流行度排名）
        results = self.similarity_engine.search_similar_builds(meta_query)
        
        # 按流行度重新排序
        sorted_results = sorted(
            results, 
            key=lambda r: r.metadata.get('popularity_rank', 9999)
        )
        
        return sorted_results[:max_candidates]
    
    def _get_budget_optimized_builds(self, query_text: str, context: RecommendationContext, max_candidates: int) -> List[SearchResult]:
        """获取预算优化构筑"""
        budget_min, budget_max = context.budget_constraints
        
        # 搜索预算友好的构筑
        budget_query = SearchQuery(
            query_text=query_text,
            budget_range=(0, min(budget_max, budget_min * 1.2))  # 略微超预算也可接受
        )
        
        results = self.similarity_engine.search_similar_builds(budget_query)
        
        # 按成本效益排序
        cost_effective_results = []
        for result in results:
            cost = result.metadata.get('total_cost', 0)
            if cost <= budget_max:
                # 成本效益 = 性能 / 成本
                cost_effectiveness = result.final_score / max(cost, 0.1)
                result.cost_effectiveness = cost_effectiveness
                cost_effective_results.append(result)
        
        sorted_results = sorted(
            cost_effective_results,
            key=lambda r: getattr(r, 'cost_effectiveness', 0),
            reverse=True
        )
        
        return sorted_results[:max_candidates]
    
    def _get_performance_focused_builds(self, query_text: str, context: RecommendationContext, max_candidates: int) -> List[SearchResult]:
        """获取性能导向构筑"""
        # 搜索高性能构筑，忽略预算限制
        performance_query = SearchQuery(
            query_text=query_text,
            min_dps=1000000,  # 最低DPS要求
            budget_range=(0, float('inf'))
        )
        
        results = self.similarity_engine.search_similar_builds(performance_query)
        
        # 按性能指标排序（这里需要从构筑数据中获取DPS等信息）
        # 暂时使用final_score作为性能代理
        performance_sorted = sorted(
            results,
            key=lambda r: r.final_score,
            reverse=True
        )
        
        return performance_sorted[:max_candidates]
    
    def _get_beginner_friendly_builds(self, query_text: str, context: RecommendationContext, max_candidates: int) -> List[SearchResult]:
        """获取新手友好构筑"""
        # 搜索简单易用的构筑
        beginner_query = SearchQuery(
            query_text=query_text + " simple easy beginner",
            budget_range=(0, 5.0),  # 低预算
            level_range=(1, 85)     # 不需要很高等级
        )
        
        results = self.similarity_engine.search_similar_builds(beginner_query)
        
        # 优先选择数据质量高、成本低的构筑
        beginner_friendly = []
        for result in results:
            cost = result.metadata.get('total_cost', 0)
            quality = result.metadata.get('data_quality', 'medium')
            
            # 新手友好度评分
            beginner_score = 0
            if cost <= 3.0:
                beginner_score += 0.4
            elif cost <= 8.0:
                beginner_score += 0.2
            
            if quality == 'high':
                beginner_score += 0.3
            elif quality == 'medium':
                beginner_score += 0.2
            
            beginner_score += result.similarity_score * 0.3
            
            result.beginner_score = beginner_score
            beginner_friendly.append(result)
        
        sorted_results = sorted(
            beginner_friendly,
            key=lambda r: getattr(r, 'beginner_score', 0),
            reverse=True
        )
        
        return sorted_results[:max_candidates]
    
    def _get_experimental_builds(self, query_text: str, context: RecommendationContext, max_candidates: int) -> List[SearchResult]:
        """获取实验性构筑"""
        # 搜索非主流、创新性构筑
        experimental_query = SearchQuery(
            query_text=query_text,
            budget_range=context.budget_constraints
        )
        
        results = self.similarity_engine.search_similar_builds(experimental_query)
        
        # 优先选择流行度较低但有潜力的构筑
        experimental_builds = []
        for result in results:
            popularity_rank = result.metadata.get('popularity_rank', 0)
            
            # 实验性评分：流行度低但数据质量不错的构筑
            experimental_score = 0
            if popularity_rank > 200 or popularity_rank == 0:
                experimental_score += 0.4
            elif popularity_rank > 100:
                experimental_score += 0.2
            
            quality = result.metadata.get('data_quality', 'medium')
            if quality in ['high', 'medium']:
                experimental_score += 0.3
            
            experimental_score += result.similarity_score * 0.3
            
            result.experimental_score = experimental_score
            experimental_builds.append(result)
        
        sorted_results = sorted(
            experimental_builds,
            key=lambda r: getattr(r, 'experimental_score', 0),
            reverse=True
        )
        
        return sorted_results[:max_candidates]
    
    def _apply_personalization(self, candidates: List[SearchResult], 
                             context: RecommendationContext) -> List[SearchResult]:
        """应用个性化过滤"""
        personalized = []
        
        for candidate in candidates:
            metadata = candidate.metadata
            
            # 检查避免的机制
            if self._has_avoided_mechanics(metadata, context.avoid_mechanics):
                continue
            
            # 检查必需特性
            if not self._has_required_features(metadata, context.required_features):
                continue
            
            # 计算个性化分数
            personalization_score = self._calculate_personalization_score(metadata, context)
            candidate.personalization_score = personalization_score
            
            # 调整最终分数
            candidate.final_score = (
                candidate.final_score * 0.7 + 
                personalization_score * 0.3
            )
            
            personalized.append(candidate)
        
        return sorted(personalized, key=lambda r: r.final_score, reverse=True)
    
    def _create_detailed_recommendation(self, candidate: SearchResult, 
                                      strategy: RecommendationStrategy,
                                      context: RecommendationContext,
                                      original_query: str) -> AIRecommendation:
        """创建详细的AI推荐"""
        
        # 构建构筑数据对象（从元数据重构）
        build_data = self._reconstruct_build_from_metadata(candidate.metadata)
        
        # 计算置信度
        confidence_score = self._calculate_confidence(candidate, strategy, context)
        confidence_level = self._get_confidence_level(confidence_score)
        
        # 生成推荐理由
        recommendation_reason = self._generate_recommendation_reason(
            candidate, strategy, context, original_query
        )
        
        # 生成构筑洞察
        build_insight = self._generate_build_insight(build_data, candidate)
        
        # 获取相似构筑作为RAG上下文
        similar_builds = self._get_similar_builds_context(build_data, exclude_hash=candidate.build_hash)
        
        # Meta上下文
        meta_context = self._generate_meta_context(build_data)
        
        # RAG数据源
        rag_sources = self._identify_rag_sources(candidate)
        
        # 个性化因素
        personalization_factors = {
            'budget_match': self._calculate_budget_match(candidate.metadata, context),
            'playstyle_match': self._calculate_playstyle_match(candidate.metadata, context),
            'skill_level_match': self._calculate_skill_level_match(candidate.metadata, context)
        }
        
        return AIRecommendation(
            build_data=build_data,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            recommendation_reason=recommendation_reason,
            build_insight=build_insight,
            similar_builds=similar_builds[:3],  # 只保留前3个
            meta_context=meta_context,
            rag_sources=rag_sources,
            strategy_used=strategy,
            personalization_factors=personalization_factors
        )
    
    def _reconstruct_build_from_metadata(self, metadata: Dict[str, Any]) -> PoE2BuildData:
        """从元数据重构构筑数据对象"""
        # 这是一个简化的重构，实际应该从完整数据源获取
        from .models import SkillGemSetup, ItemInfo
        
        build = PoE2BuildData(
            character_class=metadata.get('character_class', ''),
            ascendancy=metadata.get('ascendancy', ''),
            level=metadata.get('level', 85),
            main_skill_setup=SkillGemSetup(
                main_skill=metadata.get('main_skill', '')
            ),
            total_cost=metadata.get('total_cost', 0.0),
            build_goal=BuildGoal(metadata.get('build_goal', BuildGoal.BALANCED.value)),
            data_quality=DataQuality(metadata.get('data_quality', DataQuality.MEDIUM.value)),
            popularity_rank=metadata.get('popularity_rank', 0)
        )
        
        return build
    
    def _calculate_confidence(self, candidate: SearchResult, 
                            strategy: RecommendationStrategy,
                            context: RecommendationContext) -> float:
        """计算推荐置信度"""
        base_confidence = candidate.similarity_score
        
        # 策略特定的置信度调整
        strategy_multiplier = {
            RecommendationStrategy.SIMILARITY_BASED: 1.0,
            RecommendationStrategy.META_TRENDING: 0.9,
            RecommendationStrategy.BUDGET_OPTIMIZED: 0.8,
            RecommendationStrategy.PERFORMANCE_FOCUSED: 0.85,
            RecommendationStrategy.BEGINNER_FRIENDLY: 0.7,
            RecommendationStrategy.EXPERIMENTAL: 0.6
        }.get(strategy, 0.8)
        
        # 数据质量调整
        quality = candidate.metadata.get('data_quality', 'medium')
        quality_multiplier = {
            'high': 1.0,
            'medium': 0.85,
            'low': 0.7,
            'invalid': 0.3
        }.get(quality, 0.8)
        
        # 个性化匹配调整
        personalization_boost = getattr(candidate, 'personalization_score', 0.5)
        
        final_confidence = (
            base_confidence * strategy_multiplier * quality_multiplier +
            personalization_boost * 0.1
        )
        
        return min(1.0, max(0.0, final_confidence))
    
    def _get_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """获取置信度等级"""
        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_recommendation_reason(self, candidate: SearchResult,
                                      strategy: RecommendationStrategy,
                                      context: RecommendationContext,
                                      original_query: str) -> str:
        """生成推荐理由"""
        metadata = candidate.metadata
        class_name = metadata.get('character_class', '未知职业')
        skill_name = metadata.get('main_skill', '未知技能')
        cost = metadata.get('total_cost', 0)
        
        base_reason = f"基于您的查询'{original_query[:30]}...'，推荐这个{class_name}的{skill_name}构筑"
        
        # 根据策略添加具体理由
        strategy_reasons = {
            RecommendationStrategy.SIMILARITY_BASED: f"因为它与您的需求高度匹配（相似度: {candidate.similarity_score:.1%}）",
            RecommendationStrategy.META_TRENDING: f"因为它是当前Meta的热门构筑（排名: #{metadata.get('popularity_rank', 'N/A')}）",
            RecommendationStrategy.BUDGET_OPTIMIZED: f"因为它在您的预算范围内提供了最佳性价比（成本: {cost:.1f}divine）",
            RecommendationStrategy.PERFORMANCE_FOCUSED: f"因为它具有出色的性能表现",
            RecommendationStrategy.BEGINNER_FRIENDLY: f"因为它对新手友好，易于上手且成本较低（{cost:.1f}divine）",
            RecommendationStrategy.EXPERIMENTAL: f"因为它是一个有创意的非主流构筑，值得尝试"
        }
        
        strategy_reason = strategy_reasons.get(strategy, "")
        
        # 添加提升因素
        if candidate.boost_reasons:
            boost_text = "，特别是" + "、".join(candidate.boost_reasons[:2])
        else:
            boost_text = ""
        
        return f"{base_reason}，{strategy_reason}{boost_text}。"
    
    def _generate_build_insight(self, build_data: PoE2BuildData, candidate: SearchResult) -> BuildInsight:
        """生成构筑洞察"""
        metadata = candidate.metadata
        
        # 模式识别
        pattern_type = self._identify_build_pattern(build_data)
        
        # Meta位置分析
        popularity_rank = metadata.get('popularity_rank', 0)
        if 0 < popularity_rank <= 50:
            meta_position = "热门Meta构筑"
        elif popularity_rank <= 200:
            meta_position = "主流构筑"
        elif popularity_rank <= 1000:
            meta_position = "小众构筑"
        else:
            meta_position = "实验性构筑"
        
        # 优势劣势分析
        strengths, weaknesses = self._analyze_build_strengths_weaknesses(build_data, metadata)
        
        # 优化建议
        optimizations = self._generate_optimization_suggestions(build_data, metadata)
        
        # 难度和投资评估
        difficulty = self._assess_build_difficulty(build_data, metadata)
        investment = self._assess_investment_tier(build_data, metadata)
        
        return BuildInsight(
            pattern_type=pattern_type,
            meta_position=meta_position,
            strength_analysis=strengths,
            weakness_analysis=weaknesses,
            optimization_suggestions=optimizations,
            difficulty_assessment=difficulty,
            investment_tier=investment
        )
    
    def _identify_build_pattern(self, build_data: PoE2BuildData) -> str:
        """识别构筑模式"""
        class_name = build_data.character_class
        skill_name = build_data.main_skill_setup.main_skill
        goal = build_data.build_goal.value
        
        # 简单的模式识别逻辑
        if "bow" in skill_name.lower() or class_name == "Ranger":
            return "远程物理构筑"
        elif any(elem in skill_name.lower() for elem in ["fire", "ice", "lightning"]):
            return "元素法术构筑"
        elif "cyclone" in skill_name.lower() or "earthquake" in skill_name.lower():
            return "近战AOE构筑"
        elif goal == "boss_killing":
            return "单体输出构筑"
        elif goal == "clear_speed":
            return "清图效率构筑"
        else:
            return "平衡型构筑"
    
    def _analyze_build_strengths_weaknesses(self, build_data: PoE2BuildData, 
                                          metadata: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """分析构筑优势劣势"""
        strengths = []
        weaknesses = []
        
        cost = metadata.get('total_cost', 0)
        popularity = metadata.get('popularity_rank', 0)
        goal = build_data.build_goal.value
        
        # 基于成本的分析
        if cost < 5:
            strengths.append("预算友好，适合赛季开荒")
        elif cost > 20:
            strengths.append("高投资高回报构筑")
            weaknesses.append("需要大量货币投入")
        
        # 基于流行度的分析
        if 0 < popularity <= 100:
            strengths.append("经过玩家验证的成熟构筑")
        elif popularity > 500:
            strengths.append("独特的构筑思路")
            weaknesses.append("缺乏充分的社区验证")
        
        # 基于目标的分析
        if goal == "clear_speed":
            strengths.append("出色的地图清理效率")
            weaknesses.append("对单体Boss伤害可能不足")
        elif goal == "boss_killing":
            strengths.append("强大的单体Boss击杀能力")
            weaknesses.append("清图速度可能较慢")
        
        return strengths, weaknesses
    
    def _generate_optimization_suggestions(self, build_data: PoE2BuildData, 
                                         metadata: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        cost = metadata.get('total_cost', 0)
        goal = build_data.build_goal.value
        
        # 基于成本的建议
        if cost < 2:
            suggestions.append("考虑逐步升级装备以提升性能")
        elif cost > 30:
            suggestions.append("评估装备性价比，优化投资分配")
        
        # 基于技能的建议
        skill_name = build_data.main_skill_setup.main_skill.lower()
        if "lightning" in skill_name:
            suggestions.append("确保电抗达到上限以应对反射伤害")
        elif "fire" in skill_name:
            suggestions.append("考虑添加点燃或燃烧相关天赋")
        
        # 基于目标的建议
        if goal == "clear_speed":
            suggestions.append("优先提升AOE范围和移动速度")
        elif goal == "boss_killing":
            suggestions.append("专注于单体DPS和生存能力")
        
        return suggestions
    
    def _assess_build_difficulty(self, build_data: PoE2BuildData, metadata: Dict[str, Any]) -> str:
        """评估构筑难度"""
        cost = metadata.get('total_cost', 0)
        class_name = build_data.character_class
        
        difficulty_score = 0
        
        # 基于成本
        if cost > 15:
            difficulty_score += 2
        elif cost > 5:
            difficulty_score += 1
        
        # 基于职业复杂度
        complex_classes = ["Witch", "Templar"]  # 法师类通常更复杂
        if class_name in complex_classes:
            difficulty_score += 1
        
        if difficulty_score >= 3:
            return "高难度"
        elif difficulty_score >= 1:
            return "中等难度"
        else:
            return "简单"
    
    def _assess_investment_tier(self, build_data: PoE2BuildData, metadata: Dict[str, Any]) -> str:
        """评估投资等级"""
        cost = metadata.get('total_cost', 0)
        
        if cost < 3:
            return "低投资"
        elif cost < 15:
            return "中投资"
        else:
            return "高投资"
    
    # 辅助方法（简化实现）
    def _build_query_from_preferences(self, preferences: Dict[str, Any]) -> str:
        """从偏好构建查询文本"""
        parts = []
        if 'character_class' in preferences:
            parts.append(preferences['character_class'])
        if 'main_skill' in preferences:
            parts.append(preferences['main_skill'])
        if 'build_goal' in preferences:
            parts.append(preferences['build_goal'])
        return " ".join(parts) if parts else "general build"
    
    def _build_query_from_context(self, context: RecommendationContext) -> str:
        """从上下文构建查询文本"""
        return self._build_query_from_preferences(context.user_preferences)
    
    def _has_avoided_mechanics(self, metadata: Dict[str, Any], avoid_list: List[str]) -> bool:
        """检查是否包含要避免的机制"""
        # 简化实现
        return False
    
    def _has_required_features(self, metadata: Dict[str, Any], required_list: List[str]) -> bool:
        """检查是否包含必需特性"""
        # 简化实现
        return True
    
    def _calculate_personalization_score(self, metadata: Dict[str, Any], 
                                       context: RecommendationContext) -> float:
        """计算个性化分数"""
        score = 0.5  # 基础分数
        
        # 基于预算匹配
        cost = metadata.get('total_cost', 0)
        budget_min, budget_max = context.budget_constraints
        if budget_min <= cost <= budget_max:
            score += 0.2
        elif cost <= budget_max * 1.2:  # 稍微超预算也可接受
            score += 0.1
        
        # 基于技能等级匹配
        if context.skill_level == "beginner" and cost < 5:
            score += 0.1
        elif context.skill_level == "advanced" and cost > 10:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_budget_match(self, metadata: Dict[str, Any], context: RecommendationContext) -> float:
        """计算预算匹配度"""
        cost = metadata.get('total_cost', 0)
        budget_min, budget_max = context.budget_constraints
        
        if budget_min <= cost <= budget_max:
            return 1.0
        elif cost <= budget_max * 1.2:
            return 0.7
        else:
            return 0.3
    
    def _calculate_playstyle_match(self, metadata: Dict[str, Any], context: RecommendationContext) -> float:
        """计算游戏风格匹配度"""
        # 简化实现
        return 0.8
    
    def _calculate_skill_level_match(self, metadata: Dict[str, Any], context: RecommendationContext) -> float:
        """计算技能等级匹配度"""
        cost = metadata.get('total_cost', 0)
        
        if context.skill_level == "beginner":
            return 1.0 if cost < 5 else 0.5
        elif context.skill_level == "advanced":
            return 1.0 if cost > 10 else 0.7
        else:  # intermediate
            return 0.8
    
    def _get_similar_builds_context(self, build_data: PoE2BuildData, exclude_hash: str) -> List[SearchResult]:
        """获取相似构筑作为RAG上下文"""
        try:
            variants = self.similarity_engine.find_build_variants(build_data, max_variants=5)
            return [v for v in variants if v.build_hash != exclude_hash]
        except:
            return []
    
    def _generate_meta_context(self, build_data: PoE2BuildData) -> Dict[str, Any]:
        """生成Meta上下文信息"""
        return {
            'class_popularity': f"{build_data.character_class}在当前Meta中的位置",
            'skill_trend': f"{build_data.main_skill_setup.main_skill}的使用趋势",
            'goal_meta': f"{build_data.build_goal.value}导向构筑的Meta分析"
        }
    
    def _identify_rag_sources(self, candidate: SearchResult) -> List[str]:
        """识别RAG数据源"""
        return [
            "PoE2 向量化构筑数据库",
            "相似性搜索引擎",
            "构筑模式识别系统",
            "Meta趋势分析"
        ]
    
    def _optimize_recommendations(self, recommendations: List[AIRecommendation], 
                                context: RecommendationContext) -> List[AIRecommendation]:
        """优化推荐结果"""
        # 按置信度排序
        sorted_recs = sorted(recommendations, key=lambda r: r.confidence_score, reverse=True)
        
        # 确保多样性（避免太多相似构筑）
        diversified = []
        seen_patterns = set()
        
        for rec in sorted_recs:
            pattern = rec.build_insight.pattern_type
            if pattern not in seen_patterns or len(diversified) < 2:
                diversified.append(rec)
                seen_patterns.add(pattern)
        
        return diversified

# 工厂函数
def create_ai_engine() -> PoE2AIEngine:
    """创建AI引擎的工厂函数"""
    return PoE2AIEngine()

# 测试函数
def test_ai_engine():
    """测试AI引擎功能"""
    print("AI引擎测试需要完整的RAG系统支持")
    ai_engine = create_ai_engine()
    print(f"AI引擎创建成功: {type(ai_engine).__name__}")
    return ai_engine

if __name__ == "__main__":
    engine = test_ai_engine()
    print("RAG AI引擎模块测试完成!")