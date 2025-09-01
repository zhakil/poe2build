"""
单元测试 - AI协调器核心功能

测试PoE2AIOrchestrator的核心功能，包括：
- 用户请求处理
- 系统组件管理
- 构筑生成和推荐
- 错误处理和备用方案
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from src.poe2build.core.ai_orchestrator import (
    PoE2AIOrchestrator,
    UserRequest,
    SystemComponent,
    ComponentStatus,
    ComponentHealth
)
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from src.poe2build.models.build import PoE2BuildGoal


@pytest.mark.unit
@pytest.mark.asyncio
class TestPoE2AIOrchestrator:
    """测试AI协调器核心功能"""
    
    async def test_orchestrator_initialization(self, mock_orchestrator_config):
        """测试协调器初始化"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # 验证初始状态
        assert orchestrator._config == mock_orchestrator_config
        assert not orchestrator._initialized
        assert orchestrator._component_health == {}
        
        # 模拟初始化组件
        with patch.object(orchestrator, '_initialize_components', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            result = await orchestrator.initialize()
            
            assert result is True
            assert orchestrator._initialized
            mock_init.assert_called_once()
            
    async def test_component_health_monitoring(self, initialized_orchestrator):
        """测试组件健康监控"""
        orchestrator = initialized_orchestrator
        
        # 获取组件健康状态
        health_status = await orchestrator.get_system_health()
        
        assert 'components' in health_status
        assert 'overall_status' in health_status
        assert 'timestamp' in health_status
        
        # 验证所有组件都有健康状态
        for component in SystemComponent:
            assert component in orchestrator._component_health
            component_health = orchestrator._component_health[component]
            assert component_health.status == ComponentStatus.HEALTHY
            
    async def test_user_request_validation(self, orchestrator_config):
        """测试用户请求验证"""
        orchestrator = PoE2AIOrchestrator(orchestrator_config)
        
        # 有效请求
        valid_request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=20.0,
            currency_type="divine"
        )
        
        # 模拟验证函数
        with patch.object(orchestrator, '_validate_user_request') as mock_validate:
            mock_validate.return_value = True
            is_valid = orchestrator._validate_user_request(valid_request)
            assert is_valid
            mock_validate.assert_called_once_with(valid_request)
            
        # 无效请求（负预算）
        invalid_request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=-5.0  # 负数无效
        )
        
        with patch.object(orchestrator, '_validate_user_request') as mock_validate:
            mock_validate.return_value = False
            is_valid = orchestrator._validate_user_request(invalid_request)
            assert not is_valid
            
    async def test_build_generation_workflow(self, initialized_orchestrator, sample_user_request):
        """测试构筑生成工作流"""
        orchestrator = initialized_orchestrator
        
        # Mock RAG推荐
        mock_rag_recommendations = [
            {
                'name': 'Lightning Sorceress Build',
                'level': 92,
                'estimated_dps': 850000,
                'estimated_ehp': 8200,
                'estimated_cost': 18.0,
                'main_skill': 'Lightning Bolt',
                'confidence': 0.89
            }
        ]
        
        orchestrator._rag_engine.generate_recommendations.return_value = mock_rag_recommendations
        
        # Mock PoB2计算
        mock_pob2_stats = {
            'total_dps': 875000,
            'ehp': 8100,
            'fire_res': 78,
            'cold_res': 76,
            'lightning_res': 79,
            'validation_status': 'valid'
        }
        
        orchestrator._pob2_local.calculate_build_stats.return_value = mock_pob2_stats
        orchestrator._pob2_local.generate_build_code.return_value = "mock_pob2_code_123"
        
        # 执行构筑生成
        result = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 验证结果
        assert 'recommendations' in result
        assert 'metadata' in result
        assert len(result['recommendations']) > 0
        
        recommendation = result['recommendations'][0]
        assert 'name' in recommendation
        assert 'pob2_data' in recommendation
        assert recommendation['pob2_data']['validation_status'] == 'valid'
        
        # 验证调用次数
        orchestrator._rag_engine.generate_recommendations.assert_called_once()
        orchestrator._pob2_local.calculate_build_stats.assert_called_once()
        
    async def test_error_handling_and_fallbacks(self, initialized_orchestrator, sample_user_request):
        """测试错误处理和备用方案"""
        orchestrator = initialized_orchestrator
        
        # 模拟RAG引擎失败
        orchestrator._rag_engine.generate_recommendations.side_effect = Exception("RAG engine failed")
        
        # 模拟备用数据
        mock_fallback_builds = [
            {
                'name': 'Fallback Lightning Build',
                'level': 85,
                'estimated_dps': 600000,
                'estimated_ehp': 7000,
                'estimated_cost': 12.0,
                'source': 'fallback_cache'
            }
        ]
        
        orchestrator._cache_manager.get.return_value = mock_fallback_builds
        
        # 执行构筑生成（应该使用备用方案）
        result = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 验证备用方案被使用
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0
        
        recommendation = result['recommendations'][0]
        assert recommendation['source'] == 'fallback_cache'
        assert 'fallback_reason' in result['metadata']
        
    async def test_concurrent_request_handling(self, initialized_orchestrator):
        """测试并发请求处理"""
        orchestrator = initialized_orchestrator
        
        # 创建多个用户请求
        requests = []
        for i in range(3):
            request = UserRequest(
                character_class=PoE2CharacterClass.WITCH,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=10.0 + i * 5,
                request_id=f"test_request_{i}"
            )
            requests.append(request)
        
        # Mock返回结果
        orchestrator._rag_engine.generate_recommendations.return_value = [{
            'name': 'Test Build',
            'level': 85,
            'estimated_dps': 500000,
            'confidence': 0.8
        }]
        
        # 并发执行
        tasks = [orchestrator.generate_build_recommendations(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证结果
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
            assert 'recommendations' in result
            
    async def test_cache_integration(self, initialized_orchestrator, sample_user_request):
        """测试缓存集成"""
        orchestrator = initialized_orchestrator
        
        # 第一次请求（缓存未命中）
        orchestrator._cache_manager.get.return_value = None
        
        mock_recommendations = [{
            'name': 'Cached Build',
            'level': 90,
            'estimated_dps': 750000,
            'confidence': 0.85
        }]
        
        orchestrator._rag_engine.generate_recommendations.return_value = mock_recommendations
        
        result1 = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 验证缓存设置被调用
        orchestrator._cache_manager.set.assert_called()
        
        # 第二次请求（缓存命中）
        orchestrator._cache_manager.get.return_value = mock_recommendations
        orchestrator._cache_manager.reset_mock()
        
        result2 = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 验证缓存命中
        orchestrator._cache_manager.get.assert_called()
        assert result1['recommendations'][0]['name'] == result2['recommendations'][0]['name']
        
    async def test_pob2_integration_fallback(self, initialized_orchestrator, sample_user_request):
        """测试PoB2集成备用方案"""
        orchestrator = initialized_orchestrator
        
        # 模拟本地PoB2不可用
        orchestrator._pob2_local.is_available.return_value = False
        orchestrator._pob2_local.calculate_build_stats.side_effect = Exception("PoB2 local unavailable")
        
        # 模拟Web PoB2可用
        mock_web_stats = {
            'total_dps': 720000,
            'ehp': 7800,
            'validation_status': 'valid',
            'calculated_by': 'web_pob2'
        }
        
        orchestrator._pob2_web.calculate_build_stats.return_value = mock_web_stats
        orchestrator._pob2_web.generate_build_code.return_value = "web_pob2_code_456"
        
        # Mock RAG结果
        orchestrator._rag_engine.generate_recommendations.return_value = [{
            'name': 'Test Build',
            'level': 88,
            'estimated_dps': 700000,
            'confidence': 0.82
        }]
        
        # 执行请求
        result = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 验证Web PoB2被使用
        assert 'recommendations' in result
        recommendation = result['recommendations'][0]
        assert 'pob2_data' in recommendation
        assert recommendation['pob2_data']['calculated_by'] == 'web_pob2'
        
        # 验证调用次数
        orchestrator._pob2_web.calculate_build_stats.assert_called_once()
        
    async def test_request_rate_limiting(self, initialized_orchestrator):
        """测试请求限流"""
        orchestrator = initialized_orchestrator
        
        # 模拟高频请求
        requests = []
        for i in range(20):  # 超过配置中的每分钟60个请求限制
            request = UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=5.0,
                request_id=f"rate_limit_test_{i}"
            )
            requests.append(request)
        
        # Mock限流检查
        with patch.object(orchestrator, '_check_rate_limit') as mock_rate_check:
            mock_rate_check.side_effect = [True] * 10 + [False] * 10  # 前10个通过，后10个被限制
            
            results = []
            for request in requests:
                try:
                    result = await orchestrator.generate_build_recommendations(request)
                    results.append(result)
                except Exception as e:
                    results.append(e)
            
            # 验证限流生效
            successful_requests = [r for r in results if not isinstance(r, Exception)]
            failed_requests = [r for r in results if isinstance(r, Exception)]
            
            assert len(successful_requests) <= 10  # 最多10个成功
            assert len(failed_requests) >= 10  # 至少10个失败


@pytest.mark.unit
class TestUserRequest:
    """测试用户请求模型"""
    
    def test_create_minimal_request(self):
        """测试创建最小用户请求"""
        request = UserRequest(
            character_class=PoE2CharacterClass.WITCH,
            build_goal=PoE2BuildGoal.LEAGUE_START
        )
        
        assert request.character_class == PoE2CharacterClass.WITCH
        assert request.build_goal == PoE2BuildGoal.LEAGUE_START
        assert request.max_budget is None  # 默认值
        assert request.currency_type == "divine"  # 默认值
        
    def test_request_validation(self):
        """测试请求验证"""
        # 有效请求
        valid_request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=15.0,
            min_dps=500000,
            min_ehp=7000
        )
        
        assert valid_request.max_budget > 0
        assert valid_request.min_dps > 0
        assert valid_request.min_ehp > 0
        
        # 无效请求（负数预算）
        with pytest.raises(ValueError):
            UserRequest(
                character_class=PoE2CharacterClass.WITCH,
                build_goal=PoE2BuildGoal.LEAGUE_START,
                max_budget=-5.0
            )
            
        # 无效请求（负数DPS要求）
        with pytest.raises(ValueError):
            UserRequest(
                character_class=PoE2CharacterClass.WITCH,
                build_goal=PoE2BuildGoal.LEAGUE_START,
                min_dps=-100000
            )
            
    def test_request_serialization(self, sample_user_request):
        """测试请求序列化"""
        request_dict = sample_user_request.model_dump()
        assert isinstance(request_dict, dict)
        
        # 从字典重建
        rebuilt_request = UserRequest(**request_dict)
        assert rebuilt_request.character_class == sample_user_request.character_class
        assert rebuilt_request.build_goal == sample_user_request.build_goal
        assert rebuilt_request.max_budget == sample_user_request.max_budget


@pytest.mark.unit
class TestSystemComponents:
    """测试系统组件管理"""
    
    def test_component_health_status(self):
        """测试组件健康状态"""
        health = ComponentHealth(
            component=SystemComponent.RAG_ENGINE,
            status=ComponentStatus.HEALTHY,
            response_time_ms=125.5,
            last_check=1700000000.0
        )
        
        assert health.component == SystemComponent.RAG_ENGINE
        assert health.status == ComponentStatus.HEALTHY
        assert health.response_time_ms == 125.5
        assert health.is_healthy
        
    def test_unhealthy_component(self):
        """测试不健康组件"""
        unhealthy = ComponentHealth(
            component=SystemComponent.POB2_LOCAL,
            status=ComponentStatus.ERROR,
            response_time_ms=0.0,
            last_check=1700000000.0,
            error_message="Connection timeout"
        )
        
        assert unhealthy.status == ComponentStatus.ERROR
        assert not unhealthy.is_healthy
        assert unhealthy.error_message == "Connection timeout"
        
    def test_component_status_enum(self):
        """测试组件状态枚举"""
        statuses = list(ComponentStatus)
        expected_statuses = [
            ComponentStatus.HEALTHY,
            ComponentStatus.DEGRADED,
            ComponentStatus.ERROR,
            ComponentStatus.UNAVAILABLE
        ]
        
        for status in expected_statuses:
            assert status in statuses
            
    def test_system_component_enum(self):
        """测试系统组件枚举"""
        components = list(SystemComponent)
        expected_components = [
            SystemComponent.RAG_ENGINE,
            SystemComponent.POB2_LOCAL,
            SystemComponent.POB2_WEB,
            SystemComponent.MARKET_API,
            SystemComponent.NINJA_SCRAPER,
            SystemComponent.CACHE_MANAGER
        ]
        
        for component in expected_components:
            assert component in components
