"""PoE2物品数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class PoE2ItemRarity(Enum):
    """PoE2物品稀有度枚举"""
    NORMAL = "normal"
    MAGIC = "magic"
    RARE = "rare"
    UNIQUE = "unique"


class PoE2ItemCategory(Enum):
    """PoE2物品分类枚举"""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    FLASK = "flask"
    GEM = "gem"
    CURRENCY = "currency"
    MAP = "map"
    JEWEL = "jewel"


class PoE2WeaponType(Enum):
    """PoE2武器类型枚举"""
    # 近战武器
    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"
    DAGGER = "dagger"
    CLAW = "claw"
    STAFF = "staff"
    # 远程武器
    BOW = "bow"
    CROSSBOW = "crossbow"
    # 法术武器
    WAND = "wand"
    SCEPTRE = "sceptre"
    # 特殊武器
    QUARTERSTAFF = "quarterstaff"
    FLAIL = "flail"
    SPEAR = "spear"


class PoE2ArmorType(Enum):
    """PoE2防具类型枚举"""
    HELMET = "helmet"
    BODY_ARMOR = "body_armor"
    GLOVES = "gloves"
    BOOTS = "boots"
    SHIELD = "shield"
    BELT = "belt"


class PoE2AccessoryType(Enum):
    """PoE2饰品类型枚举"""
    RING = "ring"
    AMULET = "amulet"
    CHARM = "charm"  # PoE2新增的魅力饰品


class PoE2EquipSlot(Enum):
    """PoE2装备槽位枚举"""
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    HELMET = "helmet"
    BODY_ARMOR = "body_armor"
    GLOVES = "gloves"
    BOOTS = "boots"
    BELT = "belt"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    AMULET = "amulet"
    CHARM = "charm"


class PoE2ModifierType(Enum):
    """PoE2词缀类型枚举"""
    PREFIX = "prefix"
    SUFFIX = "suffix"
    IMPLICIT = "implicit"
    ENCHANT = "enchant"
    CORRUPTED = "corrupted"
    SYNTHESISED = "synthesised"


@dataclass
class PoE2Modifier:
    """PoE2物品词缀数据模型"""
    type: PoE2ModifierType
    text: str
    values: List[Union[int, float]]
    tier: Optional[int] = None
    is_crafted: bool = False
    
    def __post_init__(self):
        """验证词缀数据"""
        if not self.text.strip():
            raise ValueError("Modifier text cannot be empty")
        
        if self.tier is not None and self.tier < 1:
            raise ValueError("Modifier tier must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.type.value,
            'text': self.text,
            'values': self.values,
            'tier': self.tier,
            'is_crafted': self.is_crafted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2Modifier':
        """从字典创建词缀"""
        return cls(
            type=PoE2ModifierType(data['type']),
            text=data['text'],
            values=data['values'],
            tier=data.get('tier'),
            is_crafted=data.get('is_crafted', False)
        )


@dataclass
class PoE2ItemRequirements:
    """PoE2物品需求数据模型"""
    level: int = 1
    strength: int = 0
    dexterity: int = 0
    intelligence: int = 0
    
    def __post_init__(self):
        """验证需求数据"""
        if not 1 <= self.level <= 100:
            raise ValueError(f"Level requirement {self.level} must be between 1 and 100")
        
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
        """检查是否满足装备需求"""
        return (character_level >= self.level and
                character_str >= self.strength and
                character_dex >= self.dexterity and
                character_int >= self.intelligence)


@dataclass 
class PoE2Item:
    """PoE2物品数据模型基础类"""
    name: str
    base_type: str
    rarity: PoE2ItemRarity
    category: PoE2ItemCategory
    item_level: int
    requirements: PoE2ItemRequirements
    modifiers: List[PoE2Modifier]
    # 物品属性
    corrupted: bool = False
    mirrored: bool = False
    identified: bool = True
    # 数值属性
    quality: int = 0
    gem_level: Optional[int] = None
    # 市场相关
    estimated_price: Optional[float] = None
    price_currency: str = "divine"
    market_confidence: Optional[float] = None
    # 元数据
    icon_url: Optional[str] = None
    flavor_text: Optional[str] = None
    
    def __post_init__(self):
        """验证物品数据"""
        if not self.name.strip():
            raise ValueError("Item name cannot be empty")
        
        if not self.base_type.strip():
            raise ValueError("Item base type cannot be empty")
        
        if not 1 <= self.item_level <= 100:
            raise ValueError(f"Item level {self.item_level} must be between 1 and 100")
        
        if not 0 <= self.quality <= 30:  # PoE2品质上限可能不同
            raise ValueError(f"Item quality {self.quality}% must be between 0% and 30%")
        
        if self.gem_level is not None and not 1 <= self.gem_level <= 21:
            raise ValueError(f"Gem level {self.gem_level} must be between 1 and 21")
        
        if self.estimated_price is not None and self.estimated_price < 0:
            raise ValueError("Item price cannot be negative")
    
    def get_modifier_by_type(self, mod_type: PoE2ModifierType) -> List[PoE2Modifier]:
        """按类型获取词缀"""
        return [mod for mod in self.modifiers if mod.type == mod_type]
    
    def has_modifier_text(self, search_text: str) -> bool:
        """检查是否包含指定文本的词缀"""
        search_lower = search_text.lower()
        return any(search_lower in mod.text.lower() for mod in self.modifiers)
    
    def get_total_modifier_count(self) -> Dict[PoE2ModifierType, int]:
        """获取各类型词缀数量统计"""
        counts = {}
        for mod in self.modifiers:
            counts[mod.type] = counts.get(mod.type, 0) + 1
        return counts
    
    def is_influenced(self) -> bool:
        """检查是否有影响词缀"""
        influence_keywords = ['elder', 'shaper', 'hunter', 'redeemer', 'crusader', 'warlord']
        return any(
            any(keyword in mod.text.lower() for keyword in influence_keywords)
            for mod in self.modifiers
        )
    
    def calculate_approximate_value(self) -> float:
        """计算物品的大概价值（基于词缀和稀有度）"""
        base_value = 0.0
        
        # 稀有度基础值
        rarity_values = {
            PoE2ItemRarity.NORMAL: 0.1,
            PoE2ItemRarity.MAGIC: 0.5,
            PoE2ItemRarity.RARE: 1.0,
            PoE2ItemRarity.UNIQUE: 2.0
        }
        base_value += rarity_values.get(self.rarity, 0)
        
        # 词缀数量加成
        prefix_count = len(self.get_modifier_by_type(PoE2ModifierType.PREFIX))
        suffix_count = len(self.get_modifier_by_type(PoE2ModifierType.SUFFIX))
        base_value += (prefix_count + suffix_count) * 0.2
        
        # 品质加成
        base_value += self.quality * 0.01
        
        # 如果有市场价格，优先使用
        if self.estimated_price is not None:
            return self.estimated_price
        
        return base_value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'base_type': self.base_type,
            'rarity': self.rarity.value,
            'category': self.category.value,
            'item_level': self.item_level,
            'requirements': self.requirements.to_dict(),
            'modifiers': [mod.to_dict() for mod in self.modifiers],
            'properties': {
                'corrupted': self.corrupted,
                'mirrored': self.mirrored,
                'identified': self.identified,
                'quality': self.quality,
                'gem_level': self.gem_level
            },
            'market': {
                'estimated_price': self.estimated_price,
                'price_currency': self.price_currency,
                'market_confidence': self.market_confidence
            },
            'metadata': {
                'icon_url': self.icon_url,
                'flavor_text': self.flavor_text
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2Item':
        """从字典创建物品实例"""
        requirements = PoE2ItemRequirements(**data['requirements'])
        modifiers = [PoE2Modifier.from_dict(mod_data) for mod_data in data.get('modifiers', [])]
        properties = data.get('properties', {})
        market = data.get('market', {})
        metadata = data.get('metadata', {})
        
        return cls(
            name=data['name'],
            base_type=data['base_type'],
            rarity=PoE2ItemRarity(data['rarity']),
            category=PoE2ItemCategory(data['category']),
            item_level=data['item_level'],
            requirements=requirements,
            modifiers=modifiers,
            corrupted=properties.get('corrupted', False),
            mirrored=properties.get('mirrored', False),
            identified=properties.get('identified', True),
            quality=properties.get('quality', 0),
            gem_level=properties.get('gem_level'),
            estimated_price=market.get('estimated_price'),
            price_currency=market.get('price_currency', 'divine'),
            market_confidence=market.get('market_confidence'),
            icon_url=metadata.get('icon_url'),
            flavor_text=metadata.get('flavor_text')
        )


@dataclass
class PoE2Weapon(PoE2Item):
    """PoE2武器数据模型"""
    weapon_type: PoE2WeaponType = PoE2WeaponType.SWORD
    damage_min: float = 0.0
    damage_max: float = 0.0
    attack_speed: float = 1.0
    critical_chance: float = 5.0
    damage_types: List[str] = None  # ['physical', 'fire', 'cold', etc.]
    
    def __post_init__(self):
        """武器特有验证"""
        # 初始化默认值
        if self.damage_types is None:
            self.damage_types = ['physical']
        
        super().__post_init__()
        
        if self.category != PoE2ItemCategory.WEAPON:
            raise ValueError("PoE2Weapon must have category WEAPON")
        
        if self.damage_min < 0 or self.damage_max < 0:
            raise ValueError("Weapon damage cannot be negative")
        
        if self.damage_max < self.damage_min:
            raise ValueError("Maximum damage must be >= minimum damage")
        
        if self.attack_speed <= 0:
            raise ValueError("Attack speed must be positive")
        
        if not 0 <= self.critical_chance <= 100:
            raise ValueError("Critical chance must be between 0% and 100%")
    
    def get_average_damage(self) -> float:
        """计算平均伤害"""
        return (self.damage_min + self.damage_max) / 2
    
    def get_dps(self) -> float:
        """计算每秒伤害"""
        return self.get_average_damage() * self.attack_speed
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（包含武器特有属性）"""
        base_dict = super().to_dict()
        base_dict.update({
            'weapon_type': self.weapon_type.value,
            'damage': {
                'min': self.damage_min,
                'max': self.damage_max,
                'average': self.get_average_damage()
            },
            'attack_speed': self.attack_speed,
            'critical_chance': self.critical_chance,
            'damage_types': self.damage_types,
            'dps': self.get_dps()
        })
        return base_dict


@dataclass
class PoE2Armor(PoE2Item):
    """PoE2防具数据模型"""
    armor_type: PoE2ArmorType = PoE2ArmorType.BODY_ARMOR
    armor_value: int = 0
    energy_shield: int = 0
    evasion: int = 0
    block_chance: float = 0.0  # 盾牌专用
    
    def __post_init__(self):
        """防具特有验证"""
        super().__post_init__()
        
        if self.category != PoE2ItemCategory.ARMOR:
            raise ValueError("PoE2Armor must have category ARMOR")
        
        if any(val < 0 for val in [self.armor_value, self.energy_shield, self.evasion]):
            raise ValueError("Defense values cannot be negative")
        
        if not 0 <= self.block_chance <= 100:
            raise ValueError("Block chance must be between 0% and 100%")
    
    def get_total_defense(self) -> int:
        """计算总防御值"""
        return self.armor_value + self.energy_shield + self.evasion
    
    def get_defense_type(self) -> str:
        """判断主要防御类型"""
        defenses = [
            ('armor', self.armor_value),
            ('energy_shield', self.energy_shield),
            ('evasion', self.evasion)
        ]
        return max(defenses, key=lambda x: x[1])[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（包含防具特有属性）"""
        base_dict = super().to_dict()
        base_dict.update({
            'armor_type': self.armor_type.value,
            'defenses': {
                'armor': self.armor_value,
                'energy_shield': self.energy_shield,
                'evasion': self.evasion,
                'total': self.get_total_defense(),
                'primary_type': self.get_defense_type()
            },
            'block_chance': self.block_chance
        })
        return base_dict


@dataclass
class PoE2Accessory(PoE2Item):
    """PoE2饰品数据模型"""
    accessory_type: PoE2AccessoryType = PoE2AccessoryType.RING
    
    def __post_init__(self):
        """饰品特有验证"""
        super().__post_init__()
        
        if self.category != PoE2ItemCategory.ACCESSORY:
            raise ValueError("PoE2Accessory must have category ACCESSORY")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（包含饰品特有属性）"""
        base_dict = super().to_dict()
        base_dict.update({
            'accessory_type': self.accessory_type.value
        })
        return base_dict


# 物品相关工具函数
def filter_items_by_category(items: List[PoE2Item], 
                           category: PoE2ItemCategory) -> List[PoE2Item]:
    """按分类过滤物品"""
    return [item for item in items if item.category == category]


def filter_items_by_rarity(items: List[PoE2Item], 
                          rarity: PoE2ItemRarity) -> List[PoE2Item]:
    """按稀有度过滤物品"""
    return [item for item in items if item.rarity == rarity]


def filter_items_by_price_range(items: List[PoE2Item], 
                               min_price: float, 
                               max_price: float,
                               currency: str = "divine") -> List[PoE2Item]:
    """按价格范围过滤物品"""
    filtered = []
    for item in items:
        if (item.estimated_price is not None and 
            item.price_currency == currency and
            min_price <= item.estimated_price <= max_price):
            filtered.append(item)
    return filtered


def sort_items_by_value(items: List[PoE2Item], 
                       descending: bool = True) -> List[PoE2Item]:
    """按价值排序物品"""
    return sorted(items, key=lambda x: x.calculate_approximate_value(), reverse=descending)


def find_items_with_modifier(items: List[PoE2Item], 
                           search_text: str) -> List[PoE2Item]:
    """查找包含指定词缀的物品"""
    return [item for item in items if item.has_modifier_text(search_text)]


def create_item_loadout(items: Dict[PoE2EquipSlot, PoE2Item]) -> Dict[str, Any]:
    """创建装备配置摘要"""
    loadout_summary = {
        'total_items': len(items),
        'total_value': sum(item.calculate_approximate_value() for item in items.values()),
        'rarity_distribution': {},
        'category_distribution': {},
        'slots_filled': list(items.keys())
    }
    
    # 统计稀有度分布
    for item in items.values():
        rarity = item.rarity.value
        loadout_summary['rarity_distribution'][rarity] = \
            loadout_summary['rarity_distribution'].get(rarity, 0) + 1
    
    # 统计分类分布
    for item in items.values():
        category = item.category.value
        loadout_summary['category_distribution'][category] = \
            loadout_summary['category_distribution'].get(category, 0) + 1
    
    return loadout_summary