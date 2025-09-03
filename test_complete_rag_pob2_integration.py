"""
完整的RAG-PoB2集成工作流测试

这个脚本测试整个系统的端到端功能：
🔄 四大数据源集成
🧠 RAG训练和推荐算法  
🔧 PoB2路径检测和适配
📊 构建数据转换和验证
⚡ 导入代码生成和测试

确保所有组件协同工作，提供完整的用户体验。
"""

import asyncio
import logging
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 设置路径
sys.path.insert(0, str(Path(__file__).parent / "core_ai_engine/src"))

# 导入核心组件
from rag_pob2_integrated_recommender import (
    RAGPoB2IntegratedRecommender,
    IntegratedRecommendationRequest,
    create_integrated_recommender,
    quick_recommendation
)
from pob2_import_code_generator import PoB2ImportCodeGenerator, generate_build_import_code
from poe2build.pob2.path_detector import PoB2PathDetector
from poe2build.pob2.local_client import PoB2LocalClient
from poe2build.rag.recommendation import AlgorithmType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGPoB2IntegrationTester:
    """RAG-PoB2集成测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.logger = logger
        self.recommender = None
        self.code_generator = None
        self.test_results = {}
        
        logger.info("RAG-PoB2集成测试器初始化完成")
    
    async def run_complete_integration_test(self) -> Dict[str, Any]:
        """运行完整的集成测试"""
        logger.info("🚀 开始完整的RAG-PoB2集成测试")
        start_time = time.time()
        
        test_results = {
            'overall_success': False,
            'test_phases': {},
            'total_duration_ms': 0,
            'pob2_installation': {},
            'recommendation_quality': {},
            'code_generation_stats': {},
            'performance_metrics': {}
        }
        
        try:
            # Phase 1: 系统初始化测试
            logger.info("📡 Phase 1: 系统初始化测试")
            phase1_result = await self._test_system_initialization()
            test_results['test_phases']['initialization'] = phase1_result
            
            if not phase1_result['success']:
                logger.error("系统初始化失败，终止测试")
                return test_results
            
            # Phase 2: PoB2路径检测测试  
            logger.info("🔍 Phase 2: PoB2路径检测测试")
            phase2_result = await self._test_pob2_detection()
            test_results['test_phases']['pob2_detection'] = phase2_result
            test_results['pob2_installation'] = phase2_result.get('installation_info', {})
            
            # Phase 3: RAG推荐测试
            logger.info("🎯 Phase 3: RAG智能推荐测试") 
            phase3_result = await self._test_rag_recommendations()
            test_results['test_phases']['rag_recommendations'] = phase3_result
            test_results['recommendation_quality'] = phase3_result.get('quality_metrics', {})
            
            # Phase 4: PoB2代码生成测试
            logger.info("🔧 Phase 4: PoB2代码生成测试")
            phase4_result = await self._test_pob2_code_generation()
            test_results['test_phases']['code_generation'] = phase4_result
            test_results['code_generation_stats'] = phase4_result.get('generation_stats', {})
            
            # Phase 5: 端到端工作流测试
            logger.info("🌊 Phase 5: 端到端工作流测试")
            phase5_result = await self._test_end_to_end_workflow()
            test_results['test_phases']['end_to_end'] = phase5_result
            
            # Phase 6: 性能基准测试
            logger.info("⚡ Phase 6: 性能基准测试")
            phase6_result = await self._test_performance_benchmarks()
            test_results['test_phases']['performance'] = phase6_result
            test_results['performance_metrics'] = phase6_result.get('metrics', {})
            
            # 计算总体成功率
            successful_phases = sum(1 for phase in test_results['test_phases'].values() if phase['success'])
            total_phases = len(test_results['test_phases'])
            test_results['overall_success'] = successful_phases >= (total_phases * 0.8)  # 80%成功率
            
            total_duration = (time.time() - start_time) * 1000
            test_results['total_duration_ms'] = total_duration
            
            logger.info(f"✅ 集成测试完成: {successful_phases}/{total_phases} 阶段成功 ({total_duration:.2f}ms)")
            
            return test_results
            
        except Exception as e:
            logger.error(f"❌ 集成测试失败: {e}")
            test_results['error'] = str(e)
            return test_results
    
    async def _test_system_initialization(self) -> Dict[str, Any]:
        """测试系统初始化"""
        result = {'success': False, 'details': {}, 'errors': []}
        
        try:
            # 初始化集成推荐系统
            logger.info("初始化RAG-PoB2集成推荐系统...")
            self.recommender = await create_integrated_recommender()
            
            if self.recommender and self.recommender.initialized:
                result['success'] = True
                result['details']['recommender_initialized'] = True
                logger.info("✅ 集成推荐系统初始化成功")
            else:
                result['errors'].append("集成推荐系统初始化失败")
                logger.error("❌ 集成推荐系统初始化失败")
            
            # 初始化代码生成器
            self.code_generator = PoB2ImportCodeGenerator()
            result['details']['code_generator_initialized'] = True
            logger.info("✅ 代码生成器初始化成功")
            
            # 获取系统状态
            if self.recommender:
                system_status = self.recommender.get_system_status()
                result['details']['system_status'] = system_status
                
                components_healthy = sum(1 for status in system_status.get('system_components', {}).values() if status)
                result['details']['healthy_components'] = components_healthy
                
                logger.info(f"系统状态: {components_healthy} 个健康组件")
            
            return result
            
        except Exception as e:
            result['errors'].append(f"初始化异常: {str(e)}")
            logger.error(f"❌ 系统初始化异常: {e}")
            return result
    
    async def _test_pob2_detection(self) -> Dict[str, Any]:
        """测试PoB2路径检测"""
        result = {'success': False, 'details': {}, 'installation_info': {}}
        
        try:
            # 测试所有检测方法
            detection_results = PoB2PathDetector.detect_all_methods()
            result['details']['detection_methods'] = detection_results
            
            # 使用主检测方法
            pob2_path = PoB2PathDetector.detect()
            
            if pob2_path:
                result['success'] = True
                result['installation_info'] = {
                    'path': pob2_path,
                    'found': True,
                    'detection_method': 'auto'
                }
                logger.info(f"✅ 检测到PoB2安装: {pob2_path}")
                
                # 验证安装有效性
                pob2_client = PoB2LocalClient(installation_path=Path(pob2_path))
                is_available = pob2_client.is_available()
                result['installation_info']['validated'] = is_available
                
                if is_available:
                    logger.info("✅ PoB2安装验证通过")
                else:
                    logger.warning("⚠️ PoB2安装验证失败")
                    
            else:
                result['installation_info'] = {
                    'path': None,
                    'found': False,
                    'detection_method': 'none'
                }
                logger.warning("⚠️ 未检测到PoB2安装，将使用Web回退模式")
                result['success'] = True  # Web模式也算成功
            
            return result
            
        except Exception as e:
            result['details']['error'] = str(e)
            logger.error(f"❌ PoB2检测异常: {e}")
            return result
    
    async def _test_rag_recommendations(self) -> Dict[str, Any]:
        """测试RAG智能推荐"""
        result = {'success': False, 'details': {}, 'quality_metrics': {}}
        
        if not self.recommender:
            result['details']['error'] = "推荐系统未初始化"
            return result
        
        try:
            # 定义测试用例
            test_cases = [
                {
                    'name': 'Ranger弓箭手清图构建',
                    'request': IntegratedRecommendationRequest(
                        character_class='Ranger',
                        build_goal='clear_speed',
                        budget_range=(0, 15),
                        preferred_skills=['Lightning Arrow', 'Explosive Shot'],
                        max_recommendations=5
                    )
                },
                {
                    'name': 'Witch法师Boss杀手',
                    'request': IntegratedRecommendationRequest(
                        character_class='Witch',
                        build_goal='boss_killing',
                        budget_range=(10, 30),
                        preferred_skills=['Fireball', 'Meteor'],
                        max_recommendations=3
                    )
                },
                {
                    'name': '预算友好战士构建',
                    'request': IntegratedRecommendationRequest(
                        character_class='Warrior',
                        build_goal='budget_friendly',
                        budget_range=(0, 5),
                        skill_level='beginner',
                        max_recommendations=4
                    )
                }
            ]
            
            recommendation_results = []
            total_recommendations = 0
            successful_requests = 0
            
            for test_case in test_cases:
                try:
                    logger.info(f"测试推荐: {test_case['name']}")
                    recommendation_result = await self.recommender.generate_integrated_recommendations(
                        test_case['request']
                    )
                    
                    recommendation_count = len(recommendation_result.primary_recommendations)
                    total_recommendations += recommendation_count
                    
                    if recommendation_count > 0:
                        successful_requests += 1
                        logger.info(f"✅ {test_case['name']}: {recommendation_count} 个推荐")
                    else:
                        logger.warning(f"⚠️ {test_case['name']}: 无推荐结果")
                    
                    recommendation_results.append({
                        'test_case': test_case['name'],
                        'recommendation_count': recommendation_count,
                        'rag_confidence': recommendation_result.rag_confidence,
                        'processing_time_ms': recommendation_result.processing_time_ms,
                        'successful_conversions': recommendation_result.successful_conversions
                    })
                    
                except Exception as e:
                    logger.error(f"❌ 推荐测试失败 {test_case['name']}: {e}")
                    recommendation_results.append({
                        'test_case': test_case['name'],
                        'error': str(e)
                    })
            
            # 计算质量指标
            result['quality_metrics'] = {
                'total_test_cases': len(test_cases),
                'successful_requests': successful_requests,
                'total_recommendations': total_recommendations,
                'average_recommendations_per_request': total_recommendations / len(test_cases),
                'success_rate': successful_requests / len(test_cases)
            }
            
            result['details']['recommendation_results'] = recommendation_results
            result['success'] = successful_requests >= (len(test_cases) * 0.7)  # 70%成功率
            
            logger.info(f"推荐测试结果: {successful_requests}/{len(test_cases)} 成功")
            return result
            
        except Exception as e:
            result['details']['error'] = str(e)
            logger.error(f"❌ RAG推荐测试异常: {e}")
            return result
    
    async def _test_pob2_code_generation(self) -> Dict[str, Any]:
        """测试PoB2代码生成"""
        result = {'success': False, 'details': {}, 'generation_stats': {}}
        
        if not self.code_generator:
            result['details']['error'] = "代码生成器未初始化"
            return result
        
        try:
            # 定义测试构建数据
            test_builds = [
                {
                    'name': 'Ranger Lightning Arrow',
                    'data': {
                        'character_class': 'Ranger',
                        'ascendancy': 'Deadeye',
                        'level': 85,
                        'main_skill': 'Lightning Arrow',
                        'support_gems': ['Multiple Projectiles', 'Added Lightning Damage'],
                        'build_goal': 'clear_speed',
                        'total_dps': 750000,
                        'life': 4200
                    }
                },
                {
                    'name': 'Witch Fireball',
                    'data': {
                        'character_class': 'Witch',
                        'ascendancy': 'Infernalist', 
                        'level': 90,
                        'main_skill': 'Fireball',
                        'support_gems': ['Added Fire Damage', 'Concentrated Effect'],
                        'build_goal': 'boss_killing',
                        'total_dps': 950000,
                        'life': 3800,
                        'energy_shield': 2200
                    }
                },
                {
                    'name': 'Warrior Basic',
                    'data': {
                        'character_class': 'Warrior',
                        'level': 70,
                        'main_skill': 'Earthquake',
                        'support_gems': ['Added Fire Damage'],
                        'build_goal': 'budget_friendly',
                        'total_dps': 400000,
                        'life': 5000
                    }
                }
            ]
            
            generation_results = []
            successful_generations = 0
            total_code_length = 0
            total_generation_time = 0
            
            for test_build in test_builds:
                try:
                    logger.info(f"生成代码: {test_build['name']}")
                    start_time = time.time()
                    
                    generation_result = self.code_generator.generate_pob2_import_code(
                        test_build['data']
                    )
                    
                    generation_time = (time.time() - start_time) * 1000
                    total_generation_time += generation_time
                    
                    if generation_result.is_valid and generation_result.import_code:
                        successful_generations += 1
                        total_code_length += len(generation_result.import_code)
                        
                        logger.info(f"✅ {test_build['name']}: 代码长度 {len(generation_result.import_code)}")
                        
                        # 验证生成的代码
                        validation_result = self.code_generator.validate_import_code(
                            generation_result.import_code
                        )
                        
                        generation_results.append({
                            'build_name': test_build['name'],
                            'success': True,
                            'code_length': len(generation_result.import_code),
                            'generation_time_ms': generation_time,
                            'validation_passed': validation_result['valid'],
                            'warnings': len(generation_result.validation_warnings),
                            'estimated_stats': generation_result.estimated_stats
                        })
                    else:
                        logger.warning(f"⚠️ {test_build['name']}: 生成失败")
                        generation_results.append({
                            'build_name': test_build['name'],
                            'success': False,
                            'errors': generation_result.validation_errors
                        })
                        
                except Exception as e:
                    logger.error(f"❌ 代码生成异常 {test_build['name']}: {e}")
                    generation_results.append({
                        'build_name': test_build['name'],
                        'success': False,
                        'error': str(e)
                    })
            
            # 计算生成统计
            result['generation_stats'] = {
                'total_builds': len(test_builds),
                'successful_generations': successful_generations,
                'success_rate': successful_generations / len(test_builds),
                'average_code_length': total_code_length / max(1, successful_generations),
                'average_generation_time_ms': total_generation_time / len(test_builds)
            }
            
            result['details']['generation_results'] = generation_results
            result['success'] = successful_generations >= (len(test_builds) * 0.8)  # 80%成功率
            
            logger.info(f"代码生成测试结果: {successful_generations}/{len(test_builds)} 成功")
            return result
            
        except Exception as e:
            result['details']['error'] = str(e)
            logger.error(f"❌ 代码生成测试异常: {e}")
            return result
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """测试端到端工作流"""
        result = {'success': False, 'details': {}}
        
        if not (self.recommender and self.code_generator):
            result['details']['error'] = "系统组件未完全初始化"
            return result
        
        try:
            logger.info("执行端到端工作流测试...")
            
            # 1. 创建推荐请求
            request = IntegratedRecommendationRequest(
                character_class='Ranger',
                build_goal='clear_speed',
                budget_range=(0, 20),
                preferred_skills=['Lightning Arrow'],
                max_recommendations=3,
                generate_pob2_code=True,
                validate_with_pob2=True
            )
            
            # 2. 生成推荐
            workflow_start = time.time()
            recommendation_result = await self.recommender.generate_integrated_recommendations(request)
            workflow_time = (time.time() - workflow_start) * 1000
            
            # 3. 验证结果
            primary_recommendations = recommendation_result.primary_recommendations
            
            if len(primary_recommendations) > 0:
                result['success'] = True
                
                # 统计PoB2代码生成成功率
                valid_codes = 0
                for _, _, pob2_validation in primary_recommendations:
                    if pob2_validation.is_valid and pob2_validation.import_code:
                        valid_codes += 1
                
                result['details'] = {
                    'total_recommendations': len(primary_recommendations),
                    'valid_pob2_codes': valid_codes,
                    'pob2_conversion_rate': valid_codes / len(primary_recommendations),
                    'workflow_time_ms': workflow_time,
                    'rag_confidence': recommendation_result.rag_confidence,
                    'average_compatibility': recommendation_result.average_compatibility
                }
                
                logger.info(f"✅ 端到端测试成功: {len(primary_recommendations)} 推荐, {valid_codes} 有效PoB2代码")
                
                # 显示第一个推荐的详细信息
                if primary_recommendations:
                    first_rec, first_score, first_pob2 = primary_recommendations[0]
                    result['details']['sample_recommendation'] = {
                        'character_class': first_rec.metadata.get('character_class'),
                        'main_skill': first_rec.metadata.get('main_skill'),
                        'recommendation_score': first_score.total_score,
                        'pob2_valid': first_pob2.is_valid,
                        'pob2_code_length': len(first_pob2.import_code) if first_pob2.import_code else 0
                    }
            else:
                result['details']['error'] = "未生成任何推荐"
                logger.warning("⚠️ 端到端测试失败: 未生成推荐")
            
            return result
            
        except Exception as e:
            result['details']['error'] = str(e)
            logger.error(f"❌ 端到端测试异常: {e}")
            return result
    
    async def _test_performance_benchmarks(self) -> Dict[str, Any]:
        """测试性能基准"""
        result = {'success': False, 'metrics': {}, 'details': {}}
        
        if not self.recommender:
            result['details']['error'] = "推荐系统未初始化"
            return result
        
        try:
            logger.info("执行性能基准测试...")
            
            # 快速推荐性能测试
            benchmark_times = []
            benchmark_requests = [
                ('Witch', 'endgame_content', 15),
                ('Ranger', 'clear_speed', 12),
                ('Warrior', 'budget_friendly', 8),
                ('Monk', 'boss_killing', 25),
                ('Mercenary', 'clear_speed', 18)
            ]
            
            for character_class, build_goal, budget in benchmark_requests:
                try:
                    start_time = time.time()
                    result_obj = await quick_recommendation(
                        character_class=character_class,
                        build_goal=build_goal,
                        budget_max=budget
                    )
                    end_time = time.time()
                    
                    request_time = (end_time - start_time) * 1000
                    benchmark_times.append(request_time)
                    
                    logger.info(f"基准测试 {character_class}-{build_goal}: {request_time:.2f}ms")
                    
                except Exception as e:
                    logger.warning(f"基准测试失败 {character_class}-{build_goal}: {e}")
                    continue
            
            if benchmark_times:
                result['metrics'] = {
                    'total_benchmark_requests': len(benchmark_requests),
                    'successful_requests': len(benchmark_times),
                    'average_response_time_ms': sum(benchmark_times) / len(benchmark_times),
                    'min_response_time_ms': min(benchmark_times),
                    'max_response_time_ms': max(benchmark_times),
                    'requests_per_second': 1000 / (sum(benchmark_times) / len(benchmark_times))
                }
                
                # 性能等级评估
                avg_time = result['metrics']['average_response_time_ms']
                if avg_time < 1000:
                    performance_grade = 'Excellent'
                elif avg_time < 3000:
                    performance_grade = 'Good'
                elif avg_time < 10000:
                    performance_grade = 'Fair'
                else:
                    performance_grade = 'Poor'
                
                result['metrics']['performance_grade'] = performance_grade
                result['success'] = len(benchmark_times) >= (len(benchmark_requests) * 0.6)
                
                logger.info(f"性能基准: 平均 {avg_time:.2f}ms, 等级 {performance_grade}")
            
            return result
            
        except Exception as e:
            result['details']['error'] = str(e)
            logger.error(f"❌ 性能测试异常: {e}")
            return result
    
    def display_test_summary(self, test_results: Dict[str, Any]):
        """显示测试结果摘要"""
        print("\n" + "="*80)
        print("🎯 RAG-PoB2集成测试结果摘要")
        print("="*80)
        
        # 总体结果
        overall_success = test_results.get('overall_success', False)
        total_duration = test_results.get('total_duration_ms', 0)
        
        success_icon = "✅" if overall_success else "❌"
        print(f"{success_icon} 总体结果: {'成功' if overall_success else '失败'} ({total_duration:.2f}ms)")
        
        # 各阶段结果
        print(f"\n📋 测试阶段结果:")
        phases = test_results.get('test_phases', {})
        for phase_name, phase_result in phases.items():
            phase_success = phase_result.get('success', False)
            phase_icon = "✅" if phase_success else "❌"
            print(f"  {phase_icon} {phase_name}: {'通过' if phase_success else '失败'}")
        
        # PoB2安装信息
        pob2_info = test_results.get('pob2_installation', {})
        if pob2_info:
            print(f"\n🔧 PoB2安装状态:")
            print(f"  路径: {pob2_info.get('path', '未找到')}")
            print(f"  验证: {'通过' if pob2_info.get('validated', False) else '失败'}")
        
        # 推荐质量指标
        quality_metrics = test_results.get('recommendation_quality', {})
        if quality_metrics:
            print(f"\n🎯 推荐质量指标:")
            print(f"  成功率: {quality_metrics.get('success_rate', 0):.2%}")
            print(f"  平均推荐数: {quality_metrics.get('average_recommendations_per_request', 0):.1f}")
            print(f"  总推荐数: {quality_metrics.get('total_recommendations', 0)}")
        
        # 代码生成统计
        code_stats = test_results.get('code_generation_stats', {})
        if code_stats:
            print(f"\n🔧 代码生成统计:")
            print(f"  成功率: {code_stats.get('success_rate', 0):.2%}")
            print(f"  平均代码长度: {code_stats.get('average_code_length', 0):.0f} 字符")
            print(f"  平均生成时间: {code_stats.get('average_generation_time_ms', 0):.2f}ms")
        
        # 性能指标
        perf_metrics = test_results.get('performance_metrics', {})
        if perf_metrics:
            print(f"\n⚡ 性能指标:")
            print(f"  平均响应时间: {perf_metrics.get('average_response_time_ms', 0):.2f}ms")
            print(f"  性能等级: {perf_metrics.get('performance_grade', 'N/A')}")
            print(f"  请求吞吐量: {perf_metrics.get('requests_per_second', 0):.1f} req/s")
        
        print("="*80)
    
    async def run_quick_integration_test(self) -> bool:
        """运行快速集成测试"""
        logger.info("🚀 执行快速集成测试")
        
        try:
            # 快速推荐测试
            result = await quick_recommendation(
                character_class='Ranger',
                build_goal='clear_speed',
                budget_max=15
            )
            
            success = len(result.primary_recommendations) > 0
            
            if success:
                logger.info(f"✅ 快速测试成功: {len(result.primary_recommendations)} 个推荐")
                
                # 显示第一个推荐
                if result.primary_recommendations:
                    first_rec, first_score, first_pob2 = result.primary_recommendations[0]
                    metadata = first_rec.metadata
                    
                    print(f"\n🎯 示例推荐:")
                    print(f"  职业: {metadata.get('character_class', 'Unknown')}")
                    print(f"  主技能: {metadata.get('main_skill', 'Unknown')}")
                    print(f"  推荐分数: {first_score.total_score:.3f}")
                    print(f"  PoB2有效: {'是' if first_pob2.is_valid else '否'}")
                    
                    if first_pob2.import_code:
                        print(f"  导入代码: {first_pob2.import_code[:50]}...")
            else:
                logger.warning("⚠️ 快速测试失败: 无推荐结果")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 快速测试异常: {e}")
            return False

# 便捷测试函数
async def run_integration_test(full_test: bool = True) -> Dict[str, Any]:
    """运行集成测试"""
    tester = RAGPoB2IntegrationTester()
    
    if full_test:
        results = await tester.run_complete_integration_test()
        tester.display_test_summary(results)
        return results
    else:
        success = await tester.run_quick_integration_test()
        return {'overall_success': success, 'test_type': 'quick'}

async def main():
    """主测试函数"""
    print("🚀 RAG-PoB2集成系统测试")
    print("请选择测试模式:")
    print("1. 完整集成测试 (推荐)")
    print("2. 快速功能测试")
    
    try:
        choice = input("输入选择 (1/2): ").strip()
        
        if choice == '2':
            print("\n执行快速测试...")
            results = await run_integration_test(full_test=False)
        else:
            print("\n执行完整测试...")
            results = await run_integration_test(full_test=True)
        
        print(f"\n{'='*40}")
        print(f"测试{'成功' if results.get('overall_success') else '失败'}!")
        print(f"{'='*40}")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())