"""PoE2角色和职业数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class PoE2CharacterClass(Enum):
    """PoE2角色职业枚举"""
    SORCERESS = "Sorceress"
    MONK = "Monk" 
    RANGER = "Ranger"
    MERCENARY = "Mercenary"
    WITCH = "Witch"
    WARRIOR = "Warrior"


class PoE2Ascendancy(Enum):
    """PoE2升华职业枚举"""
    # Sorceress升华
    STORMWEAVER = "Stormweaver"
    CHRONOMANCER = "Chronomancer"
    
    # Monk升华
    INVOKER = "Invoker"
    ACOLYTE_OF_CHAYULA = "Acolyte of Chayula"
    
    # Ranger升华
    DEADEYE = "Deadeye"
    PATHFINDER = "Pathfinder"
    
    # Mercenary升华
    WITCHHUNTER = "Witchhunter"
    GEMLING_LEGIONNAIRE = "Gemling Legionnaire"
    
    # Witch升华
    INFERNALIST = "Infernalist" 
    BLOOD_MAGE = "Blood Mage"
    
    # Warrior升华
    TITAN = "Titan"
    WARBRINGER = "Warbringer"


class PoE2AttributeType(Enum):
    """PoE2属性类型枚举"""
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTELLIGENCE = "intelligence"


# 职业与升华的映射关系
ASCENDANCY_MAPPING = {
    PoE2CharacterClass.SORCERESS: [
        PoE2Ascendancy.STORMWEAVER,
        PoE2Ascendancy.CHRONOMANCER
    ],
    PoE2CharacterClass.MONK: [
        PoE2Ascendancy.INVOKER,
        PoE2Ascendancy.ACOLYTE_OF_CHAYULA
    ],
    PoE2CharacterClass.RANGER: [
        PoE2Ascendancy.DEADEYE,
        PoE2Ascendancy.PATHFINDER
    ],
    PoE2CharacterClass.MERCENARY: [
        PoE2Ascendancy.WITCHHUNTER,
        PoE2Ascendancy.GEMLING_LEGIONNAIRE
    ],
    PoE2CharacterClass.WITCH: [
        PoE2Ascendancy.INFERNALIST,
        PoE2Ascendancy.BLOOD_MAGE
    ],
    PoE2CharacterClass.WARRIOR: [
        PoE2Ascendancy.TITAN,
        PoE2Ascendancy.WARBRINGER
    ]
}

# 职业与主要属性的映射关系
CLASS_PRIMARY_ATTRIBUTES = {
    PoE2CharacterClass.SORCERESS: PoE2AttributeType.INTELLIGENCE,
    PoE2CharacterClass.MONK: PoE2AttributeType.DEXTERITY,
    PoE2CharacterClass.RANGER: PoE2AttributeType.DEXTERITY,
    PoE2CharacterClass.MERCENARY: PoE2AttributeType.DEXTERITY,
    PoE2CharacterClass.WITCH: PoE2AttributeType.INTELLIGENCE,
    PoE2CharacterClass.WARRIOR: PoE2AttributeType.STRENGTH
}


@dataclass
class PoE2CharacterAttributes:
    """PoE2角色属性数据模型"""
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    
    def __post_init__(self):
        """验证属性数值"""
        if any(attr < 1 for attr in [self.strength, self.dexterity, self.intelligence]):
            raise ValueError("All attributes must be at least 1")
        
        if any(attr > 2000 for attr in [self.strength, self.dexterity, self.intelligence]):
            raise ValueError("Attributes cannot exceed 2000")
    
    def get_total_attributes(self) -> int:
        """获取总属性点"""
        return self.strength + self.dexterity + self.intelligence
    
    def get_primary_attribute(self, character_class: PoE2CharacterClass) -> int:
        """获取职业主要属性值"""
        primary_attr = CLASS_PRIMARY_ATTRIBUTES.get(character_class)
        if primary_attr == PoE2AttributeType.STRENGTH:
            return self.strength
        elif primary_attr == PoE2AttributeType.DEXTERITY:
            return self.dexterity
        elif primary_attr == PoE2AttributeType.INTELLIGENCE:
            return self.intelligence
        return 0
    
    def meets_requirements(self, req_str: int, req_dex: int, req_int: int) -> bool:
        """检查是否满足属性需求"""
        return (self.strength >= req_str and
                self.dexterity >= req_dex and
                self.intelligence >= req_int)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'intelligence': self.intelligence,
            'total': self.get_total_attributes()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2CharacterAttributes':
        """从字典创建属性实例"""
        return cls(
            strength=data.get('strength', 10),
            dexterity=data.get('dexterity', 10),
            intelligence=data.get('intelligence', 10)
        )


@dataclass
class PoE2Character:
    """PoE2角色数据模型"""
    name: str
    character_class: PoE2CharacterClass
    level: int
    attributes: PoE2CharacterAttributes
    ascendancy: Optional[PoE2Ascendancy] = None
    # 经验和技能点
    experience: int = 0
    passive_skill_points: int = 0
    ascendancy_points: int = 0
    # 游戏数据
    league: str = "Standard"
    hardcore: bool = False
    # 元数据
    created_date: Optional[str] = None
    last_played: Optional[str] = None
    
    def __post_init__(self):
        """验证角色数据"""
        if not 1 <= self.level <= 100:
            raise ValueError(f"Level {self.level} must be between 1 and 100")
        
        if not self.name.strip():
            raise ValueError("Character name cannot be empty")
        
        # 验证升华与职业的匹配
        if self.ascendancy:
            valid_ascendancies = ASCENDANCY_MAPPING.get(self.character_class, [])
            if self.ascendancy not in valid_ascendancies:
                raise ValueError(f"Ascendancy {self.ascendancy.value} not valid for {self.character_class.value}")
        
        # 验证经验值
        if self.experience < 0:
            raise ValueError("Experience cannot be negative")
        
        # 验证技能点数量
        if self.passive_skill_points < 0:
            raise ValueError("Passive skill points cannot be negative")
        
        if self.ascendancy_points < 0:
            raise ValueError("Ascendancy points cannot be negative")
        
        # 检查升华点数合理性（只有升华后才能有升华点）
        if self.ascendancy_points > 0 and not self.ascendancy:
            raise ValueError("Cannot have ascendancy points without ascendancy")
    
    def get_primary_attribute_value(self) -> int:
        """获取主要属性值"""
        return self.attributes.get_primary_attribute(self.character_class)
    
    def get_attribute_bonus_from_level(self) -> int:
        """获取等级提供的属性加成"""
        # PoE2中每级提供属性点
        return (self.level - 1) * 2  # 假设每级2点属性
    
    def can_ascend(self) -> bool:
        """检查是否可以升华"""
        return self.level >= 30 and not self.ascendancy  # PoE2升华等级要求
    
    def get_expected_passive_points(self) -> int:
        """获取当前等级期望的天赋点数"""
        # PoE2天赋点公式（示例）
        base_points = self.level - 1  # 每级1点
        quest_points = min(self.level // 10, 20)  # 任务奖励点数
        return base_points + quest_points
    
    def is_valid_build_level(self, min_level: int = 1, max_level: int = 100) -> bool:
        """检查是否在有效的构筑等级范围内"""
        return min_level <= self.level <= max_level
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'class': self.character_class.value,
            'level': self.level,
            'attributes': self.attributes.to_dict(),
            'ascendancy': self.ascendancy.value if self.ascendancy else None,
            'progression': {
                'experience': self.experience,
                'passive_skill_points': self.passive_skill_points,
                'ascendancy_points': self.ascendancy_points,
                'expected_passive_points': self.get_expected_passive_points()
            },
            'game_info': {
                'league': self.league,
                'hardcore': self.hardcore
            },
            'metadata': {
                'created_date': self.created_date,
                'last_played': self.last_played,
                'can_ascend': self.can_ascend(),
                'primary_attribute_value': self.get_primary_attribute_value()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2Character':
        """从字典创建实例"""
        character_class = PoE2CharacterClass(data['class'])
        ascendancy = PoE2Ascendancy(data['ascendancy']) if data.get('ascendancy') else None
        attributes = PoE2CharacterAttributes.from_dict(data.get('attributes', {}))
        
        progression = data.get('progression', {})
        game_info = data.get('game_info', {})
        metadata = data.get('metadata', {})
        
        return cls(
            name=data['name'],
            character_class=character_class,
            level=data['level'],
            attributes=attributes,
            ascendancy=ascendancy,
            experience=progression.get('experience', 0),
            passive_skill_points=progression.get('passive_skill_points', 0),
            ascendancy_points=progression.get('ascendancy_points', 0),
            league=game_info.get('league', 'Standard'),
            hardcore=game_info.get('hardcore', False),
            created_date=metadata.get('created_date'),
            last_played=metadata.get('last_played')
        )
    
    def get_valid_ascendancies(self) -> List[PoE2Ascendancy]:
        """获取该职业可用的升华"""
        return ASCENDANCY_MAPPING.get(self.character_class, [])
    
    def calculate_character_power(self) -> float:
        """计算角色综合实力评分"""
        # 基于等级、属性、天赋点的简单评分
        level_score = self.level / 100  # 0-1分
        attribute_score = self.get_primary_attribute_value() / 500  # 假设500为高属性值
        passive_score = self.passive_skill_points / 100  # 假设100为合理天赋点数
        
        # 升华加成
        ascendancy_bonus = 0.2 if self.ascendancy else 0.0
        
        total_score = (level_score * 0.4 + 
                      attribute_score * 0.3 + 
                      passive_score * 0.3 + 
                      ascendancy_bonus)
        
        return min(1.0, total_score)  # 确保不超过1.0


# 角色相关工具函数
def filter_characters_by_class(characters: List[PoE2Character], 
                             character_class: PoE2CharacterClass) -> List[PoE2Character]:
    """按职业过滤角色"""
    return [char for char in characters if char.character_class == character_class]


def filter_characters_by_level_range(characters: List[PoE2Character],
                                   min_level: int, 
                                   max_level: int) -> List[PoE2Character]:
    """按等级范围过滤角色"""
    return [char for char in characters 
            if min_level <= char.level <= max_level]


def filter_characters_by_league(characters: List[PoE2Character],
                               league: str) -> List[PoE2Character]:
    """按联盟过滤角色"""
    return [char for char in characters if char.league == league]


def sort_characters_by_level(characters: List[PoE2Character],
                           descending: bool = True) -> List[PoE2Character]:
    """按等级排序角色"""
    return sorted(characters, key=lambda x: x.level, reverse=descending)


def sort_characters_by_power(characters: List[PoE2Character],
                           descending: bool = True) -> List[PoE2Character]:
    """按综合实力排序角色"""
    return sorted(characters, key=lambda x: x.calculate_character_power(), reverse=descending)


def get_class_distribution(characters: List[PoE2Character]) -> Dict[str, int]:
    """获取职业分布统计"""
    distribution = {}
    for char in characters:
        class_name = char.character_class.value
        distribution[class_name] = distribution.get(class_name, 0) + 1
    return distribution


def get_ascendancy_distribution(characters: List[PoE2Character]) -> Dict[str, int]:
    """获取升华分布统计"""
    distribution = {}
    for char in characters:
        if char.ascendancy:
            ascendancy_name = char.ascendancy.value
            distribution[ascendancy_name] = distribution.get(ascendancy_name, 0) + 1
    return distribution


def create_character_summary(characters: List[PoE2Character]) -> Dict[str, Any]:
    """创建角色列表摘要"""
    if not characters:
        return {'total_characters': 0}
    
    return {
        'total_characters': len(characters),
        'average_level': sum(char.level for char in characters) / len(characters),
        'max_level': max(char.level for char in characters),
        'min_level': min(char.level for char in characters),
        'class_distribution': get_class_distribution(characters),
        'ascendancy_distribution': get_ascendancy_distribution(characters),
        'league_distribution': {
            league: len([c for c in characters if c.league == league])
            for league in set(char.league for char in characters)
        },
        'hardcore_count': len([c for c in characters if c.hardcore])
    }