# -*- coding: utf-8 -*-
"""
PoE2构筑生成器数据模型包

包含所有PoE2相关的数据模型定义:
- 角色和职业模型 (characters.py)
- 构筑数据模型 (build.py)
- 物品数据模型 (items.py)
- 技能数据模型 (skills.py)
- 市场数据模型 (market.py)
"""

# 角色和职业相关
from .characters import (
    PoE2CharacterClass,
    PoE2Ascendancy,
    PoE2AttributeType,
    PoE2CharacterAttributes,
    PoE2Character,
    ASCENDANCY_MAPPING,
    CLASS_PRIMARY_ATTRIBUTES,
    filter_characters_by_class,
    filter_characters_by_level_range,
    filter_characters_by_league,
    sort_characters_by_level,
    sort_characters_by_power,
    get_class_distribution,
    get_ascendancy_distribution,
    create_character_summary
)

# 构筑相关
from .build import (
    PoE2BuildGoal,
    PoE2DamageType,
    PoE2BuildStats,
    PoE2Build,
    filter_builds_by_class,
    filter_builds_by_budget,
    filter_builds_by_goal,
    sort_builds_by_dps,
    sort_builds_by_cost
)

# 物品相关
from .items import (
    PoE2ItemRarity,
    PoE2ItemCategory,
    PoE2WeaponType,
    PoE2ArmorType,
    PoE2AccessoryType,
    PoE2EquipSlot,
    PoE2ModifierType,
    PoE2Modifier,
    PoE2ItemRequirements,
    PoE2Item,
    PoE2Weapon,
    PoE2Armor,
    PoE2Accessory,
    filter_items_by_category,
    filter_items_by_rarity,
    filter_items_by_price_range,
    sort_items_by_value,
    find_items_with_modifier,
    create_item_loadout
)

# 技能相关
from .skills import (
    PoE2SkillType,
    PoE2SkillCategory,
    PoE2GemColor,
    PoE2SocketType,
    PoE2SkillStats,
    PoE2SkillRequirements,
    PoE2Skill,
    PoE2SkillSetup,
    filter_skills_by_type,
    filter_skills_by_category,
    filter_skills_by_color,
    find_compatible_supports,
    sort_skills_by_dps,
    create_optimal_skill_setup
)

# 市场相关
from .market import (
    PoE2CurrencyType,
    PoE2LeagueType,
    PoE2MarketTrend,
    PoE2PriceData,
    PoE2MarketTrendData,
    PoE2MarketListing,
    PoE2ItemMarketData,
    PoE2CurrencyExchangeRate,
    filter_listings_by_price_range,
    filter_listings_by_league,
    sort_listings_by_price,
    calculate_market_statistics,
    estimate_item_value,
    find_arbitrage_opportunities
)

__all__ = [
    # Characters
    "PoE2CharacterClass",
    "PoE2Ascendancy", 
    "PoE2AttributeType",
    "PoE2CharacterAttributes",
    "PoE2Character",
    "ASCENDANCY_MAPPING",
    "CLASS_PRIMARY_ATTRIBUTES",
    "filter_characters_by_class",
    "filter_characters_by_level_range",
    "filter_characters_by_league",
    "sort_characters_by_level",
    "sort_characters_by_power",
    "get_class_distribution",
    "get_ascendancy_distribution", 
    "create_character_summary",
    
    # Build
    "PoE2BuildGoal",
    "PoE2DamageType",
    "PoE2BuildStats", 
    "PoE2Build",
    "filter_builds_by_class",
    "filter_builds_by_budget",
    "filter_builds_by_goal",
    "sort_builds_by_dps",
    "sort_builds_by_cost",
    
    # Items
    "PoE2ItemRarity",
    "PoE2ItemCategory",
    "PoE2WeaponType",
    "PoE2ArmorType", 
    "PoE2AccessoryType",
    "PoE2EquipSlot",
    "PoE2ModifierType",
    "PoE2Modifier",
    "PoE2ItemRequirements",
    "PoE2Item",
    "PoE2Weapon",
    "PoE2Armor", 
    "PoE2Accessory",
    "filter_items_by_category",
    "filter_items_by_rarity",
    "filter_items_by_price_range",
    "sort_items_by_value",
    "find_items_with_modifier",
    "create_item_loadout",
    
    # Skills
    "PoE2SkillType",
    "PoE2SkillCategory",
    "PoE2GemColor",
    "PoE2SocketType",
    "PoE2SkillStats",
    "PoE2SkillRequirements",
    "PoE2Skill",
    "PoE2SkillSetup",
    "filter_skills_by_type",
    "filter_skills_by_category", 
    "filter_skills_by_color",
    "find_compatible_supports",
    "sort_skills_by_dps",
    "create_optimal_skill_setup",
    
    # Market
    "PoE2CurrencyType",
    "PoE2LeagueType",
    "PoE2MarketTrend",
    "PoE2PriceData",
    "PoE2MarketTrendData",
    "PoE2MarketListing",
    "PoE2ItemMarketData",
    "PoE2CurrencyExchangeRate", 
    "filter_listings_by_price_range",
    "filter_listings_by_league",
    "sort_listings_by_price",
    "calculate_market_statistics",
    "estimate_item_value",
    "find_arbitrage_opportunities"
]

# 版本信息
__version__ = "2.0.0"

# 快速访问常用枚举的便捷函数
def get_all_character_classes():
    """获取所有角色职业"""
    return list(PoE2CharacterClass)

def get_all_ascendancies():
    """获取所有升华职业"""
    return list(PoE2Ascendancy)

def get_ascendancies_for_class(character_class):
    """获取指定职业的升华列表"""
    return ASCENDANCY_MAPPING.get(character_class, [])

def get_all_build_goals():
    """获取所有构筑目标"""
    return list(PoE2BuildGoal)

def get_all_currencies():
    """获取所有货币类型"""
    return list(PoE2CurrencyType)

def get_all_leagues():
    """获取所有联盟类型"""
    return list(PoE2LeagueType)