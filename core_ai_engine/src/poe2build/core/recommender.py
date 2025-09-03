"""
PoE2推荐引擎 - 智能构筑推荐和排序系统

这个模块负责：
1. 基于用户偏好进行构筑推荐
2. 应用多维度评分和排序
3. 整合市场数据和流行度信息
4. 提供推荐解释和置信度评估
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable

from ..models.build import PoE2Build, PoE2BuildGoal, PoE2BuildStats
from ..models.characters import PoE2CharacterClass, PoE2Ascendancy


logger = logging.getLogger(__name__)


class ScoringCriteria(Enum):
    """评分标准枚举"""
    DPS = "dps"
    SURVIVABILITY = "survivability"
    BUDGET = "budget"
    POPULARITY = "popularity"
    EASE_OF_USE = "ease_of_use"
    LEAGUE_START = "league_start"
    ENDGAME_VIABILITY = "endgame_viability"


class RecommendationType(Enum):
    """推荐类型枚举"""
    SIMILAR = "similar"           # 相似构筑推荐
    ALTERNATIVE = "alternative"   # 替代方案推荐
    UPGRADE = "upgrade"          # 升级路径推荐
    BUDGET = "budget"            # 预算友好推荐
    META = "meta"                # 流行构筑推荐


@dataclass
class ScoringWeights:
    """评分权重配置"""
    dps_weight: float = 0.3
    survivability_weight: float = 0.25
    budget_weight: float = 0.2
    popularity_weight: float = 0.15
    ease_weight: float = 0.1
    
    def normalize(self) -> 'ScoringWeights':
        """标准化权重（确保总和为1）"""
        total = (self.dps_weight + self.survivability_weight + 
                self.budget_weight + self.popularity_weight + self.ease_weight)
        
        if total > 0:
            return ScoringWeights(
                dps_weight=self.dps_weight / total,
                survivability_weight=self.survivability_weight / total,
                budget_weight=self.budget_weight / total,
                popularity_weight=self.popularity_weight / total,
                ease_weight=self.ease_weight / total
            )
        return self


@dataclass
class RecommendationScore:
    """推荐评分详情"""
    total_score: float
    component_scores: Dict[ScoringCriteria, float]
    confidence: float
    explanation: str
    reasons: List[str]


@dataclass
class BuildRecommendation:
    """构筑推荐结果"""
    build: PoE2Build
    score: RecommendationScore
    recommendation_type: RecommendationType
    similarity_to_request: float
    market_trend: Optional[str] = None
    meta_rank: Optional[int] = None


@dataclass
class RecommendationRequest:
    """推荐请求配置"""
    # 基础筛选
    character_class: Optional[PoE2CharacterClass] = None
    build_goal: Optional[PoE2BuildGoal] = None
    max_budget: Optional[float] = None
    
    # 性能要求
    min_dps: Optional[float] = None
    min_ehp: Optional[float] = None
    require_resistance_cap: bool = True
    
    # 偏好设置
    scoring_weights: Optional[ScoringWeights] = None
    preferred_complexity: Optional[str] = None  # "low", "medium", "high"
    avoid_meta: bool = False
    prioritize_budget: bool = False
    
    # 推荐控制
    max_recommendations: int = 10
    include_alternatives: bool = True
    include_upgrades: bool = True
    explanation_detail: str = "medium"  # "low", "medium", "high"


class PoE2Recommender:
    """
    PoE2推荐引擎
    
    提供智能的构筑推荐和排序功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化推荐引擎
        
        Args:
            config: 推荐引擎配置
        """
        self.config = config or {}
        self._meta_data = {}
        self._market_trends = {}
        self._popularity_cache = {}
        
        logger.info("PoE2Recommender 初始化完成")
    
    async def recommend_builds(self, 
                             request: RecommendationRequest,
                             candidate_builds: List[PoE2Build]) -> List[BuildRecommendation]:
        """
        推荐构筑
        
        Args:
            request: 推荐请求
            candidate_builds: 候选构筑列表
            
        Returns:
            推荐结果列表
        """
        logger.info(f"开始构筑推荐: {len(candidate_builds)} 个候选构筑")
        
        try:
            # 第1步: 预过滤
            filtered_builds = self._prefilter_builds(candidate_builds, request)
            logger.debug(f"预过滤后: {len(filtered_builds)} 个构筑")
            
            # 第2步: 计算评分
            scored_builds = []
            for build in filtered_builds:
                score = await self._calculate_build_score(build, request)
                recommendation_type = self._determine_recommendation_type(build, request)
                similarity = self._calculate_similarity(build, request)
                
                recommendation = BuildRecommendation(
                    build=build,
                    score=score,
                    recommendation_type=recommendation_type,
                    similarity_to_request=similarity,
                    market_trend=self._get_market_trend(build),
                    meta_rank=self._get_meta_rank(build)
                )
                scored_builds.append(recommendation)
            
            # 第3步: 排序和筛选
            final_recommendations = self._rank_and_filter_recommendations(
                scored_builds, request
            )
            
            logger.info(f"推荐完成: {len(final_recommendations)} 个推荐")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"构筑推荐失败: {e}")
            return []
    
    def _prefilter_builds(self, builds: List[PoE2Build], request: RecommendationRequest) -> List[PoE2Build]:
        """预过滤构筑"""
        filtered = []
        
        for build in builds:
            # 职业过滤
            if request.character_class and build.character_class != request.character_class:
                continue
            
            # 预算过滤
            if request.max_budget and build.estimated_cost:
                if build.estimated_cost > request.max_budget:
                    continue
            
            # 性能过滤
            if not self._meets_performance_requirements(build, request):
                continue
            
            # 复杂度过滤（基于构筑特征推断）
            if request.preferred_complexity:
                build_complexity = self._estimate_build_complexity(build)
                if not self._complexity_matches_preference(build_complexity, request.preferred_complexity):
                    continue
            
            filtered.append(build)
        
        return filtered
    
    def _meets_performance_requirements(self, build: PoE2Build, request: RecommendationRequest) -> bool:
        """检查是否满足性能要求"""
        if not build.stats:
            return False
        
        # DPS要求
        if request.min_dps and build.stats.total_dps < request.min_dps:
            return False
        
        # EHP要求
        if request.min_ehp and build.stats.effective_health_pool < request.min_ehp:
            return False
        
        # 抗性要求
        if request.require_resistance_cap and not build.stats.is_resistance_capped():
            return False
        
        return True
    
    def _estimate_build_complexity(self, build: PoE2Build) -> str:
        """估计构筑复杂度"""
        complexity_score = 0
        
        # 基于技能数量
        if build.support_gems:
            complexity_score += len(build.support_gems) * 0.5
        
        # 基于关键物品数量
        if build.key_items:
            complexity_score += len(build.key_items) * 0.3
        
        # 基于天赋关键点
        if build.passive_keystones:
            complexity_score += len(build.passive_keystones) * 0.7
        
        # 基于预算（高预算通常意味着更复杂）
        if build.estimated_cost:
            if build.estimated_cost > 20:
                complexity_score += 2
            elif build.estimated_cost > 10:
                complexity_score += 1
        
        # 转换为复杂度级别
        if complexity_score <= 2:
            return "low"
        elif complexity_score <= 5:
            return "medium"
        else:
            return "high"
    
    def _complexity_matches_preference(self, build_complexity: str, preferred: str) -> bool:
        """检查复杂度是否匹配偏好"""
        complexity_levels = {"low": 1, "medium": 2, "high": 3}
        build_level = complexity_levels.get(build_complexity, 2)
        preferred_level = complexity_levels.get(preferred, 2)
        
        # 允许1级差异
        return abs(build_level - preferred_level) <= 1
    
    async def _calculate_build_score(self, build: PoE2Build, request: RecommendationRequest) -> RecommendationScore:
        """计算构筑评分"""
        weights = request.scoring_weights or ScoringWeights()
        weights = weights.normalize()
        
        component_scores = {}
        reasons = []
        
        # DPS评分
        dps_score = self._score_dps(build, request)
        component_scores[ScoringCriteria.DPS] = dps_score
        if dps_score > 0.8:
            reasons.append(f"Excellent DPS: {build.stats.total_dps:,.0f}" if build.stats else "High DPS potential")
        
        # 生存性评分
        survivability_score = self._score_survivability(build, request)
        component_scores[ScoringCriteria.SURVIVABILITY] = survivability_score
        if survivability_score > 0.8:
            reasons.append(f"Strong survivability: {build.stats.effective_health_pool:,.0f} EHP" if build.stats else "Good survivability")
        
        # 预算评分
        budget_score = self._score_budget(build, request)
        component_scores[ScoringCriteria.BUDGET] = budget_score
        if budget_score > 0.8:
            cost_str = f"{build.estimated_cost} divine" if build.estimated_cost else "budget-friendly"
            reasons.append(f"Budget-friendly: {cost_str}")
        
        # 流行度评分
        popularity_score = await self._score_popularity(build)
        component_scores[ScoringCriteria.POPULARITY] = popularity_score
        if popularity_score > 0.7:
            reasons.append("Popular in current meta")
        
        # 易用性评分
        ease_score = self._score_ease_of_use(build)
        component_scores[ScoringCriteria.EASE_OF_USE] = ease_score
        if ease_score > 0.8:
            reasons.append("Easy to play and maintain")
        
        # 计算总分
        total_score = (
            dps_score * weights.dps_weight +
            survivability_score * weights.survivability_weight +
            budget_score * weights.budget_weight +
            popularity_score * weights.popularity_weight +
            ease_score * weights.ease_weight
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(build, component_scores)
        
        # 生成解释
        explanation = self._generate_explanation(build, component_scores, request)
        
        return RecommendationScore(
            total_score=total_score,
            component_scores=component_scores,
            confidence=confidence,
            explanation=explanation,
            reasons=reasons
        )
    
    def _score_dps(self, build: PoE2Build, request: RecommendationRequest) -> float:
        """评分DPS"""
        if not build.stats:
            return 0.5  # 默认中等分数
        
        dps = build.stats.total_dps
        
        # 定义DPS阈值
        excellent_dps = 1500000  # 150万DPS为优秀
        good_dps = 800000       # 80万DPS为良好
        acceptable_dps = 400000  # 40万DPS为可接受
        
        if dps >= excellent_dps:
            return 1.0
        elif dps >= good_dps:
            return 0.7 + 0.3 * (dps - good_dps) / (excellent_dps - good_dps)
        elif dps >= acceptable_dps:
            return 0.4 + 0.3 * (dps - acceptable_dps) / (good_dps - acceptable_dps)
        else:
            return max(0.1, 0.4 * dps / acceptable_dps)
    
    def _score_survivability(self, build: PoE2Build, request: RecommendationRequest) -> float:
        """评分生存性"""
        if not build.stats:
            return 0.5
        
        ehp = build.stats.effective_health_pool
        
        # EHP阈值
        excellent_ehp = 12000
        good_ehp = 8000
        acceptable_ehp = 5000
        
        ehp_score = 0.0
        if ehp >= excellent_ehp:
            ehp_score = 1.0
        elif ehp >= good_ehp:
            ehp_score = 0.7 + 0.3 * (ehp - good_ehp) / (excellent_ehp - good_ehp)
        elif ehp >= acceptable_ehp:
            ehp_score = 0.4 + 0.3 * (ehp - acceptable_ehp) / (good_ehp - acceptable_ehp)
        else:
            ehp_score = max(0.1, 0.4 * ehp / acceptable_ehp)
        
        # 抗性加成
        resistance_bonus = 0.0
        if build.stats.is_resistance_capped():
            resistance_bonus = 0.1
            # 过量抗性额外加成
            avg_res = (build.stats.fire_resistance + build.stats.cold_resistance + build.stats.lightning_resistance) / 3
            if avg_res > 75:
                resistance_bonus += min(0.1, (avg_res - 75) / 50)
        
        return min(1.0, ehp_score + resistance_bonus)
    
    def _score_budget(self, build: PoE2Build, request: RecommendationRequest) -> float:
        """评分预算"""
        if not build.estimated_cost:
            return 0.6  # 无成本信息给中等分数
        
        cost = build.estimated_cost
        
        # 如果有预算要求，基于预算范围评分
        if request.max_budget:
            if cost <= request.max_budget * 0.5:
                return 1.0  # 远低于预算
            elif cost <= request.max_budget * 0.8:
                return 0.8  # 预算范围内
            elif cost <= request.max_budget:
                return 0.6  # 接近预算上限
            else:
                return 0.2  # 超出预算
        
        # 无预算要求时，基于绝对成本评分
        if cost <= 3.0:
            return 1.0  # 非常便宜
        elif cost <= 8.0:
            return 0.8  # 便宜
        elif cost <= 20.0:
            return 0.6  # 中等
        elif cost <= 50.0:
            return 0.4  # 昂贵
        else:
            return 0.2  # 非常昂贵
    
    async def _score_popularity(self, build: PoE2Build) -> float:
        """评分流行度"""
        try:
            # 这里应该查询实际的流行度数据
            # 现在返回基于构筑特征的模拟分数
            
            popularity_indicators = 0
            
            # 基于主技能的流行度
            if build.main_skill_gem:
                popular_skills = [
                    "Lightning Arrow", "Explosive Shot", "Fireball", "Arc",
                    "Earthquake", "Ground Slam", "Infernal Bolt"
                ]
                if build.main_skill_gem in popular_skills:
                    popularity_indicators += 0.3
            
            # 基于职业流行度
            popular_classes = [PoE2CharacterClass.WITCH, PoE2CharacterClass.RANGER]
            if build.character_class in popular_classes:
                popularity_indicators += 0.2
            
            # 基于预算范围（中等预算通常更受欢迎）
            if build.estimated_cost:
                if 5.0 <= build.estimated_cost <= 15.0:
                    popularity_indicators += 0.2
            
            # 基于构筑目标
            popular_goals = [PoE2BuildGoal.CLEAR_SPEED, PoE2BuildGoal.ENDGAME_CONTENT]
            if build.goal in popular_goals:
                popularity_indicators += 0.2
            
            # 抗性满足会增加流行度
            if build.stats and build.stats.is_resistance_capped():
                popularity_indicators += 0.1
            
            return min(1.0, popularity_indicators)
            
        except Exception as e:
            logger.warning(f"流行度评分失败: {e}")
            return 0.5
    
    def _score_ease_of_use(self, build: PoE2Build) -> float:
        """评分易用性"""
        ease_score = 1.0
        
        # 复杂度惩罚
        complexity = self._estimate_build_complexity(build)
        if complexity == "high":
            ease_score -= 0.3
        elif complexity == "medium":
            ease_score -= 0.1
        
        # 昂贵构筑通常更难使用
        if build.estimated_cost and build.estimated_cost > 30.0:
            ease_score -= 0.2
        
        # 技能组合复杂度
        if build.support_gems and len(build.support_gems) > 5:
            ease_score -= 0.1
        
        # 关键物品依赖
        if build.key_items and len(build.key_items) > 3:
            ease_score -= 0.1
        
        return max(0.1, ease_score)
    
    def _calculate_confidence(self, build: PoE2Build, component_scores: Dict[ScoringCriteria, float]) -> float:
        """计算推荐置信度"""
        confidence_factors = []
        
        # 数据完整性
        data_completeness = 0.5
        if build.stats:
            data_completeness += 0.3
        if build.estimated_cost:
            data_completeness += 0.1
        if build.main_skill_gem:
            data_completeness += 0.1
        
        confidence_factors.append(data_completeness)
        
        # 评分一致性（各维度评分差异小说明更可靠）
        scores = list(component_scores.values())
        if scores:
            score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
            consistency = max(0.0, 1.0 - score_variance)
            confidence_factors.append(consistency)
        
        # 构筑验证状态
        validation_score = 0.8 if build.validate() else 0.3
        confidence_factors.append(validation_score)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _generate_explanation(self, build: PoE2Build, component_scores: Dict[ScoringCriteria, float], request: RecommendationRequest) -> str:
        """生成推荐解释"""
        explanations = []
        
        # 找出最强的方面
        sorted_scores = sorted(component_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_aspects = [criteria.value for criteria, score in sorted_scores[:2] if score > 0.7]
        
        if ScoringCriteria.DPS.value in top_aspects and build.stats:
            explanations.append(f"High DPS output ({build.stats.total_dps:,.0f})")
        
        if ScoringCriteria.SURVIVABILITY.value in top_aspects and build.stats:
            explanations.append(f"Strong survivability ({build.stats.effective_health_pool:,.0f} EHP)")
        
        if ScoringCriteria.BUDGET.value in top_aspects:
            cost_str = f"{build.estimated_cost} divine" if build.estimated_cost else "budget-friendly"
            explanations.append(f"Good value ({cost_str})")
        
        # 基于构筑目标的说明
        if build.goal:
            goal_explanations = {
                PoE2BuildGoal.BOSS_KILLING: "Excellent for boss encounters",
                PoE2BuildGoal.CLEAR_SPEED: "Great for map clearing",
                PoE2BuildGoal.LEAGUE_START: "Perfect for league start",
                PoE2BuildGoal.BUDGET_FRIENDLY: "Budget-conscious choice",
                PoE2BuildGoal.ENDGAME_CONTENT: "Endgame ready"
            }
            if build.goal in goal_explanations:
                explanations.append(goal_explanations[build.goal])
        
        if not explanations:
            explanations.append("Solid all-around build")
        
        return ". ".join(explanations)
    
    def _determine_recommendation_type(self, build: PoE2Build, request: RecommendationRequest) -> RecommendationType:
        """确定推荐类型"""
        # 预算推荐
        if request.prioritize_budget or (request.max_budget and build.estimated_cost and build.estimated_cost <= request.max_budget * 0.7):
            return RecommendationType.BUDGET
        
        # 流行构筑推荐
        if self._is_meta_build(build):
            return RecommendationType.META
        
        # 升级推荐（高预算，高性能）
        if build.estimated_cost and build.estimated_cost > 20.0 and build.stats and build.stats.total_dps > 1000000:
            return RecommendationType.UPGRADE
        
        # 默认为相似推荐
        return RecommendationType.SIMILAR
    
    def _calculate_similarity(self, build: PoE2Build, request: RecommendationRequest) -> float:
        """计算与用户请求的相似度"""
        similarity_score = 0.0
        factors = 0
        
        # 职业匹配
        if request.character_class:
            if build.character_class == request.character_class:
                similarity_score += 1.0
            factors += 1
        
        # 目标匹配
        if request.build_goal:
            if build.goal == request.build_goal:
                similarity_score += 1.0
            elif build.is_suitable_for_goal(request.build_goal):
                similarity_score += 0.7
            factors += 1
        
        # 预算匹配
        if request.max_budget and build.estimated_cost:
            budget_ratio = build.estimated_cost / request.max_budget
            if budget_ratio <= 1.0:
                similarity_score += max(0.0, 1.0 - budget_ratio)
            factors += 1
        
        # 性能要求匹配
        if request.min_dps and build.stats:
            if build.stats.total_dps >= request.min_dps:
                similarity_score += 1.0
            else:
                similarity_score += build.stats.total_dps / request.min_dps
            factors += 1
        
        return similarity_score / factors if factors > 0 else 0.5
    
    def _rank_and_filter_recommendations(self, recommendations: List[BuildRecommendation], request: RecommendationRequest) -> List[BuildRecommendation]:
        """排序和筛选推荐结果"""
        # 按评分排序
        recommendations.sort(key=lambda r: (r.score.total_score, r.score.confidence), reverse=True)
        
        # 多样化推荐（避免过于相似的构筑）
        diversified = self._diversify_recommendations(recommendations)
        
        # 限制数量
        final_count = min(len(diversified), request.max_recommendations)
        
        return diversified[:final_count]
    
    def _diversify_recommendations(self, recommendations: List[BuildRecommendation]) -> List[BuildRecommendation]:
        """推荐多样化"""
        if len(recommendations) <= 3:
            return recommendations
        
        diversified = [recommendations[0]]  # 总是包含最高分的
        
        for rec in recommendations[1:]:
            # 检查是否与已选择的构筑过于相似
            is_diverse = True
            for selected in diversified:
                similarity = self._calculate_build_similarity(rec.build, selected.build)
                if similarity > 0.8:  # 相似度阈值
                    is_diverse = False
                    break
            
            if is_diverse:
                diversified.append(rec)
                if len(diversified) >= 8:  # 最多8个多样化推荐
                    break
        
        # 如果多样化后数量不足，添加剩余的高分构筑
        while len(diversified) < min(len(recommendations), 10):
            for rec in recommendations:
                if rec not in diversified:
                    diversified.append(rec)
                    break
        
        return diversified
    
    def _calculate_build_similarity(self, build1: PoE2Build, build2: PoE2Build) -> float:
        """计算两个构筑的相似度"""
        similarity_factors = []
        
        # 职业相同
        if build1.character_class == build2.character_class:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
        
        # 主技能相同
        if build1.main_skill_gem == build2.main_skill_gem:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
        
        # 目标相同
        if build1.goal == build2.goal:
            similarity_factors.append(0.8)
        else:
            similarity_factors.append(0.0)
        
        # 预算相似
        if build1.estimated_cost and build2.estimated_cost:
            cost_ratio = min(build1.estimated_cost, build2.estimated_cost) / max(build1.estimated_cost, build2.estimated_cost)
            similarity_factors.append(cost_ratio)
        else:
            similarity_factors.append(0.5)
        
        return sum(similarity_factors) / len(similarity_factors)
    
    def _is_meta_build(self, build: PoE2Build) -> bool:
        """检查是否为流行构筑"""
        # 这里应该查询实际的meta数据
        # 现在基于一些启发式规则
        
        meta_skills = [
            "Lightning Arrow", "Explosive Shot", "Fireball", 
            "Arc", "Earthquake", "Ground Slam"
        ]
        
        if build.main_skill_gem in meta_skills:
            return True
        
        # 平衡的高性能构筑通常是meta
        if (build.stats and 
            build.stats.total_dps > 800000 and 
            build.stats.effective_health_pool > 6000 and
            build.stats.is_resistance_capped()):
            return True
        
        return False
    
    def _get_market_trend(self, build: PoE2Build) -> Optional[str]:
        """获取市场趋势"""
        # 这里应该查询实际的市场数据
        # 现在返回模拟数据
        
        if not build.estimated_cost:
            return None
        
        if build.estimated_cost < 5:
            return "stable"
        elif build.estimated_cost < 15:
            return "rising"
        else:
            return "volatile"
    
    def _get_meta_rank(self, build: PoE2Build) -> Optional[int]:
        """获取meta排名"""
        # 这里应该查询实际的排名数据
        # 现在返回模拟排名
        
        if self._is_meta_build(build):
            return hash(build.name) % 20 + 1  # 模拟排名1-20
        
        return None
    
    async def explain_recommendation(self, recommendation: BuildRecommendation, detail_level: str = "medium") -> Dict[str, Any]:
        """详细解释推荐理由"""
        explanation = {
            'build_name': recommendation.build.name,
            'overall_score': recommendation.score.total_score,
            'confidence': recommendation.score.confidence,
            'recommendation_type': recommendation.recommendation_type.value,
            'similarity_score': recommendation.similarity_to_request
        }
        
        if detail_level in ["medium", "high"]:
            explanation['component_scores'] = {
                criteria.value: score 
                for criteria, score in recommendation.score.component_scores.items()
            }
            explanation['strengths'] = recommendation.score.reasons
            explanation['explanation'] = recommendation.score.explanation
        
        if detail_level == "high":
            explanation['market_info'] = {
                'trend': recommendation.market_trend,
                'meta_rank': recommendation.meta_rank
            }
            
            # 添加改进建议
            explanation['improvement_suggestions'] = await self._generate_improvement_suggestions(
                recommendation.build
            )
        
        return explanation
    
    async def _generate_improvement_suggestions(self, build: PoE2Build) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if not build.stats:
            suggestions.append("Add more detailed build statistics")
            return suggestions
        
        # DPS改进建议
        if build.stats.total_dps < 500000:
            suggestions.append("Consider upgrading weapon or adding damage support gems")
        
        # 生存性改进建议
        if build.stats.effective_health_pool < 6000:
            suggestions.append("Invest in more life/energy shield on gear")
        
        # 抗性建议
        if not build.stats.is_resistance_capped():
            suggestions.append("Prioritize capping elemental resistances")
        
        # 预算优化建议
        if build.estimated_cost and build.estimated_cost > 20:
            suggestions.append("Consider budget alternatives for expensive items")
        
        return suggestions