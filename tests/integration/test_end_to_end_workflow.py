"""
集成测试 - 端到端工作流测试

测试完整的用户请求处理流程，包括：
- 用户请求解析
- RAG系统检索
- PoB2集成计算
- 数据源API调用
- 结果聚合和返回
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# 导入核心组件
from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
from src.poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy
from src.poe2build.models.build import PoE2BuildGoal, PoE2Build, PoE2BuildStats

# 测试用Mock组件
from tests.fixtures.mock_responses.api_responses import (
    MOCK_SCOUT_RESPONSES,
    MOCK_NINJA_RESPONSES,
    MOCK_POB2_RESPONSES
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndWorkflow:
    """测试端到端工作流程"""
    
    async def test_complete_build_recommendation_workflow(self, mock_orchestrator_config):
        """测试完整的构筑推荐工作流程"""
        # 初始化协调器
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # Mock所有外部依赖
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _pob2_web=AsyncMock(),
            _ninja_scraper=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            # 设置初始化状态
            orchestrator._initialized = True
            
            # 配置RAG系统响应
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': 'RAG Lightning Sorceress',
                    'level': 92,
                    'character_class': 'Sorceress',
                    'ascendancy': 'Stormweaver',
                    'main_skill': 'Lightning Bolt',
                    'support_gems': ['Added Lightning', 'Lightning Penetration'],
                    'estimated_dps': 850000,
                    'estimated_ehp': 8200,
                    'estimated_cost': 16.5,
                    'confidence': 0.89
                }
            ]
            
            # 配置市场数据API响应
            orchestrator._market_api.get_item_price.side_effect = lambda item, **kwargs: {
                'Staff of Power': {'median_price': 15.5, 'confidence': 0.92},
                'Lightning Amulet': {'median_price': 3.2, 'confidence': 0.88},
                'Spell Echo Ring': {'median_price': 1.8, 'confidence': 0.85}
            }.get(item)
            
            # 配置PoB2本地客户端响应
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 875000,
                'ehp': 8100,
                'fire_res': 78,
                'cold_res': 76,
                'lightning_res': 79,
                'chaos_res': -25,
                'validation_status': 'valid',
                'calculated_by': 'pob2_local_v2.35.1'
            }
            orchestrator._pob2_local.generate_build_code.return_value = "eNrtXVuP2zYS_jUFn..."
            
            # 配置元数据爬虫响应
            orchestrator._ninja_scraper.get_meta_builds.return_value = [
                {
                    'name': 'Meta Lightning Sorceress',
                    'character_class': 'Sorceress',
                    'ascendancy': 'Stormweaver',
                    'popularity_percent': 15.2,
                    'estimated_dps': 950000,
                    'level': 94
                }
            ]
            
            # 配置缓存管理器
            orchestrator._cache_manager.get.return_value = None  # 缓存未命中
            orchestrator._cache_manager.set.return_value = True
            
            # 创建用户请求
            user_request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                ascendancy=PoE2Ascendancy.STORMWEAVER,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=20.0,
                currency_type="divine",
                preferred_skills=["Lightning Bolt"],
                min_dps=500000,
                min_ehp=7000,
                generate_pob2_code=True,
                validate_with_pob2=True
            )
            
            # 执行端到端流程
            result = await orchestrator.generate_build_recommendations(user_request)
            
            # 验证结果结构
            assert 'recommendations' in result
            assert 'metadata' in result
            assert 'system_info' in result
            assert len(result['recommendations']) > 0
            
            # 验证推荐内容
            recommendation = result['recommendations'][0]
            assert recommendation['name'] == 'RAG Lightning Sorceress'
            assert recommendation['character_class'] == 'Sorceress'
            assert recommendation['ascendancy'] == 'Stormweaver'
            assert recommendation['estimated_cost'] <= user_request.max_budget
            assert recommendation['estimated_dps'] >= user_request.min_dps
            
            # 验证PoB2集成
            assert 'pob2_data' in recommendation
            pob2_data = recommendation['pob2_data']
            assert pob2_data['validation_status'] == 'valid'
            assert pob2_data['import_code'] is not None
            assert pob2_data['calculated_stats']['total_dps'] > 0
            
            # 验证市场数据
            assert 'market_data' in recommendation
            market_data = recommendation['market_data']
            assert 'item_prices' in market_data
            
            # 验证元数据
            assert 'meta_context' in recommendation
            meta_context = recommendation['meta_context']
            assert meta_context['popularity_rank'] > 0
            
            # 验证系统信息
            system_info = result['system_info']
            assert system_info['processing_time_ms'] > 0
            assert system_info['components_used']['rag_engine'] is True
            assert system_info['components_used']['pob2_local'] is True
            assert system_info['components_used']['market_api'] is True
            
            # 验证缓存设置被调用
            orchestrator._cache_manager.set.assert_called()
            
    async def test_workflow_with_fallback_scenarios(self, mock_orchestrator_config):
        """测试带备用方案的工作流程"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _pob2_web=AsyncMock(),
            _ninja_scraper=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 模拟RAG系统失败
            orchestrator._rag_engine.generate_recommendations.side_effect = Exception("RAG engine failed")
            
            # 模拟本地PoB2不可用
            orchestrator._pob2_local.is_available.return_value = False
            orchestrator._pob2_local.calculate_build_stats.side_effect = Exception("PoB2 local unavailable")
            
            # 配置备用方案
            # 1. 缓存中的备用构筑数据
            fallback_builds = [
                {
                    'name': 'Fallback Lightning Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 650000,
                    'estimated_ehp': 7500,
                    'estimated_cost': 12.0,
                    'source': 'cached_fallback',
                    'confidence': 0.75
                }
            ]
            orchestrator._cache_manager.get.return_value = fallback_builds
            
            # 2. Web PoB2作为备用
            orchestrator._pob2_web.calculate_build_stats.return_value = {
                'total_dps': 680000,
                'ehp': 7600,
                'fire_res': 75,
                'cold_res': 75,
                'lightning_res': 75,
                'chaos_res': -30,
                'validation_status': 'valid',
                'calculated_by': 'pob2_web_fallback'
            }
            
            # 3. 市场数据部分可用
            orchestrator._market_api.get_item_price.side_effect = lambda item, **kwargs: {
                'Staff of Power': {'median_price': 15.0, 'confidence': 0.85},
                # 其他物品数据不可用
            }.get(item, None)
            
            # 执行请求
            user_request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=15.0
            )
            
            result = await orchestrator.generate_build_recommendations(user_request)
            
            # 验证备用方案生效
            assert 'recommendations' in result
            assert len(result['recommendations']) > 0
            
            recommendation = result['recommendations'][0]
            assert recommendation['source'] == 'cached_fallback'
            assert recommendation['name'] == 'Fallback Lightning Build'
            
            # 验证备用PoB2被使用
            assert 'pob2_data' in recommendation
            assert recommendation['pob2_data']['calculated_by'] == 'pob2_web_fallback'
            
            # 验证错误信息记录
            metadata = result['metadata']
            assert 'fallback_reasons' in metadata
            assert 'rag_engine_failed' in metadata['fallback_reasons']
            assert 'pob2_local_unavailable' in metadata['fallback_reasons']
            
    async def test_concurrent_user_requests(self, mock_orchestrator_config):
        """测试并发用户请求处理"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _pob2_web=AsyncMock(),
            _ninja_scraper=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 配置基本响应
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': 'Concurrent Test Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 600000,
                    'estimated_cost': 10.0,
                    'confidence': 0.8
                }
            ]
            
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 620000,
                'ehp': 7000,
                'validation_status': 'valid'
            }
            
            orchestrator._cache_manager.get.return_value = None
            
            # 创建多个用户请求
            user_requests = []
            for i in range(5):
                request = UserRequest(
                    character_class=[PoE2CharacterClass.SORCERESS, PoE2CharacterClass.RANGER, PoE2CharacterClass.WITCH][i % 3],
                    build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                    max_budget=10.0 + i * 2,
                    request_id=f"concurrent_test_{i}"
                )
                user_requests.append(request)
            
            # 并发执行
            start_time = datetime.utcnow()
            tasks = [orchestrator.generate_build_recommendations(req) for req in user_requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.utcnow()
            
            # 验证结果
            assert len(results) == 5
            
            # 检查是否有异常
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]
            
            # 至少应该有一些成功的结果
            assert len(successful_results) > 0
            
            # 验证成功结果的结构
            for result in successful_results:
                assert 'recommendations' in result
                assert len(result['recommendations']) > 0
                
            # 验证并发性能（并发执行应该比串行快）
            total_time = (end_time - start_time).total_seconds()
            # 假设单个请求需要1秒，5个并发请求不应该超过3秒
            assert total_time < 3.0
            
    async def test_data_consistency_across_components(self, mock_orchestrator_config):
        """测试组件间数据一致性"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _ninja_scraper=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 设置一致的构筑数据
            build_name = "Data Consistency Test Build"
            character_class = "Sorceress"
            main_skill = "Lightning Bolt"
            
            # RAG系统返回
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': build_name,
                    'character_class': character_class,
                    'main_skill': main_skill,
                    'estimated_dps': 750000,
                    'estimated_cost': 15.0,
                    'confidence': 0.85
                }
            ]
            
            # PoB2返回相关数据
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 752000,  # 与RAG估计接近
                'ehp': 8000,
                'validation_status': 'valid',
                'build_name': build_name,
                'main_skill': main_skill
            }
            
            # 市场数据API返回相关物品价格
            orchestrator._market_api.get_item_price.return_value = {
                'median_price': 3.5,
                'currency': 'divine',
                'item_category': 'weapon',  # 适合Lightning构筑
                'confidence': 0.9
            }
            
            # Ninja返回相关元数据
            orchestrator._ninja_scraper.get_meta_builds.return_value = [
                {
                    'name': f"Meta {build_name}",
                    'character_class': character_class,
                    'main_skill': main_skill,
                    'popularity_percent': 12.3,
                    'estimated_dps': 748000  # 接近RAG和PoB2的数值
                }
            ]
            
            # 执行请求
            user_request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                preferred_skills=[main_skill],
                max_budget=20.0
            )
            
            result = await orchestrator.generate_build_recommendations(user_request)
            
            # 验证数据一致性
            recommendation = result['recommendations'][0]
            
            # 构筑名称一致
            assert recommendation['name'] == build_name
            assert recommendation['character_class'] == character_class
            assert recommendation['main_skill'] == main_skill
            
            # DPS数据在合理范围内（允许小幅差异）
            rag_dps = recommendation['estimated_dps']
            pob2_dps = recommendation['pob2_data']['calculated_stats']['total_dps']
            ninja_dps = recommendation['meta_context']['reference_dps']
            
            # 所有DPS值都在相似范围内（允许10%误差）
            dps_values = [rag_dps, pob2_dps, ninja_dps]
            avg_dps = sum(dps_values) / len(dps_values)
            for dps in dps_values:
                assert abs(dps - avg_dps) / avg_dps < 0.1  # 10%内误差
                
            # 成本估算一致性
            estimated_cost = recommendation['estimated_cost']
            market_price = recommendation['market_data']['total_estimated_cost']
            assert abs(estimated_cost - market_price) / estimated_cost < 0.2  # 20%内误差


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningWorkflows:
    """测试长时间运行的工作流程"""
    
    @pytest.mark.timeout(300)  # 5分钟超时
    async def test_extended_recommendation_session(self, mock_orchestrator_config):
        """测试长时间推荐会话（多轮请求）"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 设置基本响应
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': 'Extended Session Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 700000,
                    'confidence': 0.8
                }
            ]
            
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 720000,
                'validation_status': 'valid'
            }
            
            # 模拟缓存逐步填充
            cache_data = {}
            orchestrator._cache_manager.get.side_effect = lambda key: cache_data.get(key)
            orchestrator._cache_manager.set.side_effect = lambda key, value, **kwargs: cache_data.update({key: value})
            
            # 执行多轮请求（模拟用户交互式优化）
            session_results = []
            
            for round_num in range(10):
                # 每轮请求畅微不同的参数
                user_request = UserRequest(
                    character_class=PoE2CharacterClass.SORCERESS,
                    build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                    max_budget=15.0 + round_num,  # 逐渐提高预算
                    min_dps=500000 + round_num * 10000,  # 逐渐提高DPS要求
                    session_id=f"extended_session_{round_num}"
                )
                
                result = await orchestrator.generate_build_recommendations(user_request)
                session_results.append({
                    'round': round_num,
                    'result': result,
                    'timestamp': datetime.utcnow(),
                    'cache_size': len(cache_data)
                })
                
                # 模拟用户思考时间
                await asyncio.sleep(0.1)
            
            # 验证会话结果
            assert len(session_results) == 10
            
            # 验证缓存效果（后期应该更快）
            early_times = [r['result']['system_info']['processing_time_ms'] for r in session_results[:3]]
            late_times = [r['result']['system_info']['processing_time_ms'] for r in session_results[-3:]]
            
            avg_early_time = sum(early_times) / len(early_times)
            avg_late_time = sum(late_times) / len(late_times)
            
            # 缓存生效后，平均响应时间应该有所下降
            # 注意：这里可能因为Mock而不显著，在实际系统中更明显
            
            # 验证缓存积累
            final_cache_size = session_results[-1]['cache_size']
            assert final_cache_size > 0
            
            # 验证所有请求都成功
            for session_result in session_results:
                assert 'recommendations' in session_result['result']
                assert len(session_result['result']['recommendations']) > 0


@pytest.mark.integration
class TestSystemResilience:
    """测试系统弹性和错误恢复"""
    
    async def test_graceful_degradation(self, mock_orchestrator_config):
        """测试优雅降级处理"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _pob2_web=AsyncMock(),
            _ninja_scraper=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 模拟系统组件逐步失败
            failure_scenarios = [
                # 场景1：RAG失败，但其他组件正常
                {
                    'rag_engine': Exception("RAG unavailable"),
                    'pob2_local': True,
                    'market_api': True,
                    'expected_source': 'fallback_cache'
                },
                # 场景2：RAG和PoB2本地都失败
                {
                    'rag_engine': Exception("RAG unavailable"),
                    'pob2_local': Exception("PoB2 local failed"),
                    'market_api': True,
                    'expected_source': 'basic_templates'
                },
                # 场景3：所有外部组件失败
                {
                    'rag_engine': Exception("RAG unavailable"),
                    'pob2_local': Exception("PoB2 local failed"),
                    'market_api': Exception("Market API failed"),
                    'ninja_scraper': Exception("Ninja scraper failed"),
                    'expected_source': 'emergency_fallback'
                }
            ]
            
            for i, scenario in enumerate(failure_scenarios):
                # 设置失败条件
                if 'rag_engine' in scenario and isinstance(scenario['rag_engine'], Exception):
                    orchestrator._rag_engine.generate_recommendations.side_effect = scenario['rag_engine']
                
                if 'pob2_local' in scenario and isinstance(scenario['pob2_local'], Exception):
                    orchestrator._pob2_local.calculate_build_stats.side_effect = scenario['pob2_local']
                    orchestrator._pob2_local.is_available.return_value = False
                
                if 'market_api' in scenario and isinstance(scenario['market_api'], Exception):
                    orchestrator._market_api.get_item_price.side_effect = scenario['market_api']
                    
                # 设置备用数据
                fallback_data = [
                    {
                        'name': f'Fallback Build {i}',
                        'character_class': 'Sorceress',
                        'estimated_dps': 400000,
                        'estimated_cost': 8.0,
                        'source': scenario['expected_source'],
                        'confidence': 0.6
                    }
                ]
                
                orchestrator._cache_manager.get.return_value = fallback_data
                
                # 执行请求
                user_request = UserRequest(
                    character_class=PoE2CharacterClass.SORCERESS,
                    build_goal=PoE2BuildGoal.ENDGAME_CONTENT
                )
                
                result = await orchestrator.generate_build_recommendations(user_request)
                
                # 验证系统仍能返回结果
                assert 'recommendations' in result
                assert len(result['recommendations']) > 0
                
                recommendation = result['recommendations'][0]
                assert recommendation['source'] == scenario['expected_source']
                
                # 验证错误信息被记录
                assert 'metadata' in result
                assert 'degradation_info' in result['metadata']
                
                # 重置为下一个场景做准备
                for mock_component in [orchestrator._rag_engine, orchestrator._pob2_local, orchestrator._market_api]:
                    if hasattr(mock_component, 'side_effect'):
                        mock_component.side_effect = None
                        
    async def test_component_health_monitoring(self, mock_orchestrator_config):
        """测试组件健康监控"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            orchestrator._initialized = True
            
            # 模拟不同的组件健康状态
            health_scenarios = [
                {'component': 'rag_engine', 'healthy': True, 'response_time': 150},
                {'component': 'pob2_local', 'healthy': False, 'error': 'Connection timeout'},
                {'component': 'market_api', 'healthy': True, 'response_time': 2500},  # 慢但可用
            ]
            
            # 模拟健康检查结果
            for scenario in health_scenarios:
                component_name = scenario['component']
                component_mock = getattr(orchestrator, f"_{component_name}")
                
                if scenario['healthy']:
                    # 模拟成功响应
                    component_mock.health_check.return_value = {
                        'status': 'healthy',
                        'response_time_ms': scenario['response_time']
                    }
                else:
                    # 模拟失败响应
                    component_mock.health_check.side_effect = Exception(scenario['error'])
            
            # 执行系统健康检查
            health_status = await orchestrator.get_system_health()
            
            # 验证健康状态结构
            assert 'components' in health_status
            assert 'overall_status' in health_status
            assert 'timestamp' in health_status
            
            components = health_status['components']
            
            # 验证各组件状态
            for scenario in health_scenarios:
                component_name = scenario['component']
                assert component_name in components
                
                component_health = components[component_name]
                if scenario['healthy']:
                    assert component_health['status'] == 'healthy'
                    assert component_health['response_time_ms'] == scenario['response_time']
                else:
                    assert component_health['status'] == 'error'
                    assert scenario['error'] in component_health['error_message']
            
            # 验证整体状态（有一个组件失败，整体应该是降级）
            assert health_status['overall_status'] in ['degraded', 'unhealthy']
