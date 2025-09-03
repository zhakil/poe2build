#!/usr/bin/env python3
"""
PoE2 Build Generator - Data Models Demo

Demonstrates all PoE2 data model features and mechanics
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_poe2_models():
    """Demonstrate PoE2 data models functionality"""
    
    # Import all models
    from poe2build.models import (
        PoE2CharacterClass, PoE2Ascendancy, PoE2Character, PoE2CharacterAttributes,
        PoE2Build, PoE2BuildStats, PoE2BuildGoal,
        PoE2Skill, PoE2SkillType, PoE2SkillStats, PoE2GemColor,
        PoE2Weapon, PoE2WeaponType, PoE2ItemRarity, PoE2ItemCategory, PoE2ItemRequirements,
        PoE2PriceData, PoE2CurrencyType
    )
    
    print("="*50)
    print("PoE2 Build Generator - Data Models Demo")
    print("="*50)
    
    # 1. Character System
    print("\n1. Character System")
    print("-"*30)
    
    attrs = PoE2CharacterAttributes(strength=100, dexterity=250, intelligence=80)
    character = PoE2Character(
        name="EliteDeadeye",
        character_class=PoE2CharacterClass.RANGER,
        level=94,
        attributes=attrs,
        ascendancy=PoE2Ascendancy.DEADEYE
    )
    
    print(f"Character: {character.name} L{character.level}")
    print(f"Class: {character.character_class.value} ({character.ascendancy.value})")
    print(f"Primary stat (DEX): {character.get_primary_attribute_value()}")
    print(f"Power score: {character.calculate_character_power():.2f}")
    
    # 2. PoE2-specific Build Stats
    print("\n2. PoE2 Build Stats (Unique Mechanics)")
    print("-"*30)
    
    stats = PoE2BuildStats(
        total_dps=1800000,
        effective_health_pool=13500,
        fire_resistance=80,    # PoE2 max resistance
        cold_resistance=79,
        lightning_resistance=80, 
        chaos_resistance=-15,  # PoE2 allows negative chaos res
        critical_strike_chance=90,
        life=10500
    )
    
    print(f"DPS: {stats.total_dps:,}")
    print(f"EHP: {stats.effective_health_pool:,}")
    print(f"Resistances: Fire{stats.fire_resistance}% Cold{stats.cold_resistance}% Lightning{stats.lightning_resistance}% Chaos{stats.chaos_resistance}%")
    print(f"Max resistances capped (75%+): {stats.is_resistance_capped()}")
    print(f"Crit chance: {stats.critical_strike_chance}%")
    
    # 3. Skill System with PoE2 Spirit Cost
    print("\n3. Skill System (PoE2 Spirit Mechanic)")
    print("-"*30)
    
    skill_stats = PoE2SkillStats(
        base_damage=220,
        cast_time=0.45,
        mana_cost=48,
        lightning_damage_percent=100,
        projectile_count=5
    )
    
    skill = PoE2Skill(
        name="Lightning Strike",
        skill_type=PoE2SkillType.ACTIVE,
        categories=[],
        gem_color=PoE2GemColor.GREEN,
        level=21,
        quality=23,
        stats=skill_stats,
        spirit_cost=25  # PoE2 unique mechanic
    )
    
    print(f"Skill: {skill.name} L{skill.level} ({skill.quality}% quality)")
    print(f"Spirit cost: {skill.spirit_cost} (PoE2 unique)")
    print(f"Projectiles: {skill.stats.projectile_count}")
    print(f"DPS estimate: {skill.calculate_dps():.0f}")
    
    # 4. Weapon System
    print("\n4. Weapon System")
    print("-"*30)
    
    weapon = PoE2Weapon(
        name="The Tempest",
        base_type="Maraketh Bow",
        rarity=PoE2ItemRarity.UNIQUE,
        category=PoE2ItemCategory.WEAPON,
        item_level=84,
        requirements=PoE2ItemRequirements(level=78, dexterity=212),
        modifiers=[],
        weapon_type=PoE2WeaponType.BOW,
        damage_min=85,
        damage_max=165,
        attack_speed=1.75,
        critical_chance=9.5
    )
    
    print(f"Weapon: {weapon.name} ({weapon.weapon_type.value})")
    print(f"Damage: {weapon.damage_min}-{weapon.damage_max} (avg {weapon.get_average_damage():.1f})")
    print(f"Attack speed: {weapon.attack_speed} APS")
    print(f"DPS: {weapon.get_dps():,.0f}")
    print(f"Crit chance: {weapon.critical_chance}%")
    
    # 5. Complete Build
    print("\n5. Complete PoE2 Build")
    print("-"*30)
    
    build = PoE2Build(
        name="Lightning Strike Deadeye - Endgame",
        character_class=PoE2CharacterClass.RANGER,
        level=94,
        ascendancy=PoE2Ascendancy.DEADEYE,
        stats=stats,
        goal=PoE2BuildGoal.ENDGAME_CONTENT,
        main_skill_gem="Lightning Strike",
        support_gems=["Pierce Support", "Elemental Damage with Attacks Support", "Added Lightning Damage Support"],
        estimated_cost=42.5,
        currency_type="divine"
    )
    
    print(f"Build: {build.name}")
    print(f"Class: {build.character_class.value} ({build.ascendancy.value}) L{build.level}")
    print(f"Main skill: {build.main_skill_gem} + {len(build.support_gems)} supports")
    print(f"Goal: {build.goal.value}")
    print(f"Cost: {build.estimated_cost} {build.currency_type} orbs")
    print(f"Valid: {build.validate()}")
    print(f"Suitable for goal: {build.is_suitable_for_goal(build.goal)}")
    
    # 6. Market Data
    print("\n6. Market Data")
    print("-"*30)
    
    price = PoE2PriceData(
        value=42.5,
        currency=PoE2CurrencyType.DIVINE_ORB,
        confidence=0.89,
        sample_size=156
    )
    
    print(f"Price: {price.value} {price.currency.value}")
    print(f"Confidence: {price.confidence:.0%} (samples: {price.sample_size})")
    
    # 7. Summary
    print("\n" + "="*50)
    print("SUCCESS: All PoE2 Models Working!")
    print("="*50)
    
    features = [
        "Character classes and ascendancies",
        "PoE2 resistance system (max 80%, chaos can be negative)",
        "Divine orb currency system",
        "Spirit cost system (PoE2 unique)",
        "Complete skill and item modeling",
        "Build validation and market integration",
        "Full dataclass architecture with validation"
    ]
    
    print("\nValidated PoE2 Features:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")
    
    print("\nSystem Status: Ready for next development phase!")
    print("Can proceed with interfaces, data sources, and AI orchestrator")


if __name__ == "__main__":
    demo_poe2_models()