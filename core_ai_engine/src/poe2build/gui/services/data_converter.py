"""
GUI数据模型转换器

负责GUI表单数据与后端模型之间的双向转换，提供：
1. GUI表单数据到后端请求格式的转换
2. 后端结果到GUI显示格式的转换
3. 数据验证和清理
4. 类型安全的转换
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# 尝试导入后端模块，如果失败则使用模拟实现
try:
    from ...core.ai_orchestrator import UserRequest, RecommendationResult
    from ...models.build import PoE2Build, PoE2BuildGoal, PoE2BuildStats
    from ...models.characters import PoE2CharacterClass, PoE2Ascendancy
    BACKEND_AVAILABLE = True
except ImportError as e:
    logger.warning(f"后端模块导入失败: {e}, 将使用模拟实现")
    BACKEND_AVAILABLE = False
    
    # 模拟实现
    class UserRequest:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class RecommendationResult:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class PoE2Build:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class PoE2BuildGoal:
        ENDGAME_CONTENT = "endgame_content"
        BOSS_KILLING = "boss_killing"
        CLEAR_SPEED = "clear_speed"
        LEAGUE_START = "league_start"
    
    class PoE2BuildStats:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class PoE2CharacterClass:
        WITCH = "witch"
        SORCERESS = "sorceress"
        RANGER = "ranger"
        MONK = "monk"
        WARRIOR = "warrior"
        MERCENARY = "mercenary"
    
    class PoE2Ascendancy:
        pass


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """数据验证错误"""
    pass


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    data: Any = None
    error: str = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DataConverter:
    """数据转换器主类"""
    
    def __init__(self):
        """初始化转换器"""
        self._init_mappings()
        logger.debug("DataConverter 已初始化")
    
    def _init_mappings(self):
        """初始化映射表"""
        # GUI职业名称到后端枚举的映射
        self.class_mapping = {
            # 中文映射
            '女巫': PoE2CharacterClass.WITCH,
            '法师': PoE2CharacterClass.SORCERESS, 
            '游侠': PoE2CharacterClass.RANGER,
            '僧侣': PoE2CharacterClass.MONK,
            '战士': PoE2CharacterClass.WARRIOR,
            '女猎手': PoE2CharacterClass.MERCENARY,
            # 英文映射
            'Witch': PoE2CharacterClass.WITCH,
            'Sorceress': PoE2CharacterClass.SORCERESS,
            'Ranger': PoE2CharacterClass.RANGER,
            'Monk': PoE2CharacterClass.MONK,
            'Warrior': PoE2CharacterClass.WARRIOR,
            'Huntress': PoE2CharacterClass.MERCENARY,
            'Mercenary': PoE2CharacterClass.MERCENARY,
            # 带括号的格式
            '女巫 (Witch)': PoE2CharacterClass.WITCH,
            '法师 (Sorceress)': PoE2CharacterClass.SORCERESS,
            '游侠 (Ranger)': PoE2CharacterClass.RANGER,
            '僧侣 (Monk)': PoE2CharacterClass.MONK,
            '战士 (Warrior)': PoE2CharacterClass.WARRIOR,
            '女猎手 (Huntress)': PoE2CharacterClass.MERCENARY
        }
        
        # GUI构筑目标到后端枚举的映射
        self.goal_mapping = {
            # 中文映射
            '全能型 (平衡)': PoE2BuildGoal.ENDGAME_CONTENT,
            '高DPS (输出)': PoE2BuildGoal.BOSS_KILLING,
            '高生存 (防御)': PoE2BuildGoal.ENDGAME_CONTENT,
            '快速刷图': PoE2BuildGoal.CLEAR_SPEED,
            'Boss击杀': PoE2BuildGoal.BOSS_KILLING,
            '新手友好': PoE2BuildGoal.LEAGUE_START,
            # 英文映射
            'balanced': PoE2BuildGoal.ENDGAME_CONTENT,
            'high_dps': PoE2BuildGoal.BOSS_KILLING,
            'tanky': PoE2BuildGoal.ENDGAME_CONTENT,
            'clear_speed': PoE2BuildGoal.CLEAR_SPEED,
            'boss_killing': PoE2BuildGoal.BOSS_KILLING,
            'beginner_friendly': PoE2BuildGoal.LEAGUE_START,
            'league_start': PoE2BuildGoal.LEAGUE_START,
            'budget_friendly': PoE2BuildGoal.BUDGET_FRIENDLY,
            'endgame_content': PoE2BuildGoal.ENDGAME_CONTENT
        }
        
        # 专精映射表
        self.ascendancy_mapping = {
            # 女巫专精
            '血法师': PoE2Ascendancy.BLOOD_MAGE,
            '地狱女巫': PoE2Ascendancy.INFERNALIST,  
            '暴风使': PoE2Ascendancy.STORMWEAVER,
            # 法师专精
            '魔化师': PoE2Ascendancy.CHRONOMANCER,
            '时空法师': PoE2Ascendancy.CHRONOMANCER,
            '斯特姆法师': PoE2Ascendancy.STORMWEAVER,
            # 游侠专精
            '猎手': PoE2Ascendancy.DEADEYE,
            '刺客': PoE2Ascendancy.PATHFINDER,
            # 僧侣专精
            '武僧': PoE2Ascendancy.INVOKER,
            '魂师': PoE2Ascendancy.INVOKER,
            '符师': PoE2Ascendancy.ACOLYTE_OF_CHAYULA,
            # 战士专精
            # '斗士': PoE2Ascendancy.GLADIATOR,  # 暂时没有此升华
            '奴隶主': PoE2Ascendancy.WARBRINGER,
            '泰坦': PoE2Ascendancy.TITAN,
            # 女猎手专精
            '剑舞者': PoE2Ascendancy.WITCHHUNTER,
            '女武神': PoE2Ascendancy.GEMLING_LEGIONNAIRE,
            '女猎手': PoE2Ascendancy.WITCHHUNTER
        }
        
        # 货币类型映射
        self.currency_mapping = {
            'Divine Orb': 'divine',
            'Exalted Orb': 'exalted',
            'Chaos Orb': 'chaos',
            '无限制': None
        }
        
        # 反向映射（用于显示）
        self.reverse_class_mapping = {v: k for k, v in self.class_mapping.items() if '(' in k}
        self.reverse_goal_mapping = {v: k for k, v in self.goal_mapping.items() if '(' in k}
    
    def gui_to_backend_request(self, gui_data: Dict[str, Any]) -> ConversionResult:
        """
        将GUI表单数据转换为后端请求格式
        
        Args:
            gui_data: GUI表单数据
            
        Returns:
            转换结果，包含UserRequest对象或错误信息
        """
        try:
            logger.debug("开始转换GUI数据到后端请求格式")
            
            # 验证输入数据
            validation_result = self._validate_gui_data(gui_data)
            if not validation_result.success:
                return validation_result
            
            preferences = gui_data.get('preferences', {})
            warnings = []
            
            # 转换职业
            character_class = self._convert_character_class(preferences.get('class'))
            if not character_class:
                return ConversionResult(
                    success=False,
                    error="无法识别的职业选择"
                )
            
            # 转换专精
            ascendancy = self._convert_ascendancy(
                preferences.get('ascendancy'), 
                character_class
            )
            
            # 转换构筑目标
            build_goal = self._convert_build_goal(preferences.get('goal'))
            if not build_goal:
                build_goal = PoE2BuildGoal.ENDGAME_CONTENT
                warnings.append("未指定构筑目标，使用默认值：endgame_content")
            
            # 转换预算信息
            budget_info = preferences.get('budget', {})
            max_budget = None
            currency_type = 'divine'
            
            if budget_info.get('amount') and budget_info.get('amount') > 0:
                max_budget = float(budget_info['amount'])
                currency_type = self.currency_mapping.get(
                    budget_info.get('currency', 'Divine Orb'), 
                    'divine'
                )
            
            # 转换其他偏好
            preferred_skills = self._parse_skills_list(
                preferences.get('weapon_type'),
                preferences.get('ai_settings', {}).get('special_requirements')
            )
            
            playstyle = self._convert_playstyle(preferences.get('goal'))
            
            # 转换技术要求
            min_dps = self._calculate_min_dps(build_goal, preferences.get('level', 90))
            min_ehp = self._calculate_min_ehp(build_goal, preferences.get('level', 90))
            
            # 转换PoB2设置
            pob2_settings = preferences.get('pob2_integration', {})
            generate_pob2_code = pob2_settings.get('generate_import_code', True)
            validate_with_pob2 = pob2_settings.get('calculate_stats', True)
            
            # 转换AI设置
            ai_settings = preferences.get('ai_settings', {})
            max_build_complexity = self._convert_complexity(
                ai_settings.get('creativity_level', 1)
            )
            
            # 创建UserRequest对象
            user_request = UserRequest(
                character_class=character_class,
                ascendancy=ascendancy,
                build_goal=build_goal,
                max_budget=max_budget,
                currency_type=currency_type,
                preferred_skills=preferred_skills,
                playstyle=playstyle,
                min_dps=min_dps,
                min_ehp=min_ehp,
                require_resistance_cap=True,
                include_meta_builds=True,
                include_budget_builds=max_budget is None or max_budget <= 20,
                max_build_complexity=max_build_complexity,
                generate_pob2_code=generate_pob2_code,
                validate_with_pob2=validate_with_pob2
            )
            
            logger.debug("GUI数据转换成功")
            
            return ConversionResult(
                success=True,
                data=user_request,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"GUI数据转换失败: {e}")
            return ConversionResult(
                success=False,
                error=f"数据转换异常: {str(e)}"
            )
    
    def backend_to_gui_result(self, result: RecommendationResult) -> ConversionResult:
        """
        将后端结果转换为GUI显示格式
        
        Args:
            result: 后端推荐结果
            
        Returns:
            转换结果，包含GUI格式数据或错误信息
        """
        try:
            logger.debug("开始转换后端结果到GUI格式")
            
            gui_builds = []
            warnings = []
            
            for build in result.builds:
                gui_build = self._convert_build_to_gui(build)
                if gui_build:
                    gui_builds.append(gui_build)
                else:
                    warnings.append(f"构筑 {build.name} 转换失败，已跳过")
            
            # 转换元数据
            gui_metadata = self._convert_metadata_to_gui(result.metadata)
            
            # 构建GUI结果
            gui_result = {
                'success': True,
                'builds': gui_builds,
                'metadata': gui_metadata,
                'statistics': {
                    'rag_confidence': result.rag_confidence,
                    'pob2_validated': result.pob2_validated,
                    'generation_time_ms': result.generation_time_ms,
                    'used_components': [comp.value for comp in result.used_components],
                    'build_count': len(gui_builds)
                },
                'recommendations': {
                    'quality_score': self._calculate_quality_score(result),
                    'diversity_score': self._calculate_diversity_score(gui_builds),
                    'budget_efficiency': self._calculate_budget_efficiency(gui_builds)
                }
            }
            
            logger.debug(f"后端结果转换成功，转换了 {len(gui_builds)} 个构筑")
            
            return ConversionResult(
                success=True,
                data=gui_result,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"后端结果转换失败: {e}")
            return ConversionResult(
                success=False,
                error=f"结果转换异常: {str(e)}"
            )
    
    def _validate_gui_data(self, gui_data: Dict[str, Any]) -> ConversionResult:
        """验证GUI数据"""
        try:
            # 检查基本结构
            if not isinstance(gui_data, dict):
                return ConversionResult(
                    success=False,
                    error="GUI数据必须是字典类型"
                )
            
            if 'preferences' not in gui_data:
                return ConversionResult(
                    success=False,
                    error="缺少preferences字段"
                )
            
            preferences = gui_data['preferences']
            
            # 验证必需字段
            if not preferences.get('class'):
                return ConversionResult(
                    success=False,
                    error="必须选择职业"
                )
            
            # 验证数值字段
            level = preferences.get('level')
            if level is not None:
                if not isinstance(level, int) or level < 1 or level > 100:
                    return ConversionResult(
                        success=False,
                        error="等级必须在1-100之间"
                    )
            
            # 验证预算
            budget = preferences.get('budget', {})
            if budget.get('amount') is not None:
                amount = budget['amount']
                if not isinstance(amount, (int, float)) or amount < 0:
                    return ConversionResult(
                        success=False,
                        error="预算金额必须为非负数"
                    )
            
            return ConversionResult(success=True)
            
        except Exception as e:
            return ConversionResult(
                success=False,
                error=f"数据验证异常: {str(e)}"
            )
    
    def _convert_character_class(self, class_str: str) -> Optional[PoE2CharacterClass]:
        """转换职业字符串"""
        if not class_str:
            return None
        
        # 清理输入
        cleaned = class_str.strip()
        
        # 直接查找
        if cleaned in self.class_mapping:
            return self.class_mapping[cleaned]
        
        # 模糊匹配
        for key, value in self.class_mapping.items():
            if key.lower() == cleaned.lower():
                return value
            if cleaned.lower() in key.lower():
                return value
        
        return None
    
    def _convert_ascendancy(self, ascendancy_str: str, 
                          character_class: PoE2CharacterClass) -> Optional[PoE2Ascendancy]:
        """转换专精字符串"""
        if not ascendancy_str or ascendancy_str == '自动选择最佳专精':
            return None
        
        cleaned = ascendancy_str.strip()
        
        # 直接查找
        if cleaned in self.ascendancy_mapping:
            return self.ascendancy_mapping[cleaned]
        
        # 模糊匹配
        for key, value in self.ascendancy_mapping.items():
            if key.lower() == cleaned.lower():
                return value
        
        return None
    
    def _convert_build_goal(self, goal_str: str) -> Optional[PoE2BuildGoal]:
        """转换构筑目标"""
        if not goal_str:
            return None
        
        cleaned = goal_str.strip()
        
        # 直接查找
        if cleaned in self.goal_mapping:
            return self.goal_mapping[cleaned]
        
        # 模糊匹配
        for key, value in self.goal_mapping.items():
            if key.lower() == cleaned.lower():
                return value
            if cleaned.lower() in key.lower():
                return value
        
        return None
    
    def _parse_skills_list(self, weapon_type: str, 
                          special_requirements: str) -> Optional[List[str]]:
        """解析技能列表"""
        skills = []
        
        # 从武器类型推断技能偏好
        if weapon_type and weapon_type != '自动推荐':
            weapon_skills = {
                '弓': ['弓箭技能', 'bow'],
                '法杖': ['法术技能', 'spell'],
                '长杖': ['法术技能', 'staff'],
                '单手剑': ['近战技能', 'melee'],
                '双手剑': ['近战技能', 'two_handed'],
                '锤': ['近战技能', 'mace'],
                '斧': ['近战技能', 'axe'],
                '爪': ['近战技能', 'claw'],
                '长矛': ['近战技能', 'spear'],
                '十字弓': ['弓箭技能', 'crossbow'],
                '魔杖': ['法术技能', 'wand']
            }
            
            if weapon_type in weapon_skills:
                skills.extend(weapon_skills[weapon_type])
        
        # 解析特殊要求中的技能
        if special_requirements:
            # 简单的关键词提取
            req_lower = special_requirements.lower()
            skill_keywords = [
                '火球', '闪电', '冰霜', '毒素', '光环', '召唤',
                'fireball', 'lightning', 'frost', 'poison', 'aura', 'minion'
            ]
            
            for keyword in skill_keywords:
                if keyword in req_lower:
                    skills.append(keyword)
        
        return skills if skills else None
    
    def _convert_playstyle(self, goal_str: str) -> str:
        """转换游戏风格"""
        if not goal_str:
            return 'balanced'
        
        goal_lower = goal_str.lower()
        
        if 'dps' in goal_lower or '输出' in goal_lower:
            return 'aggressive'
        elif '生存' in goal_lower or '防御' in goal_lower or 'tanky' in goal_lower:
            return 'defensive'
        else:
            return 'balanced'
    
    def _calculate_min_dps(self, goal: PoE2BuildGoal, level: int) -> Optional[float]:
        """计算最低DPS要求"""
        base_dps = {
            PoE2BuildGoal.BOSS_KILLING: 600000,
            PoE2BuildGoal.CLEAR_SPEED: 400000,
            PoE2BuildGoal.ENDGAME_CONTENT: 500000,
            PoE2BuildGoal.LEAGUE_START: 200000,
            PoE2BuildGoal.BUDGET_FRIENDLY: 250000
        }
        
        min_dps = base_dps.get(goal, 300000)
        
        # 根据等级调整
        level_factor = min(level / 90, 1.2)
        return min_dps * level_factor
    
    def _calculate_min_ehp(self, goal: PoE2BuildGoal, level: int) -> Optional[float]:
        """计算最低有效生命值要求"""
        base_ehp = {
            PoE2BuildGoal.BOSS_KILLING: 6000,
            PoE2BuildGoal.CLEAR_SPEED: 4500,
            PoE2BuildGoal.ENDGAME_CONTENT: 5500,
            PoE2BuildGoal.LEAGUE_START: 3500,
            PoE2BuildGoal.BUDGET_FRIENDLY: 4000
        }
        
        min_ehp = base_ehp.get(goal, 4500)
        
        # 根据等级调整
        level_factor = min(level / 90, 1.3)
        return min_ehp * level_factor
    
    def _convert_complexity(self, creativity_level: int) -> str:
        """转换复杂度设置"""
        complexity_map = {
            0: 'low',
            1: 'medium', 
            2: 'high'
        }
        return complexity_map.get(creativity_level, 'medium')
    
    def _convert_build_to_gui(self, build: PoE2Build) -> Optional[Dict[str, Any]]:
        """转换单个构筑到GUI格式"""
        try:
            gui_build = {
                'id': f"build_{hash(build.name)}",
                'name': build.name,
                'character_class': {
                    'name': build.character_class.value,
                    'display_name': self.reverse_class_mapping.get(
                        build.character_class, 
                        build.character_class.value
                    )
                },
                'level': build.level,
                'estimated_cost': build.estimated_cost,
                'currency_type': getattr(build, 'currency_type', 'divine'),
                'main_skill': build.main_skill_gem,
                'support_gems': build.support_gems or [],
                'key_items': build.key_items or [],
                'passive_keystones': build.passive_keystones or [],
                'pob2_code': build.pob2_code,
                'notes': build.notes
            }
            
            # 添加专精信息
            if build.ascendancy:
                gui_build['ascendancy'] = {
                    'name': build.ascendancy.value,
                    'display_name': build.ascendancy.value  # 可以后续添加中文名
                }
            
            # 添加目标信息
            if build.goal:
                gui_build['goal'] = {
                    'name': build.goal.value,
                    'display_name': self.reverse_goal_mapping.get(
                        build.goal,
                        build.goal.value
                    )
                }
            
            # 转换统计数据
            if build.stats:
                gui_build['stats'] = self._convert_stats_to_gui(build.stats)
                gui_build['performance'] = self._calculate_performance_metrics(build.stats)
            
            # 计算构筑评分
            gui_build['rating'] = self._calculate_build_rating(build)
            
            # 添加标签
            gui_build['tags'] = self._generate_build_tags(build)
            
            return gui_build
            
        except Exception as e:
            logger.error(f"构筑转换失败 {build.name}: {e}")
            return None
    
    def _convert_stats_to_gui(self, stats: PoE2BuildStats) -> Dict[str, Any]:
        """转换统计数据到GUI格式"""
        return {
            'offensive': {
                'total_dps': {
                    'value': stats.total_dps,
                    'formatted': f"{stats.total_dps:,.0f}",
                    'rating': self._rate_dps(stats.total_dps)
                },
                'critical_strike_chance': getattr(stats, 'critical_strike_chance', 0),
                'critical_strike_multiplier': getattr(stats, 'critical_strike_multiplier', 150)
            },
            'defensive': {
                'effective_health_pool': {
                    'value': stats.effective_health_pool,
                    'formatted': f"{stats.effective_health_pool:,.0f}",
                    'rating': self._rate_ehp(stats.effective_health_pool)
                },
                'life': getattr(stats, 'life', 0),
                'energy_shield': getattr(stats, 'energy_shield', 0),
                'resistances': {
                    'fire': stats.fire_resistance,
                    'cold': stats.cold_resistance,
                    'lightning': stats.lightning_resistance,
                    'chaos': stats.chaos_resistance,
                    'is_capped': stats.is_resistance_capped()
                }
            },
            'utility': {
                'movement_speed': getattr(stats, 'movement_speed', 0),
                'mana_reservation': getattr(stats, 'mana_reservation', 0)
            }
        }
    
    def _calculate_performance_metrics(self, stats: PoE2BuildStats) -> Dict[str, Any]:
        """计算性能指标"""
        return {
            'survivability_score': min((stats.effective_health_pool / 8000) * 100, 100),
            'damage_score': min((stats.total_dps / 1000000) * 100, 100),
            'resistance_score': 100 if stats.is_resistance_capped() else 50,
            'overall_score': self._calculate_overall_score(stats)
        }
    
    def _calculate_overall_score(self, stats: PoE2BuildStats) -> float:
        """计算总体评分"""
        damage_weight = 0.4
        survivability_weight = 0.4
        resistance_weight = 0.2
        
        damage_score = min(stats.total_dps / 1000000, 1.0) * 100
        survivability_score = min(stats.effective_health_pool / 8000, 1.0) * 100
        resistance_score = 100 if stats.is_resistance_capped() else 30
        
        overall = (
            damage_score * damage_weight +
            survivability_score * survivability_weight +
            resistance_score * resistance_weight
        )
        
        return round(overall, 1)
    
    def _calculate_build_rating(self, build: PoE2Build) -> Dict[str, Any]:
        """计算构筑评级"""
        rating = {
            'overall': 'B',
            'damage': 'B',
            'survivability': 'B',
            'cost_efficiency': 'B'
        }
        
        if build.stats:
            # DPS评级
            if build.stats.total_dps >= 800000:
                rating['damage'] = 'A'
            elif build.stats.total_dps >= 500000:
                rating['damage'] = 'B'
            else:
                rating['damage'] = 'C'
            
            # 生存性评级
            if build.stats.effective_health_pool >= 7000 and build.stats.is_resistance_capped():
                rating['survivability'] = 'A'
            elif build.stats.effective_health_pool >= 5000:
                rating['survivability'] = 'B'
            else:
                rating['survivability'] = 'C'
        
        # 成本效率评级
        if build.estimated_cost:
            if build.estimated_cost <= 10:
                rating['cost_efficiency'] = 'A'
            elif build.estimated_cost <= 25:
                rating['cost_efficiency'] = 'B'
            else:
                rating['cost_efficiency'] = 'C'
        
        # 总体评级
        ratings = [rating['damage'], rating['survivability'], rating['cost_efficiency']]
        if 'A' in ratings and ratings.count('C') == 0:
            rating['overall'] = 'A'
        elif 'C' not in ratings:
            rating['overall'] = 'B'
        else:
            rating['overall'] = 'C'
        
        return rating
    
    def _generate_build_tags(self, build: PoE2Build) -> List[str]:
        """生成构筑标签"""
        tags = []
        
        # 基于职业的标签
        tags.append(build.character_class.value.lower())
        
        # 基于目标的标签
        if build.goal:
            goal_tags = {
                PoE2BuildGoal.BOSS_KILLING: ['boss_killer', 'high_dps'],
                PoE2BuildGoal.CLEAR_SPEED: ['fast_clear', 'mapping'],
                PoE2BuildGoal.BUDGET_FRIENDLY: ['budget', 'starter'],
                PoE2BuildGoal.LEAGUE_START: ['league_starter', 'budget'],
                PoE2BuildGoal.ENDGAME_CONTENT: ['endgame', 'versatile']
            }
            tags.extend(goal_tags.get(build.goal, []))
        
        # 基于成本的标签
        if build.estimated_cost:
            if build.estimated_cost <= 5:
                tags.append('very_budget')
            elif build.estimated_cost <= 15:
                tags.append('budget')
            elif build.estimated_cost <= 50:
                tags.append('mid_tier')
            else:
                tags.append('expensive')
        
        # 基于统计的标签
        if build.stats:
            if build.stats.total_dps >= 800000:
                tags.append('high_damage')
            if build.stats.effective_health_pool >= 7000:
                tags.append('tanky')
            if build.stats.is_resistance_capped():
                tags.append('res_capped')
        
        # 基于技能的标签
        if build.main_skill_gem:
            skill_lower = build.main_skill_gem.lower()
            if any(word in skill_lower for word in ['bow', '弓']):
                tags.append('bow')
            elif any(word in skill_lower for word in ['spell', 'cast', '法术']):
                tags.append('caster')
            elif any(word in skill_lower for word in ['melee', '近战']):
                tags.append('melee')
            elif any(word in skill_lower for word in ['summon', '召唤']):
                tags.append('minion')
        
        return tags
    
    def _rate_dps(self, dps: float) -> str:
        """评级DPS"""
        if dps >= 800000:
            return 'excellent'
        elif dps >= 500000:
            return 'good'
        elif dps >= 300000:
            return 'average'
        else:
            return 'low'
    
    def _rate_ehp(self, ehp: float) -> str:
        """评级有效生命值"""
        if ehp >= 7000:
            return 'excellent'
        elif ehp >= 5000:
            return 'good'
        elif ehp >= 3500:
            return 'average'
        else:
            return 'low'
    
    def _convert_metadata_to_gui(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """转换元数据到GUI格式"""
        return {
            'generation_info': {
                'timestamp': metadata.get('generation_timestamp'),
                'request_id': metadata.get('request_id'),
                'stages_completed': metadata.get('stages_completed', [])
            },
            'component_health': metadata.get('component_health', {}),
            'performance_metrics': metadata.get('performance_metrics', {}),
            'fallback_mode': metadata.get('fallback_mode', False),
            'warnings': metadata.get('warnings', [])
        }
    
    def _calculate_quality_score(self, result: RecommendationResult) -> float:
        """计算推荐质量评分"""
        if not result.builds:
            return 0.0
        
        # 基于RAG置信度
        rag_score = result.rag_confidence * 40
        
        # 基于PoB2验证
        pob2_score = 30 if result.pob2_validated else 10
        
        # 基于构筑数量
        count_score = min(len(result.builds) / 3, 1.0) * 20
        
        # 基于生成时间（越快越好，但有合理范围）
        time_score = 10
        if result.generation_time_ms < 5000:  # 5秒内
            time_score = 10
        elif result.generation_time_ms < 10000:  # 10秒内
            time_score = 7
        else:
            time_score = 5
        
        return rag_score + pob2_score + count_score + time_score
    
    def _calculate_diversity_score(self, builds: List[Dict[str, Any]]) -> float:
        """计算推荐多样性评分"""
        if len(builds) <= 1:
            return 0.0
        
        # 检查不同维度的多样性
        unique_costs = len(set(b.get('estimated_cost', 0) for b in builds))
        unique_skills = len(set(b.get('main_skill', '') for b in builds))
        unique_ascendancies = len(set(b.get('ascendancy', {}).get('name', '') for b in builds))
        
        max_diversity = len(builds)
        diversity = (unique_costs + unique_skills + unique_ascendancies) / (3 * max_diversity)
        
        return min(diversity * 100, 100)
    
    def _calculate_budget_efficiency(self, builds: List[Dict[str, Any]]) -> float:
        """计算预算效率评分"""
        if not builds:
            return 0.0
        
        efficiency_scores = []
        
        for build in builds:
            cost = build.get('estimated_cost', 1)
            stats = build.get('stats', {})
            
            if cost > 0 and stats:
                dps = stats.get('offensive', {}).get('total_dps', {}).get('value', 0)
                ehp = stats.get('defensive', {}).get('effective_health_pool', {}).get('value', 0)
                
                # 简单的效率计算：(DPS + EHP/10) / cost
                if dps > 0 or ehp > 0:
                    efficiency = (dps + ehp / 10) / cost
                    efficiency_scores.append(efficiency)
        
        if efficiency_scores:
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)
            # 标准化到0-100分
            return min(avg_efficiency / 100000, 100)
        
        return 50  # 默认分数