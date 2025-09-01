"""
RAG数据收集系统测试脚本

这个脚本用于测试新实现的RAG数据收集系统的各个组件：
1. 数据模型验证
2. 数据收集器测试
3. 数据预处理器测试  
4. 集成收集器测试
5. 弹性系统验证

运行方法:
python test_rag_system.py
"""

import asyncio
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_test.log')
    ]
)

logger = logging.getLogger(__name__)

# 导入RAG系统组件
try:
    from src.poe2build.rag import (
        PoE2BuildData,
        RAGDataModel,
        SuccessMetrics,
        SkillGemSetup,
        ItemInfo,
        OffensiveStats,
        DefensiveStats,
        BuildGoal,
        DataQuality,
        PoE2RAGDataCollector,
        PoE2DataPreprocessor
    )
    from src.poe2build.rag.integrated_collector import IntegratedRAGCollector
    logger.info("RAG系统组件导入成功")
except ImportError as e:
    logger.error(f"导入RAG组件失败: {e}")
    logger.error("请确保项目结构正确且所有依赖已安装")
    exit(1)

class RAGSystemTester:
    """RAG系统测试器"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.test_results['failed_tests'] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })
    
    def test_data_models(self):
        """测试数据模型"""
        logger.info("=== 测试数据模型 ===")
        
        try:
            # 测试PoE2BuildData创建
            build = PoE2BuildData(
                character_name="Test Ranger",
                character_class="Ranger",
                ascendancy="Deadeye", 
                level=85,
                main_skill_setup=SkillGemSetup(
                    main_skill="Lightning Arrow",
                    support_gems=["Pierce", "Lightning Penetration", "Added Lightning Damage"]
                ),
                offensive_stats=OffensiveStats(dps=1500000, critical_chance=75.0),
                defensive_stats=DefensiveStats(life=6000, energy_shield=0),
                total_cost=12.5,
                build_goal=BuildGoal.CLEAR_SPEED,
                data_quality=DataQuality.HIGH
            )
            
            self.log_test_result("数据模型创建", True)
            
            # 测试自动生成的字段
            assert build.build_description != "", "构筑描述应该自动生成"
            assert len(build.tags) > 0, "标签应该自动生成"
            assert build.similarity_hash != "", "相似度哈希应该自动生成"
            
            self.log_test_result("自动字段生成", True)
            
            # 测试相似度计算
            similar_build = PoE2BuildData(
                character_class="Ranger",
                ascendancy="Deadeye",
                main_skill_setup=SkillGemSetup(main_skill="Lightning Arrow"),
                build_goal=BuildGoal.CLEAR_SPEED
            )
            
            similarity = build.calculate_similarity_score(similar_build)
            assert similarity > 0.5, f"相似构筑的相似度应该较高，实际: {similarity}"
            
            self.log_test_result("相似度计算", True)
            
            # 测试RAGDataModel
            rag_data = RAGDataModel(builds=[build, similar_build])
            stats = rag_data.get_stats()
            
            assert stats['total_builds'] == 2, "构筑计数错误"
            assert 'Ranger' in stats['classes'], "职业统计错误"
            
            self.log_test_result("RAGDataModel功能", True)
            
            # 测试去重功能
            unique_data = rag_data.get_unique_builds(similarity_threshold=0.8)
            assert len(unique_data.builds) <= len(rag_data.builds), "去重后构筑数应该不增加"
            
            self.log_test_result("去重功能", True)
            
        except Exception as e:
            self.log_test_result("数据模型测试", False, str(e))
            logger.error(f"数据模型测试异常: {traceback.format_exc()}")
    
    async def test_data_collector(self):
        """测试数据收集器"""
        logger.info("=== 测试数据收集器 ===")
        
        try:
            # 创建收集器实例
            async with PoE2RAGDataCollector(
                max_concurrent_requests=1,
                enable_resilience=False  # 测试时简化配置
            ) as collector:
                
                # 测试健康检查
                health = await collector.health_check()
                assert isinstance(health, dict), "健康检查应返回字典"
                
                self.log_test_result("数据收集器健康检查", True)
                
                # 测试小规模数据收集
                try:
                    rag_data = await collector.collect_comprehensive_build_data(
                        league="Standard",
                        limit=10,  # 很小的测试数量
                        include_prices=False,  # 跳过价格采集加快测试
                        quality_filter=DataQuality.LOW
                    )
                    
                    self.log_test_result("小规模数据收集", True, f"收集到 {len(rag_data.builds)} 个构筑")
                    
                    # 验证收集的数据
                    if len(rag_data.builds) > 0:
                        first_build = rag_data.builds[0]
                        assert isinstance(first_build, PoE2BuildData), "收集的数据应该是PoE2BuildData类型"
                        assert first_build.character_class != "", "角色职业不应为空"
                        
                        self.log_test_result("收集数据验证", True)
                    else:
                        self.log_test_result("收集数据验证", False, "未收集到任何数据")
                
                except Exception as e:
                    self.log_test_result("数据收集功能", False, f"收集失败: {str(e)}")
                
        except Exception as e:
            self.log_test_result("数据收集器测试", False, str(e))
            logger.error(f"数据收集器测试异常: {traceback.format_exc()}")
    
    async def test_data_preprocessor(self):
        """测试数据预处理器"""
        logger.info("=== 测试数据预处理器 ===")
        
        try:
            # 创建测试数据
            test_builds = [
                # 正常构筑
                PoE2BuildData(
                    character_name="Normal Build",
                    character_class="Ranger",
                    level=85,
                    main_skill_setup=SkillGemSetup(main_skill="Lightning Arrow"),
                    offensive_stats=OffensiveStats(dps=1000000),
                    defensive_stats=DefensiveStats(life=5000),
                    data_quality=DataQuality.MEDIUM
                ),
                # 重复构筑
                PoE2BuildData(
                    character_name="Similar Build",
                    character_class="Ranger",
                    level=87,
                    main_skill_setup=SkillGemSetup(main_skill="Lightning Arrow"),
                    offensive_stats=OffensiveStats(dps=1100000),
                    defensive_stats=DefensiveStats(life=5200),
                    data_quality=DataQuality.MEDIUM
                ),
                # 异常构筑
                PoE2BuildData(
                    character_name="Anomaly Build",
                    character_class="Witch",
                    level=150,  # 异常等级
                    main_skill_setup=SkillGemSetup(main_skill="Fireball"),
                    offensive_stats=OffensiveStats(dps=0),  # 缺失DPS
                    defensive_stats=DefensiveStats(life=0),  # 缺失生命
                    data_quality=DataQuality.LOW
                ),
                # 缺失数据构筑
                PoE2BuildData(
                    character_name="Incomplete Build",
                    character_class="Monk",
                    level=90,
                    main_skill_setup=SkillGemSetup(main_skill="Spirit Wave"),
                    offensive_stats=OffensiveStats(dps=800000),
                    defensive_stats=DefensiveStats(life=0),  # 缺失生命值
                    data_quality=DataQuality.LOW
                )
            ]
            
            test_data = RAGDataModel(
                builds=test_builds,
                collection_metadata={'test_source': 'preprocessor_test'}
            )
            
            # 创建预处理器
            preprocessor = PoE2DataPreprocessor(
                enable_anomaly_detection=True,
                enable_missing_value_imputation=True,
                enable_feature_engineering=True,
                similarity_threshold=0.8
            )
            
            # 执行预处理
            processed_data = await preprocessor.preprocess_rag_data(test_data)
            
            self.log_test_result("数据预处理执行", True, 
                               f"输入: {len(test_data.builds)}, 输出: {len(processed_data.builds)}")
            
            # 验证预处理效果
            stats = preprocessor.get_preprocessing_stats()
            
            # 应该检测到去重
            if stats['duplicates_removed'] > 0:
                self.log_test_result("去重检测", True, f"移除 {stats['duplicates_removed']} 个重复")
            
            # 应该检测到异常值
            if stats['anomalies_detected'] > 0:
                self.log_test_result("异常值检测", True, f"检测 {stats['anomalies_detected']} 个异常")
            
            # 应该进行缺失值插值
            if stats['missing_values_imputed'] > 0:
                self.log_test_result("缺失值插值", True, f"插值 {stats['missing_values_imputed']} 个缺失值")
            
            # 验证处理后的数据质量
            processed_builds = processed_data.builds
            if len(processed_builds) > 0:
                quality_improved = any(
                    build.data_quality != DataQuality.LOW 
                    for build in processed_builds
                )
                if quality_improved:
                    self.log_test_result("数据质量提升", True)
                else:
                    self.log_test_result("数据质量提升", False, "未发现质量提升")
            
            # 验证特征工程
            enhanced_features = any(
                len(build.tags) > 3 for build in processed_builds
            )
            if enhanced_features:
                self.log_test_result("特征工程", True, "标签和特征得到增强")
            
        except Exception as e:
            self.log_test_result("数据预处理器测试", False, str(e))
            logger.error(f"数据预处理器测试异常: {traceback.format_exc()}")
    
    async def test_integrated_collector(self):
        """测试集成收集器"""
        logger.info("=== 测试集成收集器 ===")
        
        # 创建测试输出目录
        test_output_dir = Path("test_data/rag_integration_test")
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            async with IntegratedRAGCollector(
                output_dir=str(test_output_dir),
                enable_web_scraping=False,  # 测试时禁用
                enable_preprocessing=True,
                enable_resilience=False,  # 测试时简化
                max_builds=20,  # 小数量测试
                quality_threshold=DataQuality.LOW
            ) as collector:
                
                # 健康检查
                health = await collector.health_check()
                assert health['integrated_collector_status'] == 'healthy', "集成收集器应该健康"
                
                self.log_test_result("集成收集器健康检查", True)
                
                # 获取状态
                status = collector.get_collection_status()
                assert status['session_active'], "会话应该处于活跃状态"
                
                self.log_test_result("状态获取", True)
                
                try:
                    # 执行小规模收集测试
                    final_data = await collector.collect_and_process_all_data(
                        league="Standard",
                        include_prices=False,
                        save_intermediate=False  # 测试时不保存中间结果
                    )
                    
                    self.log_test_result("集成数据收集", True, 
                                       f"收集到 {len(final_data.builds)} 个构筑")
                    
                    # 测试数据保存
                    if len(final_data.builds) > 0:
                        save_path = await collector.save_data(final_data, "test_final_data.json")
                        assert Path(save_path).exists(), "保存的文件应该存在"
                        
                        self.log_test_result("数据保存", True)
                        
                        # 测试数据加载
                        loaded_data = await collector.load_data("test_final_data.json")
                        assert len(loaded_data.builds) == len(final_data.builds), "加载的数据量应该匹配"
                        
                        self.log_test_result("数据加载", True)
                    
                    # 测试报告生成
                    report_path = await collector.export_summary_report("test_report.json")
                    assert Path(report_path).exists(), "报告文件应该存在"
                    
                    self.log_test_result("报告生成", True)
                    
                except Exception as e:
                    self.log_test_result("集成收集功能", False, f"收集失败: {str(e)}")
                    logger.warning(f"集成收集测试警告: {e}")
                    # 不立即失败，继续其他测试
                
        except Exception as e:
            self.log_test_result("集成收集器测试", False, str(e))
            logger.error(f"集成收集器测试异常: {traceback.format_exc()}")
        
        finally:
            # 清理测试文件
            try:
                import shutil
                if test_output_dir.exists():
                    shutil.rmtree(test_output_dir)
                    logger.info("测试文件已清理")
            except Exception as e:
                logger.warning(f"清理测试文件失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始RAG系统综合测试")
        
        # 运行各项测试
        self.test_data_models()
        await self.test_data_collector()
        await self.test_data_preprocessor()
        await self.test_integrated_collector()
        
        # 完成测试
        self.test_results['end_time'] = datetime.now()
        duration = self.test_results['end_time'] - self.test_results['start_time']
        
        # 输出测试结果
        logger.info("=" * 50)
        logger.info("🎯 RAG系统测试完成")
        logger.info(f"总测试数: {self.test_results['total_tests']}")
        logger.info(f"通过测试: {self.test_results['passed_tests']} ✅")
        logger.info(f"失败测试: {self.test_results['failed_tests']} ❌")
        logger.info(f"成功率: {self.test_results['passed_tests'] / self.test_results['total_tests'] * 100:.1f}%")
        logger.info(f"测试耗时: {duration.total_seconds():.2f} 秒")
        
        # 保存详细测试报告
        report = {
            'test_summary': self.test_results,
            'system_info': {
                'test_time': datetime.now().isoformat(),
                'python_version': f"{__import__('sys').version}",
                'test_environment': 'development'
            }
        }
        
        try:
            with open('rag_test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            logger.info("📊 详细测试报告已保存到: rag_test_report.json")
        except Exception as e:
            logger.warning(f"保存测试报告失败: {e}")
        
        # 返回测试是否整体成功
        return self.test_results['failed_tests'] == 0

async def main():
    """主测试函数"""
    tester = RAGSystemTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("🎉 所有测试通过！RAG系统运行正常")
            exit(0)
        else:
            logger.error("⚠️  部分测试失败，请检查错误日志")
            exit(1)
            
    except Exception as e:
        logger.error(f"测试过程异常: {e}")
        logger.error(traceback.format_exc())
        exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🔬 PoE2 RAG数据收集系统测试")
    print("=" * 60)
    print()
    
    asyncio.run(main())