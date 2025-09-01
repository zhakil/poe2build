"""
测试构筑工厂 - 生成各种测试用的构筑数据

提供灵活的构筑数据生成功能，支持：
- 不同类型的构筑(预算型、高端型、平衡型)
- 不同职业的构筑
- 特定测试场景的构筑
- 批量生成数据
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from src.poe2build.models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from src.poe2build.models.characters import (
    PoE2CharacterClass, PoE2Ascendancy, PoE2Character, PoE2CharacterAttributes
)


@dataclass
class BuildTemplate:
    """构筑模板定义"""
    name_pattern: str
    character_class: PoE2CharacterClass
    ascendancy: Optional[PoE2Ascendancy] = None
    level_range: tuple = (80, 95)
    dps_range: tuple = (400000, 1200000)
    ehp_range: tuple = (6000, 12000)
    cost_range: tuple = (5.0, 30.0)
    main_skills: List[str] = field(default_factory=list)
    support_gems: List[str] = field(default_factory=list)
    key_items: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    build_goal: PoE2BuildGoal = PoE2BuildGoal.ENDGAME_CONTENT


class TestBuildFactory:
    """测试构筑工厂主类"""
    
    # 基础配置数据
    SKILL_GEMS = {
        PoE2CharacterClass.SORCERESS: {
            'main': ['Lightning Bolt', 'Chain Lightning', 'Ice Shard', 'Fireball', 'Frost Bolt'],
            'support': [
                'Added Lightning Damage', 'Lightning Penetration', 'Elemental Focus',
                'Added Cold Damage', 'Cold Penetration', 'Hypothermia',
                'Added Fire Damage', 'Fire Penetration', 'Elemental Damage with Attacks'
            ]
        },
        PoE2CharacterClass.RANGER: {
            'main': ['Ice Shot', 'Lightning Arrow', 'Explosive Shot', 'Poison Arrow', 'Split Shot'],
            'support': [
                'Added Cold Damage', 'Pierce', 'Elemental Damage with Attacks',
                'Added Lightning Damage', 'Chain', 'Multiple Projectiles',
                'Added Fire Damage', 'Increased Area of Effect'
            ]
        },
        PoE2CharacterClass.WITCH: {
            'main': ['Raise Zombie', 'Fireball', 'Dark Ritual', 'Bone Spear', 'Summon Skeletons'],
            'support': [
                'Minion Damage Support', 'Minion Life Support', 'Melee Minion Support',
                'Added Fire Damage', 'Elemental Focus', 'Spell Echo'
            ]
        },
        PoE2CharacterClass.MONK: {
            'main': ['Spirit Wave', 'Falling Thunder', 'Palm Strike', 'Tempest Bell', 'Glacial Cascade'],
            'support': [
                'Melee Physical Damage', 'Increased Area of Effect', 'Added Lightning Damage',
                'Elemental Damage with Attacks', 'Multistrike', 'Fortify'
            ]
        },
        PoE2CharacterClass.MERCENARY: {
            'main': ['Crossbow Shot', 'Gas Arrow', 'Explosive Grenade', 'Armor Piercing Shot'],
            'support': [
                'Added Fire Damage', 'Pierce', 'Increased Area of Effect',
                'Physical Projectile Damage', 'Point Blank', 'Chain'
            ]
        },
        PoE2CharacterClass.WARRIOR: {
            'main': ['Slam', 'Shield Charge', 'Ancestral Totem', 'Earthquake', 'Cleave'],
            'support': [
                'Melee Physical Damage', 'Increased Area of Effect', 'Fortify',
                'Multistrike', 'Melee Splash', 'Added Fire Damage'
            ]
        }
    }
    
    UNIQUE_ITEMS = {
        PoE2CharacterClass.SORCERESS: [
            'Staff of Power', 'Lightning Amulet', 'Spell Echo Ring', 'Mana Shield',
            'Elemental Focus Gloves', 'Storm Crown'
        ],
        PoE2CharacterClass.RANGER: {
            'weapons': ['Bow of Frost', 'Lightning Bow', 'Explosive Bow'],
            'armor': ['Hunter\'s Garb', 'Ranger Boots', 'Precision Gloves'],
            'jewelry': ['Eagle Eye Ring', 'Wind Dancer Amulet']
        },
        PoE2CharacterClass.WITCH: [
            'Necromancer Staff', 'Bone Ring', 'Death Amulet', 'Corpse Crown',
            'Minion Master Gloves', 'Soul Keeper'
        ],
        PoE2CharacterClass.MONK: [
            'Spirit Staff', 'Meditation Beads', 'Chi Flow Ring', 'Monk Robes',
            'Inner Peace Amulet', 'Balance Boots'
        ],
        PoE2CharacterClass.MERCENARY: [
            'Precision Crossbow', 'Explosive Bolts', 'Mercenary Coat', 'Tactical Gloves',
            'Combat Ring', 'Soldier Amulet'
        ],
        PoE2CharacterClass.WARRIOR: [
            'Berserker Axe', 'Defender Shield', 'Warrior Helm', 'Strength Belt',
            'Battle Ring', 'Courage Amulet'
        ]
    }
    
    # 预定义构筑模板
    BUILD_TEMPLATES = {
        'budget': BuildTemplate(
            name_pattern="Budget {skill} {class}",
            character_class=PoE2CharacterClass.MONK,
            level_range=(75, 85),
            dps_range=(300000, 600000),
            ehp_range=(5000, 8000),
            cost_range=(2.0, 8.0),
            tags=['budget', 'league_start', 'beginner'],
            build_goal=PoE2BuildGoal.BUDGET_FRIENDLY
        ),
        'endgame': BuildTemplate(
            name_pattern="Endgame {skill} {class}",
            character_class=PoE2CharacterClass.SORCERESS,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            level_range=(90, 100),
            dps_range=(800000, 1500000),
            ehp_range=(8000, 12000),
            cost_range=(15.0, 50.0),
            tags=['endgame', 'expensive', 'min-max'],
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT
        ),
        'speed_clear': BuildTemplate(
            name_pattern="Speed {skill} {class}",
            character_class=PoE2CharacterClass.RANGER,
            ascendancy=PoE2Ascendancy.DEADEYE,
            level_range=(85, 95),
            dps_range=(600000, 1000000),
            ehp_range=(6500, 9000),
            cost_range=(10.0, 25.0),
            tags=['speed', 'mapping', 'clear'],
            build_goal=PoE2BuildGoal.CLEAR_SPEED
        ),
        'boss_killer': BuildTemplate(
            name_pattern="Boss Killer {skill} {class}",
            character_class=PoE2CharacterClass.WARRIOR,
            ascendancy=PoE2Ascendancy.TITAN,
            level_range=(88, 98),
            dps_range=(1000000, 2000000),
            ehp_range=(10000, 15000),
            cost_range=(20.0, 60.0),
            tags=['boss_killer', 'single_target', 'tanky'],
            build_goal=PoE2BuildGoal.BOSS_KILLING
        )
    }
    
    def __init__(self, seed: Optional[int] = None):
        """
        初始化构筑工厂
        
        Args:
            seed: 随机数种子，用于确定性测试
        """
        if seed is not None:
            random.seed(seed)
        self._build_counter = 0
    
    def create_build_stats(self, 
                          dps_range: tuple = (500000, 1000000),
                          ehp_range: tuple = (6000, 10000),
                          resistance_base: int = 75) -> PoE2BuildStats:
        """创建构筑统计数据"""
        total_dps = random.randint(*dps_range)
        ehp = random.randint(*ehp_range)
        
        # 抗性随机变化
        fire_res = resistance_base + random.randint(-3, 5)
        cold_res = resistance_base + random.randint(-3, 5)
        lightning_res = resistance_base + random.randint(-3, 5)
        chaos_res = random.randint(-60, 20)
        
        # 生命值和能量护盾分配
        life_ratio = random.uniform(0.6, 0.8)
        life = int(ehp * life_ratio)
        energy_shield = ehp - life
        
        return PoE2BuildStats(
            total_dps=total_dps,
            effective_health_pool=ehp,
            fire_resistance=min(fire_res, 80),
            cold_resistance=min(cold_res, 80),
            lightning_resistance=min(lightning_res, 80),
            chaos_resistance=chaos_res,
            life=life,
            energy_shield=max(energy_shield, 0),
            critical_strike_chance=random.uniform(30.0, 70.0),
            critical_strike_multiplier=random.uniform(250.0, 400.0),
            attack_speed=random.uniform(1.5, 3.5),
            cast_speed=random.uniform(2.0, 4.5),
            movement_speed=random.uniform(105.0, 140.0)
        )
    
    def create_character_attributes(self, 
                                   character_class: PoE2CharacterClass,
                                   level: int = 85) -> PoE2CharacterAttributes:
        """创建角色属性"""
        # 根据职业设置基础属性傾向
        base_attrs = {
            PoE2CharacterClass.SORCERESS: {'str': 50, 'dex': 100, 'int': 200},
            PoE2CharacterClass.RANGER: {'str': 80, 'dex': 200, 'int': 70},
            PoE2CharacterClass.WITCH: {'str': 60, 'dex': 80, 'int': 210},
            PoE2CharacterClass.MONK: {'str': 150, 'dex': 150, 'int': 50},
            PoE2CharacterClass.MERCENARY: {'str': 120, 'dex': 180, 'int': 50},
            PoE2CharacterClass.WARRIOR: {'str': 220, 'dex': 100, 'int': 30}
        }
        
        base = base_attrs.get(character_class, {'str': 100, 'dex': 100, 'int': 100})
        
        # 根据等级调整属性
        level_bonus = max(0, level - 70) * 3
        
        return PoE2CharacterAttributes(
            strength=base['str'] + random.randint(0, level_bonus),
            dexterity=base['dex'] + random.randint(0, level_bonus),
            intelligence=base['int'] + random.randint(0, level_bonus)
        )
    
    def create_build_from_template(self, template_name: str, **overrides) -> PoE2Build:
        """从模板创建构筑"""
        if template_name not in self.BUILD_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.BUILD_TEMPLATES[template_name]
        
        # 生成基础数据
        level = random.randint(*template.level_range)
        character_class = template.character_class
        
        # 获取技能数据
        skills = self.SKILL_GEMS.get(character_class, {})
        main_skill = random.choice(skills.get('main', ['Basic Attack']))
        support_gems = random.sample(
            skills.get('support', ['Support Gem']), 
            random.randint(2, 4)
        )
        
        # 生成构筑名称
        build_name = template.name_pattern.format(
            skill=main_skill,
            class=character_class.value
        )
        
        # 创建统计数据
        stats = self.create_build_stats(
            dps_range=template.dps_range,
            ehp_range=template.ehp_range
        )
        
        # 生成成本
        estimated_cost = random.uniform(*template.cost_range)
        
        # 获取关键物品
        class_items = self.UNIQUE_ITEMS.get(character_class, [])
        if isinstance(class_items, dict):
            key_items = []
            for category, items in class_items.items():
                if random.random() > 0.3:  # 70%几率包含该类别物品
                    key_items.extend(random.sample(items, random.randint(1, 2)))
        else:
            key_items = random.sample(class_items, random.randint(1, 3))
        
        # 应用覆盖参数
        build_data = {
            'name': build_name,
            'character_class': character_class,
            'level': level,
            'ascendancy': template.ascendancy,
            'stats': stats,
            'estimated_cost': estimated_cost,
            'currency_type': 'divine',
            'goal': template.build_goal,
            'main_skill_gem': main_skill,
            'support_gems': support_gems,
            'key_items': key_items,
            'passive_keystones': self._generate_passive_keystones(character_class),
            'notes': f"Generated test build - {template_name} template",
            'created_by': 'test_factory',
            'league': random.choice(['Standard', 'Hardcore']),
            'hardcore': random.choice([True, False]),
            'tags': template.tags.copy()
        }
        
        # 应用用户覆盖
        build_data.update(overrides)
        
        self._build_counter += 1
        return PoE2Build(**build_data)
    
    def create_random_build(self, character_class: Optional[PoE2CharacterClass] = None) -> PoE2Build:
        """创建随机构筑"""
        if character_class is None:
            character_class = random.choice(list(PoE2CharacterClass))
        
        # 随机选择模板类型
        template_name = random.choice(list(self.BUILD_TEMPLATES.keys()))
        
        return self.create_build_from_template(
            template_name,
            character_class=character_class
        )
    
    def create_build_batch(self, 
                          count: int,
                          template_distribution: Optional[Dict[str, float]] = None) -> List[PoE2Build]:
        """
        批量创建构筑
        
        Args:
            count: 要创建的构筑数量
            template_distribution: 模板分布比例 {template_name: probability}
        
        Returns:
            构筑列表
        """
        if template_distribution is None:
            template_distribution = {
                'budget': 0.3,
                'endgame': 0.25,
                'speed_clear': 0.25,
                'boss_killer': 0.2
            }
        
        builds = []
        
        for i in range(count):
            # 根据分布选择模板
            rand_val = random.random()
            cumulative = 0
            selected_template = 'budget'  # 默认模板
            
            for template_name, probability in template_distribution.items():
                cumulative += probability
                if rand_val <= cumulative:
                    selected_template = template_name
                    break
            
            # 随机选择职业
            character_class = random.choice(list(PoE2CharacterClass))
            
            build = self.create_build_from_template(
                selected_template,
                character_class=character_class,
                created_by=f'batch_generator_{i:04d}'
            )
            
            builds.append(build)
        
        return builds
    
    def create_specific_scenario_builds(self) -> Dict[str, List[PoE2Build]]:
        """创建特定测试场景的构筑数据"""
        scenarios = {
            # 极端预算型构筑
            'ultra_budget': [
                self.create_build_from_template(
                    'budget',
                    name='Ultra Budget Starter',
                    estimated_cost=1.0,
                    stats=self.create_build_stats(
                        dps_range=(200000, 350000),
                        ehp_range=(4000, 6000)
                    )
                )
            ],
            
            # 高端构筑
            'mirror_tier': [
                self.create_build_from_template(
                    'endgame',
                    name='Mirror Tier Lightning God',
                    estimated_cost=200.0,
                    stats=self.create_build_stats(
                        dps_range=(3000000, 5000000),
                        ehp_range=(15000, 20000)
                    )
                )
            ],
            
            # 不平衡构筑(高DPS但低EHP)
            'glass_cannon': [
                self.create_build_from_template(
                    'speed_clear',
                    name='Glass Cannon Build',
                    stats=self.create_build_stats(
                        dps_range=(2000000, 3000000),
                        ehp_range=(3000, 5000)
                    ),
                    tags=['glass_cannon', 'high_risk', 'high_reward']
                )
            ],
            
            # 均衡型构筑
            'balanced': [
                self.create_build_from_template(
                    'endgame',
                    name='Perfectly Balanced Build',
                    stats=self.create_build_stats(
                        dps_range=(800000, 1200000),
                        ehp_range=(8000, 10000)
                    ),
                    estimated_cost=20.0
                )
            ],
            
            # PvP专用构筑
            'pvp_focused': [
                PoE2Build(
                    name='PvP Specialist',
                    character_class=PoE2CharacterClass.MERCENARY,
                    level=95,
                    ascendancy=PoE2Ascendancy.WITCHHUNTER,
                    goal=PoE2BuildGoal.PVP,
                    stats=self.create_build_stats(
                        dps_range=(600000, 1000000),
                        ehp_range=(9000, 12000)
                    ),
                    estimated_cost=35.0,
                    main_skill_gem='Explosive Grenade',
                    support_gems=['Increased Area', 'Added Fire Damage', 'Pierce'],
                    tags=['pvp', 'burst_damage', 'mobility']
                )
            ]
        }
        
        return scenarios
    
    def create_progression_builds(self, character_class: PoE2CharacterClass) -> List[PoE2Build]:
        """创建同一职业的进阶构筑列表"""
        progression_stages = [
            {
                'name': 'League Start',
                'template': 'budget',
                'level_range': (60, 75),
                'cost_range': (0.5, 3.0)
            },
            {
                'name': 'Early Maps',
                'template': 'speed_clear',
                'level_range': (75, 85),
                'cost_range': (3.0, 10.0)
            },
            {
                'name': 'Mid Tier',
                'template': 'endgame',
                'level_range': (85, 92),
                'cost_range': (10.0, 30.0)
            },
            {
                'name': 'End Game',
                'template': 'boss_killer',
                'level_range': (92, 100),
                'cost_range': (30.0, 100.0)
            }
        ]
        
        builds = []
        for i, stage in enumerate(progression_stages):
            level = random.randint(*stage['level_range'])
            cost = random.uniform(*stage['cost_range'])
            
            build = self.create_build_from_template(
                stage['template'],
                character_class=character_class,
                name=f"{character_class.value} {stage['name']} Build",
                level=level,
                estimated_cost=cost,
                notes=f"Progression build stage {i+1}: {stage['name']}",
                tags=[f"stage_{i+1}", stage['name'].lower().replace(' ', '_')]
            )
            
            builds.append(build)
        
        return builds
    
    def _generate_passive_keystones(self, character_class: PoE2CharacterClass) -> List[str]:
        """生成适合的天赋技能石"""
        keystone_pool = {
            PoE2CharacterClass.SORCERESS: [
                'Elemental Overload', 'Lightning Mastery', 'Spell Damage',
                'Energy Shield Mastery', 'Critical Strike Mastery'
            ],
            PoE2CharacterClass.RANGER: [
                'Bow Mastery', 'Projectile Mastery', 'Critical Strike Mastery',
                'Movement Mastery', 'Evasion Mastery'
            ],
            PoE2CharacterClass.WITCH: [
                'Minion Mastery', 'Death Magic', 'Corpse Mastery',
                'Dark Arts', 'Spirit Mastery'
            ],
            PoE2CharacterClass.MONK: [
                'Martial Arts', 'Inner Force', 'Spirit Mastery',
                'Combo Mastery', 'Balance Mastery'
            ],
            PoE2CharacterClass.MERCENARY: [
                'Crossbow Mastery', 'Tactical Mastery', 'Explosive Mastery',
                'Precision Mastery', 'Combat Mastery'
            ],
            PoE2CharacterClass.WARRIOR: [
                'Weapon Mastery', 'Shield Mastery', 'Strength Mastery',
                'Fortification', 'Battle Mastery'
            ]
        }
        
        available_keystones = keystone_pool.get(character_class, ['Generic Mastery'])
        return random.sample(available_keystones, random.randint(2, 4))
    
    def get_factory_statistics(self) -> Dict[str, Any]:
        """获取工厂统计信息"""
        return {
            'builds_created': self._build_counter,
            'available_templates': list(self.BUILD_TEMPLATES.keys()),
            'supported_classes': list(PoE2CharacterClass),
            'random_seed_used': True if hasattr(random, '_inst') else False
        }


# =============================================================================
# 便捷函数
# =============================================================================

def create_test_builds(count: int = 10, seed: Optional[int] = None) -> List[PoE2Build]:
    """快速创建测试构筑列表"""
    factory = TestBuildFactory(seed=seed)
    return factory.create_build_batch(count)


def create_builds_for_class(character_class: PoE2CharacterClass, count: int = 5) -> List[PoE2Build]:
    """为特定职业创建测试构筑"""
    factory = TestBuildFactory()
    return [factory.create_random_build(character_class) for _ in range(count)]


def create_builds_by_budget(budget_ranges: List[tuple]) -> Dict[str, List[PoE2Build]]:
    """按预算范围创建构筑"""
    factory = TestBuildFactory()
    builds_by_budget = {}
    
    for i, (min_cost, max_cost) in enumerate(budget_ranges):
        budget_key = f"budget_{min_cost}_{max_cost}"
        builds = []
        
        for _ in range(3):  # 每个预算范围3个构筑
            build = factory.create_random_build()
            # 调整成本到指定范围
            build.estimated_cost = random.uniform(min_cost, max_cost)
            builds.append(build)
        
        builds_by_budget[budget_key] = builds
    
    return builds_by_budget


def create_edge_case_builds() -> Dict[str, PoE2Build]:
    """创建边界情况测试构筑"""
    factory = TestBuildFactory()
    
    return {
        'min_level': factory.create_build_from_template('budget', level=1),
        'max_level': factory.create_build_from_template('endgame', level=100),
        'zero_cost': factory.create_build_from_template('budget', estimated_cost=0.0),
        'max_resistance': factory.create_build_from_template(
            'endgame',
            stats=factory.create_build_stats(resistance_base=80)
        ),
        'negative_chaos_res': factory.create_build_from_template(
            'speed_clear',
            stats=PoE2BuildStats(
                total_dps=800000,
                effective_health_pool=7000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-60
            )
        )
    }
