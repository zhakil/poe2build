#!/usr/bin/env python3
"""
专业AI构筑推荐接口
根据用户需求智能推荐冷门高性价比构筑
"""

from ai_build_recommender import AIBuildRecommender, AIBuildRecommendation
from unique_builds_database import UniqueBuildDatabase
from typing import Dict, List, Optional
import json

class ProfessionalAIRecommender:
    """专业AI构筑推荐系统"""
    
    def __init__(self):
        self.ai_engine = AIBuildRecommender()
        self.unique_db = UniqueBuildDatabase()
        
    def get_unpopular_recommendations(self, 
                                    budget_limit: Optional[float] = None,
                                    preferred_class: Optional[str] = None,
                                    difficulty_preference: Optional[str] = None,
                                    playstyle: Optional[str] = None,
                                    count: int = 5) -> List[Dict]:
        """
        获取冷门高性价比构筑推荐
        
        Args:
            budget_limit: 预算限制 (Divine Orbs)
            preferred_class: 偏好职业 (Sorceress, Witch, Ranger, Monk, Warrior, Mercenary)
            difficulty_preference: 难度偏好 (easy, medium, hard)
            playstyle: 游戏风格 (ranged, melee, caster, hybrid)
            count: 推荐数量
        """
        
        print(f"=== AI智能推荐 ===")
        print(f"预算限制: {budget_limit or '无限制'}")
        print(f"偏好职业: {preferred_class or '任意'}")
        print(f"难度偏好: {difficulty_preference or '任意'}")
        print(f"游戏风格: {playstyle or '任意'}")
        print(f"推荐数量: {count}")
        print()
        
        # 1. 生成AI创新构筑
        ai_builds = self.ai_engine.generate_unique_combinations(count=count * 2)
        
        # 2. 获取现有冷门构筑
        existing_builds = self.unique_db.get_unpopular_builds(max_popularity=0.15)
        
        # 3. 合并并筛选
        all_recommendations = []
        
        # 处理AI生成的构筑
        for ai_build in ai_builds:
            rec = self._convert_ai_build_to_recommendation(ai_build)
            all_recommendations.append(rec)
        
        # 处理现有构筑
        for existing_build in existing_builds:
            rec = self._convert_existing_build_to_recommendation(existing_build)
            all_recommendations.append(rec)
        
        # 4. 应用筛选条件
        filtered_recs = self._apply_filters(
            all_recommendations,
            budget_limit=budget_limit,
            preferred_class=preferred_class,
            difficulty_preference=difficulty_preference,
            playstyle=playstyle
        )
        
        # 5. 按照综合评分排序
        filtered_recs.sort(key=lambda x: x['scores']['overall'], reverse=True)
        
        return filtered_recs[:count]
    
    def _convert_ai_build_to_recommendation(self, ai_build: AIBuildRecommendation) -> Dict:
        """将AI构筑转换为标准推荐格式"""
        
        # 计算综合评分
        overall_score = (
            ai_build.innovation_score * 0.4 +                    # 创新度权重40%
            ai_build.skill_combination.synergy_score * 0.3 +     # 协同度权重30%
            ai_build.predicted_effectiveness * 0.2 +             # 有效性权重20%
            (1 - ai_build.risk_assessment) * 0.1                 # 低风险加分10%
        )
        
        return {
            'source': 'AI_Generated',
            'name': ai_build.name,
            'class': ai_build.character_class,
            'ascendancy': ai_build.ascendancy,
            'main_skill': ai_build.skill_combination.main_skill,
            'support_gems': ai_build.skill_combination.support_gems,
            
            'stats': {
                'dps': ai_build.estimated_performance.get('dps', 0),
                'survivability': ai_build.estimated_performance.get('survivability', 0),
                'clear_speed': ai_build.estimated_performance.get('clear_speed', 0),
                'boss_damage': ai_build.estimated_performance.get('boss_damage', 0)
            },
            
            'cost': {
                'league_start': ai_build.cost_prediction.get('league_start', 0),
                'mid_league': ai_build.cost_prediction.get('mid_league', 0),
                'min_max': ai_build.cost_prediction.get('min_max', 0)
            },
            
            'scores': {
                'innovation': ai_build.innovation_score,
                'synergy': ai_build.skill_combination.synergy_score,
                'effectiveness': ai_build.predicted_effectiveness,
                'risk': ai_build.risk_assessment,
                'overall': overall_score
            },
            
            'difficulty': ai_build.difficulty_factors.get('mechanical_complexity', 3),
            'popularity': 1.0 - ai_build.innovation_score,  # 创新度越高，流行度越低
            
            'unique_aspects': ai_build.why_unique,
            'potential_issues': ai_build.potential_issues,
            'optimization_paths': ai_build.optimization_paths,
            
            'equipment_strategy': ai_build.equipment_strategy,
            'passive_allocation': ai_build.passive_allocation,
            'playstyle_description': f"AI Generated: {ai_build.defense_approach}"
        }
    
    def _convert_existing_build_to_recommendation(self, existing_build) -> Dict:
        """将现有构筑转换为标准推荐格式"""
        
        # 计算综合评分
        cost_score = min(10.0 / existing_build.cost_analysis.get('mid_league_cost', 10), 1.0)
        overall_score = (
            existing_build.cost_effectiveness / 10 * 0.4 +       # 性价比权重40%
            (1 - existing_build.popularity_score) * 0.3 +        # 冷门度权重30%
            cost_score * 0.2 +                                   # 低成本加分20%
            (5 - existing_build.difficulty_rating) / 5 * 0.1     # 易操作加分10%
        )
        
        return {
            'source': 'Curated',
            'name': existing_build.name,
            'class': existing_build.character_class,
            'ascendancy': existing_build.ascendancy,
            'main_skill': existing_build.main_skill,
            'support_gems': existing_build.support_gems,
            
            'stats': {
                'dps': existing_build.offense_stats.get('total_dps', 0),
                'survivability': existing_build.defense_stats.get('effective_health_pool', 0),
                'clear_speed': 8.5,  # 估值
                'boss_damage': 8.0   # 估值
            },
            
            'cost': {
                'league_start': existing_build.cost_analysis.get('league_start_cost', 0),
                'mid_league': existing_build.cost_analysis.get('mid_league_cost', 0),
                'min_max': existing_build.cost_analysis.get('min_maxing_cost', 0)
            },
            
            'scores': {
                'innovation': 1.0 - existing_build.popularity_score,
                'synergy': 8.5 / 10,  # 精心设计的构筑默认高协同
                'effectiveness': existing_build.cost_effectiveness / 10,
                'risk': existing_build.difficulty_rating / 5,
                'overall': overall_score
            },
            
            'difficulty': existing_build.difficulty_rating,
            'popularity': existing_build.popularity_score,
            
            'unique_aspects': existing_build.pros_cons.get('pros', []),
            'potential_issues': existing_build.pros_cons.get('cons', []),
            'optimization_paths': [f"参考升级指南: {len(existing_build.leveling_guide)}个阶段"],
            
            'equipment_strategy': existing_build.equipment,
            'passive_allocation': existing_build.passive_tree,
            'playstyle_description': existing_build.playstyle,
            
            # 额外的详细数据
            'leveling_guide': existing_build.leveling_guide,
            'flask_setup': existing_build.flask_setup,
            'aura_setup': existing_build.aura_setup,
            'gameplay_tips': getattr(existing_build, 'gameplay_tips', [])
        }
    
    def _apply_filters(self, recommendations: List[Dict], 
                      budget_limit: Optional[float],
                      preferred_class: Optional[str],
                      difficulty_preference: Optional[str],
                      playstyle: Optional[str]) -> List[Dict]:
        """应用筛选条件"""
        
        filtered = recommendations.copy()
        
        # 预算筛选
        if budget_limit:
            filtered = [r for r in filtered 
                       if r['cost']['mid_league'] <= budget_limit]
        
        # 职业筛选
        if preferred_class:
            filtered = [r for r in filtered 
                       if r['class'].lower() == preferred_class.lower()]
        
        # 难度筛选
        if difficulty_preference:
            difficulty_map = {'easy': (1, 2), 'medium': (2, 4), 'hard': (4, 5)}
            if difficulty_preference.lower() in difficulty_map:
                min_diff, max_diff = difficulty_map[difficulty_preference.lower()]
                filtered = [r for r in filtered 
                           if min_diff <= r['difficulty'] <= max_diff]
        
        # 游戏风格筛选 (基于技能类型和描述)
        if playstyle:
            filtered = self._filter_by_playstyle(filtered, playstyle)
        
        return filtered
    
    def _filter_by_playstyle(self, recommendations: List[Dict], playstyle: str) -> List[Dict]:
        """根据游戏风格筛选"""
        
        playstyle = playstyle.lower()
        
        if playstyle == 'ranged':
            return [r for r in recommendations 
                   if any(keyword in r['main_skill'].lower() 
                         for keyword in ['spark', 'fireball', 'arrow', 'projectile'])]
        
        elif playstyle == 'melee':
            return [r for r in recommendations 
                   if any(keyword in r['main_skill'].lower() 
                         for keyword in ['strike', 'slash', 'blade', 'melee'])]
        
        elif playstyle == 'caster':
            return [r for r in recommendations 
                   if any(keyword in r['main_skill'].lower() 
                         for keyword in ['nova', 'cascade', 'tendrils', 'spell'])]
        
        elif playstyle == 'hybrid':
            return [r for r in recommendations 
                   if any(keyword in r['main_skill'].lower() 
                         for keyword in ['vortex', 'offering', 'hybrid'])]
        
        return recommendations
    
    def print_detailed_recommendation(self, recommendation: Dict):
        """打印详细的推荐信息"""
        
        rec = recommendation
        
        print(f"构筑名称: {rec['name']} ({rec['source']})")
        print(f"职业配置: {rec['class']} - {rec['ascendancy']}")
        print(f"技能配置: {rec['main_skill']} + {len(rec['support_gems'])}个支援宝石")
        print(f"支援宝石: {', '.join(rec['support_gems'][:4])}")
        print()
        
        print("性能表现:")
        print(f"  DPS输出: {rec['stats']['dps']:,}")
        print(f"  生存能力: {rec['stats']['survivability']:,} EHP")
        print(f"  清屏速度: {rec['stats'].get('clear_speed', 'N/A')}")
        print()
        
        print("成本分析:")
        print(f"  联赛初期: {rec['cost']['league_start']:.1f} Divine Orbs")
        print(f"  中期投入: {rec['cost']['mid_league']:.1f} Divine Orbs") 
        print(f"  极限优化: {rec['cost']['min_max']:.1f} Divine Orbs")
        print()
        
        print("评分系统:")
        print(f"  创新度: {rec['scores']['innovation']:.2f}/1.0")
        print(f"  协同度: {rec['scores']['synergy']:.2f}")
        print(f"  有效性: {rec['scores']['effectiveness']:.2f}")
        print(f"  风险度: {rec['scores']['risk']:.2f}")
        print(f"  综合评分: {rec['scores']['overall']:.2f}")
        print()
        
        print(f"操作难度: {rec['difficulty']}/5")
        print(f"流行程度: {rec['popularity']:.1%}")
        print()
        
        print("独特优势:")
        for aspect in rec['unique_aspects'][:3]:
            print(f"  + {aspect}")
        print()
        
        if rec['potential_issues']:
            print("注意事项:")
            for issue in rec['potential_issues'][:2]:
                print(f"  ! {issue}")
            print()
        
        print("优化建议:")
        for path in rec['optimization_paths'][:2]:
            print(f"  -> {path}")

def main():
    """测试专业AI推荐系统"""
    recommender = ProfessionalAIRecommender()
    
    # 示例1: 预算限制的冷门构筑
    print("=== 示例1: 低预算冷门构筑 ===")
    budget_recs = recommender.get_unpopular_recommendations(
        budget_limit=10.0,
        difficulty_preference="easy",
        count=2
    )
    
    for i, rec in enumerate(budget_recs, 1):
        print(f"\n--- 推荐 #{i} ---")
        recommender.print_detailed_recommendation(rec)
        print("="*80)
    
    # 示例2: 特定职业的创新构筑
    print("\n=== 示例2: Witch职业创新构筑 ===")
    witch_recs = recommender.get_unpopular_recommendations(
        preferred_class="Witch",
        playstyle="caster",
        count=1
    )
    
    for rec in witch_recs:
        recommender.print_detailed_recommendation(rec)

if __name__ == "__main__":
    main()