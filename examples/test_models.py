#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PoE2构筑生成器数据模型演示脚本

展示所有PoE2数据模型的功能和特性
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from poe2build.models import (
    # Characters
    PoE2CharacterClass, PoE2Ascendancy, PoE2Character, PoE2CharacterAttributes,
    # Build
    PoE2Build, PoE2BuildStats, PoE2BuildGoal,
    # Skills  
    PoE2Skill, PoE2SkillType, PoE2SkillCategory, PoE2GemColor, PoE2SkillStats,
    # Items
    PoE2Weapon, PoE2WeaponType, PoE2ItemRarity, PoE2ItemCategory, PoE2ItemRequirements,
    # Market
    PoE2PriceData, PoE2CurrencyType, PoE2MarketListing, PoE2LeagueType,
    # Utilities
    get_all_character_classes, filter_builds_by_goal, sort_builds_by_dps
)


def demonstrate_poe2_models():
    """演示PoE2数据模型的完整功能"""
    
    print("=" * 60)
    print("PoE2 Build Generator - Data Models Demo")
    print("=" * 60)
    
    # 1. 角色系统演示
    print("\n1. Character System")
    print("-" * 40)
    
    # 创建角色属性
    attributes = PoE2CharacterAttributes(
        strength=100,
        dexterity=250,  # 敏捷主属性
        intelligence=80
    )
    
    # 创建角色
    character = PoE2Character(
        name="闪电突击游侠",
        character_class=PoE2CharacterClass.RANGER,
        level=94,
        attributes=attributes,
        ascendancy=PoE2Ascendancy.DEADEYE,
        league="Standard",
        passive_skill_points=115
    )
    
    print(f"角色: {character.name}")
    print(f"职业: {character.character_class.value} ({character.ascendancy.value})")
    print(f"等级: {character.level}")
    print(f"主要属性 (敏捷): {character.get_primary_attribute_value()}")
    print(f"总属性点: {character.attributes.get_total_attributes()}")
    print(f"综合实力评分: {character.calculate_character_power():.2f}")
    
    # 2. 构筑统计演示 (PoE2特有机制)
    print("\n📊 2. 构筑统计 (PoE2特有机制)")
    print("-" * 40)
    
    build_stats = PoE2BuildStats(
        total_dps=1800000,        # 180万DPS
        effective_health_pool=13500,
        fire_resistance=80,       # PoE2最大抗性80%
        cold_resistance=79,
        lightning_resistance=80,
        chaos_resistance=-15,     # PoE2混沌抗性可以为负
        life=10500,
        energy_shield=3000,
        critical_strike_chance=90,
        critical_strike_multiplier=480,
        movement_speed=135
    )
    
    print(f"总DPS: {build_stats.total_dps:,}")
    print(f"有效生命值: {build_stats.effective_health_pool:,}")
    print(f"抗性: 火{build_stats.fire_resistance}% / 冰{build_stats.cold_resistance}% / 雷{build_stats.lightning_resistance}% / 混沌{build_stats.chaos_resistance}%")
    print(f"三抗满足(75%+): {build_stats.is_resistance_capped()}")
    print(f"暴击: {build_stats.critical_strike_chance}%几率 x {build_stats.critical_strike_multiplier}%倍率")
    
    # 3. 技能系统演示 (包含PoE2灵魂消耗)
    print("\n🔮 3. 技能系统 (PoE2灵魂机制)")
    print("-" * 40)
    
    skill_stats = PoE2SkillStats(
        base_damage=220,
        damage_multiplier=1.5,
        cast_time=0.45,
        mana_cost=48,
        critical_chance=9.5,
        lightning_damage_percent=100,
        projectile_count=5,
        area_of_effect=25
    )
    
    main_skill = PoE2Skill(
        name="闪电打击",
        skill_type=PoE2SkillType.ACTIVE,
        categories=[PoE2SkillCategory.ATTACK, PoE2SkillCategory.LIGHTNING],
        gem_color=PoE2GemColor.GREEN,
        level=21,
        quality=23,
        stats=skill_stats,
        spirit_cost=25,  # PoE2独有的灵魂消耗机制
        description="近战攻击附加闪电伤害，产生追踪弹幕"
    )
    
    print(f"技能: {main_skill.name} (等级 {main_skill.level}, 品质 {main_skill.quality}%)")
    print(f"类型: {main_skill.skill_type.value} | 颜色: {main_skill.gem_color.value}")
    print(f"灵魂消耗: {main_skill.spirit_cost} (PoE2独有机制)")
    print(f"弹幕数量: {main_skill.stats.projectile_count} | 作用范围: {main_skill.stats.area_of_effect}")
    print(f"预估DPS: {main_skill.calculate_dps():,.0f}")
    
    # 4. 武器系统演示
    print("\n⚔️ 4. 武器系统")
    print("-" * 40)
    
    weapon_requirements = PoE2ItemRequirements(level=78, dexterity=212)
    endgame_weapon = PoE2Weapon(
        name="暴风之弓",
        base_type="马拉克什之弓",
        rarity=PoE2ItemRarity.UNIQUE,
        category=PoE2ItemCategory.WEAPON,
        item_level=84,
        requirements=weapon_requirements,
        modifiers=[],
        weapon_type=PoE2WeaponType.BOW,
        damage_min=85,
        damage_max=165,
        attack_speed=1.75,
        critical_chance=9.5,
        damage_types=["物理", "闪电"],
        quality=20
    )
    
    print(f"武器: {endgame_weapon.name} ({endgame_weapon.weapon_type.value})")
    print(f"底材: {endgame_weapon.base_type} | 稀有度: {endgame_weapon.rarity.value}")
    print(f"伤害: {endgame_weapon.damage_min}-{endgame_weapon.damage_max} (平均 {endgame_weapon.get_average_damage():.1f})")
    print(f"攻速: {endgame_weapon.attack_speed} APS | DPS: {endgame_weapon.get_dps():,.0f}")
    print(f"暴击几率: {endgame_weapon.critical_chance}%")
    print(f"需求: 等级{endgame_weapon.requirements.level}, 敏捷{endgame_weapon.requirements.dexterity}")
    
    # 5. 完整构筑创建
    print("\n🏗️ 5. 完整构筑")
    print("-" * 40)
    
    complete_build = PoE2Build(
        name="闪电突击 死神之眼 - 终局版本",
        character_class=PoE2CharacterClass.RANGER,
        level=94,
        ascendancy=PoE2Ascendancy.DEADEYE,
        stats=build_stats,
        goal=PoE2BuildGoal.ENDGAME_CONTENT,
        main_skill_gem="闪电打击",
        support_gems=[
            "穿透辅助",
            "武器元素伤害辅助", 
            "附加闪电伤害辅助",
            "快速攻击辅助",
            "暴击几率提升辅助",
            "暴击伤害提升辅助"
        ],
        estimated_cost=42.5,
        currency_type="divine",
        league="Standard",
        notes="高伤害清图构筑，适合T16地图和终局Boss"
    )
    
    print(f"构筑名称: {complete_build.name}")
    print(f"职业/升华: {complete_build.character_class.value} / {complete_build.ascendancy.value}")
    print(f"等级: {complete_build.level}")
    print(f"主技能: {complete_build.main_skill_gem}")
    print(f"辅助宝石: {len(complete_build.support_gems)} 个")
    print(f"构筑目标: {complete_build.goal.value}")
    print(f"预估造价: {complete_build.estimated_cost} {complete_build.currency_type}")
    print(f"构筑验证: {'✓ 通过' if complete_build.validate() else '✗ 失败'}")
    print(f"目标适配性: {'✓ 适合' if complete_build.is_suitable_for_goal(complete_build.goal) else '✗ 不适合'}")
    
    # 6. 市场数据演示
    print("\n💰 6. 市场数据")
    print("-" * 40)
    
    market_price = PoE2PriceData(
        value=42.5,
        currency=PoE2CurrencyType.DIVINE_ORB,
        confidence=0.89,
        sample_size=156
    )
    
    market_listing = PoE2MarketListing(
        item_name="暴风之弓",
        price=market_price,
        seller="顶级玩家",
        league=PoE2LeagueType.STANDARD,
        item_level=84,
        quality=20,
        account_name="TopTrader"
    )
    
    print(f"物品: {market_listing.item_name}")
    print(f"价格: {market_listing.price.value} {market_listing.price.currency.value}")
    print(f"可信度: {market_listing.price.confidence:.0%} (样本数: {market_listing.price.sample_size})")
    print(f"卖家: {market_listing.seller} ({market_listing.account_name})")
    print(f"联盟: {market_listing.league.value}")
    print(f"交易密语: {market_listing.generate_whisper()}")
    
    # 7. 实用功能演示
    print("\n🔧 7. 实用功能")
    print("-" * 40)
    
    # 获取所有职业
    all_classes = get_all_character_classes()
    print(f"所有职业 ({len(all_classes)}): {[c.value for c in all_classes]}")
    
    # 构筑过滤和排序
    test_builds = [complete_build]
    endgame_builds = filter_builds_by_goal(test_builds, PoE2BuildGoal.ENDGAME_CONTENT)
    dps_sorted_builds = sort_builds_by_dps(test_builds)
    
    print(f"终局构筑数量: {len(endgame_builds)}")
    print(f"按DPS排序: {dps_sorted_builds[0].name} ({dps_sorted_builds[0].stats.total_dps:,} DPS)")
    
    # 8. 总结
    print("\n" + "=" * 60)
    print("✅ PoE2数据模型演示完成")
    print("=" * 60)
    
    key_features = [
        "角色职业与升华系统",
        "PoE2特有抗性机制 (最大80%, 混沌可负)",
        "神圣石货币体系",
        "灵魂消耗系统 (PoE2独有)",
        "完整技能宝石与辅助系统",
        "物品与装备建模",
        "市场数据集成",
        "构筑验证与目标匹配",
        "数据过滤与排序功能",
        "完整的dataclass架构"
    ]
    
    print("\n🎯 已验证的PoE2特性:")
    for i, feature in enumerate(key_features, 1):
        print(f"  {i:2d}. {feature}")
    
    print(f"\n📊 统计信息:")
    print(f"  • 支持职业数量: {len(all_classes)}")
    print(f"  • 支持货币类型: {len(PoE2CurrencyType)}")
    print(f"  • 构筑目标类型: {len(PoE2BuildGoal)}")
    print(f"  • 武器类型数量: {len(PoE2WeaponType)}")
    
    print(f"\n🚀 系统状态: 准备进入下一开发阶段!")
    print("   可以开始实现接口层、数据源集成和AI协调器")


if __name__ == "__main__":
    demonstrate_poe2_models()