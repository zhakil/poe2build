"""
推荐算法模块 - PoE2构筑智能推荐算法和策略

实现多种推荐算法和策略，包括协同过滤、内容推荐、
混合推荐等，为AI引擎提供丰富的推荐能力。
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import math

from .models import PoE2BuildData, BuildGoal, DataQuality
from .ai_engine import RecommendationStrategy, RecommendationContext, AIRecommendation
from .knowledge_base import PoE2KnowledgeBase, BuildPattern, MetaInsight
from .similarity_engine import SearchResult

# 配置日志
logger = logging.getLogger(__name__)

class AlgorithmType(Enum):
    """推荐算法类型"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"   # 协同过滤
    CONTENT_BASED = "content_based"                      # 基于内容
    KNOWLEDGE_BASED = "knowledge_based"                  # 基于知识
    HYBRID = "hybrid"                                    # 混合推荐
    MATRIX_FACTORIZATION = "matrix_factorization"       # 矩阵分解
    DEEP_LEARNING = "deep_learning"                      # 深度学习

class OptimizationGoal(Enum):
    """优化目标"""
    ACCURACY = "accuracy"                    # 准确性
    DIVERSITY = "diversity"                  # 多样性
    NOVELTY = "novelty"                     # 新颖性
    COVERAGE = "coverage"                   # 覆盖度
    SERENDIPITY = "serendipity"            # 意外发现性

@dataclass
class RecommendationScore:
    """推荐分数详情"""
    total_score: float                      # 总分
    similarity_score: float = 0.0          # 相似性分数
    popularity_score: float = 0.0          # 流行度分数
    freshness_score: float = 0.0          # 新鲜度分数
    diversity_score: float = 0.0          # 多样性分数
    personalization_score: float = 0.0    # 个性化分数
    knowledge_score: float = 0.0          # 知识分数
    
    # 分数权重
    weights: Dict[str, float] = field(default_factory=lambda: {
        'similarity': 0.3,
        'popularity': 0.2,
        'freshness': 0.1,
        'diversity': 0.15,
        'personalization': 0.15,
        'knowledge': 0.1
    })
    
    def calculate_weighted_score(self) -> float:
        """计算加权总分"""
        return (
            self.similarity_score * self.weights['similarity'] +
            self.popularity_score * self.weights['popularity'] +
            self.freshness_score * self.weights['freshness'] +
            self.diversity_score * self.weights['diversity'] +
            self.personalization_score * self.weights['personalization'] +
            self.knowledge_score * self.weights['knowledge']
        )

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str                           # 用户ID
    preferred_classes: Dict[str, float] = field(default_factory=dict)    # 偏好职业
    preferred_skills: Dict[str, float] = field(default_factory=dict)     # 偏好技能
    preferred_goals: Dict[str, float] = field(default_factory=dict)      # 偏好目标
    budget_range: Tuple[float, float] = (0.0, float('inf'))              # 预算范围
    skill_level: str = "intermediate"      # 技能等级
    playtime: float = 0.0                 # 游戏时间
    build_history: List[str] = field(default_factory=list)              # 构筑历史
    interaction_history: List[Dict] = field(default_factory=list)        # 交互历史
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

class PoE2RecommendationEngine:
    """PoE2推荐算法引擎
    
    实现多种推荐算法，为不同场景提供最适合的推荐策略。
    """
    
    def __init__(self, knowledge_base: Optional[PoE2KnowledgeBase] = None):
        """初始化推荐引擎
        
        Args:
            knowledge_base: 知识库管理器
        """
        self.knowledge_base = knowledge_base
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # 推荐配置
        self.default_algorithm = AlgorithmType.HYBRID
        self.optimization_goal = OptimizationGoal.ACCURACY
        
        # 缓存
        self._similarity_cache = {}
        self._recommendation_cache = {}
        self._user_item_matrix = None
        
        # 算法权重配置
        self.algorithm_weights = {
            AlgorithmType.COLLABORATIVE_FILTERING: 0.3,
            AlgorithmType.CONTENT_BASED: 0.25,
            AlgorithmType.KNOWLEDGE_BASED: 0.25,
            AlgorithmType.MATRIX_FACTORIZATION: 0.2
        }
    
    def recommend_builds(self, 
                        user_context: RecommendationContext,
                        candidates: List[SearchResult],
                        algorithm: AlgorithmType = None,
                        max_recommendations: int = 10) -> List[Tuple[SearchResult, RecommendationScore]]:
        """使用指定算法推荐构筑
        
        Args:
            user_context: 用户上下文
            candidates: 候选构筑
            algorithm: 推荐算法类型
            max_recommendations: 最大推荐数量
            
        Returns:
            推荐结果和分数列表
        """
        algorithm = algorithm or self.default_algorithm
        
        logger.info(f"使用 {algorithm.value} 算法生成推荐")
        
        if algorithm == AlgorithmType.COLLABORATIVE_FILTERING:
            return self._collaborative_filtering_recommend(user_context, candidates, max_recommendations)
        elif algorithm == AlgorithmType.CONTENT_BASED:
            return self._content_based_recommend(user_context, candidates, max_recommendations)
        elif algorithm == AlgorithmType.KNOWLEDGE_BASED:
            return self._knowledge_based_recommend(user_context, candidates, max_recommendations)
        elif algorithm == AlgorithmType.HYBRID:
            return self._hybrid_recommend(user_context, candidates, max_recommendations)
        elif algorithm == AlgorithmType.MATRIX_FACTORIZATION:
            return self._matrix_factorization_recommend(user_context, candidates, max_recommendations)
        else:
            # 默认使用内容推荐
            return self._content_based_recommend(user_context, candidates, max_recommendations)
    
    def _collaborative_filtering_recommend(self, 
                                         user_context: RecommendationContext,
                                         candidates: List[SearchResult],
                                         max_recommendations: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """协同过滤推荐"""
        recommendations = []
        
        # 获取用户偏好
        user_preferences = user_context.user_preferences
        
        for candidate in candidates:
            metadata = candidate.metadata
            
            # 计算协同过滤分数
            cf_score = self._calculate_collaborative_score(candidate, user_preferences)
            
            # 计算其他分数组件
            popularity_score = self._calculate_popularity_score(metadata)
            diversity_score = self._calculate_diversity_score(candidate, recommendations)
            personalization_score = self._calculate_personalization_score(candidate, user_context)
            
            # 组合分数
            rec_score = RecommendationScore(
                total_score=0.0,  # 稍后计算
                similarity_score=cf_score,
                popularity_score=popularity_score,
                diversity_score=diversity_score,
                personalization_score=personalization_score,
                weights={
                    'similarity': 0.4,  # 协同过滤更重视相似性
                    'popularity': 0.3,
                    'diversity': 0.15,
                    'personalization': 0.15,
                    'freshness': 0.0,
                    'knowledge': 0.0
                }
            )
            rec_score.total_score = rec_score.calculate_weighted_score()
            
            recommendations.append((candidate, rec_score))
        
        # 排序并返回
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        return recommendations[:max_recommendations]
    
    def _content_based_recommend(self, 
                                user_context: RecommendationContext,
                                candidates: List[SearchResult],
                                max_recommendations: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """基于内容的推荐"""
        recommendations = []
        user_preferences = user_context.user_preferences
        
        for candidate in candidates:
            metadata = candidate.metadata
            
            # 计算内容相似度
            content_score = self._calculate_content_similarity(candidate, user_preferences)
            
            # 计算其他分数
            popularity_score = self._calculate_popularity_score(metadata)
            freshness_score = self._calculate_freshness_score(metadata)
            personalization_score = self._calculate_personalization_score(candidate, user_context)
            
            rec_score = RecommendationScore(
                total_score=0.0,
                similarity_score=content_score,
                popularity_score=popularity_score,
                freshness_score=freshness_score,
                personalization_score=personalization_score,
                weights={
                    'similarity': 0.35,
                    'popularity': 0.25,
                    'freshness': 0.15,
                    'personalization': 0.25,
                    'diversity': 0.0,
                    'knowledge': 0.0
                }
            )
            rec_score.total_score = rec_score.calculate_weighted_score()
            
            recommendations.append((candidate, rec_score))
        
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        return recommendations[:max_recommendations]
    
    def _knowledge_based_recommend(self, 
                                  user_context: RecommendationContext,
                                  candidates: List[SearchResult],
                                  max_recommendations: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """基于知识的推荐"""
        if not self.knowledge_base:
            logger.warning("知识库未配置，回退到内容推荐")
            return self._content_based_recommend(user_context, candidates, max_recommendations)
        
        recommendations = []
        user_preferences = user_context.user_preferences
        
        for candidate in candidates:
            metadata = candidate.metadata
            
            # 基于知识库计算分数
            knowledge_score = self._calculate_knowledge_score(candidate, user_preferences)
            
            # 计算模式匹配分数
            pattern_score = self._calculate_pattern_match_score(candidate, user_preferences)
            
            # 其他分数
            popularity_score = self._calculate_popularity_score(metadata)
            personalization_score = self._calculate_personalization_score(candidate, user_context)
            
            rec_score = RecommendationScore(
                total_score=0.0,
                knowledge_score=knowledge_score,
                similarity_score=pattern_score,
                popularity_score=popularity_score,
                personalization_score=personalization_score,
                weights={
                    'knowledge': 0.4,
                    'similarity': 0.3,
                    'popularity': 0.2,
                    'personalization': 0.1,
                    'freshness': 0.0,
                    'diversity': 0.0
                }
            )
            rec_score.total_score = rec_score.calculate_weighted_score()
            
            recommendations.append((candidate, rec_score))
        
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        return recommendations[:max_recommendations]
    
    def _hybrid_recommend(self, 
                         user_context: RecommendationContext,
                         candidates: List[SearchResult],
                         max_recommendations: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """混合推荐算法"""
        # 获取不同算法的推荐结果
        cf_results = self._collaborative_filtering_recommend(user_context, candidates, max_recommendations * 2)
        content_results = self._content_based_recommend(user_context, candidates, max_recommendations * 2)
        
        if self.knowledge_base:
            knowledge_results = self._knowledge_based_recommend(user_context, candidates, max_recommendations * 2)
        else:
            knowledge_results = []
        
        # 创建候选分数字典
        candidate_scores = {}
        
        # 加权合并不同算法的结果
        for candidate, score in cf_results:
            build_hash = candidate.build_hash
            if build_hash not in candidate_scores:
                candidate_scores[build_hash] = [candidate, RecommendationScore(total_score=0.0)]
            candidate_scores[build_hash][1].similarity_score += score.total_score * self.algorithm_weights.get(AlgorithmType.COLLABORATIVE_FILTERING, 0.3)
        
        for candidate, score in content_results:
            build_hash = candidate.build_hash
            if build_hash not in candidate_scores:
                candidate_scores[build_hash] = [candidate, RecommendationScore(total_score=0.0)]
            candidate_scores[build_hash][1].similarity_score += score.total_score * self.algorithm_weights.get(AlgorithmType.CONTENT_BASED, 0.25)
        
        for candidate, score in knowledge_results:
            build_hash = candidate.build_hash
            if build_hash not in candidate_scores:
                candidate_scores[build_hash] = [candidate, RecommendationScore(total_score=0.0)]
            candidate_scores[build_hash][1].knowledge_score += score.total_score * self.algorithm_weights.get(AlgorithmType.KNOWLEDGE_BASED, 0.25)
        
        # 计算最终推荐
        final_recommendations = []
        for candidate, rec_score in candidate_scores.values():
            # 添加多样性分数
            rec_score.diversity_score = self._calculate_diversity_score(candidate, final_recommendations)
            rec_score.personalization_score = self._calculate_personalization_score(candidate, user_context)
            rec_score.popularity_score = self._calculate_popularity_score(candidate.metadata)
            
            # 混合算法权重
            rec_score.weights = {
                'similarity': 0.25,
                'popularity': 0.2,
                'diversity': 0.15,
                'personalization': 0.15,
                'knowledge': 0.15,
                'freshness': 0.1
            }
            
            rec_score.total_score = rec_score.calculate_weighted_score()
            final_recommendations.append((candidate, rec_score))
        
        # 排序并应用多样性优化
        final_recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        diversified_results = self._apply_diversity_optimization(final_recommendations, max_recommendations)
        
        return diversified_results
    
    def _matrix_factorization_recommend(self, 
                                      user_context: RecommendationContext,
                                      candidates: List[SearchResult],
                                      max_recommendations: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """矩阵分解推荐 (简化实现)"""
        # 这里是矩阵分解算法的简化版本
        # 实际实现需要用户-物品交互矩阵和SVD等技术
        
        logger.info("矩阵分解推荐 (简化实现)")
        
        recommendations = []
        user_preferences = user_context.user_preferences
        
        for candidate in candidates:
            # 简化的矩阵分解分数计算
            mf_score = self._calculate_simplified_matrix_score(candidate, user_preferences)
            
            rec_score = RecommendationScore(
                total_score=mf_score,
                similarity_score=mf_score,
                popularity_score=self._calculate_popularity_score(candidate.metadata),
                personalization_score=self._calculate_personalization_score(candidate, user_context)
            )
            
            recommendations.append((candidate, rec_score))
        
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        return recommendations[:max_recommendations]
    
    # 分数计算方法
    def _calculate_collaborative_score(self, candidate: SearchResult, user_preferences: Dict[str, Any]) -> float:
        """计算协同过滤分数"""
        # 简化的协同过滤实现
        score = 0.5  # 基础分数
        
        metadata = candidate.metadata
        
        # 基于用户偏好的相似用户行为模拟
        if user_preferences.get('character_class') == metadata.get('character_class'):
            score += 0.2
        
        if user_preferences.get('main_skill') == metadata.get('main_skill'):
            score += 0.2
        
        if user_preferences.get('build_goal') == metadata.get('build_goal'):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_content_similarity(self, candidate: SearchResult, user_preferences: Dict[str, Any]) -> float:
        """计算内容相似度分数"""
        score = 0.0
        metadata = candidate.metadata
        
        # 职业匹配
        if user_preferences.get('character_class') == metadata.get('character_class'):
            score += 0.3
        
        # 技能匹配
        if user_preferences.get('main_skill') == metadata.get('main_skill'):
            score += 0.3
        
        # 目标匹配
        if user_preferences.get('build_goal') == metadata.get('build_goal'):
            score += 0.2
        
        # 预算匹配
        user_budget = user_preferences.get('budget', 0)
        build_cost = metadata.get('total_cost', 0)
        if user_budget > 0 and build_cost <= user_budget * 1.2:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_knowledge_score(self, candidate: SearchResult, user_preferences: Dict[str, Any]) -> float:
        """基于知识库计算分数"""
        if not self.knowledge_base:
            return 0.5
        
        score = 0.5
        metadata = candidate.metadata
        
        # 检查成功因素
        success_factors = self.knowledge_base.get_success_factors_for_build(
            metadata.get('character_class', ''),
            metadata.get('main_skill', '')
        )
        
        if success_factors:
            avg_confidence = sum(sf.confidence for sf in success_factors) / len(success_factors)
            score += avg_confidence * 0.3
        
        # 检查构筑模式
        patterns = self.knowledge_base.search_patterns(
            character_class=metadata.get('character_class'),
            main_skill=metadata.get('main_skill')
        )
        
        if patterns:
            best_pattern = patterns[0]
            score += best_pattern.success_rate * 0.2
        
        return min(1.0, score)
    
    def _calculate_pattern_match_score(self, candidate: SearchResult, user_preferences: Dict[str, Any]) -> float:
        """计算模式匹配分数"""
        if not self.knowledge_base:
            return 0.5
        
        metadata = candidate.metadata
        matching_patterns = self.knowledge_base.search_patterns(
            character_class=metadata.get('character_class'),
            main_skill=metadata.get('main_skill'),
            build_goal=metadata.get('build_goal')
        )
        
        if matching_patterns:
            best_pattern = matching_patterns[0]
            return best_pattern.popularity_score
        
        return 0.3
    
    def _calculate_popularity_score(self, metadata: Dict[str, Any]) -> float:
        """计算流行度分数"""
        popularity_rank = metadata.get('popularity_rank', 0)
        
        if popularity_rank <= 0:
            return 0.3  # 默认分数
        elif popularity_rank <= 50:
            return 1.0
        elif popularity_rank <= 200:
            return 0.8
        elif popularity_rank <= 500:
            return 0.6
        else:
            return 0.4
    
    def _calculate_freshness_score(self, metadata: Dict[str, Any]) -> float:
        """计算新鲜度分数"""
        # 这里需要构筑的创建时间信息
        # 简化实现：基于数据质量推断新鲜度
        quality = metadata.get('data_quality', 'medium')
        
        if quality == 'high':
            return 0.9
        elif quality == 'medium':
            return 0.7
        else:
            return 0.5
    
    def _calculate_diversity_score(self, candidate: SearchResult, existing_recommendations: List) -> float:
        """计算多样性分数"""
        if not existing_recommendations:
            return 1.0
        
        candidate_class = candidate.metadata.get('character_class', '')
        candidate_skill = candidate.metadata.get('main_skill', '')
        
        # 检查已有推荐中是否有相似的
        similar_count = 0
        for existing_candidate, _ in existing_recommendations:
            existing_class = existing_candidate.metadata.get('character_class', '')
            existing_skill = existing_candidate.metadata.get('main_skill', '')
            
            if candidate_class == existing_class or candidate_skill == existing_skill:
                similar_count += 1
        
        # 多样性分数随相似推荐增多而降低
        diversity_score = max(0.1, 1.0 - (similar_count * 0.3))
        return diversity_score
    
    def _calculate_personalization_score(self, candidate: SearchResult, context: RecommendationContext) -> float:
        """计算个性化分数"""
        score = 0.5
        metadata = candidate.metadata
        
        # 技能等级匹配
        build_cost = metadata.get('total_cost', 0)
        if context.skill_level == "beginner" and build_cost <= 5:
            score += 0.2
        elif context.skill_level == "advanced" and build_cost >= 10:
            score += 0.2
        elif context.skill_level == "intermediate":
            score += 0.1
        
        # 游戏风格匹配
        build_goal = metadata.get('build_goal', '')
        if context.content_focus == "mapping" and "clear_speed" in build_goal:
            score += 0.15
        elif context.content_focus == "bossing" and "boss_killing" in build_goal:
            score += 0.15
        
        # 预算匹配
        budget_min, budget_max = context.budget_constraints
        if budget_min <= build_cost <= budget_max:
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_simplified_matrix_score(self, candidate: SearchResult, user_preferences: Dict[str, Any]) -> float:
        """简化的矩阵分解分数"""
        # 这是一个非常简化的实现
        # 实际的矩阵分解需要用户-物品交互历史
        
        base_score = candidate.final_score
        metadata = candidate.metadata
        
        # 基于元数据的简化"分解"
        class_factor = 0.3 if user_preferences.get('character_class') == metadata.get('character_class') else 0.1
        skill_factor = 0.3 if user_preferences.get('main_skill') == metadata.get('main_skill') else 0.1
        goal_factor = 0.2 if user_preferences.get('build_goal') == metadata.get('build_goal') else 0.1
        
        return base_score * (class_factor + skill_factor + goal_factor)
    
    def _apply_diversity_optimization(self, 
                                    recommendations: List[Tuple[SearchResult, RecommendationScore]], 
                                    max_results: int) -> List[Tuple[SearchResult, RecommendationScore]]:
        """应用多样性优化"""
        if len(recommendations) <= max_results:
            return recommendations
        
        optimized = []
        remaining = recommendations.copy()
        
        # 贪心选择：每次选择分数最高且多样性最好的
        while len(optimized) < max_results and remaining:
            best_candidate = None
            best_score = -1
            best_index = -1
            
            for i, (candidate, rec_score) in enumerate(remaining):
                # 重新计算多样性分数
                diversity_score = self._calculate_diversity_score(candidate, optimized)
                
                # 组合分数 = 原分数 * 多样性权重
                combined_score = rec_score.total_score * 0.7 + diversity_score * 0.3
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = (candidate, rec_score)
                    best_index = i
            
            if best_candidate:
                optimized.append(best_candidate)
                remaining.pop(best_index)
        
        return optimized
    
    # 用户画像管理
    def create_user_profile(self, user_id: str, preferences: Dict[str, Any]) -> UserProfile:
        """创建用户画像"""
        profile = UserProfile(
            user_id=user_id,
            preferred_classes=preferences.get('preferred_classes', {}),
            preferred_skills=preferences.get('preferred_skills', {}),
            preferred_goals=preferences.get('preferred_goals', {}),
            budget_range=preferences.get('budget_range', (0.0, float('inf'))),
            skill_level=preferences.get('skill_level', 'intermediate')
        )
        
        self.user_profiles[user_id] = profile
        logger.info(f"创建用户画像: {user_id}")
        
        return profile
    
    def update_user_profile(self, user_id: str, interaction_data: Dict[str, Any]):
        """更新用户画像"""
        if user_id not in self.user_profiles:
            return
        
        profile = self.user_profiles[user_id]
        
        # 更新交互历史
        profile.interaction_history.append({
            'timestamp': datetime.now(),
            'interaction_type': interaction_data.get('type', 'view'),
            'build_id': interaction_data.get('build_id', ''),
            'rating': interaction_data.get('rating', 0)
        })
        
        # 更新偏好
        if 'character_class' in interaction_data:
            class_name = interaction_data['character_class']
            if class_name not in profile.preferred_classes:
                profile.preferred_classes[class_name] = 0.0
            profile.preferred_classes[class_name] += 0.1
        
        profile.last_updated = datetime.now()
        logger.info(f"更新用户画像: {user_id}")
    
    def get_optimization_metrics(self, 
                               recommendations: List[Tuple[SearchResult, RecommendationScore]],
                               user_context: RecommendationContext) -> Dict[str, float]:
        """计算推荐优化指标"""
        if not recommendations:
            return {}
        
        # 准确性指标 (基于分数分布)
        scores = [rec_score.total_score for _, rec_score in recommendations]
        accuracy = sum(scores) / len(scores)
        
        # 多样性指标 (类别分布)
        classes = [rec.metadata.get('character_class', '') for rec, _ in recommendations]
        unique_classes = len(set(classes))
        diversity = unique_classes / min(len(recommendations), 6)  # 假设有6个职业
        
        # 覆盖度指标 (预算范围覆盖)
        costs = [rec.metadata.get('total_cost', 0) for rec, _ in recommendations]
        cost_range = max(costs) - min(costs) if costs else 0
        coverage = min(1.0, cost_range / 50.0)  # 归一化到50 divine
        
        # 新颖性指标 (非主流构筑比例)
        novelty_count = sum(1 for rec, _ in recommendations 
                          if rec.metadata.get('popularity_rank', 0) > 200)
        novelty = novelty_count / len(recommendations)
        
        return {
            'accuracy': accuracy,
            'diversity': diversity,
            'coverage': coverage,
            'novelty': novelty,
            'total_recommendations': len(recommendations)
        }

# 工厂函数
def create_recommendation_engine(knowledge_base: Optional[PoE2KnowledgeBase] = None) -> PoE2RecommendationEngine:
    """创建推荐引擎的工厂函数"""
    return PoE2RecommendationEngine(knowledge_base)

# 测试函数
def test_recommendation_engine():
    """测试推荐引擎"""
    engine = create_recommendation_engine()
    
    print(f"推荐引擎创建成功")
    print(f"默认算法: {engine.default_algorithm.value}")
    print(f"优化目标: {engine.optimization_goal.value}")
    
    # 测试用户画像创建
    profile = engine.create_user_profile("test_user", {
        'preferred_classes': {'Ranger': 0.8, 'Witch': 0.2},
        'skill_level': 'intermediate',
        'budget_range': (0, 20)
    })
    
    print(f"测试用户画像: {profile.user_id}")
    
    return engine

if __name__ == "__main__":
    engine = test_recommendation_engine()
    print("推荐算法引擎测试完成!")