"""
样例构筑数据
用于测试的完整构筑数据集合
"""

from typing import List, Dict, Any
from src.poe2build.models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy


def create_lightning_stormweaver_build() -> PoE2Build:
    """创建闪电风暴使者构筑"""
    stats = PoE2BuildStats(
        total_dps=1250000,
        effective_health_pool=8750,
        fire_resistance=78,
        cold_resistance=76,
        lightning_resistance=79,
        chaos_resistance=-22,
        life=5800,
        energy_shield=2950,
        mana=1200,
        critical_strike_chance=45.2,
        critical_strike_multiplier=320.0,
        attack_speed=0.0,
        cast_speed=3.2,
        movement_speed=118.0,
        block_chance=15.0,
        dodge_chance=8.0,
        physical_dps=0.0,
        elemental_dps=1100000,
        chaos_dps=0.0
    )
    
    return PoE2Build(
        name="Lightning Stormweaver",
        character_class=PoE2CharacterClass.SORCERESS,
        level=92,
        ascendancy=PoE2Ascendancy.STORMWEAVER,
        stats=stats,
        estimated_cost=25.5,
        currency_type="divine",
        goal=PoE2BuildGoal.ENDGAME_CONTENT,
        notes="High-end lightning caster with excellent clear speed and boss damage",
        main_skill_gem="Lightning Bolt",
        support_gems=[
            "Added Lightning Damage",
            "Lightning Penetration", 
            "Elemental Focus",
            "Spell Echo",
            "Increased Critical Strikes"
        ],
        key_items=[
            "Staff of Power",
            "Lightning Amulet of Power", 
            "Stormweaver's Crown",
            "Energy Shield Boots",
            "Lightning Ring x2"
        ],
        passive_keystones=[
            "Elemental Overload",
            "Lightning Mastery",
            "Energy Shield Mastery",
            "Spell Critical Strike Mastery"
        ],
        created_by="test_user",
        source_url="https://example.com/builds/lightning-stormweaver",
        league="Standard",
        last_updated="2024-01-15",
        pob2_code="eNrtXNtu2zYUfhXDuE2AJVuSJdm6qYG4bYdh2DC0BbYNuzcYkYrZyOKCkXyLlr77KNFF...",
        pob2_version="2.35.1"
    )


def create_ice_shot_deadeye_build() -> PoE2Build:
    """创建冰霜射击神射手构筑"""
    stats = PoE2BuildStats(
        total_dps=850000,
        effective_health_pool=9200,
        fire_resistance=75,
        cold_resistance=80,
        lightning_resistance=75,
        chaos_resistance=-30,
        life=6200,
        energy_shield=3000,
        mana=800,
        critical_strike_chance=65.0,
        critical_strike_multiplier=280.0,
        attack_speed=4.2,
        cast_speed=0.0,
        movement_speed=135.0,
        block_chance=0.0,
        dodge_chance=25.0,
        physical_dps=150000,
        elemental_dps=700000,
        chaos_dps=0.0
    )
    
    return PoE2Build(
        name="Ice Shot Deadeye",
        character_class=PoE2CharacterClass.RANGER,
        level=88,
        ascendancy=PoE2Ascendancy.DEADEYE,
        stats=stats,
        estimated_cost=18.2,
        currency_type="divine",
        goal=PoE2BuildGoal.CLEAR_SPEED,
        notes="Fast clear speed ice archer with good projectile mechanics",
        main_skill_gem="Ice Shot",
        support_gems=[
            "Added Cold Damage",
            "Elemental Damage with Attacks",
            "Pierce",
            "Increased Critical Strikes",
            "Hypothermia"
        ],
        key_items=[
            "Ice Bow",
            "Cold Damage Quiver",
            "Ranger's Helmet",
            "Evasion Chest",
            "Speed Boots"
        ],
        passive_keystones=[
            "Point Blank",
            "Cold Mastery",
            "Projectile Mastery",
            "Critical Strike Mastery"
        ],
        created_by="test_user",
        league="Standard",
        last_updated="2024-01-12"
    )


def create_budget_monk_invoker_build() -> PoE2Build:
    """创建预算僧侣祈法者构筑"""
    stats = PoE2BuildStats(
        total_dps=520000,
        effective_health_pool=7500,
        fire_resistance=75,
        cold_resistance=75,
        lightning_resistance=75,
        chaos_resistance=-30,
        life=5500,
        energy_shield=2000,
        mana=600,
        critical_strike_chance=25.0,
        critical_strike_multiplier=200.0,
        attack_speed=3.8,
        cast_speed=0.0,
        movement_speed=110.0,
        block_chance=20.0,
        dodge_chance=15.0,
        physical_dps=400000,
        elemental_dps=120000,
        chaos_dps=0.0
    )
    
    return PoE2Build(
        name="Budget Monk Invoker",
        character_class=PoE2CharacterClass.MONK,
        level=85,
        ascendancy=PoE2Ascendancy.INVOKER,
        stats=stats,
        estimated_cost=3.5,
        currency_type="divine",
        goal=PoE2BuildGoal.BUDGET_FRIENDLY,
        notes="League starter friendly with good survivability",
        main_skill_gem="Spirit Wave",
        support_gems=[
            "Melee Physical Damage",
            "Increased Area of Effect",
            "Fortify",
            "Multistrike"
        ],
        key_items=[
            "Basic Staff",
            "Life Ring x2",
            "Resistance Amulet",
            "Armour Chest"
        ],
        passive_keystones=[
            "Unwavering Stance",
            "Spirit Mastery",
            "Life Mastery",
            "Area Damage Mastery"
        ],
        created_by="test_user",
        league="Standard",
        last_updated="2024-01-10"
    )


def create_boss_killing_witch_build() -> PoE2Build:
    """创建专门击杀Boss的女巫构筑"""
    stats = PoE2BuildStats(
        total_dps=2100000,
        effective_health_pool=6800,
        fire_resistance=79,
        cold_resistance=75,
        lightning_resistance=75,
        chaos_resistance=-20,
        life=4800,
        energy_shield=2000,
        mana=1500,
        critical_strike_chance=75.0,
        critical_strike_multiplier=450.0,
        attack_speed=0.0,
        cast_speed=2.8,
        movement_speed=105.0,
        block_chance=10.0,
        dodge_chance=5.0,
        physical_dps=0.0,
        elemental_dps=1800000,
        chaos_dps=300000
    )
    
    return PoE2Build(
        name="Boss Killer Infernalist",
        character_class=PoE2CharacterClass.WITCH,
        level=95,
        ascendancy=PoE2Ascendancy.INFERNALIST,
        stats=stats,
        estimated_cost=45.0,
        currency_type="divine",
        goal=PoE2BuildGoal.BOSS_KILLING,
        notes="Ultra high DPS specialist for endgame bosses",
        main_skill_gem="Infernal Bolt",
        support_gems=[
            "Added Fire Damage",
            "Fire Penetration",
            "Elemental Focus",
            "Concentrated Effect",
            "Increased Critical Damage"
        ],
        key_items=[
            "Infernalist's Sceptre",
            "Fire Damage Amulet",
            "High-tier Fire Ring x2",
            "Boss Killer Helmet",
            "Fire Resistance Shield"
        ],
        passive_keystones=[
            "Elemental Overload",
            "Fire Mastery",
            "Critical Strike Mastery",
            "Spell Damage Mastery",
            "Penetration Mastery"
        ],
        created_by="boss_specialist",
        league="Standard",
        last_updated="2024-01-18"
    )


def create_league_starter_warrior_build() -> PoE2Build:
    """创建赛季开荒战士构筑"""
    stats = PoE2BuildStats(
        total_dps=280000,
        effective_health_pool=8500,
        fire_resistance=75,
        cold_resistance=75,
        lightning_resistance=75,
        chaos_resistance=-30,
        life=6500,
        energy_shield=2000,
        mana=400,
        critical_strike_chance=15.0,
        critical_strike_multiplier=150.0,
        attack_speed=2.2,
        cast_speed=0.0,
        movement_speed=100.0,
        block_chance=35.0,
        dodge_chance=5.0,
        physical_dps=280000,
        elemental_dps=0.0,
        chaos_dps=0.0
    )
    
    return PoE2Build(
        name="League Starter Titan",
        character_class=PoE2CharacterClass.WARRIOR,
        level=78,
        ascendancy=PoE2Ascendancy.TITAN,
        stats=stats,
        estimated_cost=0.5,
        currency_type="divine",
        goal=PoE2BuildGoal.LEAGUE_START,
        notes="No-gear-required league starter with excellent survivability",
        main_skill_gem="Ground Slam",
        support_gems=[
            "Melee Physical Damage",
            "Added Fire Damage",
            "Increased Area of Effect",
            "Fortify"
        ],
        key_items=[
            "Basic Two-Handed Axe",
            "Life Ring",
            "Resistance Amulet",
            "Heavy Armor"
        ],
        passive_keystones=[
            "Resolute Technique",
            "Life Mastery", 
            "Two-Handed Mastery",
            "Block Mastery"
        ],
        created_by="league_starter_pro",
        league="Standard",
        last_updated="2024-01-08"
    )


def create_experimental_mercenary_build() -> PoE2Build:
    """创建实验性佣兵构筑"""
    stats = PoE2BuildStats(
        total_dps=950000,
        effective_health_pool=7200,
        fire_resistance=78,
        cold_resistance=77,
        lightning_resistance=76,
        chaos_resistance=10,  # 正混沌抗性
        life=5200,
        energy_shield=2000,
        mana=900,
        critical_strike_chance=55.0,
        critical_strike_multiplier=300.0,
        attack_speed=3.5,
        cast_speed=0.0,
        movement_speed=125.0,
        block_chance=5.0,
        dodge_chance=30.0,
        physical_dps=600000,
        elemental_dps=200000,
        chaos_dps=150000
    )
    
    return PoE2Build(
        name="Chaos Crossbow Witchhunter",
        character_class=PoE2CharacterClass.MERCENARY,
        level=90,
        ascendancy=PoE2Ascendancy.WITCHHUNTER,
        stats=stats,
        estimated_cost=22.0,
        currency_type="divine",
        goal=PoE2BuildGoal.ENDGAME_CONTENT,
        notes="Experimental chaos damage crossbow build with unique mechanics",
        main_skill_gem="Chaos Crossbow Shot",
        support_gems=[
            "Added Chaos Damage",
            "Void Manipulation",
            "Pierce",
            "Increased Critical Strikes",
            "Poison Support"
        ],
        key_items=[
            "Chaos Crossbow",
            "Chaos Damage Quiver",
            "Chaos Resistance Amulet",
            "Evasion Armor",
            "Chaos Ring x2"
        ],
        passive_keystones=[
            "Chaos Mastery",
            "Poison Mastery",
            "Projectile Mastery",
            "Damage Over Time Mastery"
        ],
        created_by="experimental_builder",
        league="Standard",
        last_updated="2024-01-20"
    )


# 构筑数据集合
SAMPLE_BUILDS = {
    'lightning_stormweaver': create_lightning_stormweaver_build(),
    'ice_shot_deadeye': create_ice_shot_deadeye_build(),
    'budget_monk_invoker': create_budget_monk_invoker_build(),
    'boss_killing_witch': create_boss_killing_witch_build(),
    'league_starter_warrior': create_league_starter_warrior_build(),
    'experimental_mercenary': create_experimental_mercenary_build()
}


def get_sample_builds() -> List[PoE2Build]:
    """获取所有样例构筑"""
    return list(SAMPLE_BUILDS.values())


def get_sample_build(build_name: str) -> PoE2Build:
    """根据名称获取特定样例构筑"""
    return SAMPLE_BUILDS.get(build_name)


def get_builds_by_class(character_class: PoE2CharacterClass) -> List[PoE2Build]:
    """根据职业过滤样例构筑"""
    return [build for build in SAMPLE_BUILDS.values() 
            if build.character_class == character_class]


def get_builds_by_goal(goal: PoE2BuildGoal) -> List[PoE2Build]:
    """根据构筑目标过滤样例构筑"""
    return [build for build in SAMPLE_BUILDS.values() 
            if build.goal == goal]


def get_builds_by_budget(max_budget: float) -> List[PoE2Build]:
    """根据预算过滤样例构筑"""
    return [build for build in SAMPLE_BUILDS.values()
            if build.estimated_cost and build.estimated_cost <= max_budget]


# 构筑测试场景
BUILD_TEST_SCENARIOS = {
    'high_dps_scenarios': [
        {
            'name': 'Ultra High DPS Test',
            'builds': ['boss_killing_witch', 'lightning_stormweaver'],
            'min_dps_threshold': 1000000,
            'expected_pass': True
        },
        {
            'name': 'Medium DPS Test',
            'builds': ['ice_shot_deadeye', 'experimental_mercenary'],
            'min_dps_threshold': 500000,
            'expected_pass': True
        }
    ],
    
    'survivability_scenarios': [
        {
            'name': 'High Survivability Test',
            'builds': ['league_starter_warrior', 'ice_shot_deadeye'],
            'min_ehp_threshold': 8000,
            'expected_pass': True
        },
        {
            'name': 'Budget Survivability Test',
            'builds': ['budget_monk_invoker'],
            'min_ehp_threshold': 7000,
            'expected_pass': True
        }
    ],
    
    'budget_scenarios': [
        {
            'name': 'Ultra Budget Test',
            'builds': ['league_starter_warrior', 'budget_monk_invoker'],
            'max_budget': 5.0,
            'expected_pass': True
        },
        {
            'name': 'High Budget Test', 
            'builds': ['boss_killing_witch'],
            'max_budget': 50.0,
            'expected_pass': True
        }
    ],
    
    'resistance_scenarios': [
        {
            'name': 'Standard Resistance Test',
            'builds': ['lightning_stormweaver', 'ice_shot_deadeye'],
            'require_75_all_res': True,
            'expected_pass': True
        },
        {
            'name': 'Chaos Resistance Test',
            'builds': ['experimental_mercenary'],
            'require_positive_chaos_res': True,
            'expected_pass': True
        }
    ]
}


def get_test_scenario(scenario_type: str, scenario_name: str) -> Dict[str, Any]:
    """获取测试场景"""
    scenarios = BUILD_TEST_SCENARIOS.get(scenario_type, {})
    return next((s for s in scenarios if s['name'] == scenario_name), {})


def get_builds_for_scenario(scenario: Dict[str, Any]) -> List[PoE2Build]:
    """根据测试场景获取对应的构筑列表"""
    build_names = scenario.get('builds', [])
    return [SAMPLE_BUILDS[name] for name in build_names if name in SAMPLE_BUILDS]