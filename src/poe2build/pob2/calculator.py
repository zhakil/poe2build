"""
PoB2高级计算器 - 构筑分析和优化建议
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Union
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .calculation_engine import PoB2CalculationEngine
from .local_client import PoB2LocalClient
from ..utils.poe2_constants import PoE2Constants
from ..resilience.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class PoB2Calculator:
    """PoB2高级计算器 - 提供构筑分析和优化功能"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.engine = PoB2CalculationEngine()
        self.cache_manager = cache_manager or CacheManager()
        self.calculation_cache_ttl = 3600  # 1小时缓存
        self.optimization_cache_ttl = 1800  # 30分钟缓存
        
    def is_available(self) -> bool:
        """检查计算器是否可用"""
        return self.engine.is_available()
    
    def analyze_build(self, build_data: Dict, analysis_config: Optional[Dict] = None) -> Dict:
        """
        全面分析构筑性能
        
        Args:
            build_data: 构筑数据
            analysis_config: 分析配置
            
        Returns:
            Dict: 详细分析结果
        """
        
        # 生成缓存键
        cache_key = self._generate_analysis_cache_key(build_data, analysis_config)
        
        # 尝试从缓存获取
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug("使用缓存的构筑分析结果")
            return cached_result
        
        logger.info("开始全面构筑分析")
        start_time = time.time()
        
        try:
            # 基础统计计算
            base_stats = self.engine.calculate_build_stats(build_data, analysis_config)
            
            if not base_stats.get('success'):
                return {
                    'success': False,
                    'error': base_stats.get('error', 'Unknown calculation error'),
                    'fallback': base_stats.get('fallback')
                }
            
            # 扩展分析
            analysis_result = {
                'success': True,
                'base_stats': base_stats['stats'],
                'performance_analysis': self._analyze_performance(base_stats['stats']),
                'survivability_analysis': self._analyze_survivability(base_stats['stats']),
                'offense_analysis': self._analyze_offense(base_stats['stats']),
                'defense_analysis': self._analyze_defense(base_stats['stats']),
                'recommendations': self._generate_recommendations(base_stats['stats'], build_data),
                'calculation_metadata': {
                    'calculation_time': time.time() - start_time,
                    'analysis_version': '1.0.0',
                    'pob2_version': base_stats.get('engine_version'),
                    'timestamp': time.time()
                }
            }
            
            # 缓存结果
            self.cache_manager.set(cache_key, analysis_result, self.calculation_cache_ttl)
            
            logger.info(f"构筑分析完成，耗时 {analysis_result['calculation_metadata']['calculation_time']:.2f}s")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"构筑分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis_time': time.time() - start_time
            }
    
    def _analyze_performance(self, stats: Dict) -> Dict:
        """分析构筑综合性能"""
        
        dps = stats.get('total_dps', 0)
        ehp = stats.get('effective_health_pool', stats.get('total_life', 0))
        
        # DPS评级
        dps_ratings = [
            (5000000, 'Exceptional'),  # 500万+ DPS
            (2000000, 'Excellent'),    # 200万+ DPS  
            (1000000, 'Very Good'),    # 100万+ DPS
            (500000, 'Good'),          # 50万+ DPS
            (250000, 'Average'),       # 25万+ DPS
            (100000, 'Below Average'), # 10万+ DPS
            (0, 'Poor')               # < 10万 DPS
        ]
        
        dps_rating = 'Unknown'
        for threshold, rating in dps_ratings:
            if dps >= threshold:
                dps_rating = rating
                break
        
        # 生存能力评级
        ehp_ratings = [
            (15000, 'Exceptional'),    # 15k+ EHP
            (10000, 'Excellent'),      # 10k+ EHP
            (7500, 'Very Good'),       # 7.5k+ EHP
            (5000, 'Good'),            # 5k+ EHP
            (3500, 'Average'),         # 3.5k+ EHP
            (2000, 'Below Average'),   # 2k+ EHP
            (0, 'Poor')               # < 2k EHP
        ]
        
        ehp_rating = 'Unknown'
        for threshold, rating in ehp_ratings:
            if ehp >= threshold:
                ehp_rating = rating
                break
        
        # 平衡评估
        balance_score = self._calculate_balance_score(dps, ehp)
        
        return {
            'overall_rating': self._get_overall_rating(dps_rating, ehp_rating),
            'dps_rating': dps_rating,
            'dps_value': dps,
            'survivability_rating': ehp_rating,
            'survivability_value': ehp,
            'balance_score': balance_score,
            'performance_notes': self._generate_performance_notes(dps_rating, ehp_rating, balance_score)
        }
    
    def _analyze_survivability(self, stats: Dict) -> Dict:
        """分析生存能力"""
        
        life = stats.get('total_life', 0)
        es = stats.get('total_energy_shield', 0)
        ehp = stats.get('effective_health_pool', life + es)
        
        resistances = {
            'fire': stats.get('fire_resistance', 0),
            'cold': stats.get('cold_resistance', 0),
            'lightning': stats.get('lightning_resistance', 0),
            'chaos': stats.get('chaos_resistance', 0)
        }
        
        # 抗性分析
        max_resist = PoE2Constants.MAX_RESISTANCE
        resist_status = {}
        resist_issues = []
        
        for resist_type, value in resistances.items():
            if resist_type == 'chaos':
                # 混沌抗性要求较低
                if value >= 0:
                    resist_status[resist_type] = 'Good'
                elif value >= -30:
                    resist_status[resist_type] = 'Acceptable'
                else:
                    resist_status[resist_type] = 'Poor'
                    resist_issues.append(f'{resist_type.title()} resistance too low ({value}%)')
            else:
                # 元素抗性
                if value >= max_resist:
                    resist_status[resist_type] = 'Capped'
                elif value >= max_resist - 10:
                    resist_status[resist_type] = 'Near Cap'
                elif value >= 50:
                    resist_status[resist_type] = 'Moderate'
                else:
                    resist_status[resist_type] = 'Low'
                    resist_issues.append(f'{resist_type.title()} resistance needs improvement ({value}%)')
        
        # 血量/ES分析
        life_analysis = self._analyze_life_pool(life, es)
        
        # 恢复机制分析
        recovery_analysis = {
            'life_regen': stats.get('life_regen', 0),
            'es_recharge': stats.get('es_recharge', 0),
            'leech_analysis': 'Not calculated'  # 需要更详细的数据
        }
        
        return {
            'effective_health_pool': ehp,
            'life_analysis': life_analysis,
            'resistances': resistances,
            'resistance_status': resist_status,
            'resistance_issues': resist_issues,
            'recovery_analysis': recovery_analysis,
            'survivability_score': self._calculate_survivability_score(ehp, resistances),
            'recommendations': self._generate_survivability_recommendations(
                life, es, resistances, resist_issues
            )
        }
    
    def _analyze_offense(self, stats: Dict) -> Dict:
        """分析攻击性能"""
        
        dps = stats.get('total_dps', 0)
        avg_hit = stats.get('average_hit', 0)
        attack_rate = stats.get('attack_rate', 0)
        crit_chance = stats.get('crit_chance', 0)
        crit_multi = stats.get('crit_multiplier', 150)
        accuracy = stats.get('accuracy', 90)
        
        # 攻击机制分析
        attack_analysis = {
            'dps_breakdown': {
                'total_dps': dps,
                'average_hit': avg_hit,
                'attack_rate': attack_rate,
                'effective_dps': dps * (accuracy / 100) if accuracy > 0 else dps
            },
            'crit_analysis': {
                'crit_chance': crit_chance,
                'crit_multiplier': crit_multi,
                'crit_effectiveness': self._calculate_crit_effectiveness(crit_chance, crit_multi)
            },
            'accuracy_analysis': {
                'accuracy': accuracy,
                'hit_chance': min(accuracy, 100),
                'accuracy_rating': 'Excellent' if accuracy >= 95 else 
                                 'Good' if accuracy >= 90 else
                                 'Acceptable' if accuracy >= 85 else 'Poor'
            }
        }
        
        # 伤害类型分析
        damage_type_analysis = {
            'primary_damage_type': 'Unknown',  # 需要更详细的数据
            'damage_conversion': 'Not analyzed',
            'elemental_penetration': 'Not analyzed'
        }
        
        return {
            'attack_analysis': attack_analysis,
            'damage_type_analysis': damage_type_analysis,
            'offense_score': self._calculate_offense_score(dps, crit_chance, accuracy),
            'offense_recommendations': self._generate_offense_recommendations(
                dps, crit_chance, crit_multi, accuracy
            )
        }
    
    def _analyze_defense(self, stats: Dict) -> Dict:
        """分析防御机制"""
        
        block_chance = stats.get('block_chance', 0)
        dodge_chance = stats.get('dodge_chance', 0)
        movement_speed = stats.get('movement_speed', 100)
        
        # 物理减伤分析（需要更详细数据）
        physical_mitigation = {
            'armor': 'Not calculated',
            'physical_damage_reduction': 'Not calculated',
            'fortify': 'Not detected'
        }
        
        # 回避机制分析
        avoidance_analysis = {
            'block_chance': block_chance,
            'dodge_chance': dodge_chance,
            'movement_speed': movement_speed,
            'mobility_rating': 'Excellent' if movement_speed >= 130 else
                              'Good' if movement_speed >= 115 else
                              'Average' if movement_speed >= 100 else 'Poor'
        }
        
        # 主动防御分析
        active_defense = {
            'flasks': 'Not analyzed',
            'guard_skills': 'Not detected',
            'defensive_auras': 'Not analyzed'
        }
        
        return {
            'physical_mitigation': physical_mitigation,
            'avoidance_analysis': avoidance_analysis,
            'active_defense': active_defense,
            'defense_score': self._calculate_defense_score(block_chance, dodge_chance, movement_speed),
            'defense_recommendations': self._generate_defense_recommendations(
                block_chance, dodge_chance, movement_speed
            )
        }
    
    def optimize_build(self, build_data: Dict, optimization_goals: Dict) -> Dict:
        """
        构筑优化建议
        
        Args:
            build_data: 原始构筑数据
            optimization_goals: 优化目标 (dps, survivability, balance)
            
        Returns:
            Dict: 优化建议和预期改进
        """
        
        cache_key = self._generate_optimization_cache_key(build_data, optimization_goals)
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        logger.info("开始构筑优化分析")
        
        try:
            # 基础分析
            base_analysis = self.analyze_build(build_data)
            if not base_analysis.get('success'):
                return base_analysis
            
            # 生成优化建议
            optimization_result = {
                'success': True,
                'base_analysis': base_analysis,
                'optimization_suggestions': [],
                'priority_improvements': [],
                'estimated_improvements': {}
            }
            
            # 根据目标生成具体建议
            suggestions = []
            
            if optimization_goals.get('dps_focus', False):
                suggestions.extend(self._generate_dps_optimization(base_analysis))
            
            if optimization_goals.get('survivability_focus', False):
                suggestions.extend(self._generate_survivability_optimization(base_analysis))
            
            if optimization_goals.get('balance_focus', True):
                suggestions.extend(self._generate_balance_optimization(base_analysis))
            
            # 按优先级排序
            suggestions.sort(key=lambda x: x.get('priority', 0), reverse=True)
            
            optimization_result['optimization_suggestions'] = suggestions
            optimization_result['priority_improvements'] = suggestions[:5]  # Top 5
            
            # 缓存结果
            self.cache_manager.set(cache_key, optimization_result, self.optimization_cache_ttl)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"构筑优化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_analyze(self, build_list: List[Dict], analysis_config: Optional[Dict] = None) -> List[Dict]:
        """批量分析多个构筑"""
        
        logger.info(f"开始批量分析 {len(build_list)} 个构筑")
        results = []
        
        # 使用线程池进行并行分析
        max_workers = min(4, len(build_list))  # 最多4个线程
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.analyze_build, build_data, analysis_config): i 
                for i, build_data in enumerate(build_list)
            }
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    result['build_index'] = index
                    results.append(result)
                except Exception as e:
                    logger.error(f"构筑 {index} 分析失败: {e}")
                    results.append({
                        'success': False,
                        'build_index': index,
                        'error': str(e)
                    })
        
        # 按索引排序
        results.sort(key=lambda x: x.get('build_index', 0))
        
        logger.info(f"批量分析完成，成功分析 {sum(1 for r in results if r.get('success'))} 个构筑")
        
        return results
    
    # 辅助计算方法
    
    def _calculate_balance_score(self, dps: float, ehp: float) -> float:
        """计算攻防平衡评分"""
        if dps <= 0 or ehp <= 0:
            return 0.0
        
        # 标准化DPS和EHP (使用对数缩放)
        import math
        dps_score = math.log10(max(dps, 1)) / math.log10(1000000)  # 100万DPS为基准
        ehp_score = math.log10(max(ehp, 1)) / math.log10(10000)   # 1万EHP为基准
        
        # 计算平衡分数 (惩罚极端不平衡)
        avg_score = (dps_score + ehp_score) / 2
        balance_penalty = abs(dps_score - ehp_score) * 0.3
        
        return max(0.0, min(1.0, avg_score - balance_penalty))
    
    def _calculate_survivability_score(self, ehp: float, resistances: Dict) -> float:
        """计算生存能力评分"""
        ehp_score = min(1.0, ehp / 10000)  # 1万EHP为满分
        
        # 抗性评分
        resist_score = 0
        max_resist = PoE2Constants.MAX_RESISTANCE
        
        for resist_type, value in resistances.items():
            if resist_type == 'chaos':
                resist_score += max(0, (value + 60) / 60)  # -60到0的范围
            else:
                resist_score += max(0, value / max_resist)
        
        resist_score = resist_score / len(resistances)
        
        return (ehp_score * 0.7 + resist_score * 0.3)
    
    def _calculate_offense_score(self, dps: float, crit_chance: float, accuracy: float) -> float:
        """计算攻击评分"""
        dps_score = min(1.0, dps / 2000000)  # 200万DPS为满分
        crit_score = crit_chance / 100
        accuracy_score = accuracy / 100
        
        return (dps_score * 0.6 + crit_score * 0.2 + accuracy_score * 0.2)
    
    def _calculate_defense_score(self, block: float, dodge: float, movement: float) -> float:
        """计算防御评分"""
        block_score = block / 75  # 75%格挡为满分
        dodge_score = dodge / 75  # 75%闪避为满分
        movement_score = min(1.0, (movement - 100) / 50)  # 150%移速为满分
        
        return (block_score * 0.4 + dodge_score * 0.4 + movement_score * 0.2)
    
    def _calculate_crit_effectiveness(self, crit_chance: float, crit_multi: float) -> float:
        """计算暴击有效性"""
        if crit_chance <= 0:
            return 1.0
        
        # 暴击期望伤害倍数
        return 1.0 + (crit_chance / 100) * (crit_multi / 100 - 1.0)
    
    # 缓存键生成
    
    def _generate_analysis_cache_key(self, build_data: Dict, config: Optional[Dict]) -> str:
        """生成分析缓存键"""
        import hashlib
        
        key_data = {
            'build_hash': str(hash(str(sorted(build_data.items())))),
            'config_hash': str(hash(str(sorted(config.items())))) if config else 'none',
            'analysis_version': '1.0.0'
        }
        
        return f"build_analysis:{hashlib.md5(str(key_data).encode()).hexdigest()}"
    
    def _generate_optimization_cache_key(self, build_data: Dict, goals: Dict) -> str:
        """生成优化缓存键"""
        import hashlib
        
        key_data = {
            'build_hash': str(hash(str(sorted(build_data.items())))),
            'goals_hash': str(hash(str(sorted(goals.items())))),
            'optimization_version': '1.0.0'
        }
        
        return f"build_optimization:{hashlib.md5(str(key_data).encode()).hexdigest()}"
    
    # 建议生成方法（简化实现，需要根据具体需求完善）
    
    def _generate_recommendations(self, stats: Dict, build_data: Dict) -> List[Dict]:
        """生成通用建议"""
        recommendations = []
        
        # 基于统计数据的通用建议
        if stats.get('total_dps', 0) < 500000:
            recommendations.append({
                'type': 'dps_improvement',
                'priority': 8,
                'description': '考虑提升武器伤害或增加更多伤害加成',
                'category': 'offense'
            })
        
        if stats.get('total_life', 0) < 5000:
            recommendations.append({
                'type': 'life_improvement',
                'priority': 9,
                'description': '增加生命值，目标至少5000点',
                'category': 'defense'
            })
        
        return recommendations
    
    def _generate_performance_notes(self, dps_rating: str, ehp_rating: str, balance_score: float) -> List[str]:
        """生成性能注释"""
        notes = []
        
        if balance_score < 0.3:
            notes.append("构筑存在明显的攻防不平衡")
        
        if dps_rating == 'Poor':
            notes.append("DPS过低，可能无法有效清理高级内容")
        
        if ehp_rating == 'Poor':
            notes.append("生存能力不足，容易被秒杀")
        
        return notes
    
    def _analyze_life_pool(self, life: float, es: float) -> Dict:
        """分析血量池"""
        total = life + es
        
        return {
            'total_pool': total,
            'life_percentage': (life / total * 100) if total > 0 else 0,
            'es_percentage': (es / total * 100) if total > 0 else 0,
            'build_type': 'Hybrid' if life > 0 and es > 0 else 
                         'Pure ES' if es > life else 'Life-based'
        }
    
    def _generate_survivability_recommendations(self, life: float, es: float, resistances: Dict, issues: List[str]) -> List[Dict]:
        """生成生存能力建议"""
        recommendations = []
        
        for issue in issues:
            recommendations.append({
                'type': 'resistance_fix',
                'description': issue,
                'priority': 9
            })
        
        return recommendations
    
    def _generate_offense_recommendations(self, dps: float, crit_chance: float, crit_multi: float, accuracy: float) -> List[Dict]:
        """生成攻击建议"""
        recommendations = []
        
        if accuracy < 90:
            recommendations.append({
                'type': 'accuracy_improvement',
                'description': f'提升命中率从 {accuracy}% 到至少 90%',
                'priority': 8
            })
        
        return recommendations
    
    def _generate_defense_recommendations(self, block: float, dodge: float, movement: float) -> List[Dict]:
        """生成防御建议"""
        recommendations = []
        
        if movement < 110:
            recommendations.append({
                'type': 'mobility_improvement',
                'description': '考虑增加移动速度以提升生存能力',
                'priority': 6
            })
        
        return recommendations
    
    def _generate_dps_optimization(self, analysis: Dict) -> List[Dict]:
        """生成DPS优化建议"""
        return [
            {
                'type': 'weapon_upgrade',
                'description': '升级主手武器以提升基础伤害',
                'priority': 9,
                'category': 'offense'
            }
        ]
    
    def _generate_survivability_optimization(self, analysis: Dict) -> List[Dict]:
        """生成生存能力优化建议"""
        return [
            {
                'type': 'life_nodes',
                'description': '在天赋树中投资更多生命节点',
                'priority': 8,
                'category': 'defense'
            }
        ]
    
    def _generate_balance_optimization(self, analysis: Dict) -> List[Dict]:
        """生成平衡优化建议"""
        return [
            {
                'type': 'balanced_investment',
                'description': '平衡投资攻击和防御属性',
                'priority': 7,
                'category': 'balance'
            }
        ]
    
    def _get_overall_rating(self, dps_rating: str, ehp_rating: str) -> str:
        """获取综合评级"""
        rating_scores = {
            'Exceptional': 10,
            'Excellent': 8,
            'Very Good': 7,
            'Good': 6,
            'Average': 5,
            'Below Average': 3,
            'Poor': 1
        }
        
        dps_score = rating_scores.get(dps_rating, 0)
        ehp_score = rating_scores.get(ehp_rating, 0)
        avg_score = (dps_score + ehp_score) / 2
        
        for rating, score in rating_scores.items():
            if avg_score >= score:
                return rating
        
        return 'Poor'