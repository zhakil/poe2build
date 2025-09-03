"""
模型单元测试
测试所有数据模型的创建、验证和方法功能
"""

import pytest
from typing import Dict, Any

from src.poe2build.models.build import (
    PoE2Build, PoE2BuildStats, PoE2BuildGoal, PoE2DamageType,
    filter_builds_by_class, filter_builds_by_budget, filter_builds_by_goal,
    sort_builds_by_dps, sort_builds_by_cost
)
from src.poe2build.models.characters import (
    PoE2CharacterClass, PoE2Ascendancy, PoE2Character, PoE2CharacterAttributes,
    ASCENDANCY_MAPPING, CLASS_PRIMARY_ATTRIBUTES,
    filter_characters_by_class, sort_characters_by_level
)
from src.poe2build.models.items import PoE2Item
from tests.fixtures.sample_builds import get_sample_builds, SAMPLE_BUILDS
from tests.fixtures.test_data import TestDataFactory


class TestPoE2BuildStats:
    """PoE2BuildStats模型测试"""
    
    def test_valid_build_stats_creation(self):
        """测试有效构筑统计数据创建"""
        stats = PoE2BuildStats(
            total_dps=750000,
            effective_health_pool=8500,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25
        )
        
        assert stats.total_dps == 750000
        assert stats.effective_health_pool == 8500
        assert stats.fire_resistance == 78
        assert stats.chaos_resistance == -25
    
    def test_invalid_resistance_values(self):
        """测试无效抗性值"""
        # 测试超出上限
        with pytest.raises(ValueError, match="fire_resistance .* must be between -100% and \\+80%"):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=85,  # 超出80%上限
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
        
        # 测试超出下限
        with pytest.raises(ValueError, match="cold_resistance .* must be between -100% and \\+80%"):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=75,
                cold_resistance=-105,  # 低于-100%下限
                lightning_resistance=75,
                chaos_resistance=-30
            )
    
    def test_negative_dps_validation(self):
        """测试负DPS验证"""
        with pytest.raises(ValueError, match="Total DPS cannot be negative"):
            PoE2BuildStats(
                total_dps=-50000,  # 负DPS
                effective_health_pool=5000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            )
    
    def test_percentage_field_validation(self):
        """测试百分比字段验证"""
        with pytest.raises(ValueError, match="critical_strike_chance .* must be between 0% and 100%"):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30,
                critical_strike_chance=150.0  # 超出100%
            )
    
    def test_get_total_resistance_percentage(self):
        """测试总抗性百分比计算"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25
        )
        
        expected = (78 + 76 + 77) / 3
        assert abs(stats.get_total_resistance_percentage() - expected) < 0.01
    
    def test_is_resistance_capped(self):
        """测试抗性上限检查"""
        # 满足75%抗性
        capped_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25
        )
        assert capped_stats.is_resistance_capped()
        
        # 不满足75%抗性
        uncapped_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=70,  # 低于75%
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25
        )
        assert not uncapped_stats.is_resistance_capped()
    
    def test_get_ehp_breakdown(self):
        """测试EHP细分"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=8500,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-25,
            life=5500,
            energy_shield=3000
        )
        
        breakdown = stats.get_ehp_breakdown()
        assert breakdown['life'] == 5500
        assert breakdown['energy_shield'] == 3000
        assert breakdown['total_ehp'] == 8500
    
    def test_to_dict_conversion(self):
        """测试字典转换"""
        stats = PoE2BuildStats(
            total_dps=750000,
            effective_health_pool=8500,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25,
            life=5500,
            energy_shield=3000
        )
        
        data = stats.to_dict()
        
        assert data['total_dps'] == 750000
        assert data['effective_health_pool'] == 8500
        assert data['resistances']['fire'] == 78
        assert data['defenses']['life'] == 5500
        assert data['defenses']['energy_shield'] == 3000


class TestPoE2Build:
    """PoE2Build模型测试"""
    
    def test_valid_build_creation(self, sample_build_stats):
        """测试有效构筑创建"""
        build = PoE2Build(
            name="Test Lightning Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            stats=sample_build_stats,
            estimated_cost=15.5,
            goal=PoE2BuildGoal.ENDGAME_CONTENT
        )
        
        assert build.name == "Test Lightning Build"
        assert build.character_class == PoE2CharacterClass.SORCERESS
        assert build.level == 90
        assert build.ascendancy == PoE2Ascendancy.STORMWEAVER
        assert build.estimated_cost == 15.5
    
    def test_invalid_build_name(self):
        """测试无效构筑名称"""
        with pytest.raises(ValueError, match="Build name cannot be empty"):
            PoE2Build(
                name="   ",  # 空白名称
                character_class=PoE2CharacterClass.SORCERESS,
                level=90
            )
    
    def test_invalid_level_range(self):
        """测试无效等级范围"""
        with pytest.raises(ValueError, match="Level .* must be between 1 and 100"):
            PoE2Build(
                name="Test Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=150  # 超出范围
            )
    
    def test_invalid_ascendancy_class_combination(self):
        """测试无效升华与职业组合"""
        with pytest.raises(ValueError, match="Ascendancy .* not valid for .*"):
            PoE2Build(
                name="Test Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                ascendancy=PoE2Ascendancy.DEADEYE  # 游侠的升华但用在法师上
            )
    
    def test_negative_cost_validation(self):
        """测试负成本验证"""
        with pytest.raises(ValueError, match="Estimated cost cannot be negative"):
            PoE2Build(
                name="Test Build",
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                estimated_cost=-5.0  # 负成本
            )
    
    def test_build_validation_method(self, sample_build_stats):
        """测试构筑验证方法"""
        # 有效构筑
        valid_build = PoE2Build(
            name="Valid Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=sample_build_stats,
            main_skill_gem="Lightning Bolt"
        )
        assert valid_build.validate()
        
        # 无主技能构筑
        invalid_build = PoE2Build(
            name="Invalid Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=sample_build_stats
            # 缺少main_skill_gem
        )
        assert not invalid_build.validate()
    
    def test_get_build_summary(self, sample_build):
        """测试构筑摘要"""
        summary = sample_build.get_build_summary()
        
        assert summary['name'] == sample_build.name
        assert summary['class'] == sample_build.character_class.value
        assert summary['level'] == sample_build.level
        assert summary['dps'] == sample_build.stats.total_dps
        assert summary['resistances_capped'] == sample_build.stats.is_resistance_capped()
    
    def test_to_dict_and_from_dict_roundtrip(self, sample_build):
        """测试字典转换往返"""
        # 转换为字典
        build_dict = sample_build.to_dict()
        
        # 从字典恢复
        restored_build = PoE2Build.from_dict(build_dict)
        
        # 验证关键属性
        assert restored_build.name == sample_build.name
        assert restored_build.character_class == sample_build.character_class
        assert restored_build.level == sample_build.level
        assert restored_build.ascendancy == sample_build.ascendancy
        
        # 验证统计数据
        if sample_build.stats and restored_build.stats:
            assert restored_build.stats.total_dps == sample_build.stats.total_dps
            assert restored_build.stats.fire_resistance == sample_build.stats.fire_resistance
    
    def test_compare_with_method(self, sample_builds_list):
        """测试构筑比较方法"""
        build1, build2 = sample_builds_list[0], sample_builds_list[1]
        
        comparison = build1.compare_with(build2)
        
        assert 'name' in comparison
        assert 'class_match' in comparison
        assert 'level_diff' in comparison
        
        if build1.stats and build2.stats:
            assert 'stats' in comparison
            assert 'dps_diff' in comparison['stats']
    
    def test_is_suitable_for_goal_method(self, sample_build_stats):
        """测试构筑目标适用性检查"""
        # Boss击杀构筑
        boss_build = PoE2Build(
            name="Boss Killer",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            stats=PoE2BuildStats(
                total_dps=1200000,  # 高DPS
                effective_health_pool=8000,  # 高EHP
                fire_resistance=78,
                cold_resistance=76,
                lightning_resistance=77,
                chaos_resistance=-20
            )
        )
        assert boss_build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)
        
        # 预算友好构筑
        budget_build = PoE2Build(
            name="Budget Build",
            character_class=PoE2CharacterClass.MONK,
            level=80,
            estimated_cost=3.0,  # 低成本
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


class TestPoE2Character:
    """PoE2Character模型测试"""
    
    def test_valid_character_creation(self, sample_character_attributes):
        """测试有效角色创建"""
        character = PoE2Character(
            name="Test Sorceress",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            attributes=sample_character_attributes,
            ascendancy=PoE2Ascendancy.STORMWEAVER
        )
        
        assert character.name == "Test Sorceress"
        assert character.character_class == PoE2CharacterClass.SORCERESS
        assert character.level == 90
        assert character.ascendancy == PoE2Ascendancy.STORMWEAVER
    
    def test_invalid_character_level(self, sample_character_attributes):
        """测试无效角色等级"""
        with pytest.raises(ValueError, match="Level .* must be between 1 and 100"):
            PoE2Character(
                name="Test Character",
                character_class=PoE2CharacterClass.SORCERESS,
                level=150,  # 超出范围
                attributes=sample_character_attributes
            )
    
    def test_empty_character_name(self, sample_character_attributes):
        """测试空角色名称"""
        with pytest.raises(ValueError, match="Character name cannot be empty"):
            PoE2Character(
                name="   ",  # 空白名称
                character_class=PoE2CharacterClass.SORCERESS,
                level=90,
                attributes=sample_character_attributes
            )
    
    def test_get_primary_attribute_value(self, sample_character):
        """测试主要属性值获取"""
        primary_value = sample_character.get_primary_attribute_value()
        
        # 法师的主属性是智力
        if sample_character.character_class == PoE2CharacterClass.SORCERESS:
            assert primary_value == sample_character.attributes.intelligence
    
    def test_can_ascend_method(self, sample_character_attributes):
        """测试升华条件检查"""
        # 可以升华的角色（30级以上，无升华）
        can_ascend_char = PoE2Character(
            name="Ready to Ascend",
            character_class=PoE2CharacterClass.SORCERESS,
            level=35,
            attributes=sample_character_attributes
        )
        assert can_ascend_char.can_ascend()
        
        # 等级不够的角色
        too_low_char = PoE2Character(
            name="Too Low Level",
            character_class=PoE2CharacterClass.SORCERESS,
            level=25,  # 低于30级
            attributes=sample_character_attributes
        )
        assert not too_low_char.can_ascend()
        
        # 已升华的角色
        already_ascended_char = PoE2Character(
            name="Already Ascended",
            character_class=PoE2CharacterClass.SORCERESS,
            level=35,
            attributes=sample_character_attributes,
            ascendancy=PoE2Ascendancy.STORMWEAVER  # 已有升华
        )
        assert not already_ascended_char.can_ascend()
    
    def test_get_expected_passive_points(self, sample_character):
        """测试期望天赋点数计算"""
        expected_points = sample_character.get_expected_passive_points()
        
        # 基础计算：等级-1 + 任务点数
        base_points = sample_character.level - 1
        quest_points = min(sample_character.level // 10, 20)
        expected = base_points + quest_points
        
        assert expected_points == expected
    
    def test_calculate_character_power(self, sample_character):
        """测试角色综合实力计算"""
        power_score = sample_character.calculate_character_power()
        
        assert 0.0 <= power_score <= 1.0  # 分数应该在0-1之间
    
    def test_character_dict_conversion(self, sample_character):
        """测试角色字典转换"""
        char_dict = sample_character.to_dict()
        
        assert char_dict['name'] == sample_character.name
        assert char_dict['class'] == sample_character.character_class.value
        assert char_dict['level'] == sample_character.level
        assert 'attributes' in char_dict
        assert 'progression' in char_dict
        
        # 从字典恢复
        restored_char = PoE2Character.from_dict(char_dict)
        assert restored_char.name == sample_character.name
        assert restored_char.character_class == sample_character.character_class


class TestPoE2CharacterAttributes:
    """PoE2CharacterAttributes模型测试"""
    
    def test_valid_attributes_creation(self):
        """测试有效属性创建"""
        attrs = PoE2CharacterAttributes(
            strength=150,
            dexterity=200,
            intelligence=300
        )
        
        assert attrs.strength == 150
        assert attrs.dexterity == 200
        assert attrs.intelligence == 300
    
    def test_invalid_attributes_range(self):
        """测试无效属性范围"""
        with pytest.raises(ValueError, match="All attributes must be at least 1"):
            PoE2CharacterAttributes(
                strength=0,  # 低于最小值
                dexterity=100,
                intelligence=100
            )
        
        with pytest.raises(ValueError, match="Attributes cannot exceed 2000"):
            PoE2CharacterAttributes(
                strength=2500,  # 超过最大值
                dexterity=100,
                intelligence=100
            )
    
    def test_get_total_attributes(self):
        """测试总属性点计算"""
        attrs = PoE2CharacterAttributes(
            strength=150,
            dexterity=200,
            intelligence=300
        )
        
        assert attrs.get_total_attributes() == 650
    
    def test_meets_requirements(self):
        """测试属性需求检查"""
        attrs = PoE2CharacterAttributes(
            strength=150,
            dexterity=200,
            intelligence=300
        )
        
        # 满足需求
        assert attrs.meets_requirements(100, 150, 250)
        
        # 不满足需求
        assert not attrs.meets_requirements(200, 150, 250)  # 力量不足


class TestBuildUtilityFunctions:
    """构筑工具函数测试"""
    
    def test_filter_builds_by_class(self, sample_builds_list):
        """测试按职业过滤构筑"""
        filtered = filter_builds_by_class(sample_builds_list, PoE2CharacterClass.SORCERESS)
        
        # 验证结果只包含法师构筑
        for build in filtered:
            assert build.character_class == PoE2CharacterClass.SORCERESS
    
    def test_filter_builds_by_budget(self, sample_builds_list):
        """测试按预算过滤构筑"""
        max_budget = 10.0
        filtered = filter_builds_by_budget(sample_builds_list, max_budget)
        
        # 验证所有构筑成本不超过预算
        for build in filtered:
            if build.estimated_cost is not None:
                assert build.estimated_cost <= max_budget
    
    def test_filter_builds_by_goal(self, sample_builds_list):
        """测试按目标过滤构筑"""
        filtered = filter_builds_by_goal(sample_builds_list, PoE2BuildGoal.BUDGET_FRIENDLY)
        
        # 验证构筑适合预算友好目标
        for build in filtered:
            assert build.is_suitable_for_goal(PoE2BuildGoal.BUDGET_FRIENDLY)
    
    def test_sort_builds_by_dps(self, sample_builds_list):
        """测试按DPS排序构筑"""
        sorted_builds = sort_builds_by_dps(sample_builds_list, descending=True)
        
        # 验证排序正确（降序）
        for i in range(len(sorted_builds) - 1):
            current_dps = sorted_builds[i].stats.total_dps if sorted_builds[i].stats else 0
            next_dps = sorted_builds[i + 1].stats.total_dps if sorted_builds[i + 1].stats else 0
            assert current_dps >= next_dps
    
    def test_sort_builds_by_cost(self, sample_builds_list):
        """测试按成本排序构筑"""
        sorted_builds = sort_builds_by_cost(sample_builds_list, ascending=True)
        
        # 验证排序正确（升序）
        for i in range(len(sorted_builds) - 1):
            current_cost = sorted_builds[i].estimated_cost or float('inf')
            next_cost = sorted_builds[i + 1].estimated_cost or float('inf')
            assert current_cost <= next_cost


@pytest.mark.unit
class TestModelIntegration:
    """模型集成测试"""
    
    def test_complete_build_workflow(self):
        """测试完整构筑工作流程"""
        # 1. 创建角色属性
        attributes = PoE2CharacterAttributes(
            strength=120,
            dexterity=180,
            intelligence=350
        )
        
        # 2. 创建角色
        character = PoE2Character(
            name="Test Character",
            character_class=PoE2CharacterClass.SORCERESS,
            level=92,
            attributes=attributes,
            ascendancy=PoE2Ascendancy.STORMWEAVER
        )
        
        # 3. 创建构筑统计
        stats = PoE2BuildStats(
            total_dps=1200000,
            effective_health_pool=8500,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-20
        )
        
        # 4. 创建构筑
        build = PoE2Build(
            name="Complete Test Build",
            character_class=character.character_class,
            level=character.level,
            ascendancy=character.ascendancy,
            stats=stats,
            estimated_cost=25.0,
            goal=PoE2BuildGoal.ENDGAME_CONTENT,
            main_skill_gem="Lightning Bolt"
        )
        
        # 5. 验证完整性
        assert build.validate()
        assert build.character_class == character.character_class
        assert build.ascendancy == character.ascendancy
        assert build.stats.is_resistance_capped()
        assert build.is_suitable_for_goal(PoE2BuildGoal.ENDGAME_CONTENT)
    
    def test_batch_build_operations(self):
        """测试批量构筑操作"""
        # 创建测试构筑批次
        builds = []
        for i in range(10):
            build = TestDataFactory.create_random_build()
            builds.append(build)
        
        # 执行各种操作
        filtered_by_class = filter_builds_by_class(builds, PoE2CharacterClass.SORCERESS)
        filtered_by_budget = filter_builds_by_budget(builds, 20.0)
        sorted_by_dps = sort_builds_by_dps(builds)
        
        # 验证操作结果
        assert len(filtered_by_class) <= len(builds)
        assert len(filtered_by_budget) <= len(builds)
        assert len(sorted_by_dps) == len(builds)