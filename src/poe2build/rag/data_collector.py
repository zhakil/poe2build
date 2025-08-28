"""ninja.poe2 RAG数据采集器"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging

from ..data_sources.ninja_scraper import NinjaPoE2Scraper
from ..models.build import PoE2Build
from ..models.characters import PoE2CharacterClass


@dataclass
class RAGBuildData:
    """RAG构筑数据结构"""
    build_id: str
    build: PoE2Build
    description: str  # 生成的文本描述
    tags: List[str] = field(default_factory=list)
    popularity_score: float = 0.0
    last_seen: datetime = field(default_factory=datetime.now)
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'build_id': self.build_id,
            'build': self.build.to_dict(),
            'description': self.description,
            'tags': self.tags,
            'popularity_score': self.popularity_score,
            'last_seen': self.last_seen.isoformat(),
            'source_metadata': self.source_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGBuildData':
        from ..models.build import PoE2Build
        return cls(
            build_id=data['build_id'],
            build=PoE2Build.from_dict(data['build']),
            description=data['description'],
            tags=data.get('tags', []),
            popularity_score=data.get('popularity_score', 0.0),
            last_seen=datetime.fromisoformat(data.get('last_seen', datetime.now().isoformat())),
            source_metadata=data.get('source_metadata', {})
        )


@dataclass
class CollectionStats:
    """采集统计信息"""
    total_collected: int = 0
    new_builds: int = 0
    updated_builds: int = 0
    skipped_builds: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        duration = 0.0
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'total_collected': self.total_collected,
            'new_builds': self.new_builds,
            'updated_builds': self.updated_builds,
            'skipped_builds': self.skipped_builds,
            'errors': self.errors,
            'duration_seconds': duration,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class PoE2NinjaRAGCollector:
    """ninja.poe2 RAG数据采集器"""
    
    def __init__(self, data_dir: Path = None, cache_ttl: int = 1800):
        self._logger = logging.getLogger(f"{__name__}.PoE2NinjaRAGCollector")
        
        # 数据存储
        self.data_dir = data_dir or Path.cwd() / 'data' / 'rag'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件
        self.builds_file = self.data_dir / 'ninja_builds.json'
        self.meta_file = self.data_dir / 'ninja_meta.json'
        self.stats_file = self.data_dir / 'collection_stats.json'
        
        # 组件
        self.scraper = NinjaPoE2Scraper()
        
        # 配置
        self.cache_ttl = cache_ttl  # 缓存生存时间(秒)
        self.max_builds_per_class = 100  # 每个职业最大构筑数
        self.min_popularity_threshold = 0.01  # 最小流行度阈值
        
        # 运行时状态
        self.builds_cache: Dict[str, RAGBuildData] = {}
        self.last_update: Optional[datetime] = None
        self._updating = False
    
    async def collect_all_builds(self, force_refresh: bool = False) -> CollectionStats:
        """采集所有构筑数据"""
        if self._updating:
            self._logger.warning("数据采集正在进行中，跳过此次请求")
            return CollectionStats()
        
        try:
            self._updating = True
            stats = CollectionStats()
            
            # 检查是否需要更新
            if not force_refresh and await self._is_cache_valid():
                self._logger.info("缓存数据仍有效，跳过采集")
                await self._load_cached_data()
                return stats
            
            self._logger.info("开始采集ninja.poe2构筑数据...")
            
            # 按职业采集数据
            for char_class in PoE2CharacterClass:
                try:
                    class_stats = await self._collect_class_builds(char_class)
                    stats.total_collected += class_stats.total_collected
                    stats.new_builds += class_stats.new_builds
                    stats.updated_builds += class_stats.updated_builds
                    stats.skipped_builds += class_stats.skipped_builds
                    stats.errors += class_stats.errors
                    
                    # 短暂休息避免过度请求
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self._logger.error(f"采集{char_class.value}构筑失败: {e}")
                    stats.errors += 1
            
            # 采集Meta数据
            await self._collect_meta_data()
            
            # 保存数据
            await self._save_data()
            
            stats.end_time = datetime.now()
            await self._save_stats(stats)
            
            self._logger.info(f"数据采集完成: {stats.total_collected}个构筑，"
                            f"新增{stats.new_builds}，更新{stats.updated_builds}")
            
            return stats
            
        except Exception as e:
            self._logger.error(f"数据采集失败: {e}")
            stats.errors += 1
            stats.end_time = datetime.now()
            return stats
        finally:
            self._updating = False
    
    async def _collect_class_builds(self, char_class: PoE2CharacterClass) -> CollectionStats:
        """采集指定职业的构筑数据"""
        stats = CollectionStats()
        
        try:
            # 获取热门构筑
            builds = await self.scraper.get_popular_builds(
                character_class=char_class,
                limit=self.max_builds_per_class
            )
            
            for build in builds:
                try:
                    stats.total_collected += 1
                    
                    # 生成构筑ID
                    build_id = self._generate_build_id(build)
                    
                    # 检查是否已存在
                    if build_id in self.builds_cache:
                        # 更新现有构筑
                        existing = self.builds_cache[build_id]
                        if await self._should_update_build(existing, build):
                            await self._update_build_data(existing, build)
                            stats.updated_builds += 1
                        else:
                            stats.skipped_builds += 1
                    else:
                        # 创建新的构筑数据
                        rag_data = await self._create_rag_build_data(build_id, build)
                        self.builds_cache[build_id] = rag_data
                        stats.new_builds += 1
                    
                except Exception as e:
                    self._logger.error(f"处理构筑数据失败: {e}")
                    stats.errors += 1
            
            self._logger.info(f"采集{char_class.value}构筑完成: {len(builds)}个")
            
        except Exception as e:
            self._logger.error(f"采集{char_class.value}构筑失败: {e}")
            stats.errors += 1
        
        return stats
    
    async def _create_rag_build_data(self, build_id: str, build: PoE2Build) -> RAGBuildData:
        """创建RAG构筑数据"""
        # 生成构筑描述
        description = self._generate_build_description(build)
        
        # 生成标签
        tags = self._generate_build_tags(build)
        
        # 计算流行度分数(简化版)
        popularity_score = self._calculate_popularity_score(build)
        
        # 创建源数据元信息
        source_metadata = {
            'source': 'ninja.poe2',
            'collected_at': datetime.now().isoformat(),
            'source_url': build.source_url,
            'league': build.league
        }
        
        return RAGBuildData(
            build_id=build_id,
            build=build,
            description=description,
            tags=tags,
            popularity_score=popularity_score,
            source_metadata=source_metadata
        )
    
    def _generate_build_description(self, build: PoE2Build) -> str:
        """生成构筑的文本描述"""
        parts = []
        
        # 基础信息
        parts.append(f"{build.character_class.value}职业")
        if build.ascendancy:
            parts.append(f"{build.ascendancy.value}升华")
        parts.append(f"{build.level}级")
        
        # 主技能
        if build.main_skill_gem:
            parts.append(f"主技能{build.main_skill_gem}")
        
        # 辅助宝石
        if build.support_gems:
            support_list = ", ".join(build.support_gems[:3])  # 最多3个
            parts.append(f"辅助宝石包括{support_list}")
        
        # 统计数据
        if build.stats:
            if build.stats.total_dps > 0:
                dps_k = int(build.stats.total_dps / 1000)
                parts.append(f"DPS约{dps_k}K")
            
            if build.stats.effective_health_pool > 0:
                ehp_k = int(build.stats.effective_health_pool / 1000)
                parts.append(f"有效生命值{ehp_k}K")
            
            if build.stats.is_resistance_capped():
                parts.append("三抗满足")
        
        # 预算
        if build.estimated_cost:
            parts.append(f"预算约{build.estimated_cost}{build.currency_type}")
        
        # 构筑目标
        if build.goal:
            goal_map = {
                'clear_speed': '快速清图',
                'boss_killing': '击杀Boss',
                'endgame_content': '终局内容',
                'league_start': '赛季开荒',
                'budget_friendly': '经济实惠'
            }
            parts.append(goal_map.get(build.goal.value, build.goal.value))
        
        return "，".join(parts)
    
    def _generate_build_tags(self, build: PoE2Build) -> List[str]:
        """生成构筑标签"""
        tags = []
        
        # 职业标签
        tags.append(f"class_{build.character_class.value.lower()}")
        if build.ascendancy:
            tags.append(f"ascendancy_{build.ascendancy.value.lower()}")
        
        # 等级标签
        if build.level <= 30:
            tags.append("early_game")
        elif build.level <= 70:
            tags.append("mid_game") 
        else:
            tags.append("endgame")
        
        # 技能标签
        if build.main_skill_gem:
            skill_normalized = build.main_skill_gem.lower().replace(" ", "_")
            tags.append(f"skill_{skill_normalized}")
        
        # 预算标签
        if build.estimated_cost:
            if build.estimated_cost <= 1.0:
                tags.append("budget_starter")
            elif build.estimated_cost <= 5.0:
                tags.append("budget_low")
            elif build.estimated_cost <= 20.0:
                tags.append("budget_medium")
            else:
                tags.append("budget_high")
        
        # 目标标签
        if build.goal:
            tags.append(f"goal_{build.goal.value}")
        
        # 联盟标签
        tags.append(f"league_{build.league.lower()}")
        
        return tags
    
    def _calculate_popularity_score(self, build: PoE2Build) -> float:
        """计算流行度分数"""
        score = 0.0
        
        # 基于DPS的分数 (0-0.3)
        if build.stats and build.stats.total_dps > 0:
            # 归一化DPS分数 (1M DPS = 0.3分)
            dps_score = min(build.stats.total_dps / 1000000 * 0.3, 0.3)
            score += dps_score
        
        # 基于生存能力的分数 (0-0.2)
        if build.stats and build.stats.effective_health_pool > 0:
            # 归一化EHP分数 (10K EHP = 0.2分)
            ehp_score = min(build.stats.effective_health_pool / 10000 * 0.2, 0.2)
            score += ehp_score
        
        # 基于完整性的分数 (0-0.3)
        completeness = 0.0
        if build.main_skill_gem:
            completeness += 0.1
        if build.support_gems:
            completeness += 0.1
        if build.stats and build.stats.is_resistance_capped():
            completeness += 0.1
        score += completeness
        
        # 基于目标适配的分数 (0-0.2)
        if build.goal and build.stats:
            if build.is_suitable_for_goal(build.goal):
                score += 0.2
        
        return min(score, 1.0)
    
    async def _collect_meta_data(self):
        """采集Meta数据"""
        try:
            self._logger.info("采集Meta数据...")
            
            # 获取Meta分析
            meta_data = await self.scraper.get_meta_analysis()
            
            if meta_data:
                # 添加采集时间戳
                meta_data['collected_at'] = datetime.now().isoformat()
                
                # 保存到文件
                with open(self.meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=2, ensure_ascii=False)
                
                self._logger.info("Meta数据采集完成")
            else:
                self._logger.warning("未获取到Meta数据")
        
        except Exception as e:
            self._logger.error(f"采集Meta数据失败: {e}")
    
    def _generate_build_id(self, build: PoE2Build) -> str:
        """生成构筑唯一ID"""
        # 使用关键属性生成哈希ID
        key_parts = [
            build.character_class.value,
            build.ascendancy.value if build.ascendancy else "",
            str(build.level),
            build.main_skill_gem or "",
            ",".join(sorted(build.support_gems or [])),
            build.league
        ]
        
        key_string = "|".join(key_parts)
        hash_obj = hashlib.md5(key_string.encode('utf-8'))
        return hash_obj.hexdigest()[:12]  # 12位哈希
    
    async def _should_update_build(self, existing: RAGBuildData, new_build: PoE2Build) -> bool:
        """判断是否应该更新构筑数据"""
        # 检查时间间隔
        time_diff = datetime.now() - existing.last_seen
        if time_diff.total_seconds() < 3600:  # 1小时内不更新
            return False
        
        # 检查数据是否有实质性变化
        if existing.build.stats and new_build.stats:
            dps_change = abs(existing.build.stats.total_dps - new_build.stats.total_dps)
            if dps_change / max(existing.build.stats.total_dps, 1) > 0.1:  # DPS变化>10%
                return True
        
        return True
    
    async def _update_build_data(self, existing: RAGBuildData, new_build: PoE2Build):
        """更新构筑数据"""
        # 更新构筑对象
        existing.build = new_build
        
        # 重新生成描述和标签
        existing.description = self._generate_build_description(new_build)
        existing.tags = self._generate_build_tags(new_build)
        existing.popularity_score = self._calculate_popularity_score(new_build)
        existing.last_seen = datetime.now()
        
        # 更新元数据
        existing.source_metadata['last_updated'] = datetime.now().isoformat()
    
    async def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self.builds_file.exists():
            return False
        
        try:
            # 检查文件修改时间
            file_mtime = datetime.fromtimestamp(self.builds_file.stat().st_mtime)
            if datetime.now() - file_mtime > timedelta(seconds=self.cache_ttl):
                return False
            
            return True
        except Exception:
            return False
    
    async def _load_cached_data(self):
        """加载缓存的数据"""
        try:
            if self.builds_file.exists():
                with open(self.builds_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                self.builds_cache = {}
                for build_id, data in cached_data.items():
                    self.builds_cache[build_id] = RAGBuildData.from_dict(data)
                
                self.last_update = datetime.now()
                self._logger.info(f"加载缓存数据: {len(self.builds_cache)}个构筑")
        
        except Exception as e:
            self._logger.error(f"加载缓存数据失败: {e}")
    
    async def _save_data(self):
        """保存数据到文件"""
        try:
            # 保存构筑数据
            builds_data = {}
            for build_id, rag_data in self.builds_cache.items():
                builds_data[build_id] = rag_data.to_dict()
            
            with open(self.builds_file, 'w', encoding='utf-8') as f:
                json.dump(builds_data, f, indent=2, ensure_ascii=False)
            
            self.last_update = datetime.now()
            self._logger.info(f"数据已保存: {len(builds_data)}个构筑")
        
        except Exception as e:
            self._logger.error(f"保存数据失败: {e}")
    
    async def _save_stats(self, stats: CollectionStats):
        """保存采集统计"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._logger.error(f"保存统计数据失败: {e}")
    
    def get_builds_by_class(self, char_class: PoE2CharacterClass) -> List[RAGBuildData]:
        """获取指定职业的构筑数据"""
        return [
            rag_data for rag_data in self.builds_cache.values()
            if rag_data.build.character_class == char_class
        ]
    
    def get_builds_by_tags(self, tags: List[str]) -> List[RAGBuildData]:
        """根据标签获取构筑数据"""
        result = []
        for rag_data in self.builds_cache.values():
            if any(tag in rag_data.tags for tag in tags):
                result.append(rag_data)
        return result
    
    def get_all_builds(self) -> List[RAGBuildData]:
        """获取所有构筑数据"""
        return list(self.builds_cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取采集器统计信息"""
        return {
            'total_builds': len(self.builds_cache),
            'classes_distribution': self._get_class_distribution(),
            'tags_distribution': self._get_tags_distribution(),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_valid': asyncio.create_task(self._is_cache_valid()),
            'data_dir': str(self.data_dir)
        }
    
    def _get_class_distribution(self) -> Dict[str, int]:
        """获取职业分布统计"""
        distribution = {}
        for rag_data in self.builds_cache.values():
            class_name = rag_data.build.character_class.value
            distribution[class_name] = distribution.get(class_name, 0) + 1
        return distribution
    
    def _get_tags_distribution(self) -> Dict[str, int]:
        """获取标签分布统计"""
        distribution = {}
        for rag_data in self.builds_cache.values():
            for tag in rag_data.tags:
                distribution[tag] = distribution.get(tag, 0) + 1
        
        # 返回前20个最常见的标签
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:20])


# 便捷函数
async def collect_ninja_builds(data_dir: Path = None, force_refresh: bool = False) -> CollectionStats:
    """采集ninja构筑数据的便捷函数"""
    collector = PoE2NinjaRAGCollector(data_dir)
    return await collector.collect_all_builds(force_refresh)