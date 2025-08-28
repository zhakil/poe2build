"""Phase 3 PoB2集成系统测试"""

import pytest
import asyncio
from pathlib import Path

from src.poe2build.pob2.path_detector import PoB2PathDetector, PoB2Platform
from src.poe2build.pob2.local_client import PoB2LocalClient, MockPoB2LocalClient, PoB2ProcessConfig
from src.poe2build.pob2.import_export import PoB2DataConverter
from src.poe2build.pob2.calculator import PoB2Calculator
from src.poe2build.models.build import PoE2Build, PoE2BuildStats
from src.poe2build.models.characters import PoE2CharacterClass
from src.poe2build.data_sources.factory import get_factory


class TestPoB2Integration:
    """PoB2集成系统测试"""
    
    @pytest.mark.asyncio
    async def test_path_detection(self):
        """测试PoB2路径检测"""
        detector = PoB2PathDetector()
        
        # 测试平台检测
        assert detector.current_platform in [PoB2Platform.WINDOWS, PoB2Platform.MACOS, PoB2Platform.LINUX]
        
        # 测试安装检测
        installations = await detector.detect_installations(use_cache=False)
        
        # 即使没有真实安装，也应该不出错
        assert isinstance(installations, list)
        
        # 测试手动添加
        test_path = Path.cwd()  # 使用当前目录作为测试路径
        manual_install = await detector.add_manual_installation(str(test_path))
        # 预期失败，因为当前目录不是有效的PoB2安装
        assert manual_install is None
    
    @pytest.mark.asyncio
    async def test_data_converter(self):
        """测试数据格式转换"""
        converter = PoB2DataConverter()
        
        # 创建测试构筑
        test_build = PoE2Build(
            name="Test Build",
            character_class=PoE2CharacterClass.WITCH,
            level=75,
            main_skill_gem="Fireball",
            support_gems=["Fire Penetration", "Elemental Focus"],
            key_items=["Test Weapon"]
        )
        
        # 测试构筑转PoB2代码
        import_code = converter.build_to_pob2_code(test_build)
        assert import_code is not None
        assert len(import_code) > 100
        
        # 测试PoB2代码验证
        is_valid = converter.validate_pob2_code(import_code)
        assert is_valid is True
        
        # 测试PoB2代码解码
        decoded = converter.decode_pob2_code(import_code)
        assert decoded is not None
        assert decoded.version == "2.0"
        
        # 测试PoB2代码转构筑
        converted_build = converter.pob2_code_to_build(import_code)
        assert converted_build is not None
        assert converted_build.name == "Test Build"
        assert converted_build.character_class == PoE2CharacterClass.WITCH
        assert converted_build.level == 75
        
        # 测试最小代码生成
        minimal_code = converter.generate_minimal_pob2_code(
            PoE2CharacterClass.RANGER, 
            level=50, 
            main_skill="Ice Shard"
        )
        assert minimal_code is not None
        assert converter.validate_pob2_code(minimal_code)
    
    @pytest.mark.asyncio
    async def test_mock_client(self):
        """测试Mock客户端"""
        mock_client = MockPoB2LocalClient()
        
        # 测试初始化
        init_result = await mock_client.initialize()
        assert init_result is True
        
        # 测试进程启动
        start_result = await mock_client.start_process()
        assert start_result is True
        
        # 测试构筑计算
        test_import_code = "test_import_code_placeholder"
        calc_result = await mock_client.calculate_build(test_import_code)
        
        assert calc_result.success is True
        assert calc_result.data is not None
        assert calc_result.data['mock'] is True
        assert calc_result.calculation_time > 0
        
        # 测试状态获取
        status = mock_client.get_status()
        assert status['mock'] is True
        assert 'process_state' in status
        
        # 测试停止
        stop_result = await mock_client.stop_process()
        assert stop_result is True
        
        # 测试清理
        await mock_client.cleanup()
    
    @pytest.mark.asyncio 
    async def test_calculator_provider(self):
        """测试PoB2计算提供者"""
        calculator = PoB2Calculator()
        
        # 测试初始化
        init_result = await calculator.initialize()
        assert init_result is True
        
        # 测试健康状态
        health_status = await calculator.get_health_status()
        assert health_status in ['healthy', 'degraded', 'unhealthy', 'offline']
        
        # 测试连接
        connection_ok = await calculator.test_connection()
        assert isinstance(connection_ok, bool)
        
        # 测试提供者名称
        provider_name = calculator.get_provider_name()
        assert provider_name in ['PoB2Calculator', 'MockPoB2Calculator']
        
        # 测试速率限制信息
        rate_info = calculator.get_rate_limit_info()
        assert 'concurrent_calculations' in rate_info
        assert 'calculation_timeout' in rate_info
        
        # 测试构筑计算
        test_build_data = {
            'character_class': 'Witch',
            'level': 80,
            'main_skill': 'Lightning Bolt'
        }
        
        calc_result = await calculator.calculate_build_stats(test_build_data)
        assert calc_result['success'] is True
        assert 'calculated_stats' in calc_result
        assert calc_result['calculated_stats']['total_dps'] > 0
        
        # 测试构筑验证
        is_valid = await calculator.validate_build(test_build_data)
        assert isinstance(is_valid, bool)
        
        # 测试导入代码生成
        import_code = await calculator.generate_import_code(test_build_data)
        assert import_code is not None
        assert len(import_code) > 50
        
        # 测试导入代码解析
        parsed_data = await calculator.parse_import_code(import_code)
        assert parsed_data is not None
        assert 'character_class' in parsed_data
        
        # 测试统计信息
        stats = calculator.get_stats()
        assert 'provider_name' in stats
        assert 'total_calculations' in stats
        
        # 测试清理
        await calculator.cleanup()
    
    @pytest.mark.asyncio
    async def test_factory_calculation_provider(self):
        """测试工厂创建计算提供者"""
        factory = get_factory()
        
        # 测试创建PoB2计算提供者
        calculator = factory.create_calculation_provider('pob2_calculator')
        assert calculator is not None
        assert calculator.get_provider_name() in ['PoB2Calculator', 'MockPoB2Calculator']
        
        # 测试获取可用提供者
        available = factory.get_available_providers('calculation')
        assert 'pob2_calculator' in available
    
    @pytest.mark.asyncio
    async def test_process_config(self):
        """测试进程配置"""
        config = PoB2ProcessConfig()
        
        # 测试默认配置
        assert config.timeout == 120
        assert config.memory_limit == 2048
        assert config.headless_mode is True
        
        # 测试自定义配置
        custom_config = PoB2ProcessConfig(
            timeout=180,
            memory_limit=4096,
            headless_mode=False
        )
        
        assert custom_config.timeout == 180
        assert custom_config.memory_limit == 4096
        assert custom_config.headless_mode is False
    
    @pytest.mark.asyncio
    async def test_end_to_end_calculation(self):
        """测试端到端计算流程"""
        # 创建测试构筑
        test_build = PoE2Build(
            name="End-to-End Test Build",
            character_class=PoE2CharacterClass.MONK,
            level=85,
            main_skill_gem="Quarter Staff",
            support_gems=["Melee Physical Damage", "Multistrike"],
            estimated_cost=5.0
        )
        
        # 使用计算器进行完整计算流程
        calculator = PoB2Calculator()
        await calculator.initialize()
        
        try:
            # 1. 构筑数据转换
            build_dict = test_build.to_dict()
            
            # 2. 生成导入代码
            import_code = await calculator.generate_import_code(build_dict)
            assert import_code is not None
            
            # 3. 验证构筑
            is_valid = await calculator.validate_build(build_dict)
            assert is_valid is True
            
            # 4. 计算统计数据
            calc_result = await calculator.calculate_build_stats(build_dict)
            assert calc_result['success'] is True
            
            # 5. 验证计算结果
            stats = calc_result['calculated_stats']
            assert stats['total_dps'] > 0
            assert stats['life'] > 0
            assert stats['effective_health_pool'] > 0
            
            # 6. 解析导入代码
            parsed_build = await calculator.parse_import_code(import_code)
            assert parsed_build is not None
            assert parsed_build['name'] == test_build.name
            
        finally:
            await calculator.cleanup()


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))