"""
知识库管理器 - PoE2构筑知识库管理和Meta分析

负责管理构筑知识库，包括Meta趋势分析、成功模式提取、
知识更新和检索等功能。为AI引擎提供丰富的背景知识。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum

from .models import PoE2BuildData, BuildGoal, DataQuality, RAGDataModel
from .data_collector import PoE2RAGDataCollector

# 配置日志
logger = logging.getLogger(__name__)

class MetaTrend(Enum):
    """Meta趋势类型"""
    RISING = "rising"           # 上升趋势
    STABLE = "stable"           # 稳定
    DECLINING = "declining"     # 下降趋势
    EMERGING = "emerging"       # 新兴
    DEPRECATED = "deprecated"   # 已过时

class KnowledgeType(Enum):
    """知识类型"""
    BUILD_PATTERN = "build_pattern"         # 构筑模式
    META_TREND = "meta_trend"               # Meta趋势
    SUCCESS_FACTOR = "success_factor"       # 成功因素
    OPTIMIZATION_RULE = "optimization_rule" # 优化规则
    SYNERGY_INFO = "synergy_info"          # 协同信息

@dataclass
class BuildPattern:
    """构筑模式"""
    pattern_id: str                         # 模式ID
    pattern_name: str                       # 模式名称
    core_elements: Dict[str, Any]          # 核心元素
    variations: List[Dict[str, Any]] = field(default_factory=list)  # 变种
    success_rate: float = 0.0              # 成功率
    popularity_score: float = 0.0          # 流行度
    difficulty_level: str = "medium"        # 难度等级
    investment_tier: str = "medium"         # 投资等级
    
    # Meta信息
    first_seen: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    trend: MetaTrend = MetaTrend.STABLE
    sample_builds: List[str] = field(default_factory=list)  # 示例构筑哈希

@dataclass
class MetaInsight:
    """Meta洞察"""
    insight_type: str                      # 洞察类型
    title: str                             # 标题
    description: str                       # 描述
    confidence: float                      # 置信度
    supporting_data: Dict[str, Any] = field(default_factory=dict)  # 支撑数据
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

@dataclass
class KnowledgeEntry:
    """知识条目"""
    entry_id: str                          # 条目ID
    knowledge_type: KnowledgeType          # 知识类型
    title: str                             # 标题
    content: Dict[str, Any]               # 内容
    confidence: float = 0.8               # 置信度
    source: str = "rag_analysis"          # 来源
    created_at: datetime = field(default_factory=datetime.now)
    last_verified: Optional[datetime] = None
    verification_count: int = 0            # 验证次数
    tags: List[str] = field(default_factory=list)

class PoE2KnowledgeBase:
    """PoE2构筑知识库管理器
    
    管理构筑相关的知识，包括模式识别、Meta分析、优化建议等。
    """
    
    def __init__(self, knowledge_dir: str = "data/knowledge"):
        """初始化知识库管理器
        
        Args:
            knowledge_dir: 知识库存储目录
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # 知识库组件
        self.build_patterns: Dict[str, BuildPattern] = {}
        self.meta_insights: List[MetaInsight] = []
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}
        
        # 分析缓存
        self._class_stats = {}
        self._skill_stats = {}
        self._trend_analysis = {}
        
        # 配置
        self.max_patterns = 100
        self.max_insights = 500
        self.pattern_min_samples = 5
        
        self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        """加载知识库"""
        try:
            # 加载构筑模式
            patterns_file = self.knowledge_dir / "build_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                for pattern_data in patterns_data:
                    pattern = BuildPattern(**pattern_data)
                    # 转换日期时间
                    if isinstance(pattern.first_seen, str):
                        pattern.first_seen = datetime.fromisoformat(pattern.first_seen)
                    if isinstance(pattern.last_updated, str):
                        pattern.last_updated = datetime.fromisoformat(pattern.last_updated)
                    pattern.trend = MetaTrend(pattern_data.get('trend', MetaTrend.STABLE.value))
                    
                    self.build_patterns[pattern.pattern_id] = pattern
                    
                logger.info(f"加载了 {len(self.build_patterns)} 个构筑模式")
            
            # 加载Meta洞察
            insights_file = self.knowledge_dir / "meta_insights.json"
            if insights_file.exists():
                with open(insights_file, 'r', encoding='utf-8') as f:
                    insights_data = json.load(f)
                
                for insight_data in insights_data:
                    insight = MetaInsight(**insight_data)
                    if isinstance(insight.created_at, str):
                        insight.created_at = datetime.fromisoformat(insight.created_at)
                    self.meta_insights.append(insight)
                
                logger.info(f"加载了 {len(self.meta_insights)} 个Meta洞察")
            
            # 加载知识条目
            knowledge_file = self.knowledge_dir / "knowledge_entries.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                for entry_data in knowledge_data:
                    entry = KnowledgeEntry(**entry_data)
                    entry.knowledge_type = KnowledgeType(entry_data.get('knowledge_type'))
                    if isinstance(entry.created_at, str):
                        entry.created_at = datetime.fromisoformat(entry.created_at)
                    if entry.last_verified and isinstance(entry.last_verified, str):
                        entry.last_verified = datetime.fromisoformat(entry.last_verified)
                    
                    self.knowledge_entries[entry.entry_id] = entry
                
                logger.info(f"加载了 {len(self.knowledge_entries)} 个知识条目")
                
        except Exception as e:
            logger.warning(f"知识库加载失败: {e}")
    
    def save_knowledge_base(self):
        """保存知识库"""
        try:
            # 保存构筑模式
            patterns_data = []
            for pattern in self.build_patterns.values():
                pattern_dict = asdict(pattern)
                pattern_dict['first_seen'] = pattern.first_seen.isoformat()
                pattern_dict['last_updated'] = pattern.last_updated.isoformat()
                pattern_dict['trend'] = pattern.trend.value
                patterns_data.append(pattern_dict)
            
            patterns_file = self.knowledge_dir / "build_patterns.json"
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
            
            # 保存Meta洞察
            insights_data = []
            for insight in self.meta_insights:
                insight_dict = asdict(insight)
                insight_dict['created_at'] = insight.created_at.isoformat()
                insights_data.append(insight_dict)
            
            insights_file = self.knowledge_dir / "meta_insights.json"
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, ensure_ascii=False, indent=2)
            
            # 保存知识条目
            knowledge_data = []
            for entry in self.knowledge_entries.values():
                entry_dict = asdict(entry)
                entry_dict['knowledge_type'] = entry.knowledge_type.value
                entry_dict['created_at'] = entry.created_at.isoformat()
                if entry.last_verified:
                    entry_dict['last_verified'] = entry.last_verified.isoformat()
                knowledge_data.append(entry_dict)
            
            knowledge_file = self.knowledge_dir / "knowledge_entries.json"
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            
            logger.info("知识库保存成功")
            
        except Exception as e:
            logger.error(f"知识库保存失败: {e}")
    
    def update_knowledge_from_builds(self, builds: List[PoE2BuildData]):
        """从构筑数据更新知识库
        
        Args:
            builds: 构筑数据列表
        """
        logger.info(f"开始从 {len(builds)} 个构筑更新知识库...")
        
        # 1. 更新统计信息
        self._update_statistics(builds)
        
        # 2. 识别和更新构筑模式
        self._identify_build_patterns(builds)
        
        # 3. 生成Meta洞察
        self._generate_meta_insights(builds)
        
        # 4. 提取成功因素
        self._extract_success_factors(builds)
        
        # 5. 更新协同信息
        self._update_synergy_information(builds)
        
        # 6. 保存知识库
        self.save_knowledge_base()
        
        logger.info("知识库更新完成")
    
    def _update_statistics(self, builds: List[PoE2BuildData]):
        """更新统计信息"""
        # 职业统计
        class_counter = Counter()
        skill_counter = Counter()
        goal_counter = Counter()
        
        cost_by_class = defaultdict(list)
        success_by_pattern = defaultdict(list)
        
        for build in builds:
            class_counter[build.character_class] += 1
            skill_counter[build.main_skill_setup.main_skill] += 1
            goal_counter[build.build_goal.value] += 1
            
            cost_by_class[build.character_class].append(build.total_cost)
            
            # 成功度量（基于流行度和数据质量）
            success_score = 0.5
            if build.popularity_rank > 0:
                success_score += max(0, 1.0 - build.popularity_rank / 1000)
            if build.data_quality == DataQuality.HIGH:
                success_score += 0.3
            elif build.data_quality == DataQuality.MEDIUM:
                success_score += 0.1
            
            pattern_key = f"{build.character_class}_{build.main_skill_setup.main_skill}"
            success_by_pattern[pattern_key].append(success_score)
        
        # 更新缓存
        self._class_stats = {
            'popularity': dict(class_counter),
            'avg_costs': {cls: sum(costs)/len(costs) if costs else 0 
                         for cls, costs in cost_by_class.items()},
            'total_builds': len(builds)
        }
        
        self._skill_stats = {
            'popularity': dict(skill_counter),
            'success_rates': {pattern: sum(scores)/len(scores) if scores else 0.5
                            for pattern, scores in success_by_pattern.items()}
        }
        
        logger.info("统计信息已更新")
    
    def _identify_build_patterns(self, builds: List[PoE2BuildData]):
        """识别构筑模式"""
        pattern_groups = defaultdict(list)
        
        # 按核心特征分组构筑
        for build in builds:
            core_key = (
                build.character_class,
                build.ascendancy,
                build.main_skill_setup.main_skill,
                build.build_goal.value
            )
            pattern_groups[core_key].append(build)
        
        # 分析每个组，识别模式
        new_patterns = 0
        for core_key, group_builds in pattern_groups.items():
            if len(group_builds) < self.pattern_min_samples:
                continue
            
            class_name, ascendancy, skill, goal = core_key
            pattern_id = f"{class_name}_{ascendancy}_{skill}_{goal}".replace(" ", "_").lower()
            
            # 分析组内构筑的共同特征
            core_elements = {
                'character_class': class_name,
                'ascendancy': ascendancy,
                'main_skill': skill,
                'build_goal': goal
            }
            
            # 计算模式统计
            costs = [b.total_cost for b in group_builds if b.total_cost > 0]
            popularity_ranks = [b.popularity_rank for b in group_builds if b.popularity_rank > 0]
            
            avg_cost = sum(costs) / len(costs) if costs else 0
            avg_popularity = sum(popularity_ranks) / len(popularity_ranks) if popularity_ranks else 0
            
            # 成功率计算
            high_quality_builds = [b for b in group_builds if b.data_quality == DataQuality.HIGH]
            success_rate = len(high_quality_builds) / len(group_builds)
            
            # 流行度分数
            popularity_score = len(group_builds) / len(builds)
            
            # 更新或创建模式
            if pattern_id in self.build_patterns:
                pattern = self.build_patterns[pattern_id]
                pattern.last_updated = datetime.now()
                pattern.success_rate = success_rate
                pattern.popularity_score = popularity_score
                pattern.sample_builds = [b.similarity_hash for b in group_builds[:10]]
            else:
                pattern = BuildPattern(
                    pattern_id=pattern_id,
                    pattern_name=f"{class_name} {skill} ({goal})",
                    core_elements=core_elements,
                    success_rate=success_rate,
                    popularity_score=popularity_score,
                    difficulty_level=self._assess_pattern_difficulty(avg_cost, class_name),
                    investment_tier=self._assess_investment_tier(avg_cost),
                    sample_builds=[b.similarity_hash for b in group_builds[:10]]
                )
                self.build_patterns[pattern_id] = pattern
                new_patterns += 1
        
        logger.info(f"识别了 {new_patterns} 个新构筑模式，总计 {len(self.build_patterns)} 个模式")
    
    def _generate_meta_insights(self, builds: List[PoE2BuildData]):
        """生成Meta洞察"""
        current_time = datetime.now()
        
        # 职业分布洞察
        class_distribution = Counter(b.character_class for b in builds)
        most_popular_class = class_distribution.most_common(1)[0] if class_distribution else ("Unknown", 0)
        
        if most_popular_class[1] > len(builds) * 0.3:  # 超过30%的构筑使用同一职业
            insight = MetaInsight(
                insight_type="class_dominance",
                title=f"{most_popular_class[0]} 职业主导当前Meta",
                description=f"{most_popular_class[0]} 占据了 {most_popular_class[1]/len(builds):.1%} 的构筑，显示出强势的Meta地位。",
                confidence=0.9,
                supporting_data={'class_distribution': dict(class_distribution)},
                tags=['meta', 'class_analysis', most_popular_class[0].lower()]
            )
            self.meta_insights.append(insight)
        
        # 技能流行度洞察
        skill_distribution = Counter(b.main_skill_setup.main_skill for b in builds)
        top_skills = skill_distribution.most_common(3)
        
        if top_skills:
            insight = MetaInsight(
                insight_type="skill_popularity",
                title="当前Meta热门技能分析",
                description=f"最受欢迎的技能是 {top_skills[0][0]} ({top_skills[0][1]} 个构筑)，其次是 {top_skills[1][0]} 和 {top_skills[2][0]}。",
                confidence=0.8,
                supporting_data={'skill_distribution': dict(skill_distribution)},
                tags=['meta', 'skill_analysis', 'trending']
            )
            self.meta_insights.append(insight)
        
        # 预算趋势洞察
        costs = [b.total_cost for b in builds if b.total_cost > 0]
        if costs:
            avg_cost = sum(costs) / len(costs)
            
            if avg_cost > 15:
                insight = MetaInsight(
                    insight_type="cost_trend",
                    title="高投资构筑趋势",
                    description=f"当前Meta平均构筑成本达到 {avg_cost:.1f} divine，表明高投资构筑成为主流。",
                    confidence=0.7,
                    supporting_data={'average_cost': avg_cost, 'cost_distribution': costs},
                    tags=['meta', 'economy', 'high_investment']
                )
                self.meta_insights.append(insight)
        
        # 清理过期洞察
        cutoff_date = current_time - timedelta(days=30)
        self.meta_insights = [insight for insight in self.meta_insights 
                            if insight.created_at > cutoff_date]
        
        logger.info(f"生成了Meta洞察，当前共 {len(self.meta_insights)} 个洞察")
    
    def _extract_success_factors(self, builds: List[PoE2BuildData]):
        """提取成功因素"""
        # 按成功度对构筑分组
        successful_builds = []
        for build in builds:
            success_score = 0
            if build.popularity_rank > 0 and build.popularity_rank <= 100:
                success_score += 0.5
            if build.data_quality == DataQuality.HIGH:
                success_score += 0.3
            if build.total_cost < 10:  # 性价比好
                success_score += 0.2
            
            if success_score >= 0.6:
                successful_builds.append((build, success_score))
        
        if not successful_builds:
            return
        
        # 分析成功构筑的共同特征
        success_patterns = defaultdict(int)
        
        for build, score in successful_builds:
            # 职业成功因素
            success_patterns[f"class_{build.character_class}"] += 1
            
            # 技能成功因素
            success_patterns[f"skill_{build.main_skill_setup.main_skill}"] += 1
            
            # 目标成功因素
            success_patterns[f"goal_{build.build_goal.value}"] += 1
            
            # 预算成功因素
            if build.total_cost < 5:
                success_patterns["budget_friendly"] += 1
            elif build.total_cost > 20:
                success_patterns["high_investment"] += 1
            else:
                success_patterns["moderate_investment"] += 1
        
        # 创建成功因素知识条目
        for factor, count in success_patterns.items():
            if count >= len(successful_builds) * 0.3:  # 至少30%的成功构筑有这个特征
                confidence = count / len(successful_builds)
                
                entry = KnowledgeEntry(
                    entry_id=f"success_factor_{factor}",
                    knowledge_type=KnowledgeType.SUCCESS_FACTOR,
                    title=f"成功因素: {factor}",
                    content={
                        'factor': factor,
                        'occurrence_rate': confidence,
                        'sample_count': count,
                        'total_successful': len(successful_builds)
                    },
                    confidence=confidence,
                    tags=['success_factor', factor.split('_')[0] if '_' in factor else factor]
                )
                
                self.knowledge_entries[entry.entry_id] = entry
        
        logger.info(f"提取了 {len(success_patterns)} 个成功因素")
    
    def _update_synergy_information(self, builds: List[PoE2BuildData]):
        """更新协同信息"""
        # 分析技能和装备的协同效应
        skill_equipment_pairs = defaultdict(Counter)
        skill_keystone_pairs = defaultdict(Counter)
        
        for build in builds:
            skill = build.main_skill_setup.main_skill
            
            # 技能-装备协同
            if build.weapon and build.weapon.name:
                skill_equipment_pairs[skill][build.weapon.name] += 1
            
            # 技能-关键天赋协同
            for keystone in build.passive_keystones:
                skill_keystone_pairs[skill][keystone] += 1
        
        # 创建协同信息条目
        synergy_entries = 0
        for skill, equipment_counter in skill_equipment_pairs.items():
            for equipment, count in equipment_counter.items():
                if count >= 3:  # 至少被3个构筑使用
                    entry_id = f"synergy_{skill}_{equipment}".replace(" ", "_").lower()
                    
                    entry = KnowledgeEntry(
                        entry_id=entry_id,
                        knowledge_type=KnowledgeType.SYNERGY_INFO,
                        title=f"协同: {skill} + {equipment}",
                        content={
                            'skill': skill,
                            'equipment': equipment,
                            'usage_count': count,
                            'synergy_type': 'skill_equipment'
                        },
                        confidence=min(0.9, count / 10),  # 使用次数越多置信度越高
                        tags=['synergy', 'equipment', skill.replace(" ", "_").lower()]
                    )
                    
                    self.knowledge_entries[entry.entry_id] = entry
                    synergy_entries += 1
        
        logger.info(f"更新了 {synergy_entries} 个协同信息条目")
    
    def get_build_pattern(self, pattern_id: str) -> Optional[BuildPattern]:
        """获取构筑模式"""
        return self.build_patterns.get(pattern_id)
    
    def search_patterns(self, character_class: str = None, 
                       main_skill: str = None,
                       build_goal: str = None,
                       min_success_rate: float = 0.0) -> List[BuildPattern]:
        """搜索构筑模式"""
        matching_patterns = []
        
        for pattern in self.build_patterns.values():
            # 应用筛选条件
            if character_class and pattern.core_elements.get('character_class') != character_class:
                continue
            if main_skill and pattern.core_elements.get('main_skill') != main_skill:
                continue
            if build_goal and pattern.core_elements.get('build_goal') != build_goal:
                continue
            if pattern.success_rate < min_success_rate:
                continue
            
            matching_patterns.append(pattern)
        
        # 按流行度排序
        return sorted(matching_patterns, key=lambda p: p.popularity_score, reverse=True)
    
    def get_meta_insights(self, insight_type: str = None, limit: int = 10) -> List[MetaInsight]:
        """获取Meta洞察"""
        insights = self.meta_insights
        
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        # 按时间排序，最新的在前
        insights.sort(key=lambda i: i.created_at, reverse=True)
        
        return insights[:limit]
    
    def get_knowledge_by_type(self, knowledge_type: KnowledgeType) -> List[KnowledgeEntry]:
        """按类型获取知识条目"""
        return [entry for entry in self.knowledge_entries.values() 
                if entry.knowledge_type == knowledge_type]
    
    def get_success_factors_for_build(self, build_class: str, main_skill: str) -> List[KnowledgeEntry]:
        """获取特定构筑的成功因素"""
        relevant_factors = []
        
        for entry in self.knowledge_entries.values():
            if entry.knowledge_type != KnowledgeType.SUCCESS_FACTOR:
                continue
            
            factor = entry.content.get('factor', '')
            if (f"class_{build_class}" in factor or 
                f"skill_{main_skill}" in factor or 
                'budget' in factor):
                relevant_factors.append(entry)
        
        return sorted(relevant_factors, key=lambda e: e.confidence, reverse=True)
    
    def get_trending_builds(self, days: int = 7) -> List[BuildPattern]:
        """获取趋势构筑模式"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        trending_patterns = []
        for pattern in self.build_patterns.values():
            if (pattern.last_updated > cutoff_date and 
                pattern.trend in [MetaTrend.RISING, MetaTrend.EMERGING]):
                trending_patterns.append(pattern)
        
        return sorted(trending_patterns, key=lambda p: p.popularity_score, reverse=True)
    
    # 辅助方法
    def _assess_pattern_difficulty(self, avg_cost: float, class_name: str) -> str:
        """评估模式难度"""
        difficulty_score = 0
        
        if avg_cost > 15:
            difficulty_score += 2
        elif avg_cost > 5:
            difficulty_score += 1
        
        complex_classes = ["Witch", "Templar"]
        if class_name in complex_classes:
            difficulty_score += 1
        
        if difficulty_score >= 3:
            return "高难度"
        elif difficulty_score >= 1:
            return "中等难度"
        else:
            return "简单"
    
    def _assess_investment_tier(self, avg_cost: float) -> str:
        """评估投资等级"""
        if avg_cost < 3:
            return "低投资"
        elif avg_cost < 15:
            return "中投资"
        else:
            return "高投资"
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            'total_patterns': len(self.build_patterns),
            'total_insights': len(self.meta_insights),
            'total_knowledge_entries': len(self.knowledge_entries),
            'class_stats': self._class_stats,
            'skill_stats': self._skill_stats,
            'last_updated': datetime.now().isoformat()
        }

# 工厂函数
def create_knowledge_base(knowledge_dir: str = "data/knowledge") -> PoE2KnowledgeBase:
    """创建知识库管理器的工厂函数"""
    return PoE2KnowledgeBase(knowledge_dir)

# 测试函数
def test_knowledge_base():
    """测试知识库功能"""
    kb = create_knowledge_base()
    
    print(f"知识库统计: {kb.get_statistics_summary()}")
    print(f"构筑模式数量: {len(kb.build_patterns)}")
    print(f"Meta洞察数量: {len(kb.meta_insights)}")
    
    return kb

if __name__ == "__main__":
    kb = test_knowledge_base()
    print("知识库管理器测试完成!")