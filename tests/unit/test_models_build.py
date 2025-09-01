"""
单元测试 - PoE2构筑模型

测试PoE2构筑相关的模型类，包括：
- PoE2BuildStats
- PoE2BuildGoal
- PoE2Build
- 构筑验证逻辑
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.poe2build.models.build import (
    PoE2BuildStats,
    PoE2BuildGoal,
    PoE2Build
)
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy


@pytest.mark.unit
class TestPoE2BuildStats:
    """测试构筑统计数据模型"""
    
    def test_create_valid_build_stats(self):
        """测试创建有效的构筑统计"""
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
        
        assert stats.total_dps == 750000
        assert stats.effective_health_pool == 8500
        assert stats.fire_resistance == 78
        assert stats.life == 5500
        assert stats.energy_shield == 3000
        
    def test_resistance_validation(self):
        """测试抗性值验证"""
        # 测试抗性最大值（80%）
        valid_stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=80,
            cold_resistance=80,
            lightning_resistance=80,
            chaos_resistance=-60  # 混沌抗性可以是负数
        )
        assert valid_stats.fire_resistance == 80
        
        # 测试超过最大抗性
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=85  # 超过80%
            )
            
        # 测试极低抗性
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                fire_resistance=-101  # 过低
            )
            
    def test_dps_validation(self):
        """测试DPS值验证"""
        # 负数DPS无效
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=-1000,
                effective_health_pool=5000
            )
            
        # 零DPS有效
        stats = PoE2BuildStats(
            total_dps=0,
            effective_health_pool=5000
        )
        assert stats.total_dps == 0
        
    def test_health_validation(self):
        """测试生命值验证"""
        # 负数有效血量无效
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=-100
            )
            
        # 生命值和能量护盾必须非负
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                life=-100
            )
            
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                energy_shield=-100
            )
            
    def test_percentage_stats_validation(self):
        """测试百分比统计验证"""
        # 暴击率不能超过100%
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                critical_strike_chance=105.0
            )
            
        # 移动速度不能为负
        with pytest.raises(ValidationError):
            PoE2BuildStats(
                total_dps=100000,
                effective_health_pool=5000,
                movement_speed=-10.0
            )
            
    def test_stats_computation(self):
        """测试统计数据计算"""
        stats = PoE2BuildStats(
            total_dps=500000,
            effective_health_pool=6000,
            life=4000,
            energy_shield=2000,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
        
        # 检查是否满足抗性上限（75%+）
        assert stats.has_capped_resistances
        
        # 检查是否为高DPS构筑（>1M）
        assert not stats.is_high_dps  # 500k < 1M
        
        # 检查是否为生存型构筑（>10k EHP）
        assert not stats.is_tanky  # 6k < 10k


@pytest.mark.unit
class TestPoE2Build:
    """测试PoE2构筑模型"""
    
    def test_create_minimal_build(self):
        """测试创建最小构筑"""
        build = PoE2Build(
            name="Test Build",
            character_class=PoE2CharacterClass.WITCH,
            level=85
        )
        
        assert build.name == "Test Build"
        assert build.character_class == PoE2CharacterClass.WITCH
        assert build.level == 85
        assert build.league == "Standard"  # 默认值
        assert build.hardcore is False  # 默认值
        
    def test_create_complete_build(self, sample_build_stats):
        """测试创建完整构筑"""
        build = PoE2Build(
            name="Complete Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=92,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            stats=sample_build_stats,
            estimated_cost=15.5,
            currency_type="divine",
            goal=PoE2BuildGoal.ENDGAME_CONTENT,
            main_skill_gem="Lightning Bolt",
            support_gems=["Added Lightning", "Lightning Penetration"],
            key_items=["Staff of Power", "Lightning Amulet"],
            passive_keystones=["Elemental Overload"],
            notes="Test build for endgame content",
            created_by="test_user",
            league="Hardcore",
            hardcore=True
        )
        
        assert build.name == "Complete Build"
        assert build.ascendancy == PoE2Ascendancy.STORMWEAVER
        assert build.stats == sample_build_stats
        assert build.estimated_cost == 15.5
        assert build.currency_type == "divine"
        assert build.goal == PoE2BuildGoal.ENDGAME_CONTENT
        assert "Lightning Bolt" in build.main_skill_gem
        assert len(build.support_gems) == 2
        assert build.hardcore is True
        
    def test_build_name_validation(self):
        """测试构筑名称验证"""
        # 空名称无效
        with pytest.raises(ValidationError):
            PoE2Build(
                name="",
                character_class=PoE2CharacterClass.WITCH,
                level=85
            )
            
        # 纯空格名称无效
        with pytest.raises(ValidationError):
            PoE2Build(
                name="   ",
                character_class=PoE2CharacterClass.WITCH,
                level=85
            )
            
        # 过长名称无效
        with pytest.raises(ValidationError):
            PoE2Build(
                name="x" * 201,  # 超过200字符
                character_class=PoE2CharacterClass.WITCH,
                level=85
            )
            
    def test_level_validation(self):
        """测试等级验证"""
        # 等级过低
        with pytest.raises(ValidationError):
            PoE2Build(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=0
            )
            
        # 等级过高
        with pytest.raises(ValidationError):
            PoE2Build(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=101
            )
            
        # 有效等级范围
        for level in [1, 50, 85, 100]:
            build = PoE2Build(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=level
            )
            assert build.level == level
            
    def test_cost_validation(self):
        """测试成本验证"""
        # 负数成本无效
        with pytest.raises(ValidationError):
            PoE2Build(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=85,
                estimated_cost=-1.0
            )
            
        # 零成本有效
        build = PoE2Build(
            name="Budget Build",
            character_class=PoE2CharacterClass.WITCH,
            level=85,
            estimated_cost=0.0
        )
        assert build.estimated_cost == 0.0
        
    def test_ascendancy_compatibility(self):
        """测试升华职业兼容性"""
        # 兼容的组合
        build = PoE2Build(
            name="Test",
            character_class=PoE2CharacterClass.SORCERESS,
            level=85,
            ascendancy=PoE2Ascendancy.STORMWEAVER
        )
        assert build.ascendancy == PoE2Ascendancy.STORMWEAVER
        
        # TODO: 实现升华职业与基础职业的兼容性检查
        # 这里暂时不实现，因为需要在模型中添加验证逻辑
        
    def test_build_goal_enum(self):
        """测试构筑目标枚举"""
        goals = list(PoE2BuildGoal)
        expected_goals = [
            PoE2BuildGoal.LEAGUE_START,
            PoE2BuildGoal.BUDGET_FRIENDLY,
            PoE2BuildGoal.CLEAR_SPEED,
            PoE2BuildGoal.BOSS_KILLING,
            PoE2BuildGoal.ENDGAME_CONTENT,
            PoE2BuildGoal.PVP
        ]
        
        for goal in expected_goals:
            assert goal in goals
            
    def test_build_serialization(self, sample_build):
        """测试构筑序列化"""
        # 转换为字典
        build_dict = sample_build.model_dump()
        assert isinstance(build_dict, dict)
        assert build_dict['name'] == sample_build.name
        assert build_dict['level'] == sample_build.level
        
        # 从字典重建
        rebuilt_build = PoE2Build(**build_dict)
        assert rebuilt_build.name == sample_build.name
        assert rebuilt_build.level == sample_build.level
        assert rebuilt_build.character_class == sample_build.character_class
        
    def test_build_comparison(self):
        """测试构筑比较"""
        build1 = PoE2Build(
            name="Build 1",
            character_class=PoE2CharacterClass.WITCH,
            level=85
        )
        
        build2 = PoE2Build(
            name="Build 1",
            character_class=PoE2CharacterClass.WITCH,
            level=85
        )
        
        build3 = PoE2Build(
            name="Build 3",
            character_class=PoE2CharacterClass.WITCH,
            level=85
        )
        
        assert build1 == build2  # 相同内容
        assert build1 != build3  # 不同名称
        
    def test_build_str_representation(self, sample_build):
        """测试构筑字符串表示"""
        build_str = str(sample_build)
        assert sample_build.name in build_str
        assert str(sample_build.level) in build_str
        assert sample_build.character_class.value in build_str


@pytest.mark.unit
class TestBuildValidation:
    """测试构筑验证逻辑"""
    
    def test_valid_builds(self, sample_builds_list):
        """测试有效构筑验证"""
        for build in sample_builds_list:
            # 使用conftest中的验证函数
            from tests.conftest import assert_valid_build
            assert_valid_build(build)
            
    def test_build_completeness_check(self, sample_build):
        """测试构筑完整性检查"""
        # 完整的构筑
        assert sample_build.name
        assert sample_build.character_class
        assert 1 <= sample_build.level <= 100
        
        if sample_build.stats:
            assert sample_build.stats.total_dps >= 0
            assert sample_build.stats.effective_health_pool >= 0
            
        if sample_build.estimated_cost is not None:
            assert sample_build.estimated_cost >= 0
            
    def test_build_meta_validation(self):
        """测试构筑元数据验证"""
        build = PoE2Build(
            name="Meta Test Build",
            character_class=PoE2CharacterClass.RANGER,
            level=88,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert build.created_at is not None
        assert build.updated_at is not None
        
    def test_skill_gems_validation(self):
        """测试技能宝石验证"""
        # 主技能必须存在于支援宝石列表中（如果有的话）
        build = PoE2Build(
            name="Skill Test",
            character_class=PoE2CharacterClass.RANGER,
            level=85,
            main_skill_gem="Ice Shot",
            support_gems=["Added Cold Damage", "Pierce", "Elemental Damage"]
        )
        
        assert build.main_skill_gem == "Ice Shot"
        assert len(build.support_gems) == 3
        assert "Added Cold Damage" in build.support_gems
        
        # 空的支援宝石列表也应该有效
        build2 = PoE2Build(
            name="Basic Test",
            character_class=PoE2CharacterClass.WITCH,
            level=85,
            main_skill_gem="Fireball",
            support_gems=[]
        )
        
        assert build2.main_skill_gem == "Fireball"
        assert len(build2.support_gems) == 0


@pytest.mark.unit
class TestBuildStatsCalculations:
    """测试构筑统计计算"""
    
    def test_resistance_calculations(self):
        """测试抗性计算"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=5000,
            fire_resistance=78,
            cold_resistance=76,
            lightning_resistance=77,
            chaos_resistance=-25
        )
        
        # 测试抗性上限检查
        assert stats.fire_resistance >= 75  # 满抗
        assert stats.cold_resistance >= 75  # 满抗
        assert stats.lightning_resistance >= 75  # 满抗
        
        # 测试总抗性计算（不包括混沌）
        elemental_res_total = stats.fire_resistance + stats.cold_resistance + stats.lightning_resistance
        assert elemental_res_total == 78 + 76 + 77
        
    def test_ehp_calculation(self):
        """测试有效血量计算"""
        stats = PoE2BuildStats(
            total_dps=100000,
            effective_health_pool=8500,
            life=5500,
            energy_shield=3000
        )
        
        # EHP应该考虑生命值和能量护盾
        # 简化计算：EHP = Life + ES
        calculated_ehp = stats.life + stats.energy_shield
        assert calculated_ehp == 8500  # 应该匹配设定的EHP
        
    def test_dps_categories(self):
        """测试DPS分类"""
        # 低DPS构筑
        low_dps_stats = PoE2BuildStats(
            total_dps=200000,
            effective_health_pool=5000
        )
        
        # 中等DPS构筑
        medium_dps_stats = PoE2BuildStats(
            total_dps=750000,
            effective_health_pool=5000
        )
        
        # 高DPS构筑
        high_dps_stats = PoE2BuildStats(
            total_dps=1500000,
            effective_health_pool=5000
        )
        
        assert low_dps_stats.total_dps < 500000
        assert 500000 <= medium_dps_stats.total_dps < 1000000
        assert high_dps_stats.total_dps >= 1000000
        
    def test_survivability_metrics(self):
        """测试生存能力指标"""
        # 高生存构筑
        tanky_stats = PoE2BuildStats(
            total_dps=400000,
            effective_health_pool=12000,
            life=8000,
            energy_shield=4000,
            fire_resistance=80,
            cold_resistance=78,
            lightning_resistance=79,
            chaos_resistance=10  # 正混沌抗
        )
        
        # 脆皮构筑
        glass_cannon_stats = PoE2BuildStats(
            total_dps=2000000,
            effective_health_pool=4000,
            life=3500,
            energy_shield=500,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-60
        )
        
        # 验证生存能力差异
        assert tanky_stats.effective_health_pool > glass_cannon_stats.effective_health_pool
        assert tanky_stats.chaos_resistance > glass_cannon_stats.chaos_resistance
        assert glass_cannon_stats.total_dps > tanky_stats.total_dps
