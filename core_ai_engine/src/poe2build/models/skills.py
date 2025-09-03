"""PoE2技能数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class PoE2SkillType(Enum):
    """PoE2技能类型枚举"""
    ACTIVE = "active"           # 主动技能宝石
    SUPPORT = "support"         # 辅助宝石
    AURA = "aura"              # 光环技能
    CURSE = "curse"            # 诅咒技能
    MINION = "minion"          # 召唤物技能
    MOVEMENT = "movement"       # 移动技能
    UTILITY = "utility"        # 实用技能


class PoE2SkillCategory(Enum):
    """PoE2技能分类枚举"""
    # 攻击技能
    ATTACK = "attack"
    SPELL = "spell"
    # 元素系
    FIRE = "fire" 
    COLD = "cold"
    LIGHTNING = "lightning"
    # 物理系
    PHYSICAL = "physical"
    CHAOS = "chaos"
    # 特殊系
    MINION = "minion"
    TOTEM = "totem"
    TRAP = "trap"
    MINE = "mine"
    # 辅助系
    AURA = "aura"
    CURSE = "curse"
    MOVEMENT = "movement"


class PoE2GemColor(Enum):
    """PoE2技能宝石颜色枚举"""
    RED = "red"        # 力量宝石
    GREEN = "green"    # 敏捷宝石  
    BLUE = "blue"      # 智力宝石
    WHITE = "white"    # 无色宝石


class PoE2SocketType(Enum):
    """PoE2插槽类型枚举"""
    ACTIVE = "active"     # 主动技能插槽
    SUPPORT = "support"   # 辅助技能插槽
    SPIRIT = "spirit"     # 灵魂插槽 (PoE2新增)


@dataclass
class PoE2SkillStats:
    """PoE2技能数值数据"""
    base_damage: float = 0.0
    damage_multiplier: float = 1.0
    cast_time: float = 0.0
    mana_cost: int = 0
    cooldown: float = 0.0
    critical_chance: float = 0.0
    # 伤害类型分布
    physical_damage_percent: float = 0.0
    fire_damage_percent: float = 0.0
    cold_damage_percent: float = 0.0
    lightning_damage_percent: float = 0.0
    chaos_damage_percent: float = 0.0
    # 额外属性
    area_of_effect: float = 0.0
    projectile_count: int = 1
    duration: float = 0.0
    range: float = 0.0
    
    def __post_init__(self):
        """验证技能数值"""
        if self.base_damage < 0:
            raise ValueError("Base damage cannot be negative")
        
        if self.damage_multiplier <= 0:
            raise ValueError("Damage multiplier must be positive")
        
        if self.cast_time < 0:
            raise ValueError("Cast time cannot be negative")
        
        if self.mana_cost < 0:
            raise ValueError("Mana cost cannot be negative")
        
        if self.cooldown < 0:
            raise ValueError("Cooldown cannot be negative")
        
        if not 0 <= self.critical_chance <= 100:
            raise ValueError("Critical chance must be between 0% and 100%")
        
        # 验证伤害类型百分比总和
        total_damage_percent = (
            self.physical_damage_percent +
            self.fire_damage_percent + 
            self.cold_damage_percent +
            self.lightning_damage_percent +
            self.chaos_damage_percent
        )
        
        if total_damage_percent > 100.1:  # 允许小的浮点误差
            raise ValueError(f"Total damage percentage {total_damage_percent}% cannot exceed 100%")
    
    def get_damage_types(self) -> List[str]:
        """获取技能的伤害类型列表"""
        damage_types = []
        if self.physical_damage_percent > 0:
            damage_types.append("physical")
        if self.fire_damage_percent > 0:
            damage_types.append("fire")
        if self.cold_damage_percent > 0:
            damage_types.append("cold") 
        if self.lightning_damage_percent > 0:
            damage_types.append("lightning")
        if self.chaos_damage_percent > 0:
            damage_types.append("chaos")
        return damage_types
    
    def get_primary_damage_type(self) -> str:
        """获取主要伤害类型"""
        damage_percentages = [
            ("physical", self.physical_damage_percent),
            ("fire", self.fire_damage_percent),
            ("cold", self.cold_damage_percent),
            ("lightning", self.lightning_damage_percent),
            ("chaos", self.chaos_damage_percent)
        ]
        return max(damage_percentages, key=lambda x: x[1])[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'base_damage': self.base_damage,
            'damage_multiplier': self.damage_multiplier,
            'cast_time': self.cast_time,
            'mana_cost': self.mana_cost,
            'cooldown': self.cooldown,
            'critical_chance': self.critical_chance,
            'damage_breakdown': {
                'physical': self.physical_damage_percent,
                'fire': self.fire_damage_percent,
                'cold': self.cold_damage_percent,
                'lightning': self.lightning_damage_percent,
                'chaos': self.chaos_damage_percent
            },
            'mechanics': {
                'area_of_effect': self.area_of_effect,
                'projectile_count': self.projectile_count,
                'duration': self.duration,
                'range': self.range
            }
        }


@dataclass
class PoE2SkillRequirements:
    """PoE2技能需求数据"""
    level: int = 1
    strength: int = 0
    dexterity: int = 0
    intelligence: int = 0
    
    def __post_init__(self):
        """验证技能需求"""
        if not 1 <= self.level <= 21:  # PoE2技能等级上限
            raise ValueError(f"Skill level {self.level} must be between 1 and 21")
        
        if any(attr < 0 for attr in [self.strength, self.dexterity, self.intelligence]):
            raise ValueError("Attribute requirements cannot be negative")
    
    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            'level': self.level,
            'strength': self.strength,
            'dexterity': self.dexterity,  
            'intelligence': self.intelligence
        }
    
    def meets_requirements(self, character_level: int,
                          character_str: int,
                          character_dex: int, 
                          character_int: int) -> bool:
        """检查是否满足技能需求"""
        return (character_level >= self.level and
                character_str >= self.strength and
                character_dex >= self.dexterity and
                character_int >= self.intelligence)


@dataclass
class PoE2Skill:
    """PoE2技能数据模型"""
    name: str
    skill_type: PoE2SkillType
    categories: List[PoE2SkillCategory]
    gem_color: PoE2GemColor
    level: int
    quality: int = 0
    requirements: Optional[PoE2SkillRequirements] = None
    stats: Optional[PoE2SkillStats] = None
    # 技能描述
    description: str = ""
    flavor_text: Optional[str] = None
    # 辅助宝石相关
    supported_skills: Optional[List[str]] = None  # 可以辅助的技能类型
    support_effects: Optional[List[str]] = None   # 辅助效果描述
    # PoE2特有属性
    spirit_cost: int = 0  # 灵魂消耗 (PoE2新机制)
    socket_type: PoE2SocketType = PoE2SocketType.ACTIVE
    # 元数据
    icon_url: Optional[str] = None
    wiki_url: Optional[str] = None
    
    def __post_init__(self):
        """验证技能数据"""
        if not self.name.strip():
            raise ValueError("Skill name cannot be empty")
        
        if not 1 <= self.level <= 21:
            raise ValueError(f"Skill level {self.level} must be between 1 and 21")
        
        if not 0 <= self.quality <= 23:  # PoE2品质上限
            raise ValueError(f"Skill quality {self.quality}% must be between 0% and 23%")
        
        if self.spirit_cost < 0:
            raise ValueError("Spirit cost cannot be negative")
        
        # 验证辅助宝石的相关字段
        if self.skill_type == PoE2SkillType.SUPPORT:
            if not self.supported_skills:
                raise ValueError("Support gems must specify supported skills")
            if not self.support_effects:
                raise ValueError("Support gems must specify support effects")
        
        # 初始化默认需求
        if self.requirements is None:
            self.requirements = PoE2SkillRequirements(level=self.level)
        
        # 初始化列表字段
        if self.supported_skills is None:
            self.supported_skills = []
        if self.support_effects is None:
            self.support_effects = []
    
    def is_compatible_with(self, target_skill: 'PoE2Skill') -> bool:
        """检查是否可以辅助目标技能"""
        if self.skill_type != PoE2SkillType.SUPPORT:
            return False
        
        if target_skill.skill_type == PoE2SkillType.SUPPORT:
            return False  # 辅助宝石不能辅助辅助宝石
        
        # 检查是否在支持的技能类型列表中
        target_categories = [cat.value for cat in target_skill.categories]
        return any(supported in target_categories for supported in self.supported_skills)
    
    def get_effective_level(self) -> int:
        """获取有效等级（包含品质加成）"""
        if self.skill_type == PoE2SkillType.ACTIVE:
            # 主动技能：每5%品质+1等级
            quality_bonus = self.quality // 5
            return min(21, self.level + quality_bonus)
        return self.level
    
    def calculate_dps(self, character_stats: Optional[Dict[str, float]] = None) -> float:
        """计算技能DPS（简化版本）"""
        if not self.stats:
            return 0.0
        
        base_dps = self.stats.base_damage * self.stats.damage_multiplier
        
        if self.stats.cast_time > 0:
            base_dps = base_dps / self.stats.cast_time
        
        # 如果提供角色属性，可以进行更复杂的计算
        if character_stats:
            # 这里可以加入角色属性的影响
            damage_bonus = character_stats.get('damage_bonus', 1.0)
            attack_speed_bonus = character_stats.get('attack_speed_bonus', 1.0)
            base_dps *= damage_bonus * attack_speed_bonus
        
        return base_dps
    
    def get_mana_per_second(self) -> float:
        """计算每秒法力消耗"""
        if not self.stats or self.stats.mana_cost == 0:
            return 0.0
        
        if self.stats.cast_time > 0:
            return self.stats.mana_cost / self.stats.cast_time
        
        # 瞬发技能按1秒计算
        return self.stats.mana_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'skill_type': self.skill_type.value,
            'categories': [cat.value for cat in self.categories],
            'gem_color': self.gem_color.value,
            'level': self.level,
            'effective_level': self.get_effective_level(),
            'quality': self.quality,
            'requirements': self.requirements.to_dict() if self.requirements else None,
            'stats': self.stats.to_dict() if self.stats else None,
            'description': self.description,
            'flavor_text': self.flavor_text,
            'support_info': {
                'supported_skills': self.supported_skills,
                'support_effects': self.support_effects
            } if self.skill_type == PoE2SkillType.SUPPORT else None,
            'poe2_mechanics': {
                'spirit_cost': self.spirit_cost,
                'socket_type': self.socket_type.value
            },
            'metadata': {
                'icon_url': self.icon_url,
                'wiki_url': self.wiki_url
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2Skill':
        """从字典创建技能实例"""
        categories = [PoE2SkillCategory(cat) for cat in data.get('categories', [])]
        
        requirements = None
        if data.get('requirements'):
            requirements = PoE2SkillRequirements(**data['requirements'])
        
        stats = None
        if data.get('stats'):
            stats_data = data['stats']
            # 从嵌套字典提取数据
            damage_breakdown = stats_data.get('damage_breakdown', {})
            mechanics = stats_data.get('mechanics', {})
            
            stats = PoE2SkillStats(
                base_damage=stats_data.get('base_damage', 0),
                damage_multiplier=stats_data.get('damage_multiplier', 1.0),
                cast_time=stats_data.get('cast_time', 0),
                mana_cost=stats_data.get('mana_cost', 0),
                cooldown=stats_data.get('cooldown', 0),
                critical_chance=stats_data.get('critical_chance', 0),
                physical_damage_percent=damage_breakdown.get('physical', 0),
                fire_damage_percent=damage_breakdown.get('fire', 0),
                cold_damage_percent=damage_breakdown.get('cold', 0),
                lightning_damage_percent=damage_breakdown.get('lightning', 0),
                chaos_damage_percent=damage_breakdown.get('chaos', 0),
                area_of_effect=mechanics.get('area_of_effect', 0),
                projectile_count=mechanics.get('projectile_count', 1),
                duration=mechanics.get('duration', 0),
                range=mechanics.get('range', 0)
            )
        
        support_info = data.get('support_info', {})
        poe2_mechanics = data.get('poe2_mechanics', {})
        metadata = data.get('metadata', {})
        
        return cls(
            name=data['name'],
            skill_type=PoE2SkillType(data['skill_type']),
            categories=categories,
            gem_color=PoE2GemColor(data['gem_color']),
            level=data['level'],
            quality=data.get('quality', 0),
            requirements=requirements,
            stats=stats,
            description=data.get('description', ''),
            flavor_text=data.get('flavor_text'),
            supported_skills=support_info.get('supported_skills'),
            support_effects=support_info.get('support_effects'),
            spirit_cost=poe2_mechanics.get('spirit_cost', 0),
            socket_type=PoE2SocketType(poe2_mechanics.get('socket_type', 'active')),
            icon_url=metadata.get('icon_url'),
            wiki_url=metadata.get('wiki_url')
        )


@dataclass
class PoE2SkillSetup:
    """PoE2技能配置数据模型"""
    main_skill: PoE2Skill
    support_gems: List[PoE2Skill]
    name: Optional[str] = None
    
    def __post_init__(self):
        """验证技能配置"""
        if not self.name:
            self.name = f"{self.main_skill.name} Setup"
        
        # 验证所有辅助宝石都能辅助主技能
        for support in self.support_gems:
            if not support.is_compatible_with(self.main_skill):
                raise ValueError(f"Support gem '{support.name}' is not compatible with '{self.main_skill.name}'")
        
        # PoE2最多6个辅助宝石
        if len(self.support_gems) > 6:
            raise ValueError("PoE2 supports maximum 6 support gems per active skill")
    
    def calculate_total_dps(self, character_stats: Optional[Dict[str, float]] = None) -> float:
        """计算技能配置的总DPS"""
        base_dps = self.main_skill.calculate_dps(character_stats)
        
        # 应用辅助宝石的加成（简化计算）
        total_multiplier = 1.0
        for support in self.support_gems:
            if support.stats and support.stats.damage_multiplier:
                total_multiplier *= support.stats.damage_multiplier
        
        return base_dps * total_multiplier
    
    def get_total_mana_cost(self) -> int:
        """计算总法力消耗"""
        if not self.main_skill.stats:
            return 0
        
        base_cost = self.main_skill.stats.mana_cost
        
        # 辅助宝石通常增加法力消耗
        mana_multiplier = 1.0
        for support in self.support_gems:
            # 简化：每个辅助宝石增加130%法力消耗
            mana_multiplier *= 1.3
        
        return int(base_cost * mana_multiplier)
    
    def get_total_spirit_cost(self) -> int:
        """计算总灵魂消耗"""
        total_spirit = self.main_skill.spirit_cost
        for support in self.support_gems:
            total_spirit += support.spirit_cost
        return total_spirit
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'main_skill': self.main_skill.to_dict(),
            'support_gems': [support.to_dict() for support in self.support_gems],
            'calculated_stats': {
                'total_dps': self.calculate_total_dps(),
                'total_mana_cost': self.get_total_mana_cost(),
                'total_spirit_cost': self.get_total_spirit_cost(),
                'support_count': len(self.support_gems)
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2SkillSetup':
        """从字典创建技能配置"""
        main_skill = PoE2Skill.from_dict(data['main_skill'])
        support_gems = [PoE2Skill.from_dict(support_data) 
                       for support_data in data.get('support_gems', [])]
        
        return cls(
            main_skill=main_skill,
            support_gems=support_gems,
            name=data.get('name')
        )


# 技能相关工具函数
def filter_skills_by_type(skills: List[PoE2Skill], 
                         skill_type: PoE2SkillType) -> List[PoE2Skill]:
    """按技能类型过滤技能"""
    return [skill for skill in skills if skill.skill_type == skill_type]


def filter_skills_by_category(skills: List[PoE2Skill], 
                             category: PoE2SkillCategory) -> List[PoE2Skill]:
    """按技能分类过滤技能"""
    return [skill for skill in skills if category in skill.categories]


def filter_skills_by_color(skills: List[PoE2Skill], 
                          color: PoE2GemColor) -> List[PoE2Skill]:
    """按宝石颜色过滤技能"""
    return [skill for skill in skills if skill.gem_color == color]


def find_compatible_supports(main_skill: PoE2Skill, 
                           available_supports: List[PoE2Skill]) -> List[PoE2Skill]:
    """查找与主技能兼容的辅助宝石"""
    compatible = []
    for support in available_supports:
        if support.is_compatible_with(main_skill):
            compatible.append(support)
    return compatible


def sort_skills_by_dps(skills: List[PoE2Skill], 
                      character_stats: Optional[Dict[str, float]] = None,
                      descending: bool = True) -> List[PoE2Skill]:
    """按DPS排序技能"""
    return sorted(skills, 
                 key=lambda x: x.calculate_dps(character_stats), 
                 reverse=descending)


def create_optimal_skill_setup(main_skill: PoE2Skill,
                              available_supports: List[PoE2Skill],
                              max_supports: int = 6) -> PoE2SkillSetup:
    """创建最优技能配置"""
    compatible_supports = find_compatible_supports(main_skill, available_supports)
    
    # 简单策略：按伤害倍数选择最佳辅助宝石
    support_scores = []
    for support in compatible_supports:
        score = support.stats.damage_multiplier if support.stats else 1.0
        support_scores.append((support, score))
    
    # 按得分排序并选择前N个
    support_scores.sort(key=lambda x: x[1], reverse=True)
    selected_supports = [support for support, _ in support_scores[:max_supports]]
    
    return PoE2SkillSetup(
        main_skill=main_skill,
        support_gems=selected_supports,
        name=f"Optimized {main_skill.name} Setup"
    )