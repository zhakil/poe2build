"""
系统整体性能测试
测试完整系统的性能指标，包括响应时间、吞吐量、内存使用等
"""

import pytest
import asyncio
import time
import statistics
import psutil
import os
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.poe2build.core.ai_orchestrator import UserRequest
from src.poe2build.models.characters import PoE2CharacterClass
from src.poe2build.models.build import PoE2BuildGoal
from tests.integration.test_system_integration import IntegratedTestOrchestrator
from tests.fixtures.test_data import TestDataFactory


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    response_times: List[float]
    throughput: float
    success_rate: float
    error_count: int
    memory_usage_mb: float
    cpu_usage_percent: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float


class PerformanceTestOrchestrator(IntegratedTestOrchestrator):
    """性能测试用协调器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.request_times = []
        self.memory_samples = []
        self.cpu_samples = []
        self.error_count = 0
    
    async def generate_build_recommendations(self, request: UserRequest):
        """带性能监控的推荐生成"""
        start_time = time.perf_counter()
        
        try:
            # 记录系统资源使用
            process = psutil.Process(os.getpid())
            self.memory_samples.append(process.memory_info().rss / 1024 / 1024)
            self.cpu_samples.append(process.cpu_percent())
            
            result = await super().generate_build_recommendations(request)
            
            # 记录响应时间
            response_time = (time.perf_counter() - start_time) * 1000
            self.request_times.append(response_time)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            response_time = (time.perf_counter() - start_time) * 1000
            self.request_times.append(response_time)
            raise e
    
    def get_performance_metrics(self, duration_seconds: float) -> PerformanceMetrics:
        """获取性能指标"""
        if not self.request_times:
            return PerformanceMetrics(
                response_times=[], throughput=0, success_rate=0,
                error_count=0, memory_usage_mb=0, cpu_usage_percent=0,
                p50_ms=0, p90_ms=0, p95_ms=0, p99_ms=0
            )
        
        total_requests = len(self.request_times)
        successful_requests = total_requests - self.error_count
        
        # 计算百分位数
        sorted_times = sorted(self.request_times)
        p50 = statistics.median(sorted_times)
        p90 = sorted_times[int(len(sorted_times) * 0.9)] if len(sorted_times) >= 10 else sorted_times[-1]
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) >= 20 else sorted_times[-1]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) >= 100 else sorted_times[-1]
        
        return PerformanceMetrics(
            response_times=self.request_times.copy(),
            throughput=total_requests / duration_seconds,
            success_rate=successful_requests / total_requests if total_requests > 0 else 0,
            error_count=self.error_count,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            p50_ms=p50,
            p90_ms=p90,
            p95_ms=p95,
            p99_ms=p99
        )
    
    def reset_metrics(self):
        """重置性能指标"""
        self.request_times.clear()
        self.memory_samples.clear()
        self.cpu_samples.clear()
        self.error_count = 0


@pytest.mark.performance
class TestSystemPerformanceBenchmarks:
    """系统性能基准测试"""
    
    @pytest.fixture
    async def perf_orchestrator(self):
        """性能测试协调器"""
        config = {
            'max_recommendations': 20,
            'timeout_seconds': 30,
            'cache': {'ttl_seconds': 600}
        }
        orchestrator = PerformanceTestOrchestrator(config)
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_single_request_response_time(self, perf_orchestrator):
        """测试单请求响应时间"""
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=25.0,
            validate_with_pob2=True,
            generate_pob2_code=True
        )
        
        # 预热请求
        await perf_orchestrator.generate_build_recommendations(request)
        perf_orchestrator.reset_metrics()
        
        # 性能测试
        start_time = time.perf_counter()
        result = await perf_orchestrator.generate_build_recommendations(request)
        response_time = (time.perf_counter() - start_time) * 1000
        
        # 性能验证
        assert response_time < 3000  # 单请求应在3秒内完成
        assert len(result.builds) > 0
        assert result.generation_time_ms > 0
        
        print(f"Single request response time: {response_time:.2f}ms")
        print(f"Build count: {len(result.builds)}")
        print(f"RAG confidence: {result.rag_confidence:.3f}")
    
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, perf_orchestrator):
        """测试并发请求性能"""
        concurrent_requests = 10
        requests = [
            UserRequest(
                character_class=PoE2CharacterClass(list(PoE2CharacterClass)[i % len(PoE2CharacterClass)]),
                build_goal=PoE2BuildGoal(list(PoE2BuildGoal)[i % len(PoE2BuildGoal)]),
                max_budget=20.0 + (i * 5),
                validate_with_pob2=i % 2 == 0
            ) for i in range(concurrent_requests)
        ]
        
        # 并发执行
        tasks = [perf_orchestrator.generate_build_recommendations(req) for req in requests]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # 分析结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful_results) / len(results)
        throughput = len(results) / total_time
        
        # 性能验证
        assert success_rate >= 0.9  # 至少90%成功率
        assert total_time < 10.0    # 10个并发请求应在10秒内完成
        assert throughput >= 1.0    # 吞吐量至少1请求/秒
        
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} requests/sec")
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, perf_orchestrator):
        """测试持续负载性能"""
        test_duration = 60  # 60秒测试
        target_rps = 2      # 目标每秒2个请求
        
        requests = [
            UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=15.0,
                validate_with_pob2=False  # 减少计算负载以维持RPS
            ) for _ in range(test_duration * target_rps)
        ]
        
        start_time = time.perf_counter()
        request_count = 0
        
        for request in requests:
            if time.perf_counter() - start_time >= test_duration:
                break
            
            request_start = time.perf_counter()
            
            try:
                await perf_orchestrator.generate_build_recommendations(request)
                request_count += 1
            except Exception as e:
                print(f"Request failed: {e}")
            
            # 控制请求频率
            elapsed = time.perf_counter() - request_start
            sleep_time = (1.0 / target_rps) - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        total_duration = time.perf_counter() - start_time
        metrics = perf_orchestrator.get_performance_metrics(total_duration)
        
        # 性能验证
        assert metrics.success_rate >= 0.95      # 95%成功率
        assert metrics.throughput >= target_rps * 0.8  # 达到目标RPS的80%
        assert metrics.p95_ms < 5000            # P95响应时间 < 5秒
        assert metrics.memory_usage_mb < 2048   # 内存使用 < 2GB
        
        print(f"Sustained load test results:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Requests processed: {request_count}")
        print(f"  Throughput: {metrics.throughput:.2f} req/sec")
        print(f"  Success rate: {metrics.success_rate:.2%}")
        print(f"  P50: {metrics.p50_ms:.2f}ms, P95: {metrics.p95_ms:.2f}ms, P99: {metrics.p99_ms:.2f}ms")
        print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
    
    @pytest.mark.asyncio 
    async def test_memory_usage_under_load(self, perf_orchestrator):
        """测试负载下的内存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 创建内存密集型请求
        request = UserRequest(
            character_class=PoE2CharacterClass.WITCH,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=50.0,
            validate_with_pob2=True,
            generate_pob2_code=True
        )
        
        memory_samples = [initial_memory]
        
        # 执行50个请求并监控内存
        for i in range(50):
            await perf_orchestrator.generate_build_recommendations(request)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # 每10个请求检查一次内存增长
            if i % 10 == 9:
                memory_growth = current_memory - initial_memory
                assert memory_growth < 500  # 内存增长不超过500MB
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples[1:])  # 排除初始值
        
        # 内存使用验证
        total_growth = final_memory - initial_memory
        peak_growth = max_memory - initial_memory
        
        assert total_growth < 400   # 总内存增长 < 400MB
        assert peak_growth < 600    # 峰值内存增长 < 600MB
        assert avg_memory < initial_memory + 300  # 平均内存增长 < 300MB
        
        print(f"Memory usage analysis:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB") 
        print(f"  Peak: {max_memory:.2f}MB")
        print(f"  Average: {avg_memory:.2f}MB")
        print(f"  Total growth: {total_growth:.2f}MB")
        print(f"  Peak growth: {peak_growth:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, perf_orchestrator):
        """测试错误恢复性能"""
        # 正常请求基准
        normal_request = UserRequest(
            character_class=PoE2CharacterClass.MONK,
            build_goal=PoE2BuildGoal.BUDGET_FRIENDLY,
            max_budget=10.0
        )
        
        # 测试正常性能
        start_time = time.perf_counter()
        await perf_orchestrator.generate_build_recommendations(normal_request)
        baseline_time = (time.perf_counter() - start_time) * 1000
        
        # 模拟组件故障
        original_pob2_available = perf_orchestrator._pob2_local.available
        perf_orchestrator._pob2_local.available = False
        
        # 测试降级性能
        start_time = time.perf_counter()
        result = await perf_orchestrator.generate_build_recommendations(normal_request)
        degraded_time = (time.perf_counter() - start_time) * 1000
        
        # 恢复组件
        perf_orchestrator._pob2_local.available = original_pob2_available
        
        # 测试恢复后性能
        start_time = time.perf_counter()
        await perf_orchestrator.generate_build_recommendations(normal_request)
        recovery_time = (time.perf_counter() - start_time) * 1000
        
        # 性能验证
        assert len(result.builds) > 0           # 降级模式仍有结果
        assert degraded_time < baseline_time * 3 # 降级响应时间不超过3倍
        assert recovery_time < baseline_time * 1.2 # 恢复后接近基准性能
        
        print(f"Error recovery performance:")
        print(f"  Baseline: {baseline_time:.2f}ms")
        print(f"  Degraded: {degraded_time:.2f}ms ({degraded_time/baseline_time:.1f}x)")
        print(f"  Recovery: {recovery_time:.2f}ms ({recovery_time/baseline_time:.1f}x)")


@pytest.mark.performance
class TestPerformanceRegression:
    """性能回归测试"""
    
    @pytest.fixture
    async def regression_orchestrator(self):
        """回归测试协调器"""
        orchestrator = PerformanceTestOrchestrator()
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_response_time_regression(self, regression_orchestrator):
        """测试响应时间回归"""
        # 基准性能目标（基于README中的指标）
        performance_targets = {
            'rag_retrieval_ms': 100,
            'pob2_calculation_ms': 5000,
            'api_response_ms': 2000,
            'total_request_ms': 3000
        }
        
        test_cases = [
            # 轻量级请求
            UserRequest(
                character_class=PoE2CharacterClass.MONK,
                build_goal=PoE2BuildGoal.BUDGET_FRIENDLY,
                max_budget=5.0,
                validate_with_pob2=False
            ),
            # 中等复杂度请求
            UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=20.0,
                validate_with_pob2=True
            ),
            # 高复杂度请求
            UserRequest(
                character_class=PoE2CharacterClass.SORCERESS,
                build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
                max_budget=50.0,
                validate_with_pob2=True,
                generate_pob2_code=True
            )
        ]
        
        for i, request in enumerate(test_cases):
            # 执行多次测试以获得稳定结果
            times = []
            for _ in range(5):
                start_time = time.perf_counter()
                result = await regression_orchestrator.generate_build_recommendations(request)
                response_time = (time.perf_counter() - start_time) * 1000
                times.append(response_time)
                
                assert len(result.builds) > 0  # 确保有结果
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # 根据请求复杂度设置不同的目标
            if i == 0:  # 轻量级
                target = performance_targets['api_response_ms'] * 0.5
            elif i == 1:  # 中等
                target = performance_targets['api_response_ms']
            else:  # 高复杂度
                target = performance_targets['total_request_ms']
            
            assert avg_time < target, f"Performance regression: avg {avg_time:.2f}ms > target {target}ms"
            assert max_time < target * 1.5, f"Performance regression: max {max_time:.2f}ms > target {target * 1.5}ms"
            
            print(f"Test case {i+1}: avg={avg_time:.2f}ms, max={max_time:.2f}ms, target={target:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_memory_usage_regression(self, regression_orchestrator):
        """测试内存使用回归"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 基准内存目标
        memory_target_mb = 2048  # 2GB限制
        
        request = UserRequest(
            character_class=PoE2CharacterClass.WITCH,
            build_goal=PoE2BuildGoal.BOSS_KILLING,
            max_budget=30.0,
            validate_with_pob2=True
        )
        
        # 执行一系列请求
        for i in range(30):
            await regression_orchestrator.generate_build_recommendations(request)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_usage = current_memory - initial_memory
            
            # 每5个请求检查内存
            if i % 5 == 4:
                assert current_memory < memory_target_mb, f"Memory regression: {current_memory:.2f}MB > {memory_target_mb}MB"
                print(f"Request {i+1}: Memory usage {current_memory:.2f}MB (+{memory_usage:.2f}MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        # 总内存增长不应超过目标的25%
        max_acceptable_increase = memory_target_mb * 0.25
        assert total_increase < max_acceptable_increase, f"Memory leak detected: {total_increase:.2f}MB increase"
    
    @pytest.mark.asyncio
    async def test_throughput_regression(self, regression_orchestrator):
        """测试吞吐量回归"""
        # 基准吞吐量目标
        min_throughput_rps = 1.5  # 最少1.5请求/秒
        
        requests = [
            UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=15.0,
                validate_with_pob2=False  # 减少计算开销
            ) for _ in range(20)
        ]
        
        # 串行执行以测试单线程吞吐量
        start_time = time.perf_counter()
        successful_requests = 0
        
        for request in requests:
            try:
                result = await regression_orchestrator.generate_build_recommendations(request)
                if len(result.builds) > 0:
                    successful_requests += 1
            except Exception as e:
                print(f"Request failed: {e}")
        
        total_time = time.perf_counter() - start_time
        actual_throughput = successful_requests / total_time
        
        assert actual_throughput >= min_throughput_rps, f"Throughput regression: {actual_throughput:.2f} < {min_throughput_rps} req/sec"
        assert successful_requests >= len(requests) * 0.95, f"Success rate too low: {successful_requests}/{len(requests)}"
        
        print(f"Throughput test: {actual_throughput:.2f} req/sec ({successful_requests}/{len(requests)} successful)")


@pytest.mark.performance
@pytest.mark.slow
class TestStressAndLimit:
    """压力测试和极限测试"""
    
    @pytest.fixture
    async def stress_orchestrator(self):
        """压力测试协调器"""
        config = {
            'max_recommendations': 50,
            'timeout_seconds': 120,
            'cache': {'ttl_seconds': 1800}
        }
        orchestrator = PerformanceTestOrchestrator(config)
        await orchestrator.initialize_for_testing()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_maximum_concurrent_requests(self, stress_orchestrator):
        """测试最大并发请求数"""
        max_concurrent = 50
        
        request = UserRequest(
            character_class=PoE2CharacterClass.SORCERESS,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=25.0
        )
        
        # 创建大量并发任务
        tasks = [
            stress_orchestrator.generate_build_recommendations(request)
            for _ in range(max_concurrent)
        ]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # 分析结果
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        success_rate = successful / len(results)
        
        # 压力测试验证
        assert success_rate >= 0.7  # 至少70%成功率（允许在高压力下有一些失败）
        assert total_time < 60.0    # 60秒内完成
        
        print(f"Max concurrent test: {max_concurrent} requests")
        print(f"Success rate: {success_rate:.2%} ({successful}/{len(results)})")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average response time: {total_time/len(results):.2f}s")
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_behavior(self, stress_orchestrator):
        """测试资源耗尽时的行为"""
        # 快速连续发送大量请求以模拟资源耗尽
        request = UserRequest(
            character_class=PoE2CharacterClass.WARRIOR,
            build_goal=PoE2BuildGoal.BOSS_KILLING,
            validate_with_pob2=True
        )
        
        exhaustion_requests = 100
        
        # 第一轮：快速连续请求
        tasks = [
            stress_orchestrator.generate_build_recommendations(request)
            for _ in range(exhaustion_requests)
        ]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        exhaustion_time = time.perf_counter() - start_time
        
        # 分析资源耗尽期间的行为
        successful_during_exhaustion = sum(1 for r in results if not isinstance(r, Exception))
        
        # 等待系统恢复
        await asyncio.sleep(5)
        
        # 第二轮：验证恢复
        recovery_start = time.perf_counter()
        recovery_result = await stress_orchestrator.generate_build_recommendations(request)
        recovery_time = time.perf_counter() - recovery_start
        
        # 验证系统行为
        exhaustion_success_rate = successful_during_exhaustion / exhaustion_requests
        
        print(f"Resource exhaustion test:")
        print(f"  Exhaustion phase: {exhaustion_success_rate:.2%} success rate in {exhaustion_time:.2f}s")
        print(f"  Recovery: {'SUCCESS' if len(recovery_result.builds) > 0 else 'FAILED'} in {recovery_time:.2f}s")
        
        # 验证系统有一定的弹性
        assert exhaustion_success_rate >= 0.3  # 即使在压力下也有一定成功率
        assert len(recovery_result.builds) > 0  # 恢复后能正常工作
        assert recovery_time < 10.0             # 恢复时间合理
    
    @pytest.mark.asyncio
    async def test_long_running_stability(self, stress_orchestrator):
        """测试长时间运行稳定性"""
        test_duration = 180  # 3分钟测试
        requests_per_minute = 30
        
        start_time = time.perf_counter()
        request_count = 0
        success_count = 0
        
        while time.perf_counter() - start_time < test_duration:
            request = UserRequest(
                character_class=PoE2CharacterClass(list(PoE2CharacterClass)[request_count % len(PoE2CharacterClass)]),
                build_goal=PoE2BuildGoal(list(PoE2BuildGoal)[request_count % len(PoE2BuildGoal)]),
                max_budget=10.0 + (request_count % 20),
                validate_with_pob2=request_count % 3 == 0
            )
            
            try:
                result = await stress_orchestrator.generate_build_recommendations(request)
                if len(result.builds) > 0:
                    success_count += 1
            except Exception as e:
                print(f"Request {request_count} failed: {e}")
            
            request_count += 1
            
            # 控制请求频率
            await asyncio.sleep(60.0 / requests_per_minute)
        
        actual_duration = time.perf_counter() - start_time
        final_success_rate = success_count / request_count if request_count > 0 else 0
        final_throughput = request_count / actual_duration
        
        # 长期稳定性验证
        assert final_success_rate >= 0.9       # 90%成功率
        assert final_throughput >= 0.4         # 至少0.4请求/秒
        assert request_count >= test_duration * 0.8  # 完成了预期的大部分请求
        
        print(f"Long running stability test:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Requests: {request_count}")
        print(f"  Success rate: {final_success_rate:.2%}")
        print(f"  Throughput: {final_throughput:.2f} req/sec")