"""
PoE2构筑生成器 - 智能构筑生成和优化

这个模块负责：
1. 基于用户需求生成构筑配置
2. 应用构筑优化策略
3. 生成PoB2兼容的构筑数据
4. 提供构筑模板和变种管理
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple

from ..models.build import PoE2Build, PoE2BuildGoal, PoE2BuildStats, PoE2DamageType
from ..models.characters import PoE2CharacterClass, PoE2Ascendancy
from ..models.skills import PoE2Skill


logger = logging.getLogger(__name__)


class BuildComplexity(Enum):
    """构筑复杂度级别"""
    BEGINNER = "beginner"      # 新手友好
    INTERMEDIATE = "intermediate"  # 中级玩家
    ADVANCED = "advanced"      # 高级玩家
    EXPERT = "expert"         # 专家级


class BuildArchetype(Enum):
    """构筑原型"""
    PURE_DPS = "pure_dps"           # 纯输出
    TANK = "tank"                   # 坦克型
    BALANCED = "balanced"           # 平衡型
    SPEED_FARMER = "speed_farmer"   # 速刷型
    BOSS_KILLER = "boss_killer"     # 击杀Boss型
    LEAGUE_STARTER = "league_starter"  # 开荒型


@dataclass
class BuildTemplate:
    """构筑模板"""
    name: str
    archetype: BuildArchetype
    character_class: PoE2CharacterClass
    ascendancy: Optional[PoE2Ascendancy]
    complexity: BuildComplexity
    
    # 核心配置
    main_damage_type: PoE2DamageType
    primary_skills: List[str]
    key_support_gems: List[str]
    essential_items: List[str]
    passive_keystones: List[str]
    
    # 统计目标
    target_dps: float
    target_ehp: float
    min_resistances: Dict[str, int]
    
    # 预算信息
    budget_range: Tuple[float, float]  # (min, max) in divine orbs
    
    # 特性标签
    tags: Set[str]
    notes: Optional[str] = None


@dataclass
class GenerationConstraints:
    """构筑生成约束条件"""
    max_budget: Optional[float] = None
    min_dps: Optional[float] = None
    min_ehp: Optional[float] = None
    required_resistances: Optional[Dict[str, int]] = None
    forbidden_items: Optional[List[str]] = None
    preferred_damage_types: Optional[List[PoE2DamageType]] = None
    complexity_limit: Optional[BuildComplexity] = None


class PoE2BuildGenerator:
    """
    PoE2构筑生成器
    
    智能生成满足特定需求的构筑配置
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化构筑生成器
        
        Args:
            config: 生成器配置
        """
        self.config = config or {}
        self._templates = {}
        self._skill_database = {}
        self._item_database = {}
        
        # 初始化构筑模板
        self._initialize_templates()
        logger.info("PoE2BuildGenerator 初始化完成")
    
    def _initialize_templates(self):
        """初始化构筑模板库"""
        # Witch模板
        self._templates[PoE2CharacterClass.WITCH] = [
            BuildTemplate(
                name="Elemental Devastation",
                archetype=BuildArchetype.PURE_DPS,
                character_class=PoE2CharacterClass.WITCH,
                ascendancy=None,  # 可以是任何升华
                complexity=BuildComplexity.INTERMEDIATE,
                main_damage_type=PoE2DamageType.FIRE,
                primary_skills=["Fireball", "Infernal Bolt"],
                key_support_gems=["Fire Penetration", "Spell Echo", "Elemental Focus"],
                essential_items=["High-Tier Wand", "Life/ES Hybrid Gear"],
                passive_keystones=["Elemental Overload"],
                target_dps=800000,
                target_ehp=6500,
                min_resistances={"fire": 75, "cold": 75, "lightning": 75},
                budget_range=(8.0, 20.0),
                tags={"caster", "fire", "aoe", "elemental"}
            ),
            BuildTemplate(
                name="Energy Shield Tank",
                archetype=BuildArchetype.TANK,
                character_class=PoE2CharacterClass.WITCH,
                ascendancy=None,
                complexity=BuildComplexity.ADVANCED,
                main_damage_type=PoE2DamageType.LIGHTNING,
                primary_skills=["Arc", "Lightning Bolt"],
                key_support_gems=["Energy Shield Leech", "Faster Casting", "Lightning Penetration"],
                essential_items=["High ES Chest", "ES Recovery Items"],
                passive_keystones=["Ghost Reaver", "Zealot's Oath"],
                target_dps=600000,
                target_ehp=12000,
                min_resistances={"fire": 75, "cold": 75, "lightning": 78},
                budget_range=(15.0, 40.0),
                tags={"caster", "tank", "energy_shield", "lightning"}
            )
        ]
        
        # Ranger模板
        self._templates[PoE2CharacterClass.RANGER] = [
            BuildTemplate(
                name="Bow Precision Strike",
                archetype=BuildArchetype.BOSS_KILLER,
                character_class=PoE2CharacterClass.RANGER,
                ascendancy=None,
                complexity=BuildComplexity.INTERMEDIATE,
                main_damage_type=PoE2DamageType.PHYSICAL,
                primary_skills=["Explosive Shot", "Gas Arrow"],
                key_support_gems=["Deadly Ailments", "Void Manipulation", "Chance to Poison"],
                essential_items=["High DPS Bow", "Quiver with DoT Multi"],
                passive_keystones=["Perfect Agony"],
                target_dps=1200000,
                target_ehp=5500,
                min_resistances={"fire": 75, "cold": 75, "lightning": 75},
                budget_range=(12.0, 30.0),
                tags={"bow", "physical", "poison", "projectile"}
            ),
            BuildTemplate(
                name="Speed Farmer",
                archetype=BuildArchetype.SPEED_FARMER,
                character_class=PoE2CharacterClass.RANGER,
                ascendancy=None,
                complexity=BuildComplexity.BEGINNER,
                main_damage_type=PoE2DamageType.PHYSICAL,
                primary_skills=["Lightning Arrow", "Barrage"],
                key_support_gems=["Added Lightning", "Pierce", "Multiple Projectiles"],
                essential_items=["Fast Attack Speed Bow", "Movement Speed Boots"],
                passive_keystones=["Point Blank"],
                target_dps=400000,
                target_ehp=4500,
                min_resistances={"fire": 75, "cold": 75, "lightning": 75},
                budget_range=(3.0, 12.0),
                tags={"bow", "speed", "clear", "lightning"}
            )
        ]
        
        # Warrior模板
        self._templates[PoE2CharacterClass.WARRIOR] = [
            BuildTemplate(
                name="Slam Powerhouse",
                archetype=BuildArchetype.BOSS_KILLER,
                character_class=PoE2CharacterClass.WARRIOR,
                ascendancy=None,
                complexity=BuildComplexity.ADVANCED,
                main_damage_type=PoE2DamageType.PHYSICAL,
                primary_skills=["Earthquake", "Ground Slam"],
                key_support_gems=["Melee Physical Damage", "Concentrated Effect", "Brutal Force"],
                essential_items=["Two-Handed Mace/Axe", "High Armor Gear"],
                passive_keystones=["Resolute Technique"],
                target_dps=1000000,
                target_ehp=8500,
                min_resistances={"fire": 76, "cold": 76, "lightning": 76},
                budget_range=(10.0, 25.0),
                tags={"melee", "physical", "slam", "aoe"}
            )
        ]
        
        # 为其他职业添加默认模板
        for character_class in PoE2CharacterClass:
            if character_class not in self._templates:
                self._templates[character_class] = [
                    BuildTemplate(
                        name=f"Generic {character_class.value} Build",
                        archetype=BuildArchetype.BALANCED,
                        character_class=character_class,
                        ascendancy=None,
                        complexity=BuildComplexity.INTERMEDIATE,
                        main_damage_type=PoE2DamageType.PHYSICAL,
                        primary_skills=["Basic Attack"],
                        key_support_gems=["Generic Support"],
                        essential_items=["Basic Weapon"],
                        passive_keystones=[],
                        target_dps=500000,
                        target_ehp=6000,
                        min_resistances={"fire": 75, "cold": 75, "lightning": 75},
                        budget_range=(5.0, 15.0),
                        tags={character_class.value.lower(), "generic"}
                    )
                ]
    
    async def generate_builds(self, 
                            character_class: PoE2CharacterClass,
                            build_goal: PoE2BuildGoal,
                            constraints: GenerationConstraints,
                            count: int = 3) -> List[PoE2Build]:
        """
        生成构筑
        
        Args:
            character_class: 角色职业
            build_goal: 构筑目标
            constraints: 生成约束
            count: 生成数量
            
        Returns:
            生成的构筑列表
        """
        logger.info(f"生成构筑: {character_class.value}, 目标: {build_goal.value}, 数量: {count}")
        
        try:
            # 获取合适的模板
            suitable_templates = self._find_suitable_templates(
                character_class, build_goal, constraints
            )
            
            if not suitable_templates:
                logger.warning(f"未找到适合的模板: {character_class.value}, {build_goal.value}")
                suitable_templates = self._templates.get(character_class, [])
            
            generated_builds = []
            
            for i in range(count):
                template = self._select_template(suitable_templates, i)
                if template:
                    build = await self._generate_build_from_template(template, constraints)
                    if build:
                        generated_builds.append(build)
            
            logger.info(f"构筑生成完成: {len(generated_builds)} 个")
            return generated_builds
            
        except Exception as e:
            logger.error(f"构筑生成失败: {e}")
            return []
    
    def _find_suitable_templates(self, 
                               character_class: PoE2CharacterClass,
                               build_goal: PoE2BuildGoal,
                               constraints: GenerationConstraints) -> List[BuildTemplate]:
        """查找适合的构筑模板"""
        templates = self._templates.get(character_class, [])
        suitable = []
        
        for template in templates:
            # 检查目标匹配
            if not self._template_matches_goal(template, build_goal):
                continue
            
            # 检查预算约束
            if constraints.max_budget:
                if template.budget_range[0] > constraints.max_budget:
                    continue
            
            # 检查复杂度约束
            if constraints.complexity_limit:
                template_complexity = self._get_complexity_level(template.complexity)
                constraint_complexity = self._get_complexity_level(constraints.complexity_limit)
                if template_complexity > constraint_complexity:
                    continue
            
            # 检查伤害类型偏好
            if constraints.preferred_damage_types:
                if template.main_damage_type not in constraints.preferred_damage_types:
                    continue
            
            suitable.append(template)
        
        return suitable
    
    def _template_matches_goal(self, template: BuildTemplate, goal: PoE2BuildGoal) -> bool:
        """检查模板是否匹配构筑目标"""
        archetype_goal_mapping = {
            BuildArchetype.BOSS_KILLER: {PoE2BuildGoal.BOSS_KILLING, PoE2BuildGoal.ENDGAME_CONTENT},
            BuildArchetype.SPEED_FARMER: {PoE2BuildGoal.CLEAR_SPEED},
            BuildArchetype.LEAGUE_STARTER: {PoE2BuildGoal.LEAGUE_START, PoE2BuildGoal.BUDGET_FRIENDLY},
            BuildArchetype.BALANCED: {PoE2BuildGoal.ENDGAME_CONTENT},
            BuildArchetype.TANK: {PoE2BuildGoal.ENDGAME_CONTENT, PoE2BuildGoal.BOSS_KILLING},
            BuildArchetype.PURE_DPS: {PoE2BuildGoal.BOSS_KILLING, PoE2BuildGoal.CLEAR_SPEED}
        }
        
        matching_goals = archetype_goal_mapping.get(template.archetype, set())
        return goal in matching_goals or len(matching_goals) == 0
    
    def _get_complexity_level(self, complexity: BuildComplexity) -> int:
        """获取复杂度数值级别"""
        levels = {
            BuildComplexity.BEGINNER: 1,
            BuildComplexity.INTERMEDIATE: 2,
            BuildComplexity.ADVANCED: 3,
            BuildComplexity.EXPERT: 4
        }
        return levels.get(complexity, 2)
    
    def _select_template(self, templates: List[BuildTemplate], index: int) -> Optional[BuildTemplate]:
        """选择模板（带随机性）"""
        if not templates:
            return None
        
        # 使用索引选择基础模板，添加随机性避免重复
        base_index = index % len(templates)
        if len(templates) > 1 and random.random() < 0.3:  # 30%概率选择不同模板
            base_index = random.randint(0, len(templates) - 1)
        
        return templates[base_index]
    
    async def _generate_build_from_template(self, 
                                          template: BuildTemplate,
                                          constraints: GenerationConstraints) -> Optional[PoE2Build]:
        """从模板生成具体构筑"""
        try:
            # 生成变种名称
            variant_suffix = self._generate_variant_suffix(template)
            build_name = f"{template.name} {variant_suffix}"
            
            # 计算目标等级
            target_level = self._calculate_target_level(template, constraints)
            
            # 生成统计数据
            stats = self._generate_build_stats(template, constraints)
            
            # 计算预算
            estimated_cost = self._calculate_build_cost(template, constraints)
            
            # 选择技能组合
            skill_gems = self._select_skill_gems(template, constraints)
            
            # 构建完整构筑
            build = PoE2Build(
                name=build_name,
                character_class=template.character_class,
                ascendancy=template.ascendancy,
                level=target_level,
                stats=stats,
                estimated_cost=estimated_cost,
                currency_type="divine",
                goal=self._template_to_build_goal(template),
                main_skill_gem=skill_gems['main'],
                support_gems=skill_gems['supports'],
                key_items=template.essential_items.copy(),
                passive_keystones=template.passive_keystones.copy(),
                notes=f"Generated from {template.name} template. Complexity: {template.complexity.value}"
            )
            
            # 验证构筑
            if build.validate():
                logger.debug(f"构筑生成成功: {build_name}")
                return build
            else:
                logger.warning(f"构筑验证失败: {build_name}")
                return None
                
        except Exception as e:
            logger.error(f"从模板生成构筑失败: {e}")
            return None
    
    def _generate_variant_suffix(self, template: BuildTemplate) -> str:
        """生成变种后缀"""
        suffixes = [
            "Variant", "Modified", "Enhanced", "Optimized", 
            "Custom", "Adapted", "Improved", "Refined"
        ]
        return random.choice(suffixes)
    
    def _calculate_target_level(self, template: BuildTemplate, constraints: GenerationConstraints) -> int:
        """计算目标等级"""
        # 基础等级根据复杂度确定
        base_levels = {
            BuildComplexity.BEGINNER: 85,
            BuildComplexity.INTERMEDIATE: 90,
            BuildComplexity.ADVANCED: 95,
            BuildComplexity.EXPERT: 98
        }
        
        base_level = base_levels.get(template.complexity, 90)
        
        # 添加随机变化
        variation = random.randint(-3, +5)
        target_level = max(75, min(100, base_level + variation))
        
        return target_level
    
    def _generate_build_stats(self, template: BuildTemplate, constraints: GenerationConstraints) -> PoE2BuildStats:
        """生成构筑统计数据"""
        # 基础统计
        base_dps = template.target_dps
        base_ehp = template.target_ehp
        
        # 应用约束调整
        if constraints.min_dps and base_dps < constraints.min_dps:
            base_dps = constraints.min_dps
        
        if constraints.min_ehp and base_ehp < constraints.min_ehp:
            base_ehp = constraints.min_ehp
        
        # 添加随机变化
        dps_variation = random.uniform(0.85, 1.15)
        ehp_variation = random.uniform(0.90, 1.10)
        
        final_dps = base_dps * dps_variation
        final_ehp = base_ehp * ehp_variation
        
        # 抗性处理
        resistances = template.min_resistances.copy()
        if constraints.required_resistances:
            for res_type, min_value in constraints.required_resistances.items():
                resistances[res_type] = max(resistances.get(res_type, 0), min_value)
        
        # 生成其他统计数据
        stats = PoE2BuildStats(
            total_dps=final_dps,
            effective_health_pool=final_ehp,
            fire_resistance=resistances.get("fire", 75),
            cold_resistance=resistances.get("cold", 75),
            lightning_resistance=resistances.get("lightning", 75),
            chaos_resistance=resistances.get("chaos", -30),
            life=self._calculate_life_from_ehp(final_ehp, template),
            energy_shield=self._calculate_es_from_ehp(final_ehp, template),
            critical_strike_chance=self._generate_crit_stats(template)[0],
            critical_strike_multiplier=self._generate_crit_stats(template)[1],
            movement_speed=self._generate_movement_speed(template)
        )
        
        return stats
    
    def _calculate_life_from_ehp(self, ehp: float, template: BuildTemplate) -> float:
        """从EHP计算生命值"""
        if "energy_shield" in template.tags or "tank" in template.tags:
            return ehp * 0.4  # ES构筑生命较少
        else:
            return ehp * 0.7  # 生命构筑
    
    def _calculate_es_from_ehp(self, ehp: float, template: BuildTemplate) -> float:
        """从EHP计算护盾值"""
        if "energy_shield" in template.tags:
            return ehp * 0.6  # ES构筑护盾较多
        else:
            return 0.0  # 生命构筑无护盾
    
    def _generate_crit_stats(self, template: BuildTemplate) -> Tuple[float, float]:
        """生成暴击统计"""
        if template.main_damage_type in [PoE2DamageType.PHYSICAL, PoE2DamageType.FIRE]:
            # 物理和火焰构筑通常有较高暴击
            crit_chance = random.uniform(25, 45)
            crit_multi = random.uniform(250, 350)
        else:
            # 其他伤害类型
            crit_chance = random.uniform(15, 35)
            crit_multi = random.uniform(200, 300)
        
        return crit_chance, crit_multi
    
    def _generate_movement_speed(self, template: BuildTemplate) -> float:
        """生成移动速度"""
        if template.archetype == BuildArchetype.SPEED_FARMER:
            return random.uniform(120, 150)
        elif template.archetype == BuildArchetype.TANK:
            return random.uniform(100, 120)
        else:
            return random.uniform(105, 135)
    
    def _calculate_build_cost(self, template: BuildTemplate, constraints: GenerationConstraints) -> float:
        """计算构筑成本"""
        min_cost, max_cost = template.budget_range
        
        # 应用约束
        if constraints.max_budget:
            max_cost = min(max_cost, constraints.max_budget)
        
        # 在范围内随机选择
        if min_cost <= max_cost:
            return random.uniform(min_cost, max_cost)
        else:
            return min_cost
    
    def _select_skill_gems(self, template: BuildTemplate, constraints: GenerationConstraints) -> Dict[str, Any]:
        """选择技能宝石组合"""
        # 主技能选择
        main_skill = random.choice(template.primary_skills)
        
        # 辅助宝石选择
        support_count = random.randint(3, min(6, len(template.key_support_gems)))
        selected_supports = random.sample(template.key_support_gems, support_count)
        
        return {
            'main': main_skill,
            'supports': selected_supports
        }
    
    def _template_to_build_goal(self, template: BuildTemplate) -> PoE2BuildGoal:
        """将模板原型转换为构筑目标"""
        archetype_to_goal = {
            BuildArchetype.BOSS_KILLER: PoE2BuildGoal.BOSS_KILLING,
            BuildArchetype.SPEED_FARMER: PoE2BuildGoal.CLEAR_SPEED,
            BuildArchetype.LEAGUE_STARTER: PoE2BuildGoal.LEAGUE_START,
            BuildArchetype.TANK: PoE2BuildGoal.ENDGAME_CONTENT,
            BuildArchetype.PURE_DPS: PoE2BuildGoal.BOSS_KILLING,
            BuildArchetype.BALANCED: PoE2BuildGoal.ENDGAME_CONTENT
        }
        
        return archetype_to_goal.get(template.archetype, PoE2BuildGoal.ENDGAME_CONTENT)
    
    async def optimize_build(self, build: PoE2Build, constraints: GenerationConstraints) -> PoE2Build:
        """
        优化现有构筑
        
        Args:
            build: 要优化的构筑
            constraints: 优化约束
            
        Returns:
            优化后的构筑
        """
        try:
            logger.info(f"优化构筑: {build.name}")
            
            optimized_build = PoE2Build(
                name=f"Optimized {build.name}",
                character_class=build.character_class,
                ascendancy=build.ascendancy,
                level=build.level,
                stats=build.stats,
                estimated_cost=build.estimated_cost,
                currency_type=build.currency_type,
                goal=build.goal,
                main_skill_gem=build.main_skill_gem,
                support_gems=build.support_gems[:] if build.support_gems else [],
                key_items=build.key_items[:] if build.key_items else [],
                passive_keystones=build.passive_keystones[:] if build.passive_keystones else [],
                notes=f"Optimized version of {build.name}"
            )
            
            # 应用优化策略
            optimized_build = await self._apply_optimization_strategies(optimized_build, constraints)
            
            logger.info(f"构筑优化完成: {optimized_build.name}")
            return optimized_build
            
        except Exception as e:
            logger.error(f"构筑优化失败: {e}")
            return build  # 返回原构筑
    
    async def _apply_optimization_strategies(self, build: PoE2Build, constraints: GenerationConstraints) -> PoE2Build:
        """应用优化策略"""
        # 策略1: DPS优化
        if constraints.min_dps and build.stats and build.stats.total_dps < constraints.min_dps:
            build = self._optimize_dps(build, constraints.min_dps)
        
        # 策略2: 生存性优化
        if constraints.min_ehp and build.stats and build.stats.effective_health_pool < constraints.min_ehp:
            build = self._optimize_survivability(build, constraints.min_ehp)
        
        # 策略3: 预算优化
        if constraints.max_budget and build.estimated_cost and build.estimated_cost > constraints.max_budget:
            build = self._optimize_budget(build, constraints.max_budget)
        
        return build
    
    def _optimize_dps(self, build: PoE2Build, target_dps: float) -> PoE2Build:
        """优化DPS"""
        if not build.stats:
            return build
        
        # 提升DPS（简单的比例提升）
        dps_multiplier = target_dps / build.stats.total_dps
        build.stats.total_dps = target_dps
        
        # 调整相关统计
        build.stats.critical_strike_chance = min(95, build.stats.critical_strike_chance * 1.1)
        build.stats.critical_strike_multiplier = min(500, build.stats.critical_strike_multiplier * 1.05)
        
        # 添加优化笔记
        if build.notes:
            build.notes += f" | DPS optimized: {dps_multiplier:.2f}x multiplier applied"
        
        return build
    
    def _optimize_survivability(self, build: PoE2Build, target_ehp: float) -> PoE2Build:
        """优化生存性"""
        if not build.stats:
            return build
        
        # 提升EHP
        ehp_multiplier = target_ehp / build.stats.effective_health_pool
        build.stats.effective_health_pool = target_ehp
        
        # 按比例调整生命和护盾
        build.stats.life *= ehp_multiplier
        build.stats.energy_shield *= ehp_multiplier
        
        # 略微提升抗性
        build.stats.fire_resistance = min(80, build.stats.fire_resistance + 2)
        build.stats.cold_resistance = min(80, build.stats.cold_resistance + 2)
        build.stats.lightning_resistance = min(80, build.stats.lightning_resistance + 2)
        
        if build.notes:
            build.notes += f" | EHP optimized: {ehp_multiplier:.2f}x multiplier applied"
        
        return build
    
    def _optimize_budget(self, build: PoE2Build, max_budget: float) -> PoE2Build:
        """优化预算"""
        if not build.estimated_cost:
            return build
        
        # 降低预算
        budget_reduction = build.estimated_cost / max_budget
        build.estimated_cost = max_budget
        
        # 相应降低性能（现实中需要更复杂的逻辑）
        if build.stats and budget_reduction > 1.1:
            reduction_factor = 1.0 / (budget_reduction * 0.8)  # 性能降低幅度小于预算降低幅度
            build.stats.total_dps *= reduction_factor
            build.stats.effective_health_pool *= (reduction_factor + 1.0) / 2  # EHP降低更少
        
        if build.notes:
            build.notes += f" | Budget optimized: reduced to {max_budget} divine"
        
        return build
    
    def get_template_info(self, character_class: PoE2CharacterClass) -> List[Dict[str, Any]]:
        """获取指定职业的模板信息"""
        templates = self._templates.get(character_class, [])
        
        return [
            {
                'name': t.name,
                'archetype': t.archetype.value,
                'complexity': t.complexity.value,
                'main_damage_type': t.main_damage_type.value,
                'target_dps': t.target_dps,
                'target_ehp': t.target_ehp,
                'budget_range': t.budget_range,
                'tags': list(t.tags)
            }
            for t in templates
        ]
    
    def get_available_archetypes(self) -> List[str]:
        """获取所有可用的构筑原型"""
        return [archetype.value for archetype in BuildArchetype]
    
    def get_complexity_levels(self) -> List[str]:
        """获取所有复杂度级别"""
        return [complexity.value for complexity in BuildComplexity]