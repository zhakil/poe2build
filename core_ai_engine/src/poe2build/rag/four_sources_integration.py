"""
四大核心数据源集成RAG训练系统
基于四大核心数据源进行RAG AI训练和知识库构建

四大数据源:
1. PoE2Scout API (https://poe2scout.com) - 市场价格数据
2. PoE Ninja构筑爬虫 (https://poe.ninja/poe2/builds) - Meta趋势分析
3. Path of Building 2数据 (GitHub/本地) - 官方游戏数据和计算
4. PoE2DB数据源 (https://poe2db.tw/cn/) - 完整游戏数据库

这个模块协调四大数据源，为RAG AI提供统一的训练数据
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 导入四大核心数据源
from ..data_sources.poe2scout.api_client import get_poe2scout_client
from ..data_sources.ninja.scraper import get_ninja_scraper
from ..data_sources.pob2.data_extractor import get_pob2_extractor
from ..data_sources.poe2db.api_client import get_poe2db_client

# 导入RAG系统组件
from .data_collector import PoE2RAGDataCollector
from .vectorizer import PoE2BuildVectorizer
from .index_builder import PoE2BuildIndexBuilder
from .ai_engine import PoE2AIEngine
from .knowledge_base import PoE2KnowledgeBase

logger = logging.getLogger(__name__)


@dataclass
class FourSourcesData:
    """四大数据源的综合数据"""
    scout_data: Dict[str, Any]      # 市场价格数据
    ninja_data: Dict[str, Any]      # Meta趋势数据
    pob2_data: Dict[str, Any]       # Path of Building数据
    poe2db_data: Dict[str, Any]     # PoE2DB游戏数据
    collection_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'scout_data': self.scout_data,
            'ninja_data': self.ninja_data,
            'pob2_data': self.pob2_data,
            'poe2db_data': self.poe2db_data,
            'collection_timestamp': self.collection_timestamp.isoformat(),
            'total_build_examples': (
                len(self.ninja_data.get('popular_builds', [])) +
                len(self.scout_data.get('build_costs', []))
            ),
            'total_skills': len(self.pob2_data.get('skills', {})),
            'total_items': len(self.poe2db_data.get('items', {}))
        }


class FourSourcesRAGTrainer:
    """基于四大数据源的RAG AI训练器"""
    
    def __init__(self, enable_github_pob2: bool = True):
        """
        初始化四大数据源RAG训练器
        
        Args:
            enable_github_pob2: 是否使用GitHub的PoB2数据源
        """
        self.enable_github_pob2 = enable_github_pob2
        
        # 初始化四大数据源客户端
        self.scout_client = get_poe2scout_client()
        self.ninja_scraper = get_ninja_scraper()
        self.pob2_extractor = get_pob2_extractor()
        self.poe2db_client = get_poe2db_client()
        
        # RAG系统组件
        self.data_collector = None
        self.vectorizer = None
        self.index_builder = None
        self.ai_engine = None
        self.knowledge_base = None
        
        # 收集统计
        self.training_stats = {
            'sources_health': {},
            'data_volumes': {},
            'training_progress': {},
            'knowledge_base_stats': {}
        }
    
    async def collect_all_four_sources(self, league: str = "Rise of the Abyssal", limit: Optional[int] = None) -> FourSourcesData:
        """
        从四大数据源收集所有训练数据
        
        Args:
            league: 游戏联盟
            limit: 数据收集限制数量（可选）
            
        Returns:
            四大数据源的综合数据
        """
        logger.info("开始从四大核心数据源收集RAG训练数据")
        
        # 并发收集四大数据源
        tasks = [
            self._collect_scout_data(league),
            self._collect_ninja_data(league),
            self._collect_pob2_data(),
            self._collect_poe2db_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scout_data = results[0] if not isinstance(results[0], Exception) else {}
        ninja_data = results[1] if not isinstance(results[1], Exception) else {}
        pob2_data = results[2] if not isinstance(results[2], Exception) else {}
        poe2db_data = results[3] if not isinstance(results[3], Exception) else {}
        
        # 记录数据收集统计
        self.training_stats['data_volumes'] = {
            'scout_items': len(scout_data.get('item_prices', {})),
            'scout_builds': len(scout_data.get('build_costs', [])),
            'ninja_builds': len(ninja_data.get('popular_builds', [])),
            'ninja_skills': len(ninja_data.get('skill_stats', [])),
            'ninja_ascendancies': len(ninja_data.get('ascendancy_trends', [])),
            'pob2_skills': len(pob2_data.get('skills', {})),
            'pob2_items': len(pob2_data.get('items', {})),
            'pob2_passives': len(pob2_data.get('passives', {})),
            'poe2db_items': len(poe2db_data.get('items', [])),
            'poe2db_skills': len(poe2db_data.get('skills', []))
        }
        
        # 记录数据源健康状态
        self.training_stats['sources_health'] = {
            'scout': not isinstance(results[0], Exception),
            'ninja': not isinstance(results[1], Exception),
            'pob2': not isinstance(results[2], Exception),
            'poe2db': not isinstance(results[3], Exception)
        }
        
        combined_data = FourSourcesData(
            scout_data=scout_data,
            ninja_data=ninja_data,
            pob2_data=pob2_data,
            poe2db_data=poe2db_data,
            collection_timestamp=datetime.now()
        )
        
        logger.info(f"四大数据源收集完成，数据统计: {self.training_stats['data_volumes']}")
        return combined_data
    
    async def _collect_scout_data(self, league: str) -> Dict[str, Any]:
        """收集PoE2Scout市场价格数据"""
        logger.info("收集PoE2Scout市场数据...")
        
        try:
            # 获取常见PoE2构筑物品价格
            common_build_items = [
                "Midnight Fang", "The Last Resort", "Doryani's Fist", "Shavronne's Wrappings",
                "Pillars of Arun", "Thirst for Knowledge", "The Baron", "Replica Last Resort",
                "Invoker's Trews", "Stormweaver", "Shaper of Storms", "Sanguimancy"
            ]
            
            item_prices = {}
            build_costs = []
            
            for item_name in common_build_items:
                try:
                    prices = self.scout_client.get_item_prices(item_name, league)
                    if prices:
                        item_prices[item_name] = {
                            'chaos_price': prices[0].price_chaos,
                            'divine_price': prices[0].price_divine,
                            'confidence': prices[0].confidence,
                            'listing_count': prices[0].listing_count
                        }
                    
                    await asyncio.sleep(0.5)  # 尊重API限制
                    
                except Exception as e:
                    logger.warning(f"获取物品价格失败 {item_name}: {e}")
                    continue
            
            # 估算一些典型构筑的成本
            starter_build_items = ["The Last Resort", "Midnight Fang", "Doryani's Fist"]
            budget_build_cost = self.scout_client.get_build_cost_estimate(
                starter_build_items, league
            )
            build_costs.append({
                'build_type': 'starter',
                'items': starter_build_items,
                'cost': budget_build_cost
            })
            
            return {
                'item_prices': item_prices,
                'build_costs': build_costs,
                'currency_rates': [],  # 如果需要可以添加
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PoE2Scout数据收集失败: {e}")
            return {}
    
    async def _collect_ninja_data(self, league: str) -> Dict[str, Any]:
        """收集PoE Ninja Meta趋势数据"""
        logger.info("收集PoE Ninja Meta数据...")
        
        try:
            # 并发收集ninja的三种数据
            popular_builds = self.ninja_scraper.get_popular_builds(league, limit=100)
            skill_stats = self.ninja_scraper.get_skill_usage_stats(league)
            ascendancy_trends = self.ninja_scraper.get_ascendancy_trends(league)
            meta_summary = self.ninja_scraper.get_meta_summary(league)
            
            return {
                'popular_builds': [
                    {
                        'name': build.name,
                        'character_class': build.character_class,
                        'ascendancy': build.ascendancy,
                        'main_skill': build.main_skill,
                        'support_gems': build.support_gems,
                        'popularity_score': build.popularity_score,
                        'avg_level': build.avg_level,
                        'sample_size': build.sample_size,
                        'key_items': build.key_items,
                        'passive_keystones': build.passive_keystone
                    }
                    for build in popular_builds
                ],
                'skill_stats': [
                    {
                        'skill_name': stat.skill_name,
                        'usage_percentage': stat.usage_percentage,
                        'average_level': stat.average_level,
                        'popular_supports': stat.popular_supports,
                        'character_classes': stat.character_classes,
                        'trend': stat.trend
                    }
                    for stat in skill_stats
                ],
                'ascendancy_trends': [
                    {
                        'ascendancy': trend.ascendancy,
                        'character_class': trend.character_class,
                        'popularity_percentage': trend.popularity_percentage,
                        'average_level': trend.average_level,
                        'popular_skills': trend.popular_skills,
                        'trend': trend.trend
                    }
                    for trend in ascendancy_trends
                ],
                'meta_summary': meta_summary,
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PoE Ninja数据收集失败: {e}")
            return {}
    
    async def _collect_pob2_data(self) -> Dict[str, Any]:
        """收集Path of Building 2数据"""
        logger.info(f"收集Path of Building 2数据 (GitHub模式: {self.enable_github_pob2})...")
        
        try:
            # 设置数据源模式
            if self.enable_github_pob2:
                self.pob2_extractor.use_github = True
            
            # 收集技能宝石数据
            skills_data = self.pob2_extractor.get_skill_gems()
            skills_dict = {}
            for skill_id, skill in skills_data.items():
                skills_dict[skill_id] = {
                    'name': skill.name,
                    'internal_id': skill.internal_id,
                    'base_type': skill.base_type,
                    'tags': skill.tags,
                    'gem_type': skill.gem_type,
                    'required_level': skill.required_level,
                    'stat_text': skill.stat_text,
                    'quality_stats': skill.quality_stats,
                    'mana_cost': skill.mana_cost,
                    'damage_multiplier': skill.damage_multiplier
                }
            
            # 收集基础物品数据
            items_data = self.pob2_extractor.get_base_items()
            items_dict = {}
            for item_id, item in items_data.items():
                items_dict[item_id] = {
                    'name': item.name,
                    'internal_id': item.internal_id,
                    'base_type': item.base_type,
                    'item_class': item.item_class,
                    'tags': item.tags,
                    'implicit_mods': item.implicit_mods,
                    'requirements': item.requirements,
                    'weapon_type': item.weapon_type,
                    'armour_type': item.armour_type
                }
            
            # 收集天赋树数据
            passives_data = self.pob2_extractor.get_passive_tree()
            passives_dict = {}
            for node_id, node in passives_data.items():
                passives_dict[node_id] = {
                    'node_id': node.node_id,
                    'name': node.name,
                    'icon': node.icon,
                    'description': node.description,
                    'stats': node.stats,
                    'is_keystone': node.is_keystone,
                    'is_notable': node.is_notable,
                    'position': node.position
                }
            
            # 获取安装信息
            installation_info = self.pob2_extractor.get_installation_info()
            
            return {
                'skills': skills_dict,
                'items': items_dict,
                'passives': passives_dict,
                'installation_info': installation_info,
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Path of Building 2数据收集失败: {e}")
            return {}
    
    async def _collect_poe2db_data(self) -> Dict[str, Any]:
        """收集PoE2DB数据"""
        logger.info("收集PoE2DB游戏数据...")
        
        try:
            # 健康检查
            health = self.poe2db_client.health_check()
            if health['status'] != 'healthy':
                logger.warning(f"PoE2DB健康检查失败: {health}")
                return {}
            
            # 搜索一些常见技能和物品作为示例
            common_skills = ["Lightning Arrow", "Explosive Shot", "Ice Nova", "Bone Spear"]
            common_items = ["Midnight Fang", "The Last Resort", "Doryani's Fist"]
            
            skills_data = []
            for skill_name in common_skills:
                try:
                    skill_detail = self.poe2db_client.get_skill_detail(skill_name)
                    if skill_detail:
                        skills_data.append({
                            'name': skill_detail.name,
                            'name_cn': skill_detail.name_cn,
                            'skill_type': skill_detail.skill_type,
                            'gem_color': skill_detail.gem_color,
                            'level_requirement': skill_detail.level_requirement,
                            'mana_cost': skill_detail.mana_cost,
                            'description': skill_detail.description,
                            'tags': skill_detail.tags
                        })
                    await asyncio.sleep(1.0)  # 尊重服务器
                except Exception as e:
                    logger.warning(f"获取技能详情失败 {skill_name}: {e}")
                    continue
            
            items_data = []
            for item_name in common_items:
                try:
                    item_detail = self.poe2db_client.get_item_detail(item_name)
                    if item_detail:
                        items_data.append({
                            'name': item_detail.name,
                            'name_cn': item_detail.name_cn,
                            'item_class': item_detail.item_class,
                            'base_type': item_detail.base_type,
                            'level_requirement': item_detail.level_requirement,
                            'implicit_mods': item_detail.implicit_mods,
                            'explicit_mods': item_detail.explicit_mods,
                            'tags': item_detail.tags
                        })
                    await asyncio.sleep(1.0)  # 尊重服务器
                except Exception as e:
                    logger.warning(f"获取物品详情失败 {item_name}: {e}")
                    continue
            
            return {
                'skills': skills_data,
                'items': items_data,
                'health_status': health,
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PoE2DB数据收集失败: {e}")
            return {}
    
    async def train_rag_ai(self, four_sources_data: FourSourcesData) -> Dict[str, Any]:
        """
        基于四大数据源训练RAG AI系统
        
        Args:
            four_sources_data: 四大数据源的综合数据
            
        Returns:
            训练结果和统计信息
        """
        logger.info("开始基于四大数据源训练RAG AI系统")
        
        # 初始化RAG组件
        self.vectorizer = PoE2BuildVectorizer()
        self.index_builder = PoE2BuildIndexBuilder()
        self.knowledge_base = PoE2KnowledgeBase()
        self.ai_engine = PoE2AIEngine()
        
        training_result = {
            'training_stages': [],
            'knowledge_entries': 0,
            'vector_dimensions': 0,
            'index_size': 0,
            'training_timestamp': datetime.now().isoformat()
        }
        
        try:
            # 阶段1: 构建知识条目
            logger.info("RAG训练阶段1: 构建知识条目")
            knowledge_entries = self._build_knowledge_entries(four_sources_data)
            training_result['knowledge_entries'] = len(knowledge_entries)
            training_result['training_stages'].append('knowledge_construction')
            
            # 阶段2: 向量化知识
            logger.info("RAG训练阶段2: 向量化知识条目")
            vectorized_knowledge = []
            for entry in knowledge_entries:
                try:
                    vector = self.vectorizer.vectorize_build_text(entry['text_content'])
                    vectorized_knowledge.append({
                        'entry': entry,
                        'vector': vector,
                        'metadata': entry.get('metadata', {})
                    })
                except Exception as e:
                    logger.warning(f"向量化知识条目失败: {e}")
                    continue
            
            training_result['vector_dimensions'] = len(vectorized_knowledge[0]['vector']) if vectorized_knowledge else 0
            training_result['training_stages'].append('vectorization')
            
            # 阶段3: 构建索引
            logger.info("RAG训练阶段3: 构建向量索引")
            if vectorized_knowledge:
                vectors = [item['vector'] for item in vectorized_knowledge]
                metadata = [item['metadata'] for item in vectorized_knowledge]
                
                index = self.index_builder.build_index(vectors, metadata)
                training_result['index_size'] = len(vectors)
                training_result['training_stages'].append('index_building')
            
            # 阶段4: 训练AI引擎
            logger.info("RAG训练阶段4: 训练AI推荐引擎")
            ai_training_stats = self.ai_engine.train_on_knowledge(knowledge_entries)
            training_result['ai_training_stats'] = ai_training_stats
            training_result['training_stages'].append('ai_training')
            
            # 更新训练统计
            self.training_stats['training_progress'] = training_result
            self.training_stats['knowledge_base_stats'] = {
                'total_entries': len(knowledge_entries),
                'vector_index_size': training_result['index_size'],
                'ai_model_trained': True
            }
            
            logger.info(f"RAG AI训练完成，知识条目: {training_result['knowledge_entries']}, 索引大小: {training_result['index_size']}")
            return training_result
            
        except Exception as e:
            logger.error(f"RAG AI训练失败: {e}")
            raise
    
    def _build_knowledge_entries(self, data: FourSourcesData) -> List[Dict[str, Any]]:
        """基于四大数据源构建知识条目"""
        knowledge_entries = []
        
        # 来源1: PoE2Scout - 市场和成本知识
        for item_name, price_info in data.scout_data.get('item_prices', {}).items():
            entry = {
                'id': f"scout_item_{item_name}",
                'source': 'poe2scout',
                'type': 'item_price',
                'text_content': f"{item_name}的市场价格信息：混沌石价格{price_info['chaos_price']}，神圣石价格{price_info['divine_price']}，可信度{price_info['confidence']}，挂单数量{price_info['listing_count']}。",
                'metadata': {
                    'item_name': item_name,
                    'chaos_price': price_info['chaos_price'],
                    'divine_price': price_info['divine_price'],
                    'confidence': price_info['confidence']
                }
            }
            knowledge_entries.append(entry)
        
        # 来源2: PoE Ninja - 流行构筑知识
        for build in data.ninja_data.get('popular_builds', []):
            entry = {
                'id': f"ninja_build_{build['name']}",
                'source': 'poe_ninja',
                'type': 'popular_build',
                'text_content': f"{build['name']}是一个流行的{build['character_class']}构筑，使用{build['main_skill']}作为主技能，配合{', '.join(build['support_gems'][:3])}等辅助宝石。该构筑的流行度分数为{build['popularity_score']}，平均等级{build['avg_level']}，样本量{build['sample_size']}。",
                'metadata': {
                    'build_name': build['name'],
                    'character_class': build['character_class'],
                    'main_skill': build['main_skill'],
                    'popularity_score': build['popularity_score'],
                    'avg_level': build['avg_level']
                }
            }
            knowledge_entries.append(entry)
        
        # 来源3: Path of Building 2 - 技能和物品数据
        for skill_id, skill in data.pob2_data.get('skills', {}).items():
            entry = {
                'id': f"pob2_skill_{skill_id}",
                'source': 'path_of_building_2',
                'type': 'skill_gem',
                'text_content': f"{skill['name']}是一个{skill['gem_type']}类型的技能宝石，需要等级{skill['required_level']}，标签包括{', '.join(skill['tags'])}。",
                'metadata': {
                    'skill_name': skill['name'],
                    'gem_type': skill['gem_type'],
                    'required_level': skill['required_level'],
                    'tags': skill['tags']
                }
            }
            knowledge_entries.append(entry)
        
        # 来源4: PoE2DB - 游戏数据库信息
        for skill in data.poe2db_data.get('skills', []):
            entry = {
                'id': f"poe2db_skill_{skill['name']}",
                'source': 'poe2db',
                'type': 'skill_detail',
                'text_content': f"{skill['name']}({skill['name_cn']})是一个{skill['skill_type']}类型的技能，宝石颜色为{skill['gem_color']}，需要等级{skill['level_requirement']}。{skill['description']}",
                'metadata': {
                    'skill_name': skill['name'],
                    'skill_name_cn': skill['name_cn'],
                    'skill_type': skill['skill_type'],
                    'gem_color': skill['gem_color'],
                    'level_requirement': skill['level_requirement']
                }
            }
            knowledge_entries.append(entry)
        
        logger.info(f"基于四大数据源构建了 {len(knowledge_entries)} 个知识条目")
        return knowledge_entries
    
    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计信息"""
        return self.training_stats.copy()
    
    async def health_check_all_sources(self) -> Dict[str, Any]:
        """检查四大数据源的健康状态"""
        health_status = {
            'overall_health': 'unknown',
            'sources': {},
            'check_timestamp': datetime.now().isoformat()
        }
        
        # 检查PoE2Scout
        try:
            # PoE2Scout没有健康检查方法，尝试简单操作
            test_prices = self.scout_client.get_item_prices("Midnight Fang", "Rise of the Abyssal")
            health_status['sources']['poe2scout'] = {
                'status': 'healthy' if test_prices else 'degraded',
                'available': True
            }
        except Exception as e:
            health_status['sources']['poe2scout'] = {
                'status': 'unhealthy',
                'error': str(e),
                'available': False
            }
        
        # 检查PoE Ninja
        try:
            # Ninja也没有健康检查，尝试获取摘要
            test_summary = self.ninja_scraper.get_meta_summary("Standard")
            health_status['sources']['poe_ninja'] = {
                'status': 'healthy' if test_summary else 'degraded',
                'available': True
            }
        except Exception as e:
            health_status['sources']['poe_ninja'] = {
                'status': 'unhealthy', 
                'error': str(e),
                'available': False
            }
        
        # 检查PoB2
        try:
            pob2_info = self.pob2_extractor.get_installation_info()
            available = pob2_info.get('available', False)
            health_status['sources']['path_of_building_2'] = {
                'status': 'healthy' if available else 'degraded',
                'available': available,
                'source_type': pob2_info.get('source', 'unknown')
            }
        except Exception as e:
            health_status['sources']['path_of_building_2'] = {
                'status': 'unhealthy',
                'error': str(e),
                'available': False
            }
        
        # 检查PoE2DB
        try:
            poe2db_health = self.poe2db_client.health_check()
            health_status['sources']['poe2db'] = poe2db_health
        except Exception as e:
            health_status['sources']['poe2db'] = {
                'status': 'unhealthy',
                'error': str(e),
                'available': False
            }
        
        # 计算整体健康状态
        healthy_sources = sum(1 for source in health_status['sources'].values() 
                            if source.get('status') == 'healthy')
        total_sources = len(health_status['sources'])
        
        if healthy_sources >= 3:
            health_status['overall_health'] = 'healthy'
        elif healthy_sources >= 2:
            health_status['overall_health'] = 'degraded'
        else:
            health_status['overall_health'] = 'critical'
        
        health_status['healthy_sources_count'] = healthy_sources
        health_status['total_sources_count'] = total_sources
        
        return health_status


async def train_rag_with_four_sources():
    """运行基于四大数据源的RAG训练示例"""
    trainer = FourSourcesRAGTrainer(enable_github_pob2=True)
    
    try:
        # 健康检查
        print("=== 四大数据源健康检查 ===")
        health = await trainer.health_check_all_sources()
        print(f"整体健康状态: {health['overall_health']}")
        print(f"健康数据源: {health['healthy_sources_count']}/{health['total_sources_count']}")
        
        for source_name, source_health in health['sources'].items():
            status = source_health['status']
            print(f"  {source_name}: {status}")
        
        # 收集四大数据源数据
        print("\n=== 收集四大数据源数据 ===")
        four_sources_data = await trainer.collect_all_four_sources("Standard")
        
        print("数据收集完成:")
        data_stats = trainer.get_training_stats()['data_volumes']
        print(f"  PoE2Scout: {data_stats['scout_items']} 物品, {data_stats['scout_builds']} 构筑成本")
        print(f"  PoE Ninja: {data_stats['ninja_builds']} 构筑, {data_stats['ninja_skills']} 技能")
        print(f"  PoB2: {data_stats['pob2_skills']} 技能, {data_stats['pob2_items']} 物品")
        print(f"  PoE2DB: {data_stats['poe2db_items']} 物品, {data_stats['poe2db_skills']} 技能")
        
        # RAG AI训练
        print("\n=== RAG AI训练 ===")
        training_result = await trainer.train_rag_ai(four_sources_data)
        
        print(f"训练完成:")
        print(f"  知识条目: {training_result['knowledge_entries']}")
        print(f"  向量维度: {training_result['vector_dimensions']}")
        print(f"  索引大小: {training_result['index_size']}")
        print(f"  训练阶段: {', '.join(training_result['training_stages'])}")
        
        # 保存结果
        output_data = {
            'four_sources_data': four_sources_data.to_dict(),
            'training_result': training_result,
            'training_stats': trainer.get_training_stats(),
            'health_status': health
        }
        
        with open('four_sources_rag_training_result.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n=== 训练结果已保存到 four_sources_rag_training_result.json ===")
        return output_data
        
    except Exception as e:
        print(f"四大数据源RAG训练失败: {e}")
        raise


if __name__ == "__main__":
    # 运行基于四大数据源的RAG训练
    asyncio.run(train_rag_with_four_sources())