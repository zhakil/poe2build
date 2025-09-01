"""
单元测试 - PoE2角色模型

测试PoE2角色相关的模型类，包括：
- PoE2CharacterClass
- PoE2Ascendancy
- PoE2CharacterAttributes
- PoE2Character
"""

import pytest
from pydantic import ValidationError
from src.poe2build.models.characters import (
    PoE2CharacterClass,
    PoE2Ascendancy,
    PoE2CharacterAttributes,
    PoE2Character
)


@pytest.mark.unit
class TestPoE2CharacterAttributes:
    """测试角色属性模型"""
    
    def test_create_valid_attributes(self):
        """测试创建有效的角色属性"""
        attrs = PoE2CharacterAttributes(
            strength=100,
            dexterity=150,
            intelligence=200
        )
        
        assert attrs.strength == 100
        assert attrs.dexterity == 150
        assert attrs.intelligence == 200
        assert attrs.total == 450
        
    def test_minimum_attribute_values(self):
        """测试最小属性值限制"""
        with pytest.raises(ValidationError):
            PoE2CharacterAttributes(strength=-1, dexterity=50, intelligence=50)
            
        with pytest.raises(ValidationError):
            PoE2CharacterAttributes(strength=50, dexterity=-5, intelligence=50)
            
        with pytest.raises(ValidationError):
            PoE2CharacterAttributes(strength=50, dexterity=50, intelligence=-10)
            
    def test_maximum_attribute_values(self):
        """测试最大属性值限制"""
        with pytest.raises(ValidationError):
            PoE2CharacterAttributes(strength=2000, dexterity=50, intelligence=50)
            
    def test_attribute_total_calculation(self):
        """测试属性总计算"""
        attrs = PoE2CharacterAttributes(
            strength=123,
            dexterity=456,
            intelligence=789
        )
        assert attrs.total == 123 + 456 + 789
        
    def test_attribute_comparison(self):
        """测试属性比较"""
        attrs1 = PoE2CharacterAttributes(strength=100, dexterity=100, intelligence=100)
        attrs2 = PoE2CharacterAttributes(strength=100, dexterity=100, intelligence=100)
        attrs3 = PoE2CharacterAttributes(strength=150, dexterity=100, intelligence=100)
        
        assert attrs1 == attrs2
        assert attrs1 != attrs3


@pytest.mark.unit
class TestPoE2Character:
    """测试PoE2角色模型"""
    
    def test_create_valid_character(self, sample_character_attributes):
        """测试创建有效角色"""
        character = PoE2Character(
            name="Test Character",
            character_class=PoE2CharacterClass.SORCERESS,
            level=85,
            attributes=sample_character_attributes,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            experience=500000000,
            passive_skill_points=70,
            ascendancy_points=6,
            league="Standard",
            hardcore=False
        )
        
        assert character.name == "Test Character"
        assert character.character_class == PoE2CharacterClass.SORCERESS
        assert character.level == 85
        assert character.attributes == sample_character_attributes
        assert character.ascendancy == PoE2Ascendancy.STORMWEAVER
        assert character.league == "Standard"
        assert character.hardcore is False
        
    def test_character_level_validation(self, sample_character_attributes):
        """测试角色等级验证"""
        # 测试最小等级
        with pytest.raises(ValidationError):
            PoE2Character(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=0,  # 无效
                attributes=sample_character_attributes
            )
            
        # 测试最大等级
        with pytest.raises(ValidationError):
            PoE2Character(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=101,  # 无效
                attributes=sample_character_attributes
            )
            
        # 测试有效等级范围
        for level in [1, 50, 85, 100]:
            character = PoE2Character(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=level,
                attributes=sample_character_attributes
            )
            assert character.level == level
            
    def test_character_name_validation(self, sample_character_attributes):
        """测试角色名称验证"""
        # 测试空名称
        with pytest.raises(ValidationError):
            PoE2Character(
                name="",
                character_class=PoE2CharacterClass.WITCH,
                level=50,
                attributes=sample_character_attributes
            )
            
        # 测试空白名称
        with pytest.raises(ValidationError):
            PoE2Character(
                name="   ",
                character_class=PoE2CharacterClass.WITCH,
                level=50,
                attributes=sample_character_attributes
            )
            
    def test_ascendancy_class_compatibility(self, sample_character_attributes):
        """测试升华职业与基础职业的兼容性"""
        # 兼容的组合
        valid_combinations = [
            (PoE2CharacterClass.SORCERESS, PoE2Ascendancy.STORMWEAVER),
            (PoE2CharacterClass.SORCERESS, PoE2Ascendancy.CHRONOMANCER),
            (PoE2CharacterClass.RANGER, PoE2Ascendancy.DEADEYE),
            (PoE2CharacterClass.MONK, PoE2Ascendancy.INVOKER),
            (PoE2CharacterClass.WITCH, PoE2Ascendancy.INFERNALIST),
            (PoE2CharacterClass.MERCENARY, PoE2Ascendancy.WITCHHUNTER),
            (PoE2CharacterClass.WARRIOR, PoE2Ascendancy.TITAN)
        ]
        
        for char_class, ascendancy in valid_combinations:
            character = PoE2Character(
                name="Test",
                character_class=char_class,
                level=50,
                attributes=sample_character_attributes,
                ascendancy=ascendancy
            )
            assert character.character_class == char_class
            assert character.ascendancy == ascendancy
            
    def test_passive_points_validation(self, sample_character_attributes):
        """测试天赋点数验证"""
        # 负数天赋点应该无效
        with pytest.raises(ValidationError):
            PoE2Character(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=50,
                attributes=sample_character_attributes,
                passive_skill_points=-1
            )
            
        # 过多天赋点应该无效（假设最多150点）
        with pytest.raises(ValidationError):
            PoE2Character(
                name="Test",
                character_class=PoE2CharacterClass.WITCH,
                level=50,
                attributes=sample_character_attributes,
                passive_skill_points=200
            )
            
    def test_character_serialization(self, sample_character):
        """测试角色序列化和反序列化"""
        # 测试转换为字典
        char_dict = sample_character.model_dump()
        assert isinstance(char_dict, dict)
        assert char_dict['name'] == sample_character.name
        assert char_dict['level'] == sample_character.level
        
        # 测试从字典重建
        rebuilt_character = PoE2Character(**char_dict)
        assert rebuilt_character == sample_character
        
    def test_character_str_representation(self, sample_character):
        """测试角色字符串表示"""
        char_str = str(sample_character)
        assert sample_character.name in char_str
        assert str(sample_character.level) in char_str
        assert sample_character.character_class.value in char_str


@pytest.mark.unit
class TestPoE2CharacterEnums:
    """测试PoE2角色枚举"""
    
    def test_character_class_enum(self):
        """测试角色职业枚举"""
        classes = list(PoE2CharacterClass)
        
        # 验证所有职业都存在
        expected_classes = [
            PoE2CharacterClass.WITCH,
            PoE2CharacterClass.SORCERESS,
            PoE2CharacterClass.RANGER,
            PoE2CharacterClass.MONK,
            PoE2CharacterClass.MERCENARY,
            PoE2CharacterClass.WARRIOR
        ]
        
        for expected_class in expected_classes:
            assert expected_class in classes
            
        # 验证职业值
        assert PoE2CharacterClass.WITCH.value == "Witch"
        assert PoE2CharacterClass.SORCERESS.value == "Sorceress"
        assert PoE2CharacterClass.RANGER.value == "Ranger"
        
    def test_ascendancy_enum(self):
        """测试升华职业枚举"""
        ascendancies = list(PoE2Ascendancy)
        
        # 验证主要升华职业存在
        expected_ascendancies = [
            PoE2Ascendancy.STORMWEAVER,
            PoE2Ascendancy.CHRONOMANCER,
            PoE2Ascendancy.DEADEYE,
            PoE2Ascendancy.INVOKER,
            PoE2Ascendancy.INFERNALIST,
            PoE2Ascendancy.WITCHHUNTER,
            PoE2Ascendancy.TITAN
        ]
        
        for expected_ascendancy in expected_ascendancies:
            assert expected_ascendancy in ascendancies
            
        # 验证升华职业值
        assert PoE2Ascendancy.STORMWEAVER.value == "Stormweaver"
        assert PoE2Ascendancy.DEADEYE.value == "Deadeye"
        
    def test_enum_string_conversion(self):
        """测试枚举字符串转换"""
        # 测试从字符串创建角色职业
        char_class = PoE2CharacterClass("Sorceress")
        assert char_class == PoE2CharacterClass.SORCERESS
        
        # 测试从字符串创建升华职业
        ascendancy = PoE2Ascendancy("Stormweaver")
        assert ascendancy == PoE2Ascendancy.STORMWEAVER
        
        # 测试无效字符串
        with pytest.raises(ValueError):
            PoE2CharacterClass("InvalidClass")
            
        with pytest.raises(ValueError):
            PoE2Ascendancy("InvalidAscendancy")


@pytest.mark.unit
class TestCharacterModelIntegration:
    """测试角色模型集成"""
    
    def test_complete_character_creation(self):
        """测试完整角色创建流程"""
        # 创建属性
        attributes = PoE2CharacterAttributes(
            strength=120,
            dexterity=180,
            intelligence=250
        )
        
        # 创建完整角色
        character = PoE2Character(
            name="Integration Test Character",
            character_class=PoE2CharacterClass.SORCERESS,
            level=92,
            attributes=attributes,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            experience=1200000000,
            passive_skill_points=82,
            ascendancy_points=8,
            league="Standard",
            hardcore=False
        )
        
        # 验证所有属性
        assert character.name == "Integration Test Character"
        assert character.attributes.total == 550
        assert character.is_ascended is True  # 有升华职业
        assert character.is_max_level is False  # 不是满级
        
    def test_character_progression_simulation(self):
        """测试角色升级进程模拟"""
        base_attributes = PoE2CharacterAttributes(
            strength=50,
            dexterity=50,
            intelligence=50
        )
        
        # 模拟低级角色
        low_char = PoE2Character(
            name="Newbie",
            character_class=PoE2CharacterClass.WITCH,
            level=10,
            attributes=base_attributes,
            passive_skill_points=8
        )
        
        # 模拟中级角色
        mid_attributes = PoE2CharacterAttributes(
            strength=80,
            dexterity=80,
            intelligence=120
        )
        
        mid_char = PoE2Character(
            name="Intermediate",
            character_class=PoE2CharacterClass.WITCH,
            level=50,
            attributes=mid_attributes,
            ascendancy=PoE2Ascendancy.INFERNALIST,
            passive_skill_points=45
        )
        
        # 模拟高级角色
        high_attributes = PoE2CharacterAttributes(
            strength=150,
            dexterity=150,
            intelligence=300
        )
        
        high_char = PoE2Character(
            name="Endgame",
            character_class=PoE2CharacterClass.WITCH,
            level=95,
            attributes=high_attributes,
            ascendancy=PoE2Ascendancy.INFERNALIST,
            passive_skill_points=90,
            ascendancy_points=8
        )
        
        # 验证升级进程
        assert low_char.level < mid_char.level < high_char.level
        assert low_char.attributes.total < mid_char.attributes.total < high_char.attributes.total
        assert low_char.passive_skill_points < mid_char.passive_skill_points < high_char.passive_skill_points
        
        # 只有中高级角色有升华
        assert not hasattr(low_char, 'ascendancy') or low_char.ascendancy is None
        assert mid_char.ascendancy is not None
        assert high_char.ascendancy is not None
