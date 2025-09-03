"""
性能测试 - 系统基准测试

测试系统各个组件的性能指标：
- 响应时间基准测试
- 吞吐量测试
- 内存使用测试
- 并发性能测试
- 缓存效率测试
"""

import pytest
import time
import asyncio
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator, UserRequest
from src.poe2build.models.characters import PoE2CharacterClass
from src.poe2build.models.build import PoE2BuildGoal


@pytest.mark.performance
class TestResponseTimeBaselines:
    """响应时间基准测试"""
    
    @pytest.fixture
    def performance_orchestrator(self, mock_orchestrator_config):
        """性能测试用的协调器"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        # 设置高性能 Mock组件
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _market_api=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            # 配置快速响应
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': 'Perf Test Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 600000,
                    'confidence': 0.8
                }
            ]
            
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 620000,
                'validation_status': 'valid'
            }
            
            orchestrator._market_api.get_item_price.return_value = {
                'median_price': 5.0,
                'confidence': 0.9
            }
            
            orchestrator._cache_manager.get.return_value = None  # 无缓存
            orchestrator._cache_manager.set.return_value = True
            
            orchestrator._initialized = True
            yield orchestrator
    
    @pytest.mark.asyncio
    async def test_single_request_response_time(self, performance_orchestrator):
        """测试单个请求的响应时间基准"""
        user_request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=15.0
        )
        
        # 执行多次测试取平均值
        response_times = []
        
        for _ in range(10):
            start_time = time.perf_counter()
            result = await performance_orchestrator.generate_build_recommendations(user_request)
            end_time = time.perf_counter()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)
            
            # 验证请求成功
            assert 'recommendations' in result
            assert len(result['recommendations']) > 0
        
        # 计算统计数据
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # 性能基准验证
        assert avg_response_time < 1000, f"Average response time {avg_response_time:.2f}ms exceeds 1000ms baseline"
        assert p95_response_time < 2000, f"P95 response time {p95_response_time:.2f}ms exceeds 2000ms baseline"
        assert p99_response_time < 3000, f"P99 response time {p99_response_time:.2f}ms exceeds 3000ms baseline"
        
        print(f"\nResponse Time Benchmarks:")
        print(f"Average: {avg_response_time:.2f}ms")
        print(f"P95: {p95_response_time:.2f}ms")
        print(f"P99: {p99_response_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, performance_orchestrator):
        """测试并发请求性能"""
        # 创建多个并发请求
        concurrent_requests = []
        for i in range(20):  # 20个并发请求
            request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=10.0 + i,
                request_id=f"perf_test_{i}"
            )
            concurrent_requests.append(request)
        
        # 测试并发性能
        start_time = time.perf_counter()
        
        tasks = [performance_orchestrator.generate_build_recommendations(req) for req in concurrent_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # 毫秒
        
        # 验证结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        success_rate = len(successful_results) / len(results)
        avg_time_per_request = total_time / len(results)
        throughput = len(results) / (total_time / 1000)  # 每秒处理请求数
        
        # 性能基准验证
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% baseline"
        assert avg_time_per_request < 1500, f"Average time per request {avg_time_per_request:.2f}ms exceeds 1500ms baseline"
        assert throughput >= 5.0, f"Throughput {throughput:.2f} req/s below 5.0 req/s baseline"
        
        print(f"\nConcurrent Performance Benchmarks:")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Average time per request: {avg_time_per_request:.2f}ms")
        print(f"Throughput: {throughput:.2f} req/s")
        print(f"Failed requests: {len(failed_results)}")


@pytest.mark.performance
class TestMemoryUsageBenchmarks:
    """内存使用基准测试"""
    
    def get_memory_usage(self):
        """获取当前进程内存使用量（MB）"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # 转换为MB
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_orchestrator_config):
        """测试负载下的内存使用情况"""
        initial_memory = self.get_memory_usage()
        
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            # 设置基本响应
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {
                    'name': f'Memory Test Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 500000,
                    'confidence': 0.8
                }
            ]
            
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 520000,
                'validation_status': 'valid'
            }
            
            # 模拟缓存积累
            cache_data = {}
            orchestrator._cache_manager.get.side_effect = lambda key: cache_data.get(key)
            orchestrator._cache_manager.set.side_effect = lambda key, value, **kwargs: cache_data.update({key: value})
            
            orchestrator._initialized = True
            
            # 执行大量请求模拟高负载
            memory_readings = []
            
            for batch in range(5):  # 5个批次
                # 每批次执行10个请求
                batch_tasks = []
                for i in range(10):
                    request = UserRequest(
                        character_class=PoE2CharacterClass.SORCERESS,
                        build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                        max_budget=10.0 + batch * 10 + i,
                        request_id=f"memory_test_{batch}_{i}"
                    )
                    batch_tasks.append(orchestrator.generate_build_recommendations(request))
                
                # 执行批次请求
                await asyncio.gather(*batch_tasks)
                
                # 记录内存使用
                current_memory = self.get_memory_usage()
                memory_readings.append({
                    'batch': batch,
                    'memory_mb': current_memory,
                    'memory_increase': current_memory - initial_memory,
                    'cache_size': len(cache_data)
                })
                
                print(f"Batch {batch}: Memory {current_memory:.2f}MB (+{current_memory - initial_memory:.2f}MB)")
        
        # 分析内存使用趋势
        final_memory = memory_readings[-1]['memory_mb']
        peak_memory = max(reading['memory_mb'] for reading in memory_readings)
        memory_growth = final_memory - initial_memory
        
        # 内存基准验证
        assert memory_growth < 500, f"Memory growth {memory_growth:.2f}MB exceeds 500MB baseline"
        assert peak_memory < initial_memory + 600, f"Peak memory {peak_memory:.2f}MB exceeds baseline"
        
        # 检查内存泄漏（内存使用不应该持续增长）
        if len(memory_readings) >= 3:
            last_three = memory_readings[-3:]
            memory_trend = [r['memory_mb'] for r in last_three]
            
            # 简单的内存泄漏检测（最后3个读数不应该显著上升）
            if len(memory_trend) == 3:
                trend_growth = memory_trend[2] - memory_trend[0]
                assert trend_growth < 50, f"Potential memory leak detected: {trend_growth:.2f}MB growth in last 3 batches"
        
        print(f"\nMemory Usage Benchmarks:")
        print(f"Initial: {initial_memory:.2f}MB")
        print(f"Final: {final_memory:.2f}MB")
        print(f"Peak: {peak_memory:.2f}MB")
        print(f"Total growth: {memory_growth:.2f}MB")
    
    def test_large_dataset_memory_efficiency(self):
        """测试大数据集处理的内存效率"""
        initial_memory = self.get_memory_usage()
        
        # 模拟处理大量构筑数据
        large_build_dataset = []
        for i in range(1000):  # 1000个构筑
            build_data = {
                'id': f'build_{i}',
                'name': f'Test Build {i}',
                'character_class': ['Sorceress', 'Ranger', 'Witch'][i % 3],
                'level': 85 + (i % 15),
                'estimated_dps': 500000 + i * 1000,
                'estimated_cost': 10.0 + (i % 20),
                'skills': [f'Skill_{j}' for j in range(i % 10 + 1)],
                'description': f'A test build number {i} with various properties and configurations' * 3
            }
            large_build_dataset.append(build_data)
        
        # 记录数据加载后的内存
        data_loaded_memory = self.get_memory_usage()
        
        # 模拟数据处理操作（筛选、排序、聚合等）
        filtered_data = [build for build in large_build_dataset if build['estimated_cost'] <= 15.0]
        sorted_data = sorted(filtered_data, key=lambda x: x['estimated_dps'], reverse=True)
        top_100 = sorted_data[:100]
        
        # 模拟复杂计算
        stats = {
            'total_builds': len(large_build_dataset),
            'filtered_builds': len(filtered_data),
            'avg_dps': sum(build['estimated_dps'] for build in top_100) / len(top_100),
            'avg_cost': sum(build['estimated_cost'] for build in top_100) / len(top_100)
        }
        
        # 记录处理完成后的内存
        processing_done_memory = self.get_memory_usage()
        
        # 清理数据并强制垃圾回收
        del large_build_dataset, filtered_data, sorted_data, top_100
        import gc
        gc.collect()
        
        final_memory = self.get_memory_usage()
        
        # 内存效率分析
        data_loading_overhead = data_loaded_memory - initial_memory
        processing_overhead = processing_done_memory - data_loaded_memory
        memory_cleanup_efficiency = processing_done_memory - final_memory
        
        # 效率基准验证
        assert data_loading_overhead < 200, f"Data loading overhead {data_loading_overhead:.2f}MB exceeds 200MB baseline"
        assert processing_overhead < 100, f"Processing overhead {processing_overhead:.2f}MB exceeds 100MB baseline"
        assert memory_cleanup_efficiency > data_loading_overhead * 0.7, f"Memory cleanup efficiency {memory_cleanup_efficiency:.2f}MB too low"
        
        print(f"\nLarge Dataset Memory Efficiency:")
        print(f"Data loading overhead: {data_loading_overhead:.2f}MB")
        print(f"Processing overhead: {processing_overhead:.2f}MB")
        print(f"Memory cleanup: {memory_cleanup_efficiency:.2f}MB")
        print(f"Final memory delta: {final_memory - initial_memory:.2f}MB")


@pytest.mark.performance
class TestCachePerformanceBenchmarks:
    """缓存性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, mock_orchestrator_config):
        """测试缓存命中的性能表现"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            # 设置缓存数据
            cached_result = [
                {
                    'name': 'Cached Test Build',
                    'character_class': 'Sorceress',
                    'estimated_dps': 700000,
                    'confidence': 0.9,
                    'source': 'cache'
                }
            ]
            
            # 模拟缓存行为
            cache_data = {}
            call_count = {'cache_hits': 0, 'cache_misses': 0, 'rag_calls': 0}
            
            def mock_cache_get(key):
                if key in cache_data:
                    call_count['cache_hits'] += 1
                    return cache_data[key]
                else:
                    call_count['cache_misses'] += 1
                    return None
            
            def mock_cache_set(key, value, **kwargs):
                cache_data[key] = value
                return True
                
            def mock_rag_generate(*args, **kwargs):
                call_count['rag_calls'] += 1
                return cached_result
            
            orchestrator._cache_manager.get.side_effect = mock_cache_get
            orchestrator._cache_manager.set.side_effect = mock_cache_set
            orchestrator._rag_engine.generate_recommendations.side_effect = mock_rag_generate
            
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 720000,
                'validation_status': 'valid'
            }
            
            orchestrator._initialized = True
            
            # 创建用户请求
            base_request = UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=15.0
            )
            
            # 阶段1：首次请求（缓存未命中）
            start_time = time.perf_counter()
            first_result = await orchestrator.generate_build_recommendations(base_request)
            first_request_time = (time.perf_counter() - start_time) * 1000
            
            # 阶段2：重复请求（缓存命中）
            cache_hit_times = []
            for _ in range(10):
                start_time = time.perf_counter()
                cached_result = await orchestrator.generate_build_recommendations(base_request)
                cache_hit_time = (time.perf_counter() - start_time) * 1000
                cache_hit_times.append(cache_hit_time)
            
            # 计算缓存性能指标
            avg_cache_hit_time = statistics.mean(cache_hit_times)
            cache_speedup_ratio = first_request_time / avg_cache_hit_time
            cache_hit_rate = call_count['cache_hits'] / (call_count['cache_hits'] + call_count['cache_misses'])
            
            # 缓存性能基准验证
            assert avg_cache_hit_time < 100, f"Cache hit time {avg_cache_hit_time:.2f}ms exceeds 100ms baseline"
            assert cache_speedup_ratio >= 5.0, f"Cache speedup ratio {cache_speedup_ratio:.2f} below 5.0x baseline"
            assert cache_hit_rate >= 0.8, f"Cache hit rate {cache_hit_rate:.2%} below 80% baseline"
            
            # 验证RAG调用次数（缓存命中后应该减少）
            assert call_count['rag_calls'] <= 2, f"Too many RAG calls: {call_count['rag_calls']}"
            
            print(f"\nCache Performance Benchmarks:")
            print(f"First request (cache miss): {first_request_time:.2f}ms")
            print(f"Average cache hit: {avg_cache_hit_time:.2f}ms")
            print(f"Speedup ratio: {cache_speedup_ratio:.2f}x")
            print(f"Cache hit rate: {cache_hit_rate:.2%}")
            print(f"RAG calls: {call_count['rag_calls']}")
    
    def test_cache_size_scaling(self):
        """测试缓存规模伸缩性性能"""
        from src.poe2build.resilience.cache_manager import CacheManager
        
        cache_sizes = [100, 500, 1000, 5000, 10000]
        performance_results = []
        
        for cache_size in cache_sizes:
            cache_manager = CacheManager(max_size=cache_size, default_ttl=3600)
            
            # 测试缓存填充性能
            fill_start_time = time.perf_counter()
            
            for i in range(min(cache_size, 1000)):  # 填充缓存或至1000个条目
                key = f"perf_test_key_{i}"
                value = {
                    'data': f"test_value_{i}",
                    'timestamp': time.time(),
                    'metadata': {'index': i, 'size': cache_size}
                }
                cache_manager.set(key, value)
            
            fill_time = (time.perf_counter() - fill_start_time) * 1000
            
            # 测试缓存查询性能
            query_times = []
            for i in range(100):  # 100次查询
                key = f"perf_test_key_{i % min(cache_size, 1000)}"
                
                query_start_time = time.perf_counter()
                result = cache_manager.get(key)
                query_time = (time.perf_counter() - query_start_time) * 1000000  # 微秒
                
                query_times.append(query_time)
                assert result is not None  # 应该能找到
            
            avg_query_time = statistics.mean(query_times)
            
            performance_results.append({
                'cache_size': cache_size,
                'fill_time_ms': fill_time,
                'avg_query_time_us': avg_query_time,
                'items_filled': min(cache_size, 1000)
            })
        
        # 分析性能趋势
        print(f"\nCache Scaling Performance:")
        for result in performance_results:
            print(f"Size {result['cache_size']:>5}: Fill {result['fill_time_ms']:>6.2f}ms, Query {result['avg_query_time_us']:>6.2f}μs")
        
        # 验证性能不会随缓存大小显著降低
        small_cache_query_time = performance_results[0]['avg_query_time_us']
        large_cache_query_time = performance_results[-1]['avg_query_time_us']
        
        # 查询性能不应该随缓存大小显著下降（允聓2x差异）
        assert large_cache_query_time < small_cache_query_time * 2, f"Large cache query time degraded too much"


@pytest.mark.performance
@pytest.mark.slow
class TestStressTests:
    """压力测试"""
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, mock_orchestrator_config):
        """测试持续负载下的系统性能"""
        orchestrator = PoE2AIOrchestrator(mock_orchestrator_config)
        
        with patch.multiple(
            orchestrator,
            _rag_engine=AsyncMock(),
            _pob2_local=AsyncMock(),
            _cache_manager=AsyncMock()
        ):
            # 设置响应数据
            orchestrator._rag_engine.generate_recommendations.return_value = [
                {'name': 'Stress Test Build', 'estimated_dps': 600000, 'confidence': 0.8}
            ]
            orchestrator._pob2_local.is_available.return_value = True
            orchestrator._pob2_local.calculate_build_stats.return_value = {
                'total_dps': 620000, 'validation_status': 'valid'
            }
            orchestrator._cache_manager.get.return_value = None
            orchestrator._initialized = True
            
            # 持续负载测试（5分钟）
            test_duration = 300  # 5分钟
            start_time = time.time()
            
            performance_metrics = []
            request_count = 0
            
            while time.time() - start_time < test_duration:
                batch_start_time = time.time()
                
                # 每批次执行10个请求
                batch_tasks = []
                for i in range(10):
                    request = UserRequest(
                        character_class=PoE2CharacterClass.SORCERESS,
                        build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                        max_budget=10.0 + request_count + i,
                        request_id=f"stress_test_{request_count}_{i}"
                    )
                    batch_tasks.append(orchestrator.generate_build_recommendations(request))
                
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                
                # 记录性能指标
                successful_requests = len([r for r in results if not isinstance(r, Exception)])
                request_count += len(batch_tasks)
                
                performance_metrics.append({
                    'timestamp': batch_end_time,
                    'batch_duration': batch_duration,
                    'successful_requests': successful_requests,
                    'success_rate': successful_requests / len(batch_tasks),
                    'throughput': successful_requests / batch_duration,
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
                })
                
                # 小间隙防止过度资源占用
                await asyncio.sleep(0.1)
            
            # 分析性能趋势
            total_requests = sum(m['successful_requests'] for m in performance_metrics)
            avg_throughput = statistics.mean([m['throughput'] for m in performance_metrics])
            avg_success_rate = statistics.mean([m['success_rate'] for m in performance_metrics])
            
            # 内存稳定性分析
            memory_values = [m['memory_mb'] for m in performance_metrics]
            memory_growth = memory_values[-1] - memory_values[0]
            memory_volatility = statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            
            # 持续负载基准验证
            assert avg_success_rate >= 0.90, f"Average success rate {avg_success_rate:.2%} below 90% baseline"
            assert avg_throughput >= 3.0, f"Average throughput {avg_throughput:.2f} req/s below 3.0 baseline"
            assert memory_growth < 1000, f"Memory growth {memory_growth:.2f}MB exceeds 1GB baseline"
            assert memory_volatility < 200, f"Memory volatility {memory_volatility:.2f}MB too high"
            
            print(f"\nSustained Load Test Results:")
            print(f"Test duration: {test_duration}s")
            print(f"Total requests: {total_requests}")
            print(f"Average throughput: {avg_throughput:.2f} req/s")
            print(f"Average success rate: {avg_success_rate:.2%}")
            print(f"Memory growth: {memory_growth:.2f}MB")
            print(f"Memory volatility: {memory_volatility:.2f}MB")
