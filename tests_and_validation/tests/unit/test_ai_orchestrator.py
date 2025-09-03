"""
AI协调器单元测试
测试PoE2AIOrchestrator的核心功能和组件协调
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.poe2build.core.ai_orchestrator import (
    PoE2AIOrchestrator, UserRequest, RecommendationResult,
    SystemComponent, ComponentStatus, ComponentHealth
)
from src.poe2build.models.build import PoE2Build, PoE2BuildStats, PoE2BuildGoal
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from tests.fixtures.test_data import TestDataFactory


class TestPoE2AIOrchestrator:
    """AI协调器核心测试"""
    
    def test_orchestrator_initialization(self, mock_orchestrator_config):
        """测试协调器初始化"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        assert orchestrator.config == mock_orchestrator_config
        assert not orchestrator._initialized
        assert orchestrator._request_count == 0
        assert orchestrator._error_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self, mock_orchestrator_config):
        """测试成功初始化所有组件"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # Mock所有组件初始化方法
        with patch.object(orchestrator, '_init_cache_manager', return_value=1), \
             patch.object(orchestrator, '_init_market_api', return_value=1), \
             patch.object(orchestrator, '_init_ninja_scraper', return_value=1), \
             patch.object(orchestrator, '_init_pob2_local', return_value=1), \
             patch.object(orchestrator, '_init_pob2_web', return_value=1), \
             patch.object(orchestrator, '_init_rag_engine', return_value=1):
            
            success = await orchestrator.initialize()
            
            assert success
            assert orchestrator._initialized
            assert len(orchestrator._component_health) == len(SystemComponent)
    
    @pytest.mark.asyncio
    async def test_partial_initialization_failure(self, mock_orchestrator_config):
        """测试部分组件初始化失败"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # Mock部分组件初始化失败
        with patch.object(orchestrator, '_init_cache_manager', return_value=1), \
             patch.object(orchestrator, '_init_market_api', return_value=0), \
             patch.object(orchestrator, '_init_ninja_scraper', return_value=1), \
             patch.object(orchestrator, '_init_pob2_local', return_value=0), \
             patch.object(orchestrator, '_init_pob2_web', return_value=1), \
             patch.object(orchestrator, '_init_rag_engine', return_value=1):
            
            success = await orchestrator.initialize()
            
            # 4/6组件成功，成功率>50%，应该初始化成功
            assert success
            assert orchestrator._initialized
    
    @pytest.mark.asyncio
    async def test_initialization_failure_threshold(self, mock_orchestrator_config):
        """测试初始化失败阈值"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # Mock大部分组件初始化失败
        with patch.object(orchestrator, '_init_cache_manager', return_value=0), \
             patch.object(orchestrator, '_init_market_api', return_value=0), \
             patch.object(orchestrator, '_init_ninja_scraper', return_value=0), \
             patch.object(orchestrator, '_init_pob2_local', return_value=0), \
             patch.object(orchestrator, '_init_pob2_web', return_value=1), \
             patch.object(orchestrator, '_init_rag_engine', return_value=1):
            
            success = await orchestrator.initialize()
            
            # 只有2/6组件成功，成功率<50%，应该初始化失败
            assert not success
            assert not orchestrator._initialized
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_not_initialized(self):
        """测试未初始化时生成推荐"""
        orchestrator = PoE2AIOrchestrator()
        request = TestDataFactory.create_user_request()
        
        with pytest.raises(RuntimeError, match="Orchestrator not initialized"):
            await orchestrator.generate_build_recommendations(request)
    
    @pytest.mark.asyncio
    async def test_successful_recommendation_generation(self, initialized_orchestrator, sample_user_request):
        """测试成功生成推荐"""
        orchestrator = initialized_orchestrator
        
        # Mock RAG引擎响应
        orchestrator._rag_engine.generate_recommendations.return_value = [
            {
                'name': 'Test Lightning Build',
                'level': 90,
                'estimated_dps': 800000,
                'estimated_ehp': 7500,
                'estimated_cost': 12.0,
                'main_skill': 'Lightning Bolt',
                'support_gems': ['Added Lightning', 'Lightning Penetration'],
                'confidence': 0.85
            }
        ]
        
        # Mock市场API响应
        orchestrator._market_api.get_item_price.return_value = {
            'median_price': 3.5,
            'currency': 'divine',
            'confidence': 0.9
        }
        
        # Mock PoB2计算响应
        orchestrator._pob2_local.generate_build_code.return_value = "mock_pob2_code"
        orchestrator._pob2_local.calculate_build_stats.return_value = {
            'total_dps': 850000,
            'ehp': 8000,
            'fire_res': 78,
            'cold_res': 76,
            'lightning_res': 77,
            'chaos_res': -25
        }
        
        result = await orchestrator.generate_build_recommendations(sample_user_request)
        
        assert isinstance(result, RecommendationResult)
        assert len(result.builds) > 0
        assert result.pob2_validated == sample_user_request.validate_with_pob2
        assert result.generation_time_ms > 0
        assert SystemComponent.RAG_ENGINE in result.used_components
    
    @pytest.mark.asyncio
    async def test_recommendation_with_budget_filtering(self, initialized_orchestrator, budget_user_request):
        """测试带预算过滤的推荐生成"""
        orchestrator = initialized_orchestrator
        
        # Mock RAG引擎返回多个构筑，包括超预算的
        orchestrator._rag_engine.generate_recommendations.return_value = [
            {
                'name': 'Budget Build',
                'estimated_cost': 3.0,
                'estimated_dps': 400000,
                'estimated_ehp': 6000,
                'confidence': 0.8
            },
            {
                'name': 'Expensive Build',
                'estimated_cost': 25.0,  # 超出预算
                'estimated_dps': 1200000,
                'estimated_ehp': 8000,
                'confidence': 0.9
            }
        ]
        
        # Mock市场数据增强
        async def mock_enhance_market_data(builds, request):
            return [b for b in builds if b.estimated_cost <= request.max_budget]
        
        with patch.object(orchestrator, '_enhance_with_market_data', side_effect=mock_enhance_market_data):
            result = await orchestrator.generate_build_recommendations(budget_user_request)
        
        # 验证只保留预算内的构筑
        for build in result.builds:
            if build.estimated_cost:
                assert build.estimated_cost <= budget_user_request.max_budget
    
    @pytest.mark.asyncio
    async def test_recommendation_error_handling(self, initialized_orchestrator, sample_user_request):
        """测试推荐生成错误处理"""
        orchestrator = initialized_orchestrator
        
        # Mock RAG引擎抛出异常
        orchestrator._rag_engine.generate_recommendations.side_effect = Exception("RAG engine failed")
        
        result = await orchestrator.generate_build_recommendations(sample_user_request)
        
        # 应该返回降级结果
        assert isinstance(result, RecommendationResult)
        assert len(result.builds) > 0  # 应该有降级构筑
        assert result.metadata.get('fallback_mode') == True
        assert orchestrator._error_count == 1
    
    @pytest.mark.asyncio
    async def test_fallback_recommendation_generation(self, initialized_orchestrator, sample_user_request):
        """测试降级推荐生成"""
        orchestrator = initialized_orchestrator
        
        fallback_builds = await orchestrator._generate_fallback_recommendations(sample_user_request)
        
        assert len(fallback_builds) > 0
        assert all(isinstance(build, PoE2Build) for build in fallback_builds)
        
        # 验证降级构筑的基本属性
        fallback_build = fallback_builds[0]
        assert fallback_build.character_class == sample_user_request.character_class
        assert fallback_build.validate()
    
    def test_component_health_checking(self, initialized_orchestrator):
        """测试组件健康状态检查"""
        orchestrator = initialized_orchestrator
        
        # 测试健康组件
        assert orchestrator._is_component_healthy(SystemComponent.RAG_ENGINE)
        
        # 设置不健康组件
        orchestrator._component_health[SystemComponent.MARKET_API] = ComponentHealth(
            component=SystemComponent.MARKET_API,
            status=ComponentStatus.ERROR,
            error_message="API unavailable"
        )
        
        assert not orchestrator._is_component_healthy(SystemComponent.MARKET_API)
    
    def test_get_available_pob2_client(self, initialized_orchestrator):
        """测试PoB2客户端选择"""
        orchestrator = initialized_orchestrator
        
        # 本地客户端可用时应选择本地
        client = orchestrator._get_available_pob2_client()
        assert client == orchestrator._pob2_local
        
        # 本地不可用时选择Web版本
        orchestrator._component_health[SystemComponent.POB2_LOCAL].status = ComponentStatus.ERROR
        client = orchestrator._get_available_pob2_client()
        assert client == orchestrator._pob2_web
        
        # 都不可用时返回None
        orchestrator._component_health[SystemComponent.POB2_WEB].status = ComponentStatus.ERROR
        client = orchestrator._get_available_pob2_client()
        assert client is None
    
    @pytest.mark.asyncio
    async def test_health_check(self, initialized_orchestrator):
        """测试系统健康检查"""
        orchestrator = initialized_orchestrator
        orchestrator._request_count = 100
        orchestrator._error_count = 5
        orchestrator._total_response_time = 25000
        
        health_report = await orchestrator.health_check()
        
        assert 'timestamp' in health_report
        assert 'overall_status' in health_report
        assert 'components' in health_report
        assert 'performance' in health_report
        
        # 验证性能指标
        perf = health_report['performance']
        assert perf['total_requests'] == 100
        assert perf['error_count'] == 5
        assert perf['error_rate'] == 0.05
        assert perf['average_response_time_ms'] == 250.0
    
    def test_get_system_stats(self, initialized_orchestrator):
        """测试系统统计信息获取"""
        orchestrator = initialized_orchestrator
        orchestrator._request_count = 50
        orchestrator._error_count = 2
        
        stats = orchestrator.get_system_stats()
        
        assert stats['initialized'] == True
        assert stats['request_count'] == 50
        assert stats['error_count'] == 2
        assert stats['success_rate'] == 0.96
        assert stats['component_count'] == len(SystemComponent)


class TestUserRequest:
    """用户请求测试"""
    
    def test_user_request_creation(self):
        """测试用户请求创建"""
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=25.0,
            currency_type="divine",
            preferred_skills=["Lightning Bolt"],
            min_dps=500000,
            require_resistance_cap=True
        )
        
        assert request.character_class == PoE2CharacterClass.SORCERESS
        assert request.max_budget == 25.0
        assert request.min_dps == 500000
        assert request.require_resistance_cap == True
    
    def test_user_request_defaults(self):
        """测试用户请求默认值"""
        request = UserRequest()
        
        assert request.character_class is None
        assert request.currency_type == "divine"
        assert request.require_resistance_cap == True
        assert request.include_meta_builds == True
        assert request.generate_pob2_code == True


class TestRecommendationResult:
    """推荐结果测试"""
    
    def test_recommendation_result_creation(self, sample_builds_list):
        """测试推荐结果创建"""
        metadata = {
            'generation_timestamp': time.time(),
            'component_health': {'rag_engine': 'healthy'}
        }
        
        result = RecommendationResult(
            builds=sample_builds_list,
            metadata=metadata,
            rag_confidence=0.85,
            pob2_validated=True,
            generation_time_ms=234.5,
            used_components=[SystemComponent.RAG_ENGINE, SystemComponent.POB2_LOCAL]
        )
        
        assert len(result.builds) == len(sample_builds_list)
        assert result.rag_confidence == 0.85
        assert result.pob2_validated == True
        assert result.generation_time_ms == 234.5
        assert SystemComponent.RAG_ENGINE in result.used_components


class TestOrchestratorRecommendationFlow:
    """协调器推荐流程测试"""
    
    @pytest.mark.asyncio
    async def test_rag_recommendation_generation(self, initialized_orchestrator, sample_user_request):
        """测试RAG推荐生成"""
        orchestrator = initialized_orchestrator
        
        # Mock RAG引擎响应
        mock_recommendations = [
            {
                'name': 'RAG Lightning Build',
                'level': 92,
                'estimated_dps': 900000,
                'estimated_ehp': 7800,
                'estimated_cost': 15.0,
                'main_skill': 'Lightning Bolt',
                'support_gems': ['Added Lightning', 'Lightning Penetration'],
                'confidence': 0.88
            }
        ]
        orchestrator._rag_engine.generate_recommendations.return_value = mock_recommendations
        
        builds, confidence = await orchestrator._generate_rag_recommendations(sample_user_request)
        
        assert len(builds) == 1
        assert confidence == 0.88
        assert builds[0].name == 'RAG Lightning Build'
        assert builds[0].character_class == sample_user_request.character_class
    
    @pytest.mark.asyncio
    async def test_market_data_enhancement(self, initialized_orchestrator, sample_builds_list, sample_user_request):
        """测试市场数据增强"""
        orchestrator = initialized_orchestrator
        
        # Mock市场API返回价格数据
        orchestrator._market_api.get_item_price.return_value = {
            'median_price': 4.5,
            'currency': 'divine'
        }
        
        enhanced_builds = await orchestrator._enhance_with_market_data(sample_builds_list, sample_user_request)
        
        assert len(enhanced_builds) <= len(sample_builds_list)
        
        # 验证市场API被调用
        assert orchestrator._market_api.get_item_price.called
    
    @pytest.mark.asyncio
    async def test_pob2_validation(self, initialized_orchestrator, sample_builds_list, sample_user_request):
        """测试PoB2验证"""
        orchestrator = initialized_orchestrator
        
        # Mock PoB2客户端响应
        orchestrator._pob2_local.generate_build_code.return_value = "mock_pob2_import_code"
        orchestrator._pob2_local.calculate_build_stats.return_value = {
            'total_dps': 950000,
            'ehp': 8200,
            'fire_res': 78,
            'cold_res': 76,
            'lightning_res': 77,
            'chaos_res': -25
        }
        
        validated_builds = await orchestrator._validate_with_pob2(
            sample_builds_list, orchestrator._pob2_local, sample_user_request
        )
        
        assert len(validated_builds) <= len(sample_builds_list)
        
        # 验证PoB2代码生成被调用
        assert orchestrator._pob2_local.generate_build_code.called
        assert orchestrator._pob2_local.calculate_build_stats.called
    
    @pytest.mark.asyncio
    async def test_build_requirements_validation(self, initialized_orchestrator):
        """测试构筑需求验证"""
        orchestrator = initialized_orchestrator
        
        # 创建满足需求的构筑
        valid_build = PoE2Build(
            name="Valid Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=PoE2BuildStats(
                total_dps=800000,  # 满足最低DPS
                effective_health_pool=7500,  # 满足最低EHP
                fire_resistance=78,  # 满足抗性需求
                cold_resistance=76,
                lightning_resistance=77,
                chaos_resistance=-25
            )
        )
        
        request = UserRequest(
            min_dps=500000,
            min_ehp=6000,
            require_resistance_cap=True
        )
        
        assert orchestrator._validate_build_requirements(valid_build, request)
        
        # 创建不满足需求的构筑
        invalid_build = PoE2Build(
            name="Invalid Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=90,
            stats=PoE2BuildStats(
                total_dps=300000,  # DPS不足
                effective_health_pool=4000,  # EHP不足
                fire_resistance=70,  # 抗性不足
                cold_resistance=70,
                lightning_resistance=70,
                chaos_resistance=-30
            )
        )
        
        assert not orchestrator._validate_build_requirements(invalid_build, request)
    
    def test_build_score_calculation(self, initialized_orchestrator):
        """测试构筑评分计算"""
        orchestrator = initialized_orchestrator
        
        high_score_build = PoE2Build(
            name="High Score Build",
            character_class=PoE2CharacterClass.SORCERESS,
            level=95,
            estimated_cost=10.0,
            stats=PoE2BuildStats(
                total_dps=1500000,  # 高DPS
                effective_health_pool=10000,  # 高EHP
                fire_resistance=78,  # 满抗
                cold_resistance=76,
                lightning_resistance=77,
                chaos_resistance=-20
            )
        )
        
        request = UserRequest(max_budget=20.0)
        
        score = orchestrator._calculate_build_score(high_score_build, request)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # 高质量构筑应该有较高分数
    
    @pytest.mark.asyncio
    async def test_final_recommendations_sorting(self, initialized_orchestrator, sample_builds_list):
        """测试最终推荐排序"""
        orchestrator = initialized_orchestrator
        
        # 按Boss击杀目标排序
        boss_request = UserRequest(build_goal=PoE2BuildGoal.BOSS_KILLING)
        sorted_builds = await orchestrator._finalize_recommendations(sample_builds_list, boss_request)
        
        # 验证按DPS降序排列
        for i in range(len(sorted_builds) - 1):
            current_dps = sorted_builds[i].stats.total_dps if sorted_builds[i].stats else 0
            next_dps = sorted_builds[i + 1].stats.total_dps if sorted_builds[i + 1].stats else 0
            assert current_dps >= next_dps
        
        # 按预算友好目标排序
        budget_request = UserRequest(build_goal=PoE2BuildGoal.BUDGET_FRIENDLY)
        sorted_builds = await orchestrator._finalize_recommendations(sample_builds_list, budget_request)
        
        # 验证按成本升序排列
        for i in range(len(sorted_builds) - 1):
            current_cost = sorted_builds[i].estimated_cost or float('inf')
            next_cost = sorted_builds[i + 1].estimated_cost or float('inf')
            assert current_cost <= next_cost