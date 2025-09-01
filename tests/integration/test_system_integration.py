"""
系统集成测试
测试整个PoE2构筑生成系统的端到端集成
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, Mock
from typing import Dict, List, Any, Optional

from src.poe2build.core.ai_orchestrator import (
    PoE2AIOrchestrator, UserRequest, RecommendationResult,
    SystemComponent, ComponentStatus
)
from src.poe2build.models.build import PoE2Build, PoE2BuildGoal
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from tests.fixtures.sample_builds import get_sample_builds, SAMPLE_BUILDS
from tests.fixtures.test_data import TestDataFactory
from tests.integration.test_api_integration import (
    MockPoE2ScoutAPI, MockNinjaAPI, MockPoE2DBAPI
)


class IntegratedTestOrchestrator(PoE2AIOrchestrator):
    """用于集成测试的协调器实现"""
    
    def __init__(self, config: Dict[str, Any] = None, use_real_apis: bool = False):
        super().__init__(config)
        self.use_real_apis = use_real_apis
        self._test_mode = True
    
    async def initialize_for_testing(self):
        """为测试初始化组件"""
        # 使用Mock组件
        self._rag_engine = MockRAGEngine()
        self._market_api = MockPoE2ScoutAPI()
        self._ninja_scraper = MockNinjaAPI()
        self._pob2_local = MockPoB2LocalClient()
        self._pob2_web = MockPoB2WebClient()
        self._cache_manager = MockCacheManager()
        
        # 设置所有组件为健康状态
        from src.poe2build.core.ai_orchestrator import ComponentHealth
        for component in SystemComponent:
            self._component_health[component] = ComponentHealth(
                component=component,
                status=ComponentStatus.HEALTHY,
                response_time_ms=100.0,
                last_check=time.time()
            )
        
        self._initialized = True
        return True


class MockRAGEngine:
    """Mock RAG引擎用于集成测试"""
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self):
        """构建知识库"""
        return {
            'builds': get_sample_builds(),
            'meta_patterns': {
                'Lightning': {'popularity': 0.85, 'effectiveness': 0.90},
                'Ice': {'popularity': 0.70, 'effectiveness': 0.85},
                'Physical': {'popularity': 0.60, 'effectiveness': 0.80}
            }
        }
    
    async def generate_recommendations(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成RAG增强推荐"""
        await asyncio.sleep(0.1)  # 模拟计算时间
        
        character_class = query.get('character_class')
        build_goal = query.get('build_goal')
        max_budget = query.get('max_budget')
        
        # 从知识库中找到相似构筑
        similar_builds = []
        for build in self.knowledge_base['builds']:
            if character_class and build.character_class.value != character_class:
                continue
            
            if max_budget and build.estimated_cost and build.estimated_cost > max_budget:
                continue
            
            confidence = self._calculate_similarity_confidence(build, query)
            
            similar_builds.append({
                'name': f"RAG Enhanced {build.name}",
                'level': build.level,
                'estimated_dps': int(build.stats.total_dps * 1.1) if build.stats else 500000,
                'estimated_ehp': int(build.stats.effective_health_pool * 1.05) if build.stats else 6000,
                'estimated_cost': build.estimated_cost or 10.0,
                'main_skill': build.main_skill_gem,
                'support_gems': build.support_gems[:4] if build.support_gems else [],
                'confidence': confidence,
                'rag_source': f"Similar to {build.name}",
                'adaptations': self._generate_adaptations(build, query)
            })
        
        # 按置信度排序并返回前5个
        similar_builds.sort(key=lambda x: x['confidence'], reverse=True)
        return similar_builds[:5]
    
    def _calculate_similarity_confidence(self, build: PoE2Build, query: Dict[str, Any]) -> float:
        """计算相似度置信度"""
        confidence = 0.5  # 基础置信度
        
        # 职业匹配加分
        if query.get('character_class') == build.character_class.value:
            confidence += 0.2
        
        # 目标匹配加分
        if query.get('build_goal') and build.goal and query['build_goal'] == build.goal.value:
            confidence += 0.15
        
        # 预算匹配加分
        if query.get('max_budget') and build.estimated_cost:
            if build.estimated_cost <= query['max_budget']:
                confidence += 0.1
        
        # 技能匹配加分
        preferred_skills = query.get('preferred_skills', [])
        if build.main_skill_gem and any(skill in build.main_skill_gem for skill in preferred_skills):
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _generate_adaptations(self, build: PoE2Build, query: Dict[str, Any]) -> List[str]:
        """生成RAG适应性改进建议"""
        adaptations = []
        
        if query.get('max_budget') and build.estimated_cost:
            if build.estimated_cost > query['max_budget']:
                adaptations.append("Optimized for lower budget with alternative gear choices")
        
        if query.get('build_goal') == 'boss_killing':
            adaptations.append("Enhanced single-target damage focus")
        elif query.get('build_goal') == 'clear_speed':
            adaptations.append("Improved area damage and movement speed")
        
        if query.get('playstyle') == 'defensive':
            adaptations.append("Increased defensive layers and survivability")
        
        return adaptations


class MockPoB2LocalClient:
    """Mock PoB2本地客户端"""
    
    def __init__(self):
        self.available = True
        self.version = "2.35.1"
    
    async def is_available(self) -> bool:
        return self.available
    
    async def generate_build_code(self, build: PoE2Build) -> str:
        """生成PoB2导入代码"""
        await asyncio.sleep(0.2)  # 模拟计算时间
        return f"pob2_code_{hash(build.name) % 10000}"
    
    async def calculate_build_stats(self, build: PoE2Build) -> Dict[str, Any]:
        """计算构筑统计数据"""
        await asyncio.sleep(0.3)  # 模拟计算时间
        
        if not build.stats:
            return None
        
        # 模拟PoB2的精确计算（稍微调整原始数据）
        calculated_stats = {
            'total_dps': int(build.stats.total_dps * 1.05),  # PoB2更精确
            'ehp': int(build.stats.effective_health_pool * 1.02),
            'fire_res': min(80, build.stats.fire_resistance + 1),
            'cold_res': min(80, build.stats.cold_resistance + 1),
            'lightning_res': min(80, build.stats.lightning_resistance + 1),
            'chaos_res': build.stats.chaos_resistance + 5,  # 稍微改善
            'validation_status': 'valid',
            'calculation_time_ms': 285,
            'pob2_version': self.version
        }
        
        return calculated_stats


class MockPoB2WebClient:
    """Mock PoB2 Web客户端"""
    
    async def generate_build_code(self, build: PoE2Build) -> str:
        await asyncio.sleep(0.4)  # Web版本稍慢
        return f"web_pob2_code_{hash(build.name) % 10000}"
    
    async def calculate_build_stats(self, build: PoE2Build) -> Dict[str, Any]:
        await asyncio.sleep(0.5)  # Web版本稍慢且精度略低
        
        if not build.stats:
            return None
        
        calculated_stats = {
            'total_dps': int(build.stats.total_dps * 1.02),  # 精度略低于本地版
            'ehp': int(build.stats.effective_health_pool * 1.01),
            'fire_res': build.stats.fire_resistance,
            'cold_res': build.stats.cold_resistance,
            'lightning_res': build.stats.lightning_resistance,
            'chaos_res': build.stats.chaos_resistance + 2,
            'validation_status': 'valid',
            'calculation_time_ms': 445,
            'pob2_version': '2.34.8_web'
        }
        
        return calculated_stats


class MockCacheManager:
    """Mock缓存管理器"""
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str) -> Any:
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        self.cache[key] = value
        return True
    
    async def clear(self) -> bool:
        self.cache.clear()
        return True


@pytest.mark.integration
class TestSystemEndToEndIntegration:
    """系统端到端集成测试"""
    
    @pytest.fixture
    async def integrated_orchestrator(self):
        """创建集成测试协调器"""
        config = {
            'max_recommendations': 10,
            'timeout_seconds': 30,
            'cache': {'ttl_seconds': 600},
            'rag': {'similarity_threshold': 0.7}
        }
        
        orchestrator = IntegratedTestOrchestrator(config)
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_complete_recommendation_workflow(self, integrated_orchestrator):
        """测试完整的推荐工作流程"""
        # 创建用户请求
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            ascendancy=PoE2Ascendancy.STORMWEAVER,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=25.0,
            preferred_skills=["Lightning Bolt"],
            min_dps=500000,
            min_ehp=7000,
            require_resistance_cap=True,
            generate_pob2_code=True,
            validate_with_pob2=True
        )
        
        # 执行完整的推荐流程
        start_time = time.time()
        result = await integrated_orchestrator.generate_build_recommendations(request)
        end_time = time.time()
        
        # 验证结果结构
        assert isinstance(result, RecommendationResult)
        assert len(result.builds) > 0
        assert result.generation_time_ms > 0
        assert result.rag_confidence > 0
        assert result.pob2_validated == True
        
        # 验证使用的组件
        expected_components = [
            SystemComponent.RAG_ENGINE,
            SystemComponent.MARKET_API,
            SystemComponent.POB2_LOCAL
        ]
        for component in expected_components:
            assert component in result.used_components
        
        # 验证构筑质量
        for build in result.builds:
            assert build.character_class == request.character_class
            assert build.validate()
            
            if build.stats:
                assert build.stats.total_dps >= request.min_dps
                assert build.stats.effective_health_pool >= request.min_ehp
                
                if request.require_resistance_cap:
                    assert build.stats.is_resistance_capped()
            
            if build.estimated_cost and request.max_budget:
                assert build.estimated_cost <= request.max_budget
        
        # 验证性能
        total_time = end_time - start_time
        assert total_time < 5.0  # 整个流程应在5秒内完成
        
        # 验证元数据
        assert 'request_id' in result.metadata
        assert 'generation_timestamp' in result.metadata
        assert 'stages_completed' in result.metadata
        assert 'component_health' in result.metadata
        
        return result
    
    @pytest.mark.asyncio
    async def test_budget_constraint_integration(self, integrated_orchestrator):
        """测试预算约束的集成处理"""
        # 低预算请求
        budget_request = UserRequest(
            character_class=PoE2CharacterClass.MONK,
            build_goal=PoE2BuildGoal.BUDGET_FRIENDLY,
            max_budget=5.0,
            min_dps=200000,
            generate_pob2_code=False,
            validate_with_pob2=False
        )
        
        result = await integrated_orchestrator.generate_build_recommendations(budget_request)
        
        # 验证所有推荐都在预算内
        assert len(result.builds) > 0
        for build in result.builds:
            if build.estimated_cost:
                assert build.estimated_cost <= budget_request.max_budget
            
            # 验证适合预算友好目标
            assert build.is_suitable_for_goal(PoE2BuildGoal.BUDGET_FRIENDLY)
    
    @pytest.mark.asyncio
    async def test_high_performance_build_integration(self, integrated_orchestrator):
        """测试高性能构筑集成"""
        # 高性能Boss击杀请求
        boss_request = UserRequest(
            character_class=PoE2CharacterClass.WITCH,
            build_goal=PoE2BuildGoal.BOSS_KILLING,
            max_budget=50.0,
            min_dps=1000000,
            min_ehp=8000,
            require_resistance_cap=True,
            generate_pob2_code=True,
            validate_with_pob2=True
        )
        
        result = await integrated_orchestrator.generate_build_recommendations(boss_request)
        
        # 验证高性能要求
        assert len(result.builds) > 0
        for build in result.builds:
            if build.stats:
                assert build.stats.total_dps >= boss_request.min_dps
                assert build.stats.effective_health_pool >= boss_request.min_ehp
                assert build.stats.is_resistance_capped()
            
            # 验证适合Boss击杀
            assert build.is_suitable_for_goal(PoE2BuildGoal.BOSS_KILLING)
            
            # 验证PoB2验证
            assert build.pob2_code is not None
        
        assert result.pob2_validated == True
    
    @pytest.mark.asyncio
    async def test_rag_enhancement_integration(self, integrated_orchestrator):
        """测试RAG增强集成"""
        request = UserRequest(
            character_class=PoE2CharacterClass.RANGER,
            preferred_skills=["Ice Shot"],
            playstyle="balanced",
            include_meta_builds=True
        )
        
        result = await integrated_orchestrator.generate_build_recommendations(request)
        
        # 验证RAG增强特性
        assert result.rag_confidence > 0.5  # 应该有合理的置信度
        assert len(result.builds) > 0
        
        # 检查构筑描述中是否包含RAG信息
        for build in result.builds:
            if build.notes:
                # 应该包含RAG来源信息
                assert any(keyword in build.notes.lower() 
                          for keyword in ['rag', 'similar', 'enhanced', 'adapted'])
    
    @pytest.mark.asyncio
    async def test_component_failure_resilience(self, integrated_orchestrator):
        """测试组件失败时的弹性处理"""
        # 模拟PoB2本地客户端不可用
        integrated_orchestrator._pob2_local.available = False
        integrated_orchestrator._component_health[SystemComponent.POB2_LOCAL].status = ComponentStatus.ERROR
        
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            validate_with_pob2=True,  # 仍然请求PoB2验证
            generate_pob2_code=True
        )
        
        result = await integrated_orchestrator.generate_build_recommendations(request)
        
        # 系统应该降级到Web版本
        assert len(result.builds) > 0
        assert SystemComponent.POB2_WEB in result.used_components
        assert SystemComponent.POB2_LOCAL not in result.used_components
        
        # 构筑仍应有PoB2代码
        for build in result.builds:
            if build.pob2_code:
                assert 'web_pob2_code' in build.pob2_code
    
    @pytest.mark.asyncio
    async def test_multiple_class_recommendation_integration(self, integrated_orchestrator):
        """测试多职业推荐集成"""
        # 不指定特定职业
        open_request = UserRequest(
            build_goal=PoE2BuildGoal.CLEAR_SPEED,
            max_budget=20.0,
            min_dps=300000
        )
        
        result = await integrated_orchestrator.generate_build_recommendations(open_request)
        
        # 应该包含多个职业的推荐
        classes_found = set()
        for build in result.builds:
            classes_found.add(build.character_class)
        
        assert len(classes_found) >= 2  # 至少包含2个不同职业
        
        # 所有构筑都应该适合清图速度目标
        for build in result.builds:
            assert build.is_suitable_for_goal(PoE2BuildGoal.CLEAR_SPEED)


@pytest.mark.integration
class TestDataFlowIntegration:
    """数据流集成测试"""
    
    @pytest.fixture
    async def data_flow_orchestrator(self):
        """创建数据流测试协调器"""
        orchestrator = IntegratedTestOrchestrator()
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_rag_to_market_data_flow(self, data_flow_orchestrator):
        """测试RAG到市场数据的数据流"""
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            max_budget=15.0
        )
        
        # 手动执行各阶段以观察数据流
        # 阶段1: RAG推荐生成
        rag_builds, rag_confidence = await data_flow_orchestrator._generate_rag_recommendations(request)
        
        assert len(rag_builds) > 0
        assert rag_confidence > 0
        
        # 阶段2: 市场数据增强
        market_enhanced = await data_flow_orchestrator._enhance_with_market_data(rag_builds, request)
        
        # 验证数据流转换
        assert len(market_enhanced) <= len(rag_builds)  # 可能过滤掉超预算构筑
        
        for build in market_enhanced:
            assert build.estimated_cost <= request.max_budget
    
    @pytest.mark.asyncio
    async def test_market_to_pob2_data_flow(self, data_flow_orchestrator):
        """测试市场数据到PoB2的数据流"""
        request = UserRequest(
            character_class=PoE2CharacterClass.RANGER,
            validate_with_pob2=True,
            generate_pob2_code=True
        )
        
        # 生成初始构筑
        rag_builds, _ = await data_flow_orchestrator._generate_rag_recommendations(request)
        market_enhanced = await data_flow_orchestrator._enhance_with_market_data(rag_builds, request)
        
        # PoB2验证阶段
        pob2_client = data_flow_orchestrator._get_available_pob2_client()
        validated_builds = await data_flow_orchestrator._validate_with_pob2(
            market_enhanced, pob2_client, request
        )
        
        # 验证PoB2数据增强
        for build in validated_builds:
            assert build.pob2_code is not None  # 应该有PoB2代码
            
            # 统计数据应该被PoB2重新计算
            if build.stats:
                # PoB2计算结果应该与原始略有不同（模拟更精确的计算）
                pass  # 在实际实现中会验证计算结果的差异
    
    @pytest.mark.asyncio
    async def test_complete_data_transformation_pipeline(self, data_flow_orchestrator):
        """测试完整的数据转换管道"""
        request = UserRequest(
            character_class=PoE2CharacterClass.MONK,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=30.0,
            validate_with_pob2=True
        )
        
        # 追踪整个数据转换过程
        transformations = []
        
        # 阶段1: 原始RAG数据
        rag_builds, rag_confidence = await data_flow_orchestrator._generate_rag_recommendations(request)
        transformations.append({
            'stage': 'rag_generation',
            'build_count': len(rag_builds),
            'sample_dps': rag_builds[0].stats.total_dps if rag_builds and rag_builds[0].stats else None
        })
        
        # 阶段2: 市场数据增强
        market_enhanced = await data_flow_orchestrator._enhance_with_market_data(rag_builds, request)
        transformations.append({
            'stage': 'market_enhancement',
            'build_count': len(market_enhanced),
            'filtered_count': len(rag_builds) - len(market_enhanced)
        })
        
        # 阶段3: PoB2验证
        pob2_client = data_flow_orchestrator._get_available_pob2_client()
        validated_builds = await data_flow_orchestrator._validate_with_pob2(
            market_enhanced, pob2_client, request
        )
        transformations.append({
            'stage': 'pob2_validation',
            'build_count': len(validated_builds),
            'validated_count': len([b for b in validated_builds if b.pob2_code])
        })
        
        # 阶段4: 最终排序
        final_builds = await data_flow_orchestrator._finalize_recommendations(validated_builds, request)
        transformations.append({
            'stage': 'final_ranking',
            'build_count': len(final_builds),
            'top_dps': final_builds[0].stats.total_dps if final_builds and final_builds[0].stats else None
        })
        
        # 验证数据转换链的完整性
        assert len(transformations) == 4
        assert all(t['build_count'] > 0 for t in transformations)
        
        # 验证数据质量在每个阶段都有所提升
        final_stage = transformations[-1]
        assert final_stage['build_count'] > 0
        
        return transformations


@pytest.mark.integration
@pytest.mark.slow
class TestScalabilityIntegration:
    """可扩展性集成测试"""
    
    @pytest.fixture
    async def scalability_orchestrator(self):
        """创建可扩展性测试协调器"""
        config = {
            'max_recommendations': 50,  # 增加限制以测试规模
            'timeout_seconds': 60,
            'cache': {'ttl_seconds': 3600}
        }
        orchestrator = IntegratedTestOrchestrator(config)
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_high_volume_request_handling(self, scalability_orchestrator):
        """测试高并发请求处理"""
        # 创建多个不同的用户请求
        requests = [
            UserRequest(character_class=cls, max_budget=budget, build_goal=goal)
            for cls in list(PoE2CharacterClass)[:3]
            for budget in [10.0, 25.0, 50.0]
            for goal in list(PoE2BuildGoal)[:2]
        ]
        
        # 并发处理所有请求
        start_time = time.time()
        tasks = [
            scalability_orchestrator.generate_build_recommendations(req)
            for req in requests[:10]  # 限制并发数量以避免超时
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 验证结果
        successful_results = [r for r in results if isinstance(r, RecommendationResult)]
        assert len(successful_results) >= len(requests) * 0.8  # 至少80%成功
        
        # 验证性能
        assert total_time < 30.0  # 30秒内完成
        
        # 验证系统仍然健康
        health = await scalability_orchestrator.health_check()
        assert health['overall_status'] in ['healthy', 'degraded']  # 允许降级但不应该不健康
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_under_load(self, scalability_orchestrator):
        """测试负载下的内存效率"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 执行大量操作
        for i in range(20):
            request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                max_budget=20.0,
                validate_with_pob2=True
            )
            
            result = await scalability_orchestrator.generate_build_recommendations(request)
            assert len(result.builds) > 0
            
            # 每5次操作检查一次内存
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                assert memory_increase < 200  # 内存增长不应超过200MB
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        assert total_increase < 300  # 总内存增长不超过300MB
    
    @pytest.mark.asyncio
    async def test_system_recovery_after_stress(self, scalability_orchestrator):
        """测试压力后的系统恢复"""
        # 执行压力测试
        stress_requests = [
            UserRequest(
                character_class=PoE2CharacterClass.WARRIOR,
                build_goal=PoE2BuildGoal.BOSS_KILLING,
                validate_with_pob2=True
            ) for _ in range(15)
        ]
        
        # 快速连续执行
        stress_tasks = [
            scalability_orchestrator.generate_build_recommendations(req)
            for req in stress_requests
        ]
        
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        
        # 等待系统恢复
        await asyncio.sleep(2)
        
        # 执行正常请求以验证系统恢复
        recovery_request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            max_budget=15.0
        )
        
        recovery_result = await scalability_orchestrator.generate_build_recommendations(recovery_request)
        
        # 验证系统已恢复正常
        assert isinstance(recovery_result, RecommendationResult)
        assert len(recovery_result.builds) > 0
        assert recovery_result.generation_time_ms > 0
        
        # 验证系统健康状态
        health = await scalability_orchestrator.health_check()
        assert health['overall_status'] != 'unhealthy'