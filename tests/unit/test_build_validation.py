"""
构筑验证单元测试
测试构筑数据的验证逻辑、边界条件和错误处理
"""

import pytest
from typing import List, Dict, Any

from src.poe2build.models.build import (
    PoE2Build, PoE2BuildStats, PoE2BuildGoal, PoE2DamageType
)
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from tests.fixtures.test_data import TestDataFactory, TestCaseGenerator


class TestBuildStatsValidation:
    """构筑统计数据验证测试"""
    
    @pytest.mark.parametrize("resistance_value,should_pass", [
        (80, True),   # 上限
        (75, True),   # 标准值
        (0, True),    # 中性
        (-30, True),  # 常见负值
        (-100, True), # 下限
        (81, False),  # 超出上限
        (-101, False) # 超出下限
    ])
    def test_resistance_range_validation(self, resistance_value, should_pass):
        """测试抗性范围验证"""
        if should_pass:
            stats = PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=resistance_value,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
            assert stats.fire_resistance == resistance_value
        else:
            with pytest.raises(ValueError):
                PoE2BuildStats(
                    total_dps=100000,
                    effective_health_pool=5000,
                    fire_resistance=resistance_value,
                    cold_resistance=75,
                    lightning_resistance=75,
                    chaos_resistance=-30
                )
    
    @pytest.mark.parametrize("dps_value,should_pass", [
        (0, True),      # 最小值
        (100000, True), # 正常值
        (5000000, True), # 极高值
        (-1, False),    # 负值
        (-100000, False) # 大负值
    ])
    def test_dps_validation(self, dps_value, should_pass):
        """测试DPS值验证"""
        if should_pass:
            stats = PoE2BuildStats(
                total_dps=dps_value,
                effective_health_pool=5000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
            assert stats.total_dps == dps_value
        else:
            with pytest.raises(ValueError):
                PoE2BuildStats(
                    total_dps=dps_value,
                    effective_health_pool=5000,
                    fire_resistance=75,
                    cold_resistance=75,
                    lightning_resistance=75,
                    chaos_resistance=-30
                )
    
    @pytest.mark.parametrize("ehp_value,should_pass", [
        (0, True),      # 最小值
        (5000, True),   # 正常值
        (50000, True),  # 极高值
        (-1, False),    # 负值
        (-5000, False)  # 大负值
    ])
    def test_ehp_validation(self, ehp_value, should_pass):
        """测试有效血量验证"""
        if should_pass:
            stats = PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=ehp_value,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
            assert stats.effective_health_pool == ehp_value
        else:
            with pytest.raises(ValueError):
                PoE2BuildStats(
                    total_dps=100000,
                    effective_health_pool=ehp_value,
                    fire_resistance=75,
                    cold_resistance=75,
                    lightning_resistance=75,
                    chaos_resistance=-30
                )
    
    @pytest.mark.parametrize("percentage_field,value,should_pass", [
        ("critical_strike_chance", 0.0, True),
        ("critical_strike_chance", 50.0, True),
        ("critical_strike_chance", 100.0, True),
        ("critical_strike_chance", 100.1, False),
        ("critical_strike_chance", -0.1, False),
        ("block_chance", 0.0, True),
        ("block_chance", 75.0, True),
        ("block_chance", 100.0, True),
        ("block_chance", 101.0, False),
        ("dodge_chance", 25.0, True),
        ("dodge_chance", 100.0, True),
        ("dodge_chance", -1.0, False)
    ])
    def test_percentage_fields_validation(self, percentage_field, value, should_pass):
        """测试百分比字段验证"""
        kwargs = {
            'total_dps': 100000,
            'effective_health_pool': 5000,
            'fire_resistance': 75,
            'cold_resistance': 75,
            'lightning_resistance': 75,
            'chaos_resistance': -30,
            percentage_field: value
        }
        
        if should_pass:
            stats = PoE2BuildStats(**kwargs)
            assert getattr(stats, percentage_field) == value
        else:
            with pytest.raises(ValueError):
                PoE2BuildStats(**kwargs)
    
    def test_resistance_cap_check(self):
        """测试抗性上限检查"""
        # 满抗构筑
        capped_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        assert capped_stats.is_resistance_capped()
        
        # 超满抗构筑
        over_capped_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=78,
            cold_resistance=79,
            lightning_resistance=80,
            chaos_resistance=-20
        )
        assert over_capped_stats.is_resistance_capped()
        
        # 未满抗构筑
        under_capped_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=70,  # 低于75%
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        assert not under_capped_stats.is_resistance_capped()
    
    def test_total_resistance_calculation(self):
        """测试总抗性计算"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=74,
            chaos_resistance=-25
        )
        
        expected_average = (78 + 76 + 74) / 3
        assert abs(stats.get_total_resistance_percentage() - expected_average) < 0.01
    
    def test_ehp_breakdown(self):
        """测试EHP细分"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=8500,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30,
            life=5500,
            energy_shield=3000
        )
        
        breakdown = stats.get_ehp_breakdown()
        assert breakdown['life'] == 5500
        assert breakdown['energy_shield'] == 3000
        assert breakdown['total_ehp'] == 8500


class TestBuildValidation:
    """构筑整体验证测试"""
    
    @pytest.mark.parametrize("level,should_pass", [
        (1, True),    # 最低等级
        (50, True),   # 中等等级
        (100, True),  # 最高等级
        (0, False),   # 零等级
        (101, False), # 超出上限
        (-1, False)   # 负等级
    ])
    def test_level_validation(self, level, should_pass, sample_build_stats):
        """测试等级验证"""
        if should_pass:
            build = PoE2Build(
                name="Test Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=level,
                stats=sample_build_stats
            )
            assert build.level == level
        else:
            with pytest.raises(ValueError):
                PoE2Build(
                    name="Test Build",
                    character_class=PoE2CharacterClass.SORCERESS,
                    level=level,
                    stats=sample_build_stats
                )
    
    def test_empty_build_name_validation(self):
        """测试空构筑名称验证"""
        invalid_names = ["", "   ", "\t", "\n"]
        
        for name in invalid_names:
            with pytest.raises(ValueError, match="Build name cannot be empty"):
                PoE2Build(
                    name=name,
                    character_class=PoE2CharacterClass.SORCERESS,
                    level=90
                )
    
    def test_ascendancy_class_compatibility(self):
        """测试升华与职业兼容性"""
        # 有效组合
        valid_build = PoE2Build(
            name="Valid Ascendancy Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            ascendancy=PoE2Ascendancy.STORMWEAVER
        )
        assert valid_build.ascendancy == PoE2Ascendancy.STORMWEAVER
        
        # 无效组合
        with pytest.raises(ValueError, match="Ascendancy .* not valid for .*"):
            PoE2Build(
                name="Invalid Ascendancy Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                ascendancy=PoE2Ascendancy.DEADEYE  # 游侠升华用在法师上
            )
    
    @pytest.mark.parametrize("cost,should_pass", [
        (0.0, True),    # 免费构筑
        (10.5, True),   # 正常成本
        (100.0, True),  # 高成本
        (-0.1, False),  # 负成本
        (-10.0, False)  # 大负成本
    ])
    def test_build_cost_validation(self, cost, should_pass):
        """测试构筑成本验证"""
        if should_pass:
            build = PoE2Build(
                name="Test Cost Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                estimated_cost=cost
            )
            assert build.estimated_cost == cost
        else:
            with pytest.raises(ValueError):
                PoE2Build(
                    name="Test Cost Build",
                    character_class=PoE2CharacterClass.SORCERESS,
                    level=90,
                    estimated_cost=cost
                )
    
    def test_build_validate_method_comprehensive(self):
        """测试构筑验证方法的综合测试"""
        # 完全有效的构筑
        valid_stats = PoE2BuildStats(
            total_dps=500000,
            effective_health_pool=7000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        
        valid_build = PoE2Build(
            name="Valid Complete Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=valid_stats,
            main_skill_gem="Lightning Bolt",
            estimated_cost=15.0
        )
        assert valid_build.validate()
        
        # 缺少主技能的构筑
        no_skill_build = PoE2Build(
            name="No Skill Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=valid_stats
            # 缺少main_skill_gem
        )
        assert not no_skill_build.validate()
        
        # DPS为0的构筑
        zero_dps_stats = PoE2BuildStats(
            total_dps=0,  # 零DPS
            effective_health_pool=7000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        
        zero_dps_build = PoE2Build(
            name="Zero DPS Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=zero_dps_stats,
            main_skill_gem="Lightning Bolt"
        )
        assert not zero_dps_build.validate()
        
        # EHP为0的构筑
        zero_ehp_stats = PoE2BuildStats(
            total_dps=500000,
            effective_health_pool=0,  # 零EHP
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        
        zero_ehp_build = PoE2Build(
            name="Zero EHP Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=zero_ehp_stats,
            main_skill_gem="Lightning Bolt"
        )
        assert not zero_ehp_build.validate()


class TestBuildSuitabilityChecks:
    """构筑适用性检查测试"""
    
    def test_boss_killing_suitability(self):
        """测试Boss击杀构筑适用性"""
        # 适合Boss击杀的高DPS高EHP构筑
        boss_stats = PoE2BuildStats(
            total_dps=1200000,  # 满足>500k要求
            effective_health_pool=8000,  # 满足>6k要求
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25
        )
        
        boss_build = PoE2Build(
            name="Boss Killer",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            stats=boss_stats
        )
        
        assert boss_build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)
        
        # 不适合Boss击杀的低DPS构筑
        low_dps_stats = PoE2BuildStats(
            total_dps=300000,  # 低于500k要求
            effective_health_pool=8000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25
        )
        
        low_dps_build = PoE2Build(
            name="Low DPS Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=low_dps_stats
        )
        
        assert not low_dps_build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)
    
    def test_clear_speed_suitability(self):
        """测试清图速度构筑适用性"""
        # 适合清图的高移速构筑
        clear_stats = PoE2BuildStats(
            total_dps=400000,  # 满足>200k要求
            effective_health_pool=6000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25,
            movement_speed=130.0  # 满足>100要求
        )
        
        clear_build = PoE2Build(
            name="Clear Speed Build",
            character_class=PoE2CharacterClass.RANGER,
            level=88,
            stats=clear_stats
        )
        
        assert clear_build.is_suitable_for_goal(PoE2BuildGoal.CLEAR_SPEED)
        
        # 移速不足的构筑
        slow_stats = PoE2BuildStats(
            total_dps=400000,
            effective_health_pool=6000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25,
            movement_speed=90.0  # 低于100要求
        )
        
        slow_build = PoE2Build(
            name="Slow Build",
            character_class=PoE2CharacterClass.RANGER,
            level=88,
            stats=slow_stats
        )
        
        assert not slow_build.is_suitable_for_goal(PoE2BuildGoal.CLEAR_SPEED)
    
    def test_budget_friendly_suitability(self):
        """测试预算友好构筑适用性"""
        # 预算友好构筑
        budget_build = PoE2Build(
            name="Budget Build",
            character_class=PoE2CharacterClass.MONK,
            level=80,
            estimated_cost=3.0,  # 满足<=5要求
            stats=PoE2BuildStats(
                total_dps=300000,
                effective_health_pool=6000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
        )
        
        assert budget_build.is_suitable_for_goal(PoE2BuildGoal.BUDGET_FRIENDLY)
        
        # 高成本构筑
        expensive_build = PoE2Build(
            name="Expensive Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            estimated_cost=25.0,  # 超过5的要求
            stats=PoE2BuildStats(
                total_dps=1500000,
                effective_health_pool=8000,
                fire_resistance=78,
                cold_resistance=76,
                lightning_resistance=77,
                chaos_resistance=-20
            )
        )
        
        assert not expensive_build.is_suitable_for_goal(PoE2BuildGoal.BUDGET_FRIENDLY)
    
    def test_league_start_suitability(self):
        """测试赛季开荒构筑适用性"""
        # 无成本构筑（赛季开荒）
        league_start_build = PoE2Build(
            name="League Starter",
            character_class=PoE2CharacterClass.WARRIOR,
            level=70,
            estimated_cost=None,  # 无成本要求
            stats=PoE2BuildStats(
                total_dps=200000,
                effective_health_pool=7000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
        )
        
        assert league_start_build.is_suitable_for_goal(PoE2BuildGoal.LEAGUE_START)
        
        # 低成本构筑
        low_cost_build = PoE2Build(
            name="Low Cost Build",
            character_class=PoE2CharacterClass.WARRIOR,
            level=70,
            estimated_cost=0.5,  # 满足<=1要求
            stats=PoE2BuildStats(
                total_dps=200000,
                effective_health_pool=7000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
        )
        
        assert low_cost_build.is_suitable_for_goal(PoE2BuildGoal.LEAGUE_START)
        
        # 成本过高构筑
        high_cost_build = PoE2Build(
            name="High Cost Build",
            character_class=PoE2CharacterClass.WARRIOR,
            level=70,
            estimated_cost=5.0,  # 超过1的要求
            stats=PoE2BuildStats(
                total_dps=500000,
                effective_health_pool=7000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
        )
        
        assert not high_cost_build.is_suitable_for_goal(PoE2BuildGoal.LEAGUE_START)
    
    def test_endgame_content_suitability(self):
        """测试终局内容构筑适用性"""
        # 适合终局内容的全面构筑
        endgame_stats = PoE2BuildStats(
            total_dps=1200000,  # 满足>1M要求
            effective_health_pool=8500,  # 满足>8k要求
            fire_resistance=75,  # 满足抗性要求
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25
        )
        
        endgame_build = PoE2Build(
            name="Endgame Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            stats=endgame_stats
        )
        
        assert endgame_build.is_suitable_for_goal(PoE2BuildGoal.ENDGAME_CONTENT)
        
        # DPS不足的构筑
        low_dps_endgame = PoE2Build(
            name="Low DPS Endgame",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            stats=PoE2BuildStats(
                total_dps=800000,  # 低于1M要求
                effective_health_pool=8500,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-25
            )
        )
        
        assert not low_dps_endgame.is_suitable_for_goal(PoE2BuildGoal.ENDGAME_CONTENT)
        
        # 抗性不足的构筑
        low_res_endgame = PoE2Build(
            name="Low Resistance Endgame",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            stats=PoE2BuildStats(
                total_dps=1200000,
                effective_health_pool=8500,
                fire_resistance=70,  # 低于75%
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-25
            )
        )
        
        assert not low_res_endgame.is_suitable_for_goal(PoE2BuildGoal.ENDGAME_CONTENT)


class TestBuildComparisonAndRanking:
    """构筑比较和排名测试"""
    
    def test_build_comparison(self, sample_builds_list):
        """测试构筑比较功能"""
        build1, build2 = sample_builds_list[0], sample_builds_list[1]
        
        comparison = build1.compare_with(build2)
        
        # 验证比较结果结构
        assert 'name' in comparison
        assert 'class_match' in comparison
        assert 'level_diff' in comparison
        
        # 验证名称比较
        assert comparison['name']['this'] == build1.name
        assert comparison['name']['other'] == build2.name
        
        # 验证职业匹配
        assert comparison['class_match'] == (build1.character_class == build2.character_class)
        
        # 验证等级差异
        assert comparison['level_diff'] == (build1.level - build2.level)
        
        # 如果两个构筑都有统计数据，验证统计比较
        if build1.stats and build2.stats:
            assert 'stats' in comparison
            assert 'dps_diff' in comparison['stats']
            assert 'ehp_diff' in comparison['stats']
            assert comparison['stats']['dps_diff'] == (
                build1.stats.total_dps - build2.stats.total_dps
            )
        
        # 如果两个构筑都有成本，验证成本比较
        if build1.estimated_cost and build2.estimated_cost:
            assert 'cost_diff' in comparison
            assert comparison['cost_diff'] == (
                build1.estimated_cost - build2.estimated_cost
            )
    
    def test_build_comparison_error_handling(self, sample_build):
        """测试构筑比较错误处理"""
        with pytest.raises(ValueError, match="Can only compare with another PoE2Build"):
            sample_build.compare_with("not a build")
        
        with pytest.raises(ValueError):
            sample_build.compare_with(None)


class TestEdgeCasesAndBoundaryConditions:
    """边界条件和边缘情况测试"""
    
    def test_extreme_resistance_values(self):
        """测试极端抗性值"""
        # 最高抗性
        max_res_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=80,
            cold_resistance=80,
            lightning_resistance=80,
            chaos_resistance=80
        )
        assert max_res_stats.is_resistance_capped()
        
        # 最低抗性
        min_res_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=-100,
            cold_resistance=-100,
            lightning_resistance=-100,
            chaos_resistance=-100
        )
        assert not min_res_stats.is_resistance_capped()
    
    def test_extreme_dps_and_ehp_values(self):
        """测试极端DPS和EHP值"""
        # 极高DPS构筑
        ultra_dps_stats = PoE2BuildStats(
            total_dps=10000000,  # 1000万DPS
            effective_health_pool=1000,  # 玻璃大炮
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        
        ultra_dps_build = PoE2Build(
            name="Ultra DPS Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=100,
            stats=ultra_dps_stats,
            main_skill_gem="Ultimate Skill"
        )
        
        assert ultra_dps_build.validate()
        assert ultra_dps_build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)
        
        # 极高EHP构筑
        ultra_tank_stats = PoE2BuildStats(
            total_dps=50000,  # 极低DPS
            effective_health_pool=50000,  # 5万EHP
            fire_resistance=80,
            cold_resistance=80,
            lightning_resistance=80,
            chaos_resistance=50
        )
        
        ultra_tank_build = PoE2Build(
            name="Ultra Tank Build",
            character_class=PoE2CharacterClass.WARRIOR,
            level=100,
            stats=ultra_tank_stats,
            main_skill_gem="Tank Skill"
        )
        
        assert ultra_tank_build.validate()
        assert not ultra_tank_build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)  # DPS太低
    
    def test_minimum_valid_build(self):
        """测试最小有效构筑"""
        minimal_build = PoE2Build(
            name="Minimal Build",
            character_class=PoE2CharacterClass.WITCH,
            level=1,  # 最低等级
            stats=PoE2BuildStats(
                total_dps=1,  # 最低DPS
                effective_health_pool=1,  # 最低EHP
                fire_resistance=-100,  # 最低抗性
                cold_resistance=-100,
                lightning_resistance=-100,
                chaos_resistance=-100
            ),
            estimated_cost=0.0,  # 最低成本
            main_skill_gem="Basic Attack"
        )
        
        assert minimal_build.validate()
    
    def test_unicode_and_special_characters_in_names(self):
        """测试Unicode和特殊字符的构筑名称"""
        unicode_names = [
            "Lightning ⚡ Master",
            "Ice ❄️ Queen",
            "构筑测试",  # 中文
            "Построение теста",  # 俄文
            "Build with émojis 🔥",
            "Build-with_special.chars!@#"
        ]
        
        for name in unicode_names:
            build = PoE2Build(
                name=name,
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                stats=PoE2BuildStats(
                    total_dps=100000,
                    effective_health_pool=5000,
                    fire_resistance=75,
                    cold_resistance=75,
                    lightning_resistance=75,
                    chaos_resistance=-30
                ),
                main_skill_gem="Test Skill"
            )
            
            assert build.validate()
            assert build.name == name