"""
集成RAG数据收集系统 - 统一的数据收集、预处理和输出接口

这个模块提供了一个统一的接口来协调所有RAG数据收集组件:
- 数据收集器 (API和爬虫)
- 数据预处理器 (清洗、去重、质量提升)
- 弹性系统集成 (circuit breaker, retry, rate limiting)
- 输出管理 (保存、加载、导出)

使用方式:
```python
async with IntegratedRAGCollector() as collector:
    rag_data = await collector.collect_and_process_all_data()
    await collector.save_data("rag_data.json")
```
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .models import RAGDataModel, DataQuality
from .data_collector import PoE2RAGDataCollector
from .build_scraper import PoE2BuildScraper
from .data_preprocessor import PoE2DataPreprocessor
from ..resilience import ResilientService

logger = logging.getLogger(__name__)

class IntegratedRAGCollector:
    """
    集成RAG数据收集系统
    
    提供统一的接口来协调所有数据收集和处理组件，
    包含完整的错误处理、监控和输出管理功能。
    """
    
    def __init__(self,
                 output_dir: str = "data/rag",
                 enable_web_scraping: bool = False,
                 enable_preprocessing: bool = True,
                 enable_resilience: bool = True,
                 max_builds: int = 1000,
                 quality_threshold: DataQuality = DataQuality.MEDIUM):
        """
        初始化集成收集器
        
        Args:
            output_dir: 输出目录
            enable_web_scraping: 是否启用Web爬取(除了API收集)
            enable_preprocessing: 是否启用数据预处理
            enable_resilience: 是否启用弹性系统
            max_builds: 最大收集构筑数量
            quality_threshold: 最低数据质量要求
        """
        self.output_dir = Path(output_dir)
        self.enable_web_scraping = enable_web_scraping
        self.enable_preprocessing = enable_preprocessing  
        self.enable_resilience = enable_resilience
        self.max_builds = max_builds
        self.quality_threshold = quality_threshold
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 组件初始化
        self.api_collector: Optional[PoE2RAGDataCollector] = None
        self.web_scraper: Optional[PoE2BuildScraper] = None
        self.data_preprocessor: Optional[PoE2DataPreprocessor] = None
        
        # 收集统计
        self.collection_stats = {
            'session_start_time': None,
            'session_end_time': None,
            'total_builds_collected': 0,
            'api_builds': 0,
            'web_builds': 0,
            'final_builds': 0,
            'processing_stages': {},
            'errors': []
        }
        
        # 最后收集的数据
        self.last_collected_data: Optional[RAGDataModel] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize_components()
        self.collection_stats['session_start_time'] = datetime.now()
        logger.info("[Integrated RAG] 集成收集器已初始化")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._cleanup_components()
        self.collection_stats['session_end_time'] = datetime.now()
        logger.info("[Integrated RAG] 集成收集器已清理")
    
    async def _initialize_components(self):
        """初始化所有组件"""
        try:
            # 初始化API收集器
            self.api_collector = PoE2RAGDataCollector(
                max_concurrent_requests=2,
                enable_resilience=self.enable_resilience
            )
            await self.api_collector._initialize_session()
            
            # 初始化Web爬虫(如果启用)
            if self.enable_web_scraping:
                self.web_scraper = PoE2BuildScraper(
                    max_concurrent=1,
                    request_delay=2.0,
                    enable_resilience=self.enable_resilience
                )
                await self.web_scraper._initialize_session()
            
            # 初始化数据预处理器(如果启用)
            if self.enable_preprocessing:
                self.data_preprocessor = PoE2DataPreprocessor(
                    enable_anomaly_detection=True,
                    enable_missing_value_imputation=True,
                    enable_feature_engineering=True,
                    similarity_threshold=0.85
                )
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 组件初始化失败: {e}")
            raise
    
    async def _cleanup_components(self):
        """清理所有组件"""
        try:
            if self.api_collector:
                await self.api_collector._close_session()
            
            if self.web_scraper:
                await self.web_scraper._close_session()
            
        except Exception as e:
            logger.warning(f"[Integrated RAG] 组件清理警告: {e}")
    
    async def collect_and_process_all_data(self,
                                         league: str = "Standard",
                                         include_prices: bool = True,
                                         save_intermediate: bool = True) -> RAGDataModel:
        """
        收集和处理所有RAG数据
        
        Args:
            league: 游戏联赛
            include_prices: 是否包含价格信息
            save_intermediate: 是否保存中间结果
            
        Returns:
            最终处理后的RAG数据
        """
        logger.info("[Integrated RAG] 开始完整的RAG数据收集和处理流程")
        
        try:
            # 阶段1: API数据收集
            api_data = await self._collect_api_data(league, include_prices)
            self.collection_stats['api_builds'] = len(api_data.builds)
            self.collection_stats['processing_stages']['api_collection'] = 'completed'
            
            if save_intermediate:
                await self.save_data(api_data, "api_raw_data.json")
            
            # 阶段2: Web爬取(如果启用)
            web_data = None
            if self.enable_web_scraping:
                web_data = await self._collect_web_data()
                self.collection_stats['web_builds'] = len(web_data.builds) if web_data else 0
                self.collection_stats['processing_stages']['web_scraping'] = 'completed'
                
                if save_intermediate and web_data:
                    await self.save_data(web_data, "web_raw_data.json")
            
            # 阶段3: 数据合并
            combined_data = await self._combine_data_sources(api_data, web_data)
            self.collection_stats['total_builds_collected'] = len(combined_data.builds)
            self.collection_stats['processing_stages']['data_combination'] = 'completed'
            
            if save_intermediate:
                await self.save_data(combined_data, "combined_raw_data.json")
            
            # 阶段4: 数据预处理(如果启用)
            final_data = combined_data
            if self.enable_preprocessing:
                final_data = await self._preprocess_data(combined_data)
                self.collection_stats['processing_stages']['preprocessing'] = 'completed'
                
                if save_intermediate:
                    await self.save_data(final_data, "preprocessed_data.json")
            
            # 阶段5: 质量过滤
            filtered_data = await self._apply_quality_filter(final_data)
            self.collection_stats['final_builds'] = len(filtered_data.builds)
            self.collection_stats['processing_stages']['quality_filtering'] = 'completed'
            
            # 更新最终数据的元数据
            filtered_data.collection_metadata.update({
                'integrated_collection': True,
                'collection_stages': list(self.collection_stats['processing_stages'].keys()),
                'final_processing_timestamp': datetime.now(),
                'quality_threshold': self.quality_threshold.value
            })
            
            self.last_collected_data = filtered_data
            
            logger.info(f"[Integrated RAG] 数据收集完成，最终获得 {len(filtered_data.builds)} 个高质量构筑")
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 数据收集过程失败: {e}")
            self.collection_stats['errors'].append({
                'timestamp': datetime.now(),
                'error': str(e),
                'stage': 'collect_and_process_all_data'
            })
            raise
    
    async def _collect_api_data(self, league: str, include_prices: bool) -> RAGDataModel:
        """收集API数据"""
        logger.info("[Integrated RAG] 开始API数据收集")
        
        try:
            if not self.api_collector:
                raise RuntimeError("API收集器未初始化")
            
            api_data = await self.api_collector.collect_comprehensive_build_data(
                league=league,
                limit=self.max_builds,
                include_prices=include_prices,
                quality_filter=DataQuality.LOW  # 初始阶段接受所有数据
            )
            
            logger.info(f"[Integrated RAG] API数据收集完成，获得 {len(api_data.builds)} 个构筑")
            return api_data
            
        except Exception as e:
            logger.error(f"[Integrated RAG] API数据收集失败: {e}")
            self.collection_stats['errors'].append({
                'timestamp': datetime.now(),
                'error': str(e),
                'stage': 'api_collection'
            })
            raise
    
    async def _collect_web_data(self) -> Optional[RAGDataModel]:
        """收集Web爬取数据"""
        if not self.web_scraper:
            logger.warning("[Integrated RAG] Web爬虫未启用")
            return None
        
        logger.info("[Integrated RAG] 开始Web数据爬取")
        
        try:
            # 只使用poe.ninja的前端接口作为补充
            web_data = await self.web_scraper.scrape_builds_from_web(
                target_names=['poe_ninja_web'],
                max_builds=min(200, self.max_builds // 2),  # Web数据作为补充
                include_guides=False
            )
            
            logger.info(f"[Integrated RAG] Web数据爬取完成，获得 {len(web_data.builds)} 个构筑")
            return web_data
            
        except Exception as e:
            logger.error(f"[Integrated RAG] Web数据爬取失败: {e}")
            self.collection_stats['errors'].append({
                'timestamp': datetime.now(),
                'error': str(e),
                'stage': 'web_scraping'
            })
            return None
    
    async def _combine_data_sources(self, 
                                  api_data: RAGDataModel,
                                  web_data: Optional[RAGDataModel]) -> RAGDataModel:
        """合并多个数据源"""
        logger.info("[Integrated RAG] 开始合并数据源")
        
        # 以API数据为基础
        combined_builds = api_data.builds.copy()
        
        # 合并Web数据(如果有)
        if web_data and web_data.builds:
            # 简单合并，去重在预处理阶段处理
            combined_builds.extend(web_data.builds)
            logger.info(f"[Integrated RAG] 合并了 {len(web_data.builds)} 个Web构筑")
        
        # 创建合并的元数据
        combined_metadata = api_data.collection_metadata.copy()
        combined_metadata.update({
            'data_sources_combined': ['api'],
            'combination_timestamp': datetime.now()
        })
        
        if web_data:
            combined_metadata['data_sources_combined'].append('web')
            combined_metadata.update({
                'web_metadata': web_data.collection_metadata
            })
        
        combined_data = RAGDataModel(
            builds=combined_builds,
            collection_metadata=combined_metadata,
            processing_stats=api_data.processing_stats.copy()
        )
        
        logger.info(f"[Integrated RAG] 数据源合并完成，总计 {len(combined_builds)} 个构筑")
        return combined_data
    
    async def _preprocess_data(self, raw_data: RAGDataModel) -> RAGDataModel:
        """预处理数据"""
        if not self.data_preprocessor:
            logger.warning("[Integrated RAG] 数据预处理器未启用")
            return raw_data
        
        logger.info("[Integrated RAG] 开始数据预处理")
        
        try:
            processed_data = await self.data_preprocessor.preprocess_rag_data(raw_data)
            
            # 添加预处理统计到收集统计
            preprocessing_stats = self.data_preprocessor.get_preprocessing_stats()
            self.collection_stats['processing_stages']['preprocessing_stats'] = preprocessing_stats
            
            logger.info(f"[Integrated RAG] 数据预处理完成，处理后剩余 {len(processed_data.builds)} 个构筑")
            return processed_data
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 数据预处理失败: {e}")
            self.collection_stats['errors'].append({
                'timestamp': datetime.now(),
                'error': str(e),
                'stage': 'preprocessing'
            })
            # 预处理失败时返回原始数据
            return raw_data
    
    async def _apply_quality_filter(self, data: RAGDataModel) -> RAGDataModel:
        """应用质量过滤"""
        logger.info(f"[Integrated RAG] 应用质量过滤 (阈值: {self.quality_threshold.value})")
        
        filtered_data = data.filter_by_quality(self.quality_threshold)
        
        # 限制最终数据量
        if len(filtered_data.builds) > self.max_builds:
            # 按成功分数排序，保留最好的构筑
            sorted_builds = sorted(
                filtered_data.builds,
                key=lambda b: b.success_metrics.overall_score(),
                reverse=True
            )
            filtered_data.builds = sorted_builds[:self.max_builds]
            
            logger.info(f"[Integrated RAG] 数据量限制应用，保留前 {self.max_builds} 个最佳构筑")
        
        filtered_data.collection_metadata['quality_filtering_applied'] = True
        filtered_data.collection_metadata['final_build_count'] = len(filtered_data.builds)
        
        return filtered_data
    
    async def save_data(self, data: RAGDataModel, filename: str) -> str:
        """保存RAG数据到文件"""
        filepath = self.output_dir / filename
        
        try:
            # 保存为JSON格式
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data.to_json())
            
            logger.info(f"[Integrated RAG] 数据已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 保存数据失败 {filepath}: {e}")
            raise
    
    async def load_data(self, filename: str) -> RAGDataModel:
        """从文件加载RAG数据"""
        filepath = self.output_dir / filename
        
        try:
            if not filepath.exists():
                raise FileNotFoundError(f"数据文件不存在: {filepath}")
            
            data = RAGDataModel.load_from_file(str(filepath))
            logger.info(f"[Integrated RAG] 数据已从 {filepath} 加载，包含 {len(data.builds)} 个构筑")
            return data
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 加载数据失败 {filepath}: {e}")
            raise
    
    async def export_summary_report(self, output_file: str = "collection_report.json") -> str:
        """导出收集摘要报告"""
        report = {
            'collection_summary': self.collection_stats.copy(),
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'output_dir': str(self.output_dir),
                'enable_web_scraping': self.enable_web_scraping,
                'enable_preprocessing': self.enable_preprocessing,
                'enable_resilience': self.enable_resilience,
                'max_builds': self.max_builds,
                'quality_threshold': self.quality_threshold.value
            }
        }
        
        # 添加最新数据的统计信息
        if self.last_collected_data:
            report['data_statistics'] = self.last_collected_data.get_stats()
        
        # 计算会话时长
        if (self.collection_stats['session_start_time'] and 
            self.collection_stats['session_end_time']):
            duration = (self.collection_stats['session_end_time'] - 
                       self.collection_stats['session_start_time'])
            report['collection_summary']['session_duration_seconds'] = duration.total_seconds()
        
        # 保存报告
        report_path = self.output_dir / output_file
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"[Integrated RAG] 收集报告已保存到: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"[Integrated RAG] 保存报告失败: {e}")
            raise
    
    def get_collection_status(self) -> Dict[str, Any]:
        """获取收集状态信息"""
        status = {
            'session_active': self.collection_stats['session_start_time'] is not None,
            'components_initialized': {
                'api_collector': self.api_collector is not None,
                'web_scraper': self.web_scraper is not None,
                'data_preprocessor': self.data_preprocessor is not None
            },
            'last_collection_stats': self.collection_stats,
            'output_directory': str(self.output_dir),
            'last_data_available': self.last_collected_data is not None
        }
        
        if self.last_collected_data:
            status['last_data_summary'] = {
                'build_count': len(self.last_collected_data.builds),
                'collection_timestamp': self.last_collected_data.collection_metadata.get(
                    'final_processing_timestamp'
                )
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        health = {
            'integrated_collector_status': 'healthy',
            'output_directory_accessible': self.output_dir.exists() and os.access(self.output_dir, os.W_OK),
            'components_health': {}
        }
        
        # 检查各个组件的健康状态
        try:
            if self.api_collector:
                health['components_health']['api_collector'] = await self.api_collector.health_check()
        except Exception as e:
            health['components_health']['api_collector'] = {'status': 'error', 'error': str(e)}
        
        try:
            if self.web_scraper:
                health['components_health']['web_scraper'] = await self.web_scraper.health_check()
        except Exception as e:
            health['components_health']['web_scraper'] = {'status': 'error', 'error': str(e)}
        
        # 检查数据预处理器(没有异步健康检查)
        if self.data_preprocessor:
            health['components_health']['data_preprocessor'] = {
                'status': 'healthy',
                'configuration': {
                    'anomaly_detection': self.data_preprocessor.enable_anomaly_detection,
                    'missing_value_imputation': self.data_preprocessor.enable_missing_value_imputation,
                    'feature_engineering': self.data_preprocessor.enable_feature_engineering
                }
            }
        
        return health

# 使用示例和测试函数
async def run_integrated_collection_example():
    """运行集成数据收集示例"""
    
    # 配置集成收集器
    async with IntegratedRAGCollector(
        output_dir="data/rag_example",
        enable_web_scraping=False,  # 测试时禁用Web爬取
        enable_preprocessing=True,
        enable_resilience=True,
        max_builds=100,  # 测试时使用较小数量
        quality_threshold=DataQuality.LOW
    ) as collector:
        
        try:
            # 健康检查
            print("=== 系统健康检查 ===")
            health = await collector.health_check()
            print(f"集成收集器状态: {health['integrated_collector_status']}")
            print(f"输出目录可访问: {health['output_directory_accessible']}")
            
            # 执行完整的数据收集和处理
            print("\n=== 开始完整数据收集流程 ===")
            final_data = await collector.collect_and_process_all_data(
                league="Standard",
                include_prices=False,  # 测试时跳过价格采集
                save_intermediate=True
            )
            
            # 保存最终数据
            final_file = await collector.save_data(final_data, "final_rag_data.json")
            print(f"最终数据已保存: {final_file}")
            
            # 生成收集报告
            report_file = await collector.export_summary_report()
            print(f"收集报告已生成: {report_file}")
            
            # 显示结果摘要
            print(f"\n=== 收集结果摘要 ===")
            stats = final_data.get_stats()
            print(f"最终构筑数量: {stats['total_builds']}")
            print(f"职业分布: {stats['classes']}")
            print(f"主要技能分布: {dict(list(stats['main_skills'].items())[:5])}")
            
            # 显示收集状态
            status = collector.get_collection_status()
            print(f"\n=== 收集统计 ===")
            print(f"API构筑: {status['last_collection_stats']['api_builds']}")
            print(f"Web构筑: {status['last_collection_stats']['web_builds']}")
            print(f"最终构筑: {status['last_collection_stats']['final_builds']}")
            print(f"处理阶段: {list(status['last_collection_stats']['processing_stages'].keys())}")
            
            if status['last_collection_stats']['errors']:
                print(f"遇到错误: {len(status['last_collection_stats']['errors'])}")
                for error in status['last_collection_stats']['errors']:
                    print(f"  - {error['stage']}: {error['error']}")
            
            return final_data
            
        except Exception as e:
            print(f"数据收集失败: {e}")
            raise

if __name__ == "__main__":
    # 运行示例
    asyncio.run(run_integrated_collection_example())