"""
RAG数据模型定义 - PoE2构筑数据结构

定义了用于RAG系统的标准化数据模型，包括:
- PoE2BuildData: 核心构筑数据模型
- RAGDataModel: RAG预处理数据容器  
- 各种辅助数据类型和验证器
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class BuildGoal(Enum):
    """构筑目标枚举"""
    CLEAR_SPEED = "clear_speed"           # 清速
    BOSS_KILLING = "boss_killing"         # 打boss
    BALANCED = "balanced"                 # 平衡
    BUDGET_FRIENDLY = "budget_friendly"   # 预算友好
    LEAGUE_START = "league_start"         # 赛季开荒
    ENDGAME_CONTENT = "endgame_content"   # 终局内容

class DataQuality(Enum):
    """数据质量等级"""
    HIGH = "high"         # 高质量 - 完整数据，来源可靠
    MEDIUM = "medium"     # 中等 - 部分数据缺失，但核心信息完整  
    LOW = "low"          # 低质量 - 数据不完整或来源不可靠
    INVALID = "invalid"   # 无效数据

@dataclass
class SuccessMetrics:
    """构筑成功指标"""
    popularity_score: float = 0.0          # 流行度分数 (0-1)
    level_achievement: float = 0.0         # 等级成就度 (0-1)
    gear_quality_score: float = 0.0       # 装备质量分数 (0-1)
    build_completeness: float = 0.0       # 构筑完整度 (0-1)
    meta_alignment: float = 0.0           # Meta符合度 (0-1)
    cost_effectiveness: float = 0.0       # 成本效益 (0-1)

    def overall_score(self) -> float:
        """计算综合成功分数"""
        weights = {
            'popularity': 0.25,
            'level': 0.15,
            'gear': 0.20,
            'completeness': 0.20,
            'meta': 0.15,
            'cost_effectiveness': 0.05
        }
        
        return (
            self.popularity_score * weights['popularity'] +
            self.level_achievement * weights['level'] +
            self.gear_quality_score * weights['gear'] +
            self.build_completeness * weights['completeness'] +
            self.meta_alignment * weights['meta'] +
            self.cost_effectiveness * weights['cost_effectiveness']
        )

@dataclass
class ItemInfo:
    """物品信息"""
    name: str
    type: str = ""                    # 物品类型
    rarity: str = "normal"           # 稀有度
    ilvl: int = 0                    # 物品等级
    price: float = 0.0               # 价格
    currency: str = "divine"         # 货币类型
    
    def __post_init__(self):
        """数据清理"""
        if self.name:
            self.name = self.name.strip()
        if self.type:
            self.type = self.type.strip().lower()

@dataclass 
class SkillGemSetup:
    """技能宝石配置"""
    main_skill: str = ""                    # 主技能
    support_gems: List[str] = field(default_factory=list)  # 辅助宝石列表
    skill_level: int = 20                   # 技能等级
    quality: int = 0                        # 技能品质
    socket_colors: str = ""                 # 插槽颜色 (如: "RRRRRR")
    links: int = 6                          # 连接数
    
    def __post_init__(self):
        """数据清理和验证"""
        if self.main_skill:
            self.main_skill = self.main_skill.strip()
        
        # 清理辅助宝石列表
        self.support_gems = [gem.strip() for gem in self.support_gems if gem and gem.strip()]
        
        # 限制等级和品质范围
        self.skill_level = max(1, min(30, self.skill_level))
        self.quality = max(0, min(23, self.quality))
        self.links = max(1, min(6, self.links))

@dataclass
class DefensiveStats:
    """防御属性"""
    life: int = 0                      # 生命值
    energy_shield: int = 0             # 能量护盾
    life_regen: float = 0.0           # 生命回复
    es_regen: float = 0.0             # ES回复
    
    # 抗性
    fire_resistance: int = 0          # 火抗
    cold_resistance: int = 0          # 冰抗
    lightning_resistance: int = 0     # 电抗
    chaos_resistance: int = -30       # 混沌抗 (默认-30%)
    
    # 其他防御
    armour: int = 0                   # 护甲
    evasion: int = 0                  # 闪避
    block_chance: float = 0.0         # 格挡几率
    spell_block_chance: float = 0.0   # 法术格挡几率
    
    def effective_health_pool(self) -> int:
        """计算有效生命池"""
        return self.life + int(self.energy_shield * 0.5)  # ES按50%计算
    
    def max_resistance(self) -> int:
        """获取最大抗性值"""
        return max(self.fire_resistance, self.cold_resistance, 
                  self.lightning_resistance, self.chaos_resistance)
    
    def is_resistance_capped(self, cap: int = 75) -> bool:
        """检查抗性是否达标"""
        return (self.fire_resistance >= cap and 
                self.cold_resistance >= cap and 
                self.lightning_resistance >= cap)

@dataclass
class OffensiveStats:
    """攻击属性"""
    dps: float = 0.0                  # 总DPS
    average_damage: float = 0.0       # 平均伤害
    attack_speed: float = 1.0         # 攻击速度
    critical_chance: float = 5.0      # 暴击几率
    critical_multiplier: float = 150.0 # 暴击倍率
    accuracy: float = 90.0            # 命中率
    
    # 伤害类型分布
    physical_dps: float = 0.0
    elemental_dps: float = 0.0
    chaos_dps: float = 0.0
    
    def validate_stats(self):
        """验证攻击属性的合理性"""
        if self.dps < 0:
            self.dps = 0
        if self.critical_chance > 95:
            self.critical_chance = 95
        if self.critical_multiplier < 150:
            self.critical_multiplier = 150

@dataclass
class PoE2BuildData:
    """PoE2构筑数据 - 核心数据模型
    
    这是RAG系统的核心数据结构，包含了一个完整PoE2构筑的所有关键信息。
    设计遵循PoE2游戏机制和现实构筑需求。
    """
    # 基础信息
    character_name: str = ""                        # 角色名称
    character_class: str = ""                       # 角色职业
    ascendancy: str = ""                           # 升华职业
    level: int = 85                                # 角色等级
    
    # 技能配置
    main_skill_setup: SkillGemSetup = field(default_factory=SkillGemSetup)
    secondary_skills: List[SkillGemSetup] = field(default_factory=list)
    
    # 装备信息  
    weapon: Optional[ItemInfo] = None              # 主手武器
    offhand: Optional[ItemInfo] = None             # 副手
    helmet: Optional[ItemInfo] = None              # 头盔
    body_armour: Optional[ItemInfo] = None         # 胸甲
    gloves: Optional[ItemInfo] = None              # 手套
    boots: Optional[ItemInfo] = None               # 鞋子
    belt: Optional[ItemInfo] = None                # 腰带
    amulet: Optional[ItemInfo] = None              # 项链
    rings: List[ItemInfo] = field(default_factory=list)  # 戒指列表
    jewels: List[ItemInfo] = field(default_factory=list) # 珠宝列表
    
    # 天赋相关
    passive_keystones: List[str] = field(default_factory=list)  # 关键天赋
    major_nodes: List[str] = field(default_factory=list)       # 主要天赋节点
    passive_points_used: int = 0                               # 已用天赋点
    
    # 属性数据
    offensive_stats: OffensiveStats = field(default_factory=OffensiveStats)
    defensive_stats: DefensiveStats = field(default_factory=DefensiveStats)
    
    # 经济信息
    total_cost: float = 0.0                        # 总成本
    currency_type: str = "divine"                  # 货币类型
    budget_tier: str = "medium"                    # 预算等级: "budget", "medium", "expensive"
    
    # Meta信息
    popularity_rank: int = 0                       # 流行度排名
    success_metrics: SuccessMetrics = field(default_factory=SuccessMetrics)
    build_goal: BuildGoal = BuildGoal.BALANCED     # 构筑目标
    
    # 数据来源和质量
    data_source: str = ""                          # 数据来源
    data_quality: DataQuality = DataQuality.MEDIUM # 数据质量
    collection_timestamp: datetime = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None        # 最后更新时间
    
    # RAG相关字段
    build_description: str = ""                    # 构筑描述文本
    tags: List[str] = field(default_factory=list) # 标签列表
    similarity_hash: str = ""                      # 相似度哈希
    
    def __post_init__(self):
        """初始化后处理"""
        self._validate_data()
        self._generate_description()
        self._generate_similarity_hash()
        self._extract_tags()
    
    def _validate_data(self):
        """数据验证和清理"""
        # 清理字符串字段
        self.character_name = self.character_name.strip() if self.character_name else ""
        self.character_class = self.character_class.strip() if self.character_class else ""
        self.ascendancy = self.ascendancy.strip() if self.ascendancy else ""
        
        # 验证等级范围
        self.level = max(1, min(100, self.level))
        
        # 验证成本
        if self.total_cost < 0:
            self.total_cost = 0.0
            
        # 验证攻击属性
        if self.offensive_stats:
            self.offensive_stats.validate_stats()
        
        # 确保rings列表不超过2个
        if len(self.rings) > 2:
            self.rings = self.rings[:2]
            
        # 清理关键天赋列表
        self.passive_keystones = [ks.strip() for ks in self.passive_keystones if ks and ks.strip()]
        
    def _generate_description(self):
        """生成构筑描述文本用于RAG向量化"""
        if self.build_description:  # 如果已有描述就不重新生成
            return
            
        parts = []
        
        # 基础信息
        if self.character_class:
            class_desc = f"{self.character_class}"
            if self.ascendancy:
                class_desc += f" ({self.ascendancy})"
            parts.append(f"职业: {class_desc}")
        
        parts.append(f"等级: {self.level}")
        
        # 主技能信息
        if self.main_skill_setup.main_skill:
            skill_desc = f"主技能: {self.main_skill_setup.main_skill}"
            if self.main_skill_setup.support_gems:
                support_list = ", ".join(self.main_skill_setup.support_gems[:3])  # 只显示前3个
                skill_desc += f" + {support_list}"
            parts.append(skill_desc)
        
        # 武器信息
        if self.weapon and self.weapon.name:
            parts.append(f"武器: {self.weapon.name}")
        
        # 关键天赋
        if self.passive_keystones:
            keystones = ", ".join(self.passive_keystones[:3])
            parts.append(f"关键天赋: {keystones}")
        
        # 属性信息
        if self.offensive_stats.dps > 0:
            parts.append(f"DPS: {self.offensive_stats.dps:,.0f}")
        
        if self.defensive_stats.effective_health_pool() > 0:
            parts.append(f"有效生命: {self.defensive_stats.effective_health_pool():,}")
        
        # 经济信息
        if self.total_cost > 0:
            parts.append(f"成本: {self.total_cost:.1f} {self.currency_type}")
        
        # 构筑目标
        parts.append(f"目标: {self.build_goal.value}")
        
        # 流行度
        if self.popularity_rank > 0:
            parts.append(f"排名: #{self.popularity_rank}")
        
        self.build_description = " | ".join(parts)
    
    def _generate_similarity_hash(self):
        """生成用于相似度比较的哈希值"""
        # 使用核心特征生成哈希
        key_features = [
            self.character_class,
            self.ascendancy,
            self.main_skill_setup.main_skill,
            "|".join(sorted(self.main_skill_setup.support_gems)),
            "|".join(sorted(self.passive_keystones)),
            self.weapon.name if self.weapon else "",
            self.build_goal.value
        ]
        
        # 创建哈希字符串
        hash_string = "|".join([str(f) for f in key_features])
        self.similarity_hash = hashlib.md5(hash_string.encode('utf-8')).hexdigest()[:16]
    
    def _extract_tags(self):
        """从构筑数据中提取标签"""
        tags = set()
        
        # 职业标签
        if self.character_class:
            tags.add(self.character_class.lower())
        if self.ascendancy:
            tags.add(self.ascendancy.lower())
        
        # 技能标签
        if self.main_skill_setup.main_skill:
            tags.add(self.main_skill_setup.main_skill.lower().replace(" ", "_"))
        
        # 武器类型标签
        if self.weapon and self.weapon.type:
            tags.add(self.weapon.type.lower())
        
        # 构筑目标标签
        tags.add(self.build_goal.value)
        
        # 预算标签
        tags.add(self.budget_tier)
        
        # DPS层级标签
        if self.offensive_stats.dps > 5000000:
            tags.add("high_dps")
        elif self.offensive_stats.dps > 1000000:
            tags.add("medium_dps")
        elif self.offensive_stats.dps > 0:
            tags.add("low_dps")
        
        # 防御类型标签
        ehp = self.defensive_stats.effective_health_pool()
        if ehp > 10000:
            tags.add("high_defense")
        elif ehp > 6000:
            tags.add("medium_defense")
        elif ehp > 0:
            tags.add("low_defense")
        
        # 存储为列表
        self.tags = sorted(list(tags))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        data = self.to_dict()
        # 处理datetime对象
        if self.collection_timestamp:
            data['collection_timestamp'] = self.collection_timestamp.isoformat()
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoE2BuildData':
        """从字典创建实例"""
        # 处理日期时间字段
        if 'collection_timestamp' in data and isinstance(data['collection_timestamp'], str):
            data['collection_timestamp'] = datetime.fromisoformat(data['collection_timestamp'])
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
    
    def calculate_similarity_score(self, other: 'PoE2BuildData') -> float:
        """计算与另一个构筑的相似度分数 (0-1)"""
        if not isinstance(other, PoE2BuildData):
            return 0.0
        
        scores = []
        
        # 职业相似度 (权重: 0.3)
        class_score = 1.0 if self.character_class == other.character_class else 0.0
        if self.ascendancy and other.ascendancy:
            ascendancy_score = 1.0 if self.ascendancy == other.ascendancy else 0.5
        else:
            ascendancy_score = 0.5  # 如果有一个没有升华职业
        class_similarity = (class_score + ascendancy_score) / 2
        scores.append(('class', class_similarity, 0.3))
        
        # 技能相似度 (权重: 0.4)
        skill_score = 1.0 if self.main_skill_setup.main_skill == other.main_skill_setup.main_skill else 0.0
        
        # 辅助宝石相似度
        my_supports = set(self.main_skill_setup.support_gems)
        other_supports = set(other.main_skill_setup.support_gems)
        if my_supports or other_supports:
            support_score = len(my_supports & other_supports) / len(my_supports | other_supports)
        else:
            support_score = 1.0
        
        skill_similarity = (skill_score * 0.7 + support_score * 0.3)
        scores.append(('skill', skill_similarity, 0.4))
        
        # 关键天赋相似度 (权重: 0.15)
        my_keystones = set(self.passive_keystones)
        other_keystones = set(other.passive_keystones)
        if my_keystones or other_keystones:
            keystone_similarity = len(my_keystones & other_keystones) / len(my_keystones | other_keystones)
        else:
            keystone_similarity = 1.0
        scores.append(('keystones', keystone_similarity, 0.15))
        
        # 构筑目标相似度 (权重: 0.15)
        goal_similarity = 1.0 if self.build_goal == other.build_goal else 0.0
        scores.append(('goal', goal_similarity, 0.15))
        
        # 计算加权平均分
        total_weight = sum(weight for _, _, weight in scores)
        weighted_score = sum(score * weight for _, score, weight in scores) / total_weight
        
        return weighted_score
    
    def is_similar_to(self, other: 'PoE2BuildData', threshold: float = 0.7) -> bool:
        """判断是否与另一个构筑相似"""
        return self.calculate_similarity_score(other) >= threshold
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.character_class} {self.ascendancy} - {self.main_skill_setup.main_skill} (Lv.{self.level})"
    
    def __hash__(self) -> int:
        """哈希值基于相似度哈希"""
        return hash(self.similarity_hash)

@dataclass
class RAGDataModel:
    """RAG数据容器 - 用于批量处理和预处理的数据模型"""
    
    builds: List[PoE2BuildData] = field(default_factory=list)  # 构筑数据列表
    collection_metadata: Dict[str, Any] = field(default_factory=dict)  # 收集元数据
    processing_stats: Dict[str, Any] = field(default_factory=dict)     # 处理统计
    
    def add_build(self, build: PoE2BuildData):
        """添加构筑数据"""
        if isinstance(build, PoE2BuildData):
            self.builds.append(build)
        else:
            raise TypeError("只能添加PoE2BuildData类型的数据")
    
    def filter_by_quality(self, min_quality: DataQuality = DataQuality.MEDIUM) -> 'RAGDataModel':
        """按数据质量过滤"""
        quality_order = {
            DataQuality.INVALID: 0,
            DataQuality.LOW: 1, 
            DataQuality.MEDIUM: 2,
            DataQuality.HIGH: 3
        }
        
        min_level = quality_order[min_quality]
        filtered_builds = [
            build for build in self.builds 
            if quality_order[build.data_quality] >= min_level
        ]
        
        return RAGDataModel(
            builds=filtered_builds,
            collection_metadata=self.collection_metadata.copy(),
            processing_stats={"filtered_by_quality": min_quality.value}
        )
    
    def filter_by_class(self, character_class: str) -> 'RAGDataModel':
        """按职业过滤"""
        filtered_builds = [
            build for build in self.builds
            if build.character_class.lower() == character_class.lower()
        ]
        
        return RAGDataModel(
            builds=filtered_builds,
            collection_metadata=self.collection_metadata.copy(),
            processing_stats={"filtered_by_class": character_class}
        )
    
    def get_unique_builds(self, similarity_threshold: float = 0.8) -> 'RAGDataModel':
        """获取去重后的构筑数据"""
        unique_builds = []
        seen_hashes = set()
        
        for build in self.builds:
            # 首先检查相似度哈希
            if build.similarity_hash in seen_hashes:
                continue
                
            # 检查是否与已有构筑过于相似
            is_duplicate = False
            for unique_build in unique_builds:
                if build.calculate_similarity_score(unique_build) >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_builds.append(build)
                seen_hashes.add(build.similarity_hash)
        
        return RAGDataModel(
            builds=unique_builds,
            collection_metadata=self.collection_metadata.copy(),
            processing_stats={
                "deduplication_threshold": similarity_threshold,
                "original_count": len(self.builds),
                "unique_count": len(unique_builds)
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        if not self.builds:
            return {"total_builds": 0}
        
        # 基础统计
        stats = {
            "total_builds": len(self.builds),
            "classes": {},
            "ascendancies": {},
            "main_skills": {},
            "build_goals": {},
            "data_quality": {},
            "cost_ranges": {
                "budget": 0,      # < 5 divine
                "medium": 0,      # 5-20 divine  
                "expensive": 0,   # > 20 divine
                "unknown": 0
            }
        }
        
        for build in self.builds:
            # 职业统计
            if build.character_class:
                stats["classes"][build.character_class] = \
                    stats["classes"].get(build.character_class, 0) + 1
            
            # 升华统计
            if build.ascendancy:
                stats["ascendancies"][build.ascendancy] = \
                    stats["ascendancies"].get(build.ascendancy, 0) + 1
            
            # 主技能统计
            if build.main_skill_setup.main_skill:
                skill = build.main_skill_setup.main_skill
                stats["main_skills"][skill] = stats["main_skills"].get(skill, 0) + 1
            
            # 构筑目标统计
            goal = build.build_goal.value
            stats["build_goals"][goal] = stats["build_goals"].get(goal, 0) + 1
            
            # 数据质量统计
            quality = build.data_quality.value
            stats["data_quality"][quality] = stats["data_quality"].get(quality, 0) + 1
            
            # 成本统计
            if build.total_cost == 0:
                stats["cost_ranges"]["unknown"] += 1
            elif build.total_cost < 5:
                stats["cost_ranges"]["budget"] += 1
            elif build.total_cost < 20:
                stats["cost_ranges"]["medium"] += 1
            else:
                stats["cost_ranges"]["expensive"] += 1
        
        return stats
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        data = {
            "builds": [build.to_dict() for build in self.builds],
            "collection_metadata": self.collection_metadata,
            "processing_stats": self.processing_stats
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'RAGDataModel':
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        builds = [PoE2BuildData.from_dict(build_data) for build_data in data['builds']]
        
        return cls(
            builds=builds,
            collection_metadata=data.get('collection_metadata', {}),
            processing_stats=data.get('processing_stats', {})
        )
    
    def __len__(self) -> int:
        return len(self.builds)
    
    def __iter__(self):
        return iter(self.builds)
    
    def __getitem__(self, index):
        return self.builds[index]