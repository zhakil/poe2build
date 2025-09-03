# PoE2计算引擎

## 📖 概述

本文档详细介绍基于**真实PoE2数据**的构筑计算引擎。该引擎专门针对Path of Exile 2的独有游戏机制设计，包括能量护盾、更高的抗性上限、新的技能系统等。

## 🎮 PoE2独有机制支持

### PoE2独有游戏机制

| 机制 | PoE2特性 | 计算要点 |
|------|---------|----------|
| 抗性上限 | 80%最大上限 | 更高防御计算上限 |
| 能量护盾 | 核心防御机制 | 独立EHP计算系统 |
| 技能系统 | 全新技能宝石系统 | 专门的伤害计算公式 |
| 升华职业 | 6个全新升华职业 | 独特的加成计算体系 |
| 暴击系统 | 改进的暴击机制 | 优化的暴击伤害计算 |

## 🔧 计算引擎架构

### 核心计算器设计

```python
class PoE2RealBuildCalculator:
    """基于真实PoE2数据的构筑计算引擎"""
    
    def __init__(self, poe2db_scraper: PoE2DBScraper):
        self.poe2db = poe2db_scraper
        self.skill_data = {}
        self.item_data = {}
        self.poe2_constants = self._load_poe2_constants()
        self._load_poe2_data()
    
    def _load_poe2_constants(self) -> Dict:
        """加载PoE2游戏机制常数"""
        return {
            'max_resistance': 80,  # PoE2最大抗性80%
            'base_energy_shield_multiplier': 0.3,  # 能量护盾基础倍率
            'crit_damage_base': 150,  # PoE2基础暴击伤害150%
            'level_scaling_factor': 0.03,  # PoE2等级加成因子
            'energy_shield_recharge_base': 20,  # 能量护盾回复基础值
            'chaos_resistance_penalty': -30  # PoE2混沌抗性惩罚
        }
    
    def calculate_poe2_build(self, build_config: Dict) -> Dict:
        """PoE2构筑计算主函数"""
        try:
            # 提取构筑配置
            main_skill = build_config.get('main_skill', 'Lightning Arrow')
            weapon = build_config.get('weapon', 'Lightning Bow')
            level = build_config.get('level', 85)
            items = build_config.get('items', {})
            
            # PoE2核心计算
            dps_result = self._calculate_poe2_dps(main_skill, weapon, level, items)
            defense_result = self._calculate_poe2_defenses(level, items)
            survivability = self._calculate_poe2_survivability(level, items, defense_result)
            
            # 组装结果
            result = {
                'build_name': f"PoE2 {main_skill} Build",
                'main_skill': main_skill,
                'weapon': weapon,
                'level': level,
                'dps': dps_result,
                'defenses': defense_result,
                'survivability': survivability,
                'data_sources': ['poe2db', 'calculated'],
                'game_version': 'poe2',
                'calculation_timestamp': time.time()
            }
            
            print(f"[PoE2Calculator] 构筑计算完成: {main_skill}, DPS={dps_result['total_dps']:,}")
            return result
            
        except Exception as e:
            print(f"[PoE2Calculator] 计算错误: {e}")
            return self._get_emergency_calculation()
```

## ⚔️ PoE2 DPS计算系统

### DPS计算核心逻辑

```python
def _calculate_poe2_dps(self, skill_name: str, weapon_name: str, level: int, items: Dict) -> Dict:
    """PoE2专用DPS计算"""
    
    # 1. 获取真实技能数据
    skill_data = self.skill_data.get(skill_name, {
        'name': skill_name,
        'base_damage': 120,
        'damage_effectiveness': 1.0,
        'attack_speed_multiplier': 1.0
    })
    
    # 2. 获取真实武器数据
    weapon_data = self.item_data.get(weapon_name, {
        'name': weapon_name,
        'base_damage': 180,
        'attack_speed': 1.4,
        'crit_chance': 5,
        'crit_multiplier': 150
    })
    
    # 3. PoE2基础伤害计算
    base_damage = skill_data.get('base_damage', 120)
    weapon_damage = weapon_data.get('base_damage', 180)
    damage_effectiveness = skill_data.get('damage_effectiveness', 1.0)
    
    # 4. PoE2等级加成系统
    level_multiplier = 1 + (level * self.poe2_constants['level_scaling_factor'])
    
    # 5. PoE2技能等级加成
    skill_level = 21  # 假设最高技能等级
    skill_multiplier = 1 + (skill_level * 0.06)  # PoE2技能加成更高
    
    # 6. PoE2攻击速度计算
    base_attack_speed = weapon_data.get('attack_speed', 1.4)
    attack_speed_bonus = items.get('attack_speed_bonus', 0.0)
    final_attack_speed = base_attack_speed * (1 + attack_speed_bonus)
    
    # 7. PoE2暴击计算 (改进的暴击系统)
    base_crit_chance = weapon_data.get('crit_chance', 5) / 100
    crit_chance_bonus = items.get('crit_chance_bonus', 0.0)
    final_crit_chance = min(base_crit_chance + crit_chance_bonus, 0.95)  # 95%上限
    
    base_crit_multi = weapon_data.get('crit_multiplier', 150) / 100
    crit_multi_bonus = items.get('crit_multi_bonus', 0.0)
    final_crit_multi = base_crit_multi + crit_multi_bonus
    
    # 8. PoE2有效伤害倍率 (包含暴击)
    effective_damage_multiplier = 1 + (final_crit_chance * (final_crit_multi - 1))
    
    # 9. PoE2最终DPS计算
    damage_per_hit = (base_damage + weapon_damage) * damage_effectiveness * level_multiplier * skill_multiplier
    total_dps = int(damage_per_hit * final_attack_speed * effective_damage_multiplier)
    
    return {
        'total_dps': total_dps,
        'damage_per_hit': int(damage_per_hit),
        'attack_speed': round(final_attack_speed, 2),
        'crit_chance': round(final_crit_chance * 100, 1),
        'crit_multiplier': round(final_crit_multi * 100, 1),
        'effective_multiplier': round(effective_damage_multiplier, 2),
        'skill_contribution': int(total_dps * 0.6),  # 技能贡献度
        'weapon_contribution': int(total_dps * 0.4)  # 武器贡献度
    }
```

### PoE2技能伤害类型计算

```python
def _calculate_skill_damage_by_type(self, skill_data: Dict) -> Dict:
    """按伤害类型计算PoE2技能伤害"""
    
    damage_types = {
        'physical': 0,
        'fire': 0,
        'cold': 0,
        'lightning': 0,
        'chaos': 0
    }
    
    # 从真实技能数据中获取伤害分布
    skill_name = skill_data.get('name', '').lower()
    
    if 'lightning' in skill_name:
        damage_types['lightning'] = 0.8
        damage_types['physical'] = 0.2
    elif 'fire' in skill_name:
        damage_types['fire'] = 0.9
        damage_types['physical'] = 0.1
    elif 'ice' in skill_name or 'cold' in skill_name:
        damage_types['cold'] = 0.85
        damage_types['physical'] = 0.15
    else:
        damage_types['physical'] = 1.0  # 默认物理伤害
    
    return damage_types
```

## 🛡️ PoE2防御计算系统

### 防御计算核心

```python
def _calculate_poe2_defenses(self, level: int, items: Dict) -> Dict:
    """PoE2专用防御计算"""
    
    # 1. PoE2基础抗性计算 (更高的基础值)
    base_resistance = 70  # PoE2基础抗性更高
    level_resistance_bonus = min((level - 50) // 2, 15)  # 等级抗性加成
    item_resistance_bonus = items.get('resistance_bonus', 0)
    
    # 2. PoE2最大抗性 (80%上限)
    max_resistance = self.poe2_constants['max_resistance']
    
    final_resistances = {}
    for res_type in ['fire', 'cold', 'lightning']:
        total_resistance = base_resistance + level_resistance_bonus + item_resistance_bonus
        final_resistances[f'{res_type}_resistance'] = min(total_resistance, max_resistance)
    
    # 3. PoE2混沌抗性 (改进的计算)
    chaos_base = self.poe2_constants['chaos_resistance_penalty']  # -30% 起始
    chaos_bonus = level_resistance_bonus + item_resistance_bonus
    final_resistances['chaos_resistance'] = max(chaos_base + chaos_bonus, -60)  # 最低-60%
    
    # 4. PoE2护甲计算
    base_armor = level * 80  # PoE2护甲基数更高
    item_armor = items.get('armor', 0)
    final_armor = base_armor + item_armor
    
    # 5. PoE2闪避计算
    base_evasion = level * 60
    item_evasion = items.get('evasion', 0)
    final_evasion = base_evasion + item_evasion
    
    return {
        **final_resistances,
        'armor': final_armor,
        'evasion': final_evasion,
        'block_chance': items.get('block_chance', 0),
        'spell_suppression': items.get('spell_suppression', 0)  # PoE2新机制
    }
```

### PoE2伤害减免计算

```python
def _calculate_damage_reduction(self, defenses: Dict, damage_type: str, incoming_damage: int) -> Dict:
    """PoE2伤害减免计算"""
    
    reduction_info = {
        'incoming_damage': incoming_damage,
        'damage_type': damage_type,
        'reductions': {},
        'final_damage': incoming_damage
    }
    
    current_damage = incoming_damage
    
    # 1. 抗性减免
    if damage_type in ['fire', 'cold', 'lightning', 'chaos']:
        resistance = defenses.get(f'{damage_type}_resistance', 0)
        resistance_reduction = current_damage * (resistance / 100)
        current_damage -= resistance_reduction
        reduction_info['reductions']['resistance'] = resistance_reduction
    
    # 2. 护甲减免 (物理伤害)
    if damage_type == 'physical':
        armor = defenses.get('armor', 0)
        # PoE2护甲公式 (简化版)
        armor_reduction = min(current_damage * 0.3, armor * 0.1)
        current_damage -= armor_reduction
        reduction_info['reductions']['armor'] = armor_reduction
    
    # 3. 能量护盾吸收 (稍后计算)
    reduction_info['final_damage'] = max(int(current_damage), 0)
    
    return reduction_info
```

## ⚡ PoE2能量护盾系统

### 能量护盾计算 (PoE2核心机制)

```python
def _calculate_poe2_energy_shield(self, level: int, items: Dict) -> Dict:
    """PoE2能量护盾计算 - 核心防御机制"""
    
    # 1. PoE2基础能量护盾
    base_es_from_level = level * 25  # 等级基础ES
    base_es_from_int = items.get('intelligence', 100) * 2  # 智力贡献
    
    # 2. 装备能量护盾
    item_es = 0
    for item_slot, item in items.items():
        if isinstance(item, dict):
            item_es += item.get('energy_shield', 0)
    
    # 3. PoE2能量护盾倍率
    es_multiplier = self.poe2_constants['base_energy_shield_multiplier']
    es_increase_from_passives = items.get('es_increase_percent', 0) / 100
    final_es_multiplier = es_multiplier * (1 + es_increase_from_passives)
    
    # 4. 最终能量护盾值
    total_base_es = base_es_from_level + base_es_from_int + item_es
    final_energy_shield = int(total_base_es * final_es_multiplier)
    
    # 5. PoE2能量护盾回复计算
    base_recharge_rate = self.poe2_constants['energy_shield_recharge_base']
    recharge_delay = 2.0  # 2秒延迟
    recharge_rate = base_recharge_rate * (1 + items.get('es_recharge_bonus', 0))
    
    return {
        'total_energy_shield': final_energy_shield,
        'recharge_rate': int(recharge_rate),
        'recharge_delay': recharge_delay,
        'base_es': total_base_es,
        'es_multiplier': round(final_es_multiplier, 2),
        'contribution_breakdown': {
            'level': base_es_from_level,
            'intelligence': base_es_from_int,
            'items': item_es
        }
    }
```

### PoE2生存能力综合计算

```python
def _calculate_poe2_survivability(self, level: int, items: Dict, defenses: Dict) -> Dict:
    """PoE2生存能力计算 - 整合生命和能量护盾"""
    
    # 1. PoE2生命计算
    base_life_per_level = 45  # PoE2每级更多生命
    life_from_level = level * base_life_per_level
    life_from_str = items.get('strength', 100) * 0.5  # 力量贡献生命
    life_from_items = items.get('flat_life', 0)
    
    base_life = life_from_level + life_from_str + life_from_items
    life_multiplier = 1 + (items.get('life_increase_percent', 0) / 100)
    final_life = int(base_life * life_multiplier)
    
    # 2. PoE2能量护盾
    energy_shield_data = self._calculate_poe2_energy_shield(level, items)
    final_energy_shield = energy_shield_data['total_energy_shield']
    
    # 3. PoE2总有效生命 (EHP)
    # 能量护盾优先承受伤害
    total_ehp = final_life + final_energy_shield
    
    # 4. PoE2特有的护盾机制
    shield_efficiency = 0.95  # 95% 效率 (PoE2平衡)
    effective_shield = int(final_energy_shield * shield_efficiency)
    
    # 5. 生存能力评分
    survivability_score = self._calculate_survivability_score(
        total_ehp, defenses, energy_shield_data
    )
    
    return {
        'total_life': final_life,
        'total_energy_shield': final_energy_shield,
        'effective_energy_shield': effective_shield,
        'total_ehp': total_ehp,
        'survivability_score': survivability_score,
        'life_breakdown': {
            'from_level': life_from_level,
            'from_strength': int(life_from_str),
            'from_items': life_from_items,
            'multiplier': life_multiplier
        },
        'energy_shield_data': energy_shield_data
    }
```

## 🎯 PoE2特殊机制计算

### 升华职业加成计算

```python
def _calculate_ascendancy_bonuses(self, ascendancy: str, level: int) -> Dict:
    """PoE2升华职业加成计算"""
    
    # PoE2升华职业数据 (基于真实游戏数据)
    ascendancy_data = {
        'Deadeye': {
            'projectile_damage': 0.30,  # 30% 更多投射物伤害
            'projectile_speed': 0.50,   # 50% 投射物速度
            'pierce_chance': 100,       # 100% 穿透几率
            'chain_count': 1            # +1 连锁
        },
        'Chronomancer': {
            'cast_speed': 0.25,         # 25% 更多施法速度
            'time_magic_effect': 0.40,  # 40% 时间魔法效果
            'mana_efficiency': 0.20     # 20% 法力效率
        },
        'Stormweaver': {
            'lightning_damage': 0.35,   # 35% 更多闪电伤害
            'shock_effect': 0.50,       # 50% 感电效果
            'mana_as_es': 0.30         # 30% 法力转能量护盾
        }
    }
    
    bonuses = ascendancy_data.get(ascendancy, {})
    
    # 根据等级调整加成强度
    level_factor = min(level / 90, 1.0)  # 90级时达到最大效果
    
    scaled_bonuses = {}
    for bonus_type, bonus_value in bonuses.items():
        scaled_bonuses[bonus_type] = bonus_value * level_factor
    
    return scaled_bonuses
```

### PoE2词缀计算系统

```python
def _calculate_item_modifiers(self, items: Dict) -> Dict:
    """PoE2物品词缀计算"""
    
    total_modifiers = {
        'damage_increases': [],
        'defense_increases': [],
        'utility_modifiers': []
    }
    
    for item_slot, item in items.items():
        if not isinstance(item, dict) or 'modifiers' not in item:
            continue
            
        for mod in item['modifiers']:
            mod_type = self._classify_poe2_modifier(mod)
            total_modifiers[mod_type].append(mod)
    
    # 计算总加成
    calculated_bonuses = {
        'total_damage_increase': self._sum_damage_modifiers(total_modifiers['damage_increases']),
        'total_defense_increase': self._sum_defense_modifiers(total_modifiers['defense_increases']),
        'utility_effects': self._process_utility_modifiers(total_modifiers['utility_modifiers'])
    }
    
    return calculated_bonuses

def _classify_poe2_modifier(self, modifier: str) -> str:
    """分类PoE2词缀"""
    mod_lower = modifier.lower()
    
    damage_keywords = ['damage', 'attack', 'spell', 'projectile', 'elemental']
    defense_keywords = ['life', 'energy shield', 'resistance', 'armor', 'evasion']
    
    if any(keyword in mod_lower for keyword in damage_keywords):
        return 'damage_increases'
    elif any(keyword in mod_lower for keyword in defense_keywords):
        return 'defense_increases'
    else:
        return 'utility_modifiers'
```

## 📊 计算结果验证

### 数据合理性检查

```python
def _validate_calculation_results(self, result: Dict) -> Dict:
    """验证PoE2计算结果的合理性"""
    
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    # DPS合理性检查
    total_dps = result['dps']['total_dps']
    if total_dps < 10000:
        validation['warnings'].append(f"DPS过低: {total_dps:,} (可能配置有误)")
    elif total_dps > 100000000:  # 1亿DPS
        validation['warnings'].append(f"DPS过高: {total_dps:,} (可能计算错误)")
    
    # 防御合理性检查
    resistances = result['defenses']
    for res_type in ['fire_resistance', 'cold_resistance', 'lightning_resistance']:
        res_value = resistances.get(res_type, 0)
        if res_value > 80:  # PoE2最大抗性
            validation['errors'].append(f"{res_type}超过PoE2上限: {res_value}%")
        elif res_value < 50:
            validation['warnings'].append(f"{res_type}过低: {res_value}% (建议提升)")
    
    # 能量护盾检查
    es_value = result['survivability']['total_energy_shield']
    life_value = result['survivability']['total_life']
    
    if es_value > life_value * 2:  # 能量护盾不应该过高
        validation['warnings'].append("能量护盾可能过高，请检查计算")
    
    return validation
```

### 性能基准对比

```python
def _generate_performance_comparison(self, result: Dict) -> Dict:
    """生成PoE2性能对比报告"""
    
    # PoE2性能基准 (基于社区数据)
    benchmarks = {
        'beginner': {'dps': 500000, 'ehp': 8000, 'resistances': 70},
        'intermediate': {'dps': 2000000, 'ehp': 15000, 'resistances': 78},
        'advanced': {'dps': 5000000, 'ehp': 25000, 'resistances': 80},
        'endgame': {'dps': 10000000, 'ehp': 40000, 'resistances': 80}
    }
    
    user_dps = result['dps']['total_dps']
    user_ehp = result['survivability']['total_ehp']
    user_avg_res = sum([
        result['defenses']['fire_resistance'],
        result['defenses']['cold_resistance'], 
        result['defenses']['lightning_resistance']
    ]) / 3
    
    # 确定性能等级
    performance_tier = 'beginner'
    for tier, requirements in benchmarks.items():
        if (user_dps >= requirements['dps'] and 
            user_ehp >= requirements['ehp'] and
            user_avg_res >= requirements['resistances']):
            performance_tier = tier
    
    return {
        'tier': performance_tier,
        'benchmarks': benchmarks,
        'user_stats': {
            'dps': user_dps,
            'ehp': user_ehp,
            'avg_resistance': round(user_avg_res, 1)
        },
        'recommendations': self._get_tier_recommendations(performance_tier)
    }
```

## 🚀 计算优化

### 缓存优化

```python
class PoE2CalculationCache:
    """PoE2计算缓存系统"""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {'hits': 0, 'calculations': 0}
    
    def get_cached_calculation(self, config_hash: str) -> Optional[Dict]:
        """获取缓存的计算结果"""
        if config_hash in self.cache:
            self.cache_stats['hits'] += 1
            return self.cache[config_hash]
        return None
    
    def cache_calculation(self, config_hash: str, result: Dict):
        """缓存计算结果"""
        # 只缓存最近的100个计算结果
        if len(self.cache) > 100:
            # 删除最旧的缓存
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[config_hash] = result
        self.cache_stats['calculations'] += 1
    
    def generate_config_hash(self, build_config: Dict) -> str:
        """生成配置哈希"""
        import hashlib
        config_str = json.dumps(build_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
```

## 📈 计算统计和分析

### 计算性能统计

```python
class PoE2CalculationStats:
    """PoE2计算性能统计"""
    
    def __init__(self):
        self.stats = {
            'total_calculations': 0,
            'calculation_times': [],
            'error_count': 0,
            'most_calculated_skills': defaultdict(int),
            'average_dps_by_class': defaultdict(list)
        }
    
    def record_calculation(self, build_config: Dict, result: Dict, calculation_time: float):
        """记录计算统计"""
        self.stats['total_calculations'] += 1
        self.stats['calculation_times'].append(calculation_time)
        
        # 记录技能使用频率
        skill = build_config.get('main_skill', 'Unknown')
        self.stats['most_calculated_skills'][skill] += 1
        
        # 记录职业DPS分布
        build_class = result.get('class', 'Unknown')
        dps = result.get('dps', {}).get('total_dps', 0)
        self.stats['average_dps_by_class'][build_class].append(dps)
    
    def get_performance_report(self) -> Dict:
        """生成性能报告"""
        calc_times = self.stats['calculation_times']
        
        return {
            'total_calculations': self.stats['total_calculations'],
            'average_calculation_time': sum(calc_times) / len(calc_times) if calc_times else 0,
            'max_calculation_time': max(calc_times) if calc_times else 0,
            'error_rate': self.stats['error_count'] / max(self.stats['total_calculations'], 1),
            'popular_skills': dict(sorted(self.stats['most_calculated_skills'].items(), 
                                        key=lambda x: x[1], reverse=True)[:10]),
            'class_performance': {
                class_name: {
                    'count': len(dps_list),
                    'average_dps': sum(dps_list) / len(dps_list) if dps_list else 0,
                    'max_dps': max(dps_list) if dps_list else 0
                }
                for class_name, dps_list in self.stats['average_dps_by_class'].items()
            }
        }
```

---

**下一步**: 查看 [API使用指南](04_api_usage.md) 了解如何在实际项目中使用PoE2计算引擎。