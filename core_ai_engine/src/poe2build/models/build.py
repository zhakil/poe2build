"""PoE2构筑数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from .characters import PoE2CharacterClass, PoE2Ascendancy


class PoE2BuildGoal(Enum):
    """PoE2构筑目标枚举"""
    CLEAR_SPEED = "clear_speed"
    BOSS_KILLING = "boss_killing" 
    ENDGAME_CONTENT = "endgame_content"
    LEAGUE_START = "league_start"
    BUDGET_FRIENDLY = "budget_friendly"


class PoE2DamageType(Enum):
    """PoE2伤害类型枚举"""
    PHYSICAL = "physical"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    CHAOS = "chaos"


@dataclass
class PoE2BuildStats:
    """PoE2构筑统计数据类"""
    total_dps: float
    effective_health_pool: float
    fire_resistance: int
    cold_resistance: int
    lightning_resistance: int
    chaos_resistance: int
    energy_shield: float = 0.0
    life: float = 0.0
    mana: float = 0.0
    # 额外统计数据
    critical_strike_chance: float = 0.0
    critical_strike_multiplier: float = 0.0
    attack_speed: float = 0.0
    cast_speed: float = 0.0
    movement_speed: float = 0.0
    block_chance: float = 0.0
    dodge_chance: float = 0.0
    # 伤害细分
    physical_dps: float = 0.0
    elemental_dps: float = 0.0
    chaos_dps: float = 0.0

    def __post_init__(self):
        """验证统计数据合理性"""
        # 验证抗性范围 (PoE2特有: -100% 到 +80%)
        resistances = [
            ('fire_resistance', self.fire_resistance),
            ('cold_resistance', self.cold_resistance), 
            ('lightning_resistance', self.lightning_resistance),
            ('chaos_resistance', self.chaos_resistance)
        ]
        
        for name, value in resistances:
            if not -100 <= value <= 80:
                raise ValueError(f"{name} {value}% must be between -100% and +80%")
        
        # 验证基础数值
        if self.total_dps < 0:
            raise ValueError("Total DPS cannot be negative")
        
        if self.effective_health_pool < 0:
            raise ValueError("Effective health pool cannot be negative")
        
        if self.life < 0:
            raise ValueError("Life cannot be negative")
        
        if self.energy_shield < 0:
            raise ValueError("Energy shield cannot be negative")
        
        # 验证百分比数值
        percentage_fields = [
            ('critical_strike_chance', self.critical_strike_chance),
            ('block_chance', self.block_chance),
            ('dodge_chance', self.dodge_chance)
        ]
        
        for name, value in percentage_fields:
            if not 0 <= value <= 100:
                raise ValueError(f"{name} {value}% must be between 0% and 100%")

    def get_total_resistance_percentage(self) -> float:
        """计算总抗性百分比 (不包含混沌抗性)"""
        return (self.fire_resistance + self.cold_resistance + self.lightning_resistance) / 3

    def is_resistance_capped(self) -> bool:
        """检查三抗是否都达到75% (PoE2推荐值)"""
        return (self.fire_resistance >= 75 and 
                self.cold_resistance >= 75 and 
                self.lightning_resistance >= 75)

    def get_ehp_breakdown(self) -> Dict[str, float]:
        """获取有效生命值细分"""
        return {
            'life': self.life,
            'energy_shield': self.energy_shield,
            'total_ehp': self.effective_health_pool
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_dps': self.total_dps,
            'effective_health_pool': self.effective_health_pool,
            'resistances': {
                'fire': self.fire_resistance,
                'cold': self.cold_resistance,
                'lightning': self.lightning_resistance,
                'chaos': self.chaos_resistance
            },
            'defenses': {
                'life': self.life,
                'energy_shield': self.energy_shield,
                'block_chance': self.block_chance,
                'dodge_chance': self.dodge_chance
            },
            'offense': {
                'physical_dps': self.physical_dps,
                'elemental_dps': self.elemental_dps,
                'chaos_dps': self.chaos_dps,
                'crit_chance': self.critical_strike_chance,
                'crit_multiplier': self.critical_strike_multiplier
            },
            'speed': {
                'attack_speed': self.attack_speed,
                'cast_speed': self.cast_speed,
                'movement_speed': self.movement_speed
            }
        }


@dataclass
class PoE2Build:
    """PoE2构筑数据模型主类"""
    name: str
    character_class: PoE2CharacterClass
    level: int
    ascendancy: Optional[PoE2Ascendancy] = None
    stats: Optional[PoE2BuildStats] = None
    estimated_cost: Optional[float] = None
    currency_type: str = "divine"
    goal: Optional[PoE2BuildGoal] = None
    notes: Optional[str] = None
    # 构筑组成部分
    main_skill_gem: Optional[str] = None
    support_gems: Optional[List[str]] = None
    key_items: Optional[List[str]] = None
    passive_keystones: Optional[List[str]] = None
    # 元数据
    created_by: Optional[str] = None
    source_url: Optional[str] = None
    league: str = "Standard"
    last_updated: Optional[str] = None
    # PoB2集成
    pob2_code: Optional[str] = None
    pob2_version: Optional[str] = None

    def __post_init__(self):
        """验证构筑数据完整性"""
        # 验证基础数据
        if not self.name.strip():
            raise ValueError("Build name cannot be empty")
        
        if not 1 <= self.level <= 100:
            raise ValueError(f"Level {self.level} must be between 1 and 100")
        
        # 验证升华与职业匹配
        if self.ascendancy:
            from .characters import ASCENDANCY_MAPPING
            valid_ascendancies = ASCENDANCY_MAPPING.get(self.character_class, [])
            if self.ascendancy not in valid_ascendancies:
                raise ValueError(f"Ascendancy {self.ascendancy.value} not valid for {self.character_class.value}")
        
        # 验证预算合理性
        if self.estimated_cost is not None and self.estimated_cost < 0:
            raise ValueError("Estimated cost cannot be negative")
        
        # 初始化列表字段
        if self.support_gems is None:
            self.support_gems = []
        if self.key_items is None:
            self.key_items = []
        if self.passive_keystones is None:
            self.passive_keystones = []

    def validate(self) -> bool:
        """验证构筑完整性"""
        try:
            # 基础验证
            if not self.name.strip():
                return False
            
            if not 1 <= self.level <= 100:
                return False
            
            # 检查主技能
            if not self.main_skill_gem:
                return False
            
            # 检查统计数据合理性
            if self.stats:
                if self.stats.total_dps <= 0:
                    return False
                    
                if self.stats.effective_health_pool <= 0:
                    return False
                
                # 检查抗性
                if not self.stats.is_resistance_capped():
                    # 警告但不失败
                    pass
            
            return True
            
        except Exception:
            return False

    def get_build_summary(self) -> Dict[str, Any]:
        """获取构筑摘要信息"""
        return {
            'name': self.name,
            'class': self.character_class.value,
            'ascendancy': self.ascendancy.value if self.ascendancy else None,
            'level': self.level,
            'main_skill': self.main_skill_gem,
            'goal': self.goal.value if self.goal else None,
            'estimated_cost': f"{self.estimated_cost} {self.currency_type}" if self.estimated_cost else "Unknown",
            'dps': self.stats.total_dps if self.stats else 0,
            'ehp': self.stats.effective_health_pool if self.stats else 0,
            'resistances_capped': self.stats.is_resistance_capped() if self.stats else False
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为完整字典"""
        return {
            'name': self.name,
            'character_class': self.character_class.value,
            'ascendancy': self.ascendancy.value if self.ascendancy else None,
            'level': self.level,
            'stats': self.stats.to_dict() if self.stats else None,
            'estimated_cost': self.estimated_cost,
            'currency_type': self.currency_type,
            'goal': self.goal.value if self.goal else None,
            'notes': self.notes,
            'build_components': {
                'main_skill_gem': self.main_skill_gem,
                'support_gems': self.support_gems,
                'key_items': self.key_items,
                'passive_keystones': self.passive_keystones
            },
            'metadata': {
                'created_by': self.created_by,
                'source_url': self.source_url,
                'league': self.league,
                'last_updated': self.last_updated
            },
            'pob2_integration': {
                'pob2_code': self.pob2_code,
                'pob2_version': self.pob2_version
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2Build':
        """从字典创建构筑实例"""
        # 解析角色职业和升华
        character_class = PoE2CharacterClass(data['character_class'])
        ascendancy = PoE2Ascendancy(data['ascendancy']) if data.get('ascendancy') else None
        
        # 解析目标
        goal = PoE2BuildGoal(data['goal']) if data.get('goal') else None
        
        # 解析统计数据
        stats = None
        if data.get('stats'):
            stats_data = data['stats']
            # 从嵌套字典中提取数据
            resistances = stats_data.get('resistances', {})
            defenses = stats_data.get('defenses', {})
            offense = stats_data.get('offense', {})
            speed = stats_data.get('speed', {})
            
            stats = PoE2BuildStats(
                total_dps=stats_data.get('total_dps', 0),
                effective_health_pool=stats_data.get('effective_health_pool', 0),
                fire_resistance=resistances.get('fire', 0),
                cold_resistance=resistances.get('cold', 0),
                lightning_resistance=resistances.get('lightning', 0),
                chaos_resistance=resistances.get('chaos', 0),
                life=defenses.get('life', 0),
                energy_shield=defenses.get('energy_shield', 0),
                block_chance=defenses.get('block_chance', 0),
                dodge_chance=defenses.get('dodge_chance', 0),
                physical_dps=offense.get('physical_dps', 0),
                elemental_dps=offense.get('elemental_dps', 0),
                chaos_dps=offense.get('chaos_dps', 0),
                critical_strike_chance=offense.get('crit_chance', 0),
                critical_strike_multiplier=offense.get('crit_multiplier', 0),
                attack_speed=speed.get('attack_speed', 0),
                cast_speed=speed.get('cast_speed', 0),
                movement_speed=speed.get('movement_speed', 0)
            )
        
        # 解析构筑组件
        build_components = data.get('build_components', {})
        metadata = data.get('metadata', {})
        pob2_integration = data.get('pob2_integration', {})
        
        return cls(
            name=data['name'],
            character_class=character_class,
            ascendancy=ascendancy,
            level=data['level'],
            stats=stats,
            estimated_cost=data.get('estimated_cost'),
            currency_type=data.get('currency_type', 'divine'),
            goal=goal,
            notes=data.get('notes'),
            main_skill_gem=build_components.get('main_skill_gem'),
            support_gems=build_components.get('support_gems', []),
            key_items=build_components.get('key_items', []),
            passive_keystones=build_components.get('passive_keystones', []),
            created_by=metadata.get('created_by'),
            source_url=metadata.get('source_url'),
            league=metadata.get('league', 'Standard'),
            last_updated=metadata.get('last_updated'),
            pob2_code=pob2_integration.get('pob2_code'),
            pob2_version=pob2_integration.get('pob2_version')
        )

    def compare_with(self, other: 'PoE2Build') -> Dict[str, Any]:
        """与另一个构筑进行比较"""
        if not isinstance(other, PoE2Build):
            raise ValueError("Can only compare with another PoE2Build")
        
        comparison = {
            'name': {'this': self.name, 'other': other.name},
            'class_match': self.character_class == other.character_class,
            'level_diff': self.level - other.level,
        }
        
        if self.stats and other.stats:
            comparison['stats'] = {
                'dps_diff': self.stats.total_dps - other.stats.total_dps,
                'ehp_diff': self.stats.effective_health_pool - other.stats.effective_health_pool,
                'resistance_comparison': {
                    'fire': self.stats.fire_resistance - other.stats.fire_resistance,
                    'cold': self.stats.cold_resistance - other.stats.cold_resistance,
                    'lightning': self.stats.lightning_resistance - other.stats.lightning_resistance
                }
            }
        
        if self.estimated_cost and other.estimated_cost:
            comparison['cost_diff'] = self.estimated_cost - other.estimated_cost
        
        return comparison

    def is_suitable_for_goal(self, target_goal: PoE2BuildGoal) -> bool:
        """检查构筑是否适合指定目标"""
        if not self.stats:
            return False
        
        # 根据不同目标检查不同的阈值
        if target_goal == PoE2BuildGoal.BOSS_KILLING:
            return (self.stats.total_dps >= 500000 and  # 50万DPS用于Boss
                    self.stats.effective_health_pool >= 6000)  # 6000+ EHP
        
        elif target_goal == PoE2BuildGoal.CLEAR_SPEED:
            return (self.stats.total_dps >= 200000 and  # 20万DPS用于清图
                    self.stats.movement_speed >= 100)  # 移动速度
        
        elif target_goal == PoE2BuildGoal.BUDGET_FRIENDLY:
            return (self.estimated_cost is not None and 
                    self.estimated_cost <= 5.0)  # 5 divine以下
        
        elif target_goal == PoE2BuildGoal.LEAGUE_START:
            return (self.estimated_cost is None or self.estimated_cost <= 1.0)  # 1 divine以下或无成本要求
        
        elif target_goal == PoE2BuildGoal.ENDGAME_CONTENT:
            return (self.stats.total_dps >= 1000000 and  # 100万DPS
                    self.stats.effective_health_pool >= 8000 and  # 8000+ EHP
                    self.stats.is_resistance_capped())  # 三抗满足
        
        return True  # 默认适合


# 构筑比较和过滤工具函数
def filter_builds_by_class(builds: List[PoE2Build], 
                          character_class: PoE2CharacterClass) -> List[PoE2Build]:
    """按职业过滤构筑"""
    return [build for build in builds if build.character_class == character_class]


def filter_builds_by_budget(builds: List[PoE2Build], 
                           max_budget: float,
                           currency: str = "divine") -> List[PoE2Build]:
    """按预算过滤构筑"""
    filtered = []
    for build in builds:
        if build.estimated_cost is None:
            # 无成本信息的构筑默认包含
            filtered.append(build)
        elif build.currency_type == currency and build.estimated_cost <= max_budget:
            filtered.append(build)
    return filtered


def filter_builds_by_goal(builds: List[PoE2Build], 
                         goal: PoE2BuildGoal) -> List[PoE2Build]:
    """按目标过滤构筑"""
    return [build for build in builds if build.is_suitable_for_goal(goal)]


def sort_builds_by_dps(builds: List[PoE2Build], 
                      descending: bool = True) -> List[PoE2Build]:
    """按DPS排序构筑"""
    def get_dps(build: PoE2Build) -> float:
        return build.stats.total_dps if build.stats else 0
    
    return sorted(builds, key=get_dps, reverse=descending)


def sort_builds_by_cost(builds: List[PoE2Build], 
                       ascending: bool = True) -> List[PoE2Build]:
    """按成本排序构筑"""
    def get_cost(build: PoE2Build) -> float:
        return build.estimated_cost if build.estimated_cost is not None else float('inf')
    
    return sorted(builds, key=get_cost, reverse=not ascending)