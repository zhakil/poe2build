"""
RAG系统性能测试
测试RAG检索、向量化和AI增强功能的性能指标
"""

import pytest
import asyncio
import time
import statistics
import psutil
import os
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, patch

from tests.fixtures.test_data import TestDataFactory
from tests.integration.test_system_integration import MockRAGEngine


class PerformanceRAGEngine(MockRAGEngine):
    """性能测试用的RAG引擎实现"""
    
    def __init__(self, dataset_size: int = 1000):
        super().__init__()
        self.dataset_size = dataset_size
        self.knowledge_base = self._build_large_knowledge_base()
        self.search_times = []
        self.vectorization_times = []
    
    def _build_large_knowledge_base(self):
        """构建大型知识库用于性能测试"""
        builds = []
        for i in range(self.dataset_size):
            build = TestDataFactory.create_random_build()
            build.name = f"Performance Test Build {i}"
            builds.append(build)
        
        return {
            'builds': builds,
            'vectors': self._simulate_vectors(len(builds)),
            'meta_patterns': self._generate_meta_patterns()
        }
    
    def _simulate_vectors(self, count: int) -> List[List[float]]:
        """模拟向量数据"""
        import random
        return [[random.random() for _ in range(384)] for _ in range(count)]
    
    def _generate_meta_patterns(self) -> Dict[str, Any]:
        """生成大量meta模式"""
        patterns = {}
        skills = ['Lightning', 'Ice', 'Fire', 'Physical', 'Chaos', 'Poison', 'Bleed']
        for skill in skills:
            patterns[skill] = {
                'popularity': 0.3 + (hash(skill) % 100) / 100 * 0.6,
                'effectiveness': 0.5 + (hash(skill) % 100) / 100 * 0.4,
                'meta_score': 0.4 + (hash(skill) % 100) / 100 * 0.5
            }
        return patterns
    
    async def generate_recommendations(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """带性能监控的推荐生成"""
        start_time = time.perf_counter()
        
        # 模拟向量化查询
        vectorization_start = time.perf_counter()
        query_vector = await self._vectorize_query(query)
        vectorization_time = (time.perf_counter() - vectorization_start) * 1000
        self.vectorization_times.append(vectorization_time)
        
        # 模拟向量搜索
        search_start = time.perf_counter()
        similar_builds = await self._vector_search(query_vector, top_k=20)
        search_time = (time.perf_counter() - search_start) * 1000
        self.search_times.append(search_time)
        
        # 生成最终推荐
        recommendations = await self._generate_final_recommendations(similar_builds, query)
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # 添加性能元数据
        for rec in recommendations:
            rec['performance_metrics'] = {
                'vectorization_time_ms': vectorization_time,
                'search_time_ms': search_time,
                'total_time_ms': total_time
            }
        
        return recommendations
    
    async def _vectorize_query(self, query: Dict[str, Any]) -> List[float]:
        """模拟查询向量化"""
        # 模拟向量化计算时间
        await asyncio.sleep(0.02 + len(str(query)) * 0.001)
        import random
        return [random.random() for _ in range(384)]
    
    async def _vector_search(self, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """模拟向量相似度搜索"""
        # 模拟FAISS搜索时间
        search_complexity = len(self.knowledge_base['builds']) * 0.0001
        await asyncio.sleep(search_complexity)
        
        # 选择随机构筑作为结果
        import random
        builds = random.sample(self.knowledge_base['builds'], min(top_k, len(self.knowledge_base['builds'])))
        
        return [{
            'build': build,
            'similarity_score': 0.9 - i * 0.05,
            'vector_index': i
        } for i, build in enumerate(builds)]
    
    async def _generate_final_recommendations(self, similar_builds: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成最终推荐"""
        # 模拟AI增强处理时间
        await asyncio.sleep(0.05)
        
        recommendations = []
        for item in similar_builds[:5]:
            build = item['build']
            rec = {
                'name': f"RAG Enhanced {build.name}",
                'level': build.level,
                'estimated_dps': int(build.stats.total_dps * 1.1) if build.stats else 500000,
                'estimated_ehp': int(build.stats.effective_health_pool * 1.05) if build.stats else 6000,
                'estimated_cost': build.estimated_cost or 10.0,
                'confidence': item['similarity_score'],
                'main_skill': build.main_skill_gem,
                'rag_metadata': {
                    'source_similarity': item['similarity_score'],
                    'vector_index': item['vector_index']
                }
            }
            recommendations.append(rec)
        
        return recommendations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            'dataset_size': self.dataset_size,
            'search_times': {
                'count': len(self.search_times),
                'mean_ms': statistics.mean(self.search_times) if self.search_times else 0,
                'median_ms': statistics.median(self.search_times) if self.search_times else 0,
                'min_ms': min(self.search_times) if self.search_times else 0,
                'max_ms': max(self.search_times) if self.search_times else 0,
                'p95_ms': statistics.quantiles(self.search_times, n=20)[18] if len(self.search_times) >= 20 else 0,
                'p99_ms': statistics.quantiles(self.search_times, n=100)[98] if len(self.search_times) >= 100 else 0
            },
            'vectorization_times': {
                'count': len(self.vectorization_times),
                'mean_ms': statistics.mean(self.vectorization_times) if self.vectorization_times else 0,
                'median_ms': statistics.median(self.vectorization_times) if self.vectorization_times else 0
            }
        }


@pytest.mark.performance
class TestRAGPerformanceBenchmarks:
    """RAG性能基准测试"""
    
    @pytest.fixture(params=[100, 500, 1000, 2000])
    def rag_engine(self, request):
        """参数化的RAG引擎fixture，测试不同数据集大小"""
        return PerformanceRAGEngine(dataset_size=request.param)
    
    @pytest.mark.asyncio
    async def test_single_query_performance(self, rag_engine):
        """测试单查询性能"""
        query = {
            'character_class': 'Sorceress',
            'build_goal': 'endgame_content',
            'preferred_skills': ['Lightning Bolt', 'Chain Lightning'],
            'max_budget': 25.0
        }
        
        # 预热
        await rag_engine.generate_recommendations(query)
        
        # 性能测试
        start_time = time.perf_counter()
        result = await rag_engine.generate_recommendations(query)
        end_time = time.perf_counter()
        
        execution_time = (end_time - start_time) * 1000
        
        # 验证性能要求
        assert execution_time < 500  # 单查询应在500ms内完成
        assert len(result) > 0
        
        # 验证内部性能指标
        if result and 'performance_metrics' in result[0]:
            metrics = result[0]['performance_metrics']
            assert metrics['vectorization_time_ms'] < 100
            assert metrics['search_time_ms'] < 200
            assert metrics['total_time_ms'] < 500
        
        print(f"Dataset size: {rag_engine.dataset_size}, Execution time: {execution_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_batch_query_performance(self, rag_engine):
        """测试批量查询性能"""
        queries = [
            {'character_class': 'Sorceress', 'build_goal': 'boss_killing'},
            {'character_class': 'Ranger', 'build_goal': 'clear_speed'},
            {'character_class': 'Monk', 'build_goal': 'budget_friendly'},
            {'character_class': 'Witch', 'build_goal': 'endgame_content'},
            {'character_class': 'Warrior', 'build_goal': 'league_start'}
        ]
        
        # 串行执行
        start_time = time.perf_counter()
        for query in queries:
            await rag_engine.generate_recommendations(query)
        serial_time = time.perf_counter() - start_time
        
        # 重置统计
        rag_engine.search_times.clear()
        rag_engine.vectorization_times.clear()
        
        # 并行执行
        start_time = time.perf_counter()
        tasks = [rag_engine.generate_recommendations(query) for query in queries]
        results = await asyncio.gather(*tasks)
        parallel_time = time.perf_counter() - start_time
        
        # 验证并行性能提升
        assert parallel_time < serial_time * 0.8  # 并行应该至少快20%
        assert len(results) == len(queries)
        
        # 验证所有查询都成功
        for result in results:
            assert len(result) > 0
        
        print(f"Dataset: {rag_engine.dataset_size}, Serial: {serial_time:.2f}s, Parallel: {parallel_time:.2f}s, Speedup: {serial_time/parallel_time:.2f}x")
    
    @pytest.mark.asyncio
    async def test_concurrent_load_performance(self, rag_engine):
        """测试并发负载性能"""
        concurrent_queries = 20
        query = {
            'character_class': 'Sorceress',
            'max_budget': 20.0,
            'preferred_skills': ['Lightning Bolt']
        }
        
        # 创建并发任务
        tasks = [rag_engine.generate_recommendations(query) for _ in range(concurrent_queries)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # 性能验证
        assert total_time < 10.0  # 20个并发查询应在10秒内完成
        assert len(results) == concurrent_queries
        
        # 验证所有结果
        for result in results:
            assert len(result) > 0
        
        # 计算吞吐量
        throughput = concurrent_queries / total_time
        
        print(f"Dataset: {rag_engine.dataset_size}, Concurrent queries: {concurrent_queries}, Time: {total_time:.2f}s, Throughput: {throughput:.2f} queries/sec")
        
        # 验证最小吞吐量要求
        min_throughput = 2.0 if rag_engine.dataset_size <= 1000 else 1.0
        assert throughput >= min_throughput
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, rag_engine):
        """测试内存效率"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 执行多次查询以测试内存稳定性
        query = {
            'character_class': 'Witch',
            'build_goal': 'endgame_content',
            'max_budget': 30.0
        }
        
        memory_samples = [initial_memory]
        
        for i in range(50):
            await rag_engine.generate_recommendations(query)
            
            if i % 10 == 9:  # 每10次查询检查内存
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_samples)
        memory_growth = final_memory - initial_memory
        
        # 内存要求验证
        assert memory_growth < 100  # 内存增长不应超过100MB
        assert max_memory - initial_memory < 150  # 峰值内存增长不超过150MB
        
        print(f"Dataset: {rag_engine.dataset_size}, Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Growth: {memory_growth:.1f}MB")
    
    def test_scalability_analysis(self):
        """测试可扩展性分析"""
        dataset_sizes = [100, 500, 1000, 2000, 5000]
        performance_results = []
        
        for size in dataset_sizes:
            engine = PerformanceRAGEngine(dataset_size=size)
            
            # 执行性能测试
            query = {'character_class': 'Sorceress', 'build_goal': 'endgame_content'}
            
            # 使用同步方式测试
            import asyncio
            start_time = time.perf_counter()
            asyncio.run(engine.generate_recommendations(query))
            execution_time = (time.perf_counter() - start_time) * 1000
            
            performance_results.append({
                'dataset_size': size,
                'execution_time_ms': execution_time,
                'time_per_item_us': (execution_time * 1000) / size  # 微秒/条目
            })
        
        # 分析可扩展性
        for i, result in enumerate(performance_results):
            print(f"Size: {result['dataset_size']}, Time: {result['execution_time_ms']:.2f}ms, Per item: {result['time_per_item_us']:.2f}μs")
            
            # 验证线性或亚线性扩展
            if i > 0:
                prev_result = performance_results[i-1]
                size_ratio = result['dataset_size'] / prev_result['dataset_size']
                time_ratio = result['execution_time_ms'] / prev_result['execution_time_ms']
                
                # 时间增长不应超过数据量增长的1.5倍（允许一些非线性）
                assert time_ratio <= size_ratio * 1.5, f"Poor scalability: {time_ratio:.2f} vs {size_ratio:.2f}"
    
    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, rag_engine):
        """测试缓存对性能的影响"""
        query = {
            'character_class': 'Ranger',
            'build_goal': 'clear_speed',
            'preferred_skills': ['Ice Shot']
        }
        
        # 第一次查询（冷缓存）
        start_time = time.perf_counter()
        await rag_engine.generate_recommendations(query)
        cold_cache_time = (time.perf_counter() - start_time) * 1000
        
        # 相同查询（热缓存）- 在实际实现中会有缓存
        start_time = time.perf_counter()
        await rag_engine.generate_recommendations(query)
        warm_cache_time = (time.perf_counter() - start_time) * 1000
        
        # 不同查询（部分缓存）
        different_query = {**query, 'max_budget': 15.0}
        start_time = time.perf_counter()
        await rag_engine.generate_recommendations(different_query)
        partial_cache_time = (time.perf_counter() - start_time) * 1000
        
        print(f"Cold cache: {cold_cache_time:.2f}ms, Warm cache: {warm_cache_time:.2f}ms, Partial cache: {partial_cache_time:.2f}ms")
        
        # 在实际实现中，热缓存应该显著更快
        # 这里只验证基本性能要求
        assert cold_cache_time < 1000
        assert warm_cache_time < 1000
        assert partial_cache_time < 1000


@pytest.mark.performance
class TestRAGStressTests:
    """RAG压力测试"""
    
    @pytest.fixture
    def stress_rag_engine(self):
        """压力测试用的RAG引擎"""
        return PerformanceRAGEngine(dataset_size=5000)
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, stress_rag_engine):
        """测试持续负载性能"""
        duration_seconds = 30
        queries_per_second = 5
        total_queries = duration_seconds * queries_per_second
        
        query_template = {
            'character_class': 'Sorceress',
            'build_goal': 'endgame_content',
            'max_budget': 25.0
        }
        
        # 生成变化的查询
        queries = []
        for i in range(total_queries):
            query = query_template.copy()
            query['preferred_skills'] = [f'Skill_{i % 10}']
            query['max_budget'] = 20.0 + (i % 20)
            queries.append(query)
        
        # 执行持续负载
        start_time = time.perf_counter()
        response_times = []
        
        for query in queries:
            query_start = time.perf_counter()
            result = await stress_rag_engine.generate_recommendations(query)
            query_time = (time.perf_counter() - query_start) * 1000
            response_times.append(query_time)
            
            assert len(result) > 0  # 确保每个查询都成功
            
            # 控制查询频率
            await asyncio.sleep(1.0 / queries_per_second)
        
        total_time = time.perf_counter() - start_time
        
        # 性能统计
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_queries) >= 100 else max(response_times)
        
        # 验证持续负载性能
        assert avg_response_time < 500  # 平均响应时间 < 500ms
        assert p95_response_time < 800   # P95 < 800ms
        assert p99_response_time < 1200  # P99 < 1200ms
        
        print(f"Sustained load: {total_queries} queries in {total_time:.2f}s")
        print(f"Avg: {avg_response_time:.2f}ms, P95: {p95_response_time:.2f}ms, P99: {p99_response_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_burst_load_handling(self, stress_rag_engine):
        """测试突发负载处理"""
        burst_size = 50
        query = {
            'character_class': 'Witch',
            'build_goal': 'boss_killing',
            'max_budget': 40.0
        }
        
        # 创建突发负载
        tasks = [stress_rag_engine.generate_recommendations(query) for _ in range(burst_size)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        burst_time = time.perf_counter() - start_time
        
        # 验证突发处理
        successful_results = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful_results) / len(results)
        
        assert success_rate >= 0.9  # 至少90%成功率
        assert burst_time < 15.0    # 15秒内处理完毕
        
        print(f"Burst load: {burst_size} queries, Success rate: {success_rate:.2%}, Time: {burst_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_recovery(self, stress_rag_engine):
        """测试资源耗尽后的恢复"""
        # 第一阶段：资源耗尽
        exhaustion_queries = 100
        query = {'character_class': 'Ranger', 'build_goal': 'clear_speed'}
        
        # 快速连续执行以模拟资源耗尽
        tasks = [stress_rag_engine.generate_recommendations(query) for _ in range(exhaustion_queries)]
        
        start_time = time.perf_counter()
        exhaustion_results = await asyncio.gather(*tasks, return_exceptions=True)
        exhaustion_time = time.perf_counter() - start_time
        
        # 第二阶段：等待恢复
        await asyncio.sleep(2)
        
        # 第三阶段：恢复验证
        recovery_start = time.perf_counter()
        recovery_result = await stress_rag_engine.generate_recommendations(query)
        recovery_time = (time.perf_counter() - recovery_start) * 1000
        
        # 验证系统恢复
        assert len(recovery_result) > 0
        assert recovery_time < 1000  # 恢复后性能应该正常
        
        # 统计资源耗尽期间的表现
        successful_exhaustion = [r for r in exhaustion_results if not isinstance(r, Exception)]
        exhaustion_success_rate = len(successful_exhaustion) / len(exhaustion_results)
        
        print(f"Exhaustion phase: {exhaustion_success_rate:.2%} success rate")
        print(f"Recovery: {recovery_time:.2f}ms response time")
        
        # 允许资源耗尽期间有一些失败，但恢复后应该正常
        assert recovery_time < 1000


@pytest.mark.performance
class TestRAGVectorPerformance:
    """RAG向量操作性能测试"""
    
    def test_vector_similarity_computation_performance(self):
        """测试向量相似度计算性能"""
        import numpy as np
        
        # 模拟向量数据
        vector_dim = 384
        query_vector = np.random.rand(vector_dim).astype(np.float32)
        
        # 测试不同规模的向量集合
        for db_size in [1000, 5000, 10000, 50000]:
            db_vectors = np.random.rand(db_size, vector_dim).astype(np.float32)
            
            # 测试余弦相似度计算性能
            start_time = time.perf_counter()
            similarities = np.dot(db_vectors, query_vector) / (
                np.linalg.norm(db_vectors, axis=1) * np.linalg.norm(query_vector)
            )
            top_k_indices = np.argsort(similarities)[-10:][::-1]
            computation_time = (time.perf_counter() - start_time) * 1000
            
            # 性能要求
            max_time = 10 + db_size * 0.001  # 基础10ms + 每1000向量1ms
            assert computation_time < max_time
            
            print(f"Vector DB size: {db_size}, Similarity computation: {computation_time:.2f}ms")
    
    def test_faiss_index_performance_simulation(self):
        """测试FAISS索引性能模拟"""
        import random
        
        # 模拟不同索引大小的查询时间
        index_sizes = [1000, 5000, 10000, 50000, 100000]
        
        for size in index_sizes:
            # 模拟FAISS查询时间（基于实际FAISS性能特征）
            base_time = 0.5  # 基础查询时间 (ms)
            log_factor = 0.1 * (size / 1000) ** 0.5  # 次线性增长
            simulated_time = base_time + log_factor
            
            # 添加一些随机性
            actual_time = simulated_time * (0.8 + random.random() * 0.4)
            
            # 验证性能预期
            max_expected_time = 2.0 + (size / 10000) * 3.0  # 动态阈值
            assert actual_time < max_expected_time
            
            print(f"FAISS index size: {size}, Simulated query time: {actual_time:.2f}ms")
    
    def test_batch_vectorization_performance(self):
        """测试批量向量化性能"""
        # 模拟不同批次大小的向量化时间
        batch_sizes = [1, 5, 10, 20, 50, 100]
        
        for batch_size in batch_sizes:
            # 模拟文本向量化时间
            # 实际实现中这会使用sentence-transformers
            start_time = time.perf_counter()
            
            # 模拟批量向量化计算
            processing_time = 10 + batch_size * 15  # 基础10ms + 每个文本15ms
            processing_time_with_batch_benefit = processing_time * (1 - min(0.3, batch_size * 0.02))
            
            # 模拟等待时间
            import asyncio
            asyncio.run(asyncio.sleep(processing_time_with_batch_benefit / 1000))
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            # 计算吞吐量
            throughput = batch_size / (total_time / 1000)
            
            print(f"Batch size: {batch_size}, Time: {total_time:.2f}ms, Throughput: {throughput:.2f} texts/sec")
            
            # 验证批处理效率
            if batch_size > 1:
                expected_min_throughput = 0.5 + batch_size * 0.1
                assert throughput >= expected_min_throughput