"""
RAG数据预处理器 - 清洗和标准化PoE2构筑数据

主要功能:
1. 数据清洗和去重
2. 缺失值处理和插值
3. 异常值检测和处理
4. 数据标准化和归一化
5. 特征工程和增强
6. 质量评估和过滤

预处理流程:
原始数据 -> 清洗 -> 去重 -> 缺失值处理 -> 异常值处理 -> 标准化 -> 特征增强 -> 质量评估 -> 输出
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
from dataclasses import asdict, replace
import re

import numpy as np

from .models import (
    PoE2BuildData,
    RAGDataModel,
    SkillGemSetup,
    ItemInfo,
    OffensiveStats,
    DefensiveStats,
    SuccessMetrics,
    BuildGoal,
    DataQuality
)

logger = logging.getLogger(__name__)

class PoE2DataPreprocessor:
    """
    PoE2数据预处理器
    
    专门用于处理从多个数据源收集的PoE2构筑数据，
    执行全面的清洗、标准化和质量增强。
    """
    
    def __init__(self,
                 enable_anomaly_detection: bool = True,
                 enable_missing_value_imputation: bool = True,
                 enable_feature_engineering: bool = True,
                 similarity_threshold: float = 0.85):
        """
        初始化数据预处理器
        
        Args:
            enable_anomaly_detection: 是否启用异常值检测
            enable_missing_value_imputation: 是否启用缺失值插值
            enable_feature_engineering: 是否启用特征工程
            similarity_threshold: 去重相似度阈值
        """
        self.enable_anomaly_detection = enable_anomaly_detection
        self.enable_missing_value_imputation = enable_missing_value_imputation
        self.enable_feature_engineering = enable_feature_engineering
        self.similarity_threshold = similarity_threshold
        
        # 预处理统计
        self.preprocessing_stats = {
            'input_builds': 0,
            'cleaned_builds': 0,
            'duplicates_removed': 0,
            'anomalies_detected': 0,
            'missing_values_imputed': 0,
            'features_engineered': 0,
            'quality_upgrades': 0,
            'processing_start_time': None,
            'processing_end_time': None
        }
        
        # 游戏数据常量和验证规则
        self.game_constants = self._initialize_game_constants()
        self.validation_rules = self._initialize_validation_rules()
        
        # 统计数据缓存(用于插值和异常检测)
        self.class_stats: Dict[str, Dict[str, Any]] = {}
        self.skill_stats: Dict[str, Dict[str, Any]] = {}
        self.global_stats: Dict[str, Any] = {}
        
    def _initialize_game_constants(self) -> Dict[str, Any]:
        """初始化PoE2游戏常量"""
        return {
            'max_character_level': 100,
            'min_character_level': 1,
            'max_resistance': 90,  # 实际可达到的最高抗性
            'base_resistance_cap': 75,  # 基础抗性上限
            'chaos_resistance_penalty': -30,  # 基础混沌抗性惩罚
            'max_skill_level': 30,
            'max_gem_quality': 23,
            'max_skill_links': 6,
            
            # 合理的属性范围
            'reasonable_ranges': {
                'life': {'min': 2000, 'max': 12000},
                'energy_shield': {'min': 0, 'max': 8000},
                'dps': {'min': 10000, 'max': 50000000},  # 宽范围以包含各种构筑
                'critical_chance': {'min': 5.0, 'max': 95.0},
                'critical_multiplier': {'min': 150.0, 'max': 800.0},
                'accuracy': {'min': 80.0, 'max': 100.0}
            },
            
            # PoE2职业和升华
            'character_classes': [
                'Sorceress', 'Witch', 'Monk', 'Mercenary', 'Ranger', 'Warrior'
            ],
            'ascendancies': {
                'Sorceress': ['Chronomancer', 'Stormweaver'],
                'Witch': ['Infernalist', 'Blood Mage'],
                'Monk': ['Invoker', 'Acolyte of Chayula'],
                'Mercenary': ['Gemling Legionnaire', 'Witchhunter'],
                'Ranger': ['Deadeye', 'Pathfinder'],
                'Warrior': ['Titan', 'Warbringer']
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """初始化数据验证规则"""
        return {
            'required_fields': [
                'character_class', 'level', 'main_skill_setup'
            ],
            'numeric_fields': [
                'level', 'total_cost', 'popularity_rank'
            ],
            'string_fields': [
                'character_name', 'character_class', 'ascendancy'
            ],
            'list_fields': [
                'passive_keystones', 'tags'
            ]
        }
    
    async def preprocess_rag_data(self, raw_data: RAGDataModel) -> RAGDataModel:
        """
        预处理RAG数据
        
        Args:
            raw_data: 原始RAG数据模型
            
        Returns:
            处理后的RAG数据模型
        """
        self.preprocessing_stats['processing_start_time'] = datetime.now()
        self.preprocessing_stats['input_builds'] = len(raw_data.builds)
        
        logger.info(f"[Data Preprocessor] 开始预处理 {len(raw_data.builds)} 个构筑")
        
        try:
            # 1. 计算统计信息用于后续处理
            await self._compute_statistics(raw_data.builds)
            
            # 2. 数据清洗
            cleaned_builds = await self._clean_data(raw_data.builds)
            logger.info(f"[Data Preprocessor] 数据清洗完成，剩余 {len(cleaned_builds)} 个构筑")
            
            # 3. 去重处理
            unique_builds = await self._remove_duplicates(cleaned_builds)
            self.preprocessing_stats['duplicates_removed'] = len(cleaned_builds) - len(unique_builds)
            logger.info(f"[Data Preprocessor] 去重完成，移除 {self.preprocessing_stats['duplicates_removed']} 个重复构筑")
            
            # 4. 缺失值处理
            if self.enable_missing_value_imputation:
                imputed_builds = await self._impute_missing_values(unique_builds)
                logger.info(f"[Data Preprocessor] 缺失值插值完成")
            else:
                imputed_builds = unique_builds
            
            # 5. 异常值检测和处理
            if self.enable_anomaly_detection:
                filtered_builds = await self._detect_and_handle_anomalies(imputed_builds)
                logger.info(f"[Data Preprocessor] 异常值处理完成")
            else:
                filtered_builds = imputed_builds
            
            # 6. 数据标准化
            normalized_builds = await self._normalize_data(filtered_builds)
            logger.info(f"[Data Preprocessor] 数据标准化完成")
            
            # 7. 特征工程
            if self.enable_feature_engineering:
                enhanced_builds = await self._engineer_features(normalized_builds)
                logger.info(f"[Data Preprocessor] 特征工程完成")
            else:
                enhanced_builds = normalized_builds
            
            # 8. 质量评估和升级
            quality_assessed_builds = await self._assess_and_upgrade_quality(enhanced_builds)
            logger.info(f"[Data Preprocessor] 质量评估完成")
            
            # 9. 最终验证
            validated_builds = await self._final_validation(quality_assessed_builds)
            
            self.preprocessing_stats['cleaned_builds'] = len(validated_builds)
            self.preprocessing_stats['processing_end_time'] = datetime.now()
            
            # 创建处理后的RAG数据模型
            processed_data = RAGDataModel(
                builds=validated_builds,
                collection_metadata=raw_data.collection_metadata.copy(),
                processing_stats={
                    **raw_data.processing_stats,
                    'preprocessing': self.preprocessing_stats.copy()
                }
            )
            
            # 更新元数据
            processed_data.collection_metadata['preprocessing_timestamp'] = datetime.now()
            processed_data.collection_metadata['preprocessing_enabled'] = {
                'anomaly_detection': self.enable_anomaly_detection,
                'missing_value_imputation': self.enable_missing_value_imputation,
                'feature_engineering': self.enable_feature_engineering
            }
            
            logger.info(f"[Data Preprocessor] 预处理完成，最终输出 {len(validated_builds)} 个高质量构筑")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"[Data Preprocessor] 预处理过程出错: {e}")
            self.preprocessing_stats['processing_end_time'] = datetime.now()
            raise
    
    async def _compute_statistics(self, builds: List[PoE2BuildData]):
        """计算统计信息用于后续处理"""
        logger.info("[Data Preprocessor] 计算统计信息")
        
        # 按职业统计
        class_groups = defaultdict(list)
        skill_groups = defaultdict(list)
        
        # 全局统计数据
        all_levels = []
        all_dps = []
        all_life = []
        all_es = []
        all_costs = []
        
        for build in builds:
            if build.character_class:
                class_groups[build.character_class].append(build)
            
            if build.main_skill_setup.main_skill:
                skill_groups[build.main_skill_setup.main_skill].append(build)
            
            # 收集数值数据
            if build.level > 0:
                all_levels.append(build.level)
            if build.offensive_stats.dps > 0:
                all_dps.append(build.offensive_stats.dps)
            if build.defensive_stats.life > 0:
                all_life.append(build.defensive_stats.life)
            if build.defensive_stats.energy_shield > 0:
                all_es.append(build.defensive_stats.energy_shield)
            if build.total_cost > 0:
                all_costs.append(build.total_cost)
        
        # 计算职业统计
        for class_name, class_builds in class_groups.items():
            self.class_stats[class_name] = self._compute_build_group_stats(class_builds)
        
        # 计算技能统计
        for skill_name, skill_builds in skill_groups.items():
            self.skill_stats[skill_name] = self._compute_build_group_stats(skill_builds)
        
        # 计算全局统计
        self.global_stats = {
            'level': self._compute_numeric_stats(all_levels),
            'dps': self._compute_numeric_stats(all_dps),
            'life': self._compute_numeric_stats(all_life),
            'energy_shield': self._compute_numeric_stats(all_es),
            'cost': self._compute_numeric_stats(all_costs),
            'total_builds': len(builds),
            'unique_classes': len(class_groups),
            'unique_skills': len(skill_groups)
        }
        
        logger.info(f"[Data Preprocessor] 统计完成 - {len(class_groups)}职业, {len(skill_groups)}技能")
    
    def _compute_build_group_stats(self, builds: List[PoE2BuildData]) -> Dict[str, Any]:
        """计算构筑组统计信息"""
        if not builds:
            return {}
        
        levels = [b.level for b in builds if b.level > 0]
        dps_values = [b.offensive_stats.dps for b in builds if b.offensive_stats.dps > 0]
        life_values = [b.defensive_stats.life for b in builds if b.defensive_stats.life > 0]
        es_values = [b.defensive_stats.energy_shield for b in builds if b.defensive_stats.energy_shield > 0]
        costs = [b.total_cost for b in builds if b.total_cost > 0]
        
        return {
            'count': len(builds),
            'level': self._compute_numeric_stats(levels),
            'dps': self._compute_numeric_stats(dps_values),
            'life': self._compute_numeric_stats(life_values),
            'energy_shield': self._compute_numeric_stats(es_values),
            'cost': self._compute_numeric_stats(costs)
        }
    
    def _compute_numeric_stats(self, values: List[float]) -> Dict[str, float]:
        """计算数值统计信息"""
        if not values:
            return {'count': 0}
        
        values = [float(v) for v in values if v is not None]
        if not values:
            return {'count': 0}
        
        try:
            return {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                'min': min(values),
                'max': max(values),
                'q1': np.percentile(values, 25) if len(values) >= 4 else min(values),
                'q3': np.percentile(values, 75) if len(values) >= 4 else max(values)
            }
        except Exception as e:
            logger.warning(f"[Data Preprocessor] 计算统计信息失败: {e}")
            return {'count': len(values), 'mean': sum(values) / len(values)}
    
    async def _clean_data(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """数据清洗"""
        cleaned_builds = []
        
        for build in builds:
            try:
                # 清洗后的构筑
                cleaned_build = self._clean_single_build(build)
                
                if cleaned_build and self._validate_build_basic(cleaned_build):
                    cleaned_builds.append(cleaned_build)
                    
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 清洗构筑失败 {build.character_name}: {e}")
                continue
        
        return cleaned_builds
    
    def _clean_single_build(self, build: PoE2BuildData) -> Optional[PoE2BuildData]:
        """清洗单个构筑数据"""
        try:
            # 创建副本以避免修改原数据
            cleaned_data = asdict(build)
            
            # 清洗字符串字段
            cleaned_data['character_name'] = self._clean_string(build.character_name, max_length=100)
            cleaned_data['character_class'] = self._clean_character_class(build.character_class)
            cleaned_data['ascendancy'] = self._clean_ascendancy(build.ascendancy, cleaned_data['character_class'])
            
            # 清洗数值字段
            cleaned_data['level'] = self._clean_level(build.level)
            cleaned_data['total_cost'] = max(0.0, float(build.total_cost)) if build.total_cost else 0.0
            cleaned_data['popularity_rank'] = max(1, int(build.popularity_rank)) if build.popularity_rank else 999999
            
            # 清洗技能配置
            cleaned_data['main_skill_setup'] = self._clean_skill_setup(build.main_skill_setup)
            
            # 清洗属性数据
            cleaned_data['offensive_stats'] = self._clean_offensive_stats(build.offensive_stats)
            cleaned_data['defensive_stats'] = self._clean_defensive_stats(build.defensive_stats)
            
            # 清洗列表字段
            cleaned_data['passive_keystones'] = self._clean_string_list(build.passive_keystones)
            cleaned_data['tags'] = self._clean_string_list(build.tags)
            
            # 重建对象
            cleaned_build = PoE2BuildData(**cleaned_data)
            
            return cleaned_build
            
        except Exception as e:
            logger.warning(f"[Data Preprocessor] 清洗构筑数据失败: {e}")
            return None
    
    def _clean_string(self, value: str, max_length: int = 200) -> str:
        """清洗字符串"""
        if not value:
            return ""
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', str(value).strip())
        
        # 移除特殊字符(保留基本的字母数字和常用符号)
        cleaned = re.sub(r'[^\w\s\-_\(\)\[\]\'\",.!?]', '', cleaned)
        
        # 截断长度
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].strip()
        
        return cleaned
    
    def _clean_character_class(self, class_name: str) -> str:
        """清洗职业名称"""
        if not class_name:
            return "Unknown"
        
        cleaned = self._clean_string(class_name).title()
        
        # 验证是否为有效职业
        valid_classes = self.game_constants['character_classes']
        
        # 模糊匹配
        for valid_class in valid_classes:
            if valid_class.lower() in cleaned.lower() or cleaned.lower() in valid_class.lower():
                return valid_class
        
        # 如果找不到匹配，保留清洗后的字符串
        return cleaned if cleaned else "Unknown"
    
    def _clean_ascendancy(self, ascendancy: str, character_class: str) -> str:
        """清洗升华职业"""
        if not ascendancy:
            return ""
        
        cleaned = self._clean_string(ascendancy).title()
        
        # 验证升华职业是否匹配职业
        if character_class in self.game_constants['ascendancies']:
            valid_ascendancies = self.game_constants['ascendancies'][character_class]
            
            for valid_asc in valid_ascendancies:
                if valid_asc.lower() in cleaned.lower() or cleaned.lower() in valid_asc.lower():
                    return valid_asc
        
        return cleaned
    
    def _clean_level(self, level: int) -> int:
        """清洗等级数据"""
        if not level or level <= 0:
            return 85  # 默认等级
        
        # 限制在合理范围内
        return max(1, min(100, int(level)))
    
    def _clean_skill_setup(self, skill_setup: SkillGemSetup) -> SkillGemSetup:
        """清洗技能配置"""
        main_skill = self._clean_string(skill_setup.main_skill, max_length=50)
        
        # 清洗辅助宝石列表
        support_gems = []
        for gem in skill_setup.support_gems:
            cleaned_gem = self._clean_string(gem, max_length=50)
            if cleaned_gem and cleaned_gem not in support_gems:
                support_gems.append(cleaned_gem)
        
        # 限制辅助宝石数量
        support_gems = support_gems[:5]  # 最多5个辅助宝石
        
        return SkillGemSetup(
            main_skill=main_skill,
            support_gems=support_gems,
            skill_level=max(1, min(30, skill_setup.skill_level)),
            quality=max(0, min(23, skill_setup.quality)),
            links=max(1, min(6, skill_setup.links))
        )
    
    def _clean_offensive_stats(self, stats: OffensiveStats) -> OffensiveStats:
        """清洗攻击属性"""
        ranges = self.game_constants['reasonable_ranges']
        
        return OffensiveStats(
            dps=max(0.0, float(stats.dps)) if stats.dps else 0.0,
            average_damage=max(0.0, float(stats.average_damage)) if stats.average_damage else 0.0,
            attack_speed=max(0.1, float(stats.attack_speed)) if stats.attack_speed else 1.0,
            critical_chance=max(5.0, min(95.0, float(stats.critical_chance))) if stats.critical_chance else 5.0,
            critical_multiplier=max(150.0, min(800.0, float(stats.critical_multiplier))) if stats.critical_multiplier else 150.0,
            accuracy=max(80.0, min(100.0, float(stats.accuracy))) if stats.accuracy else 90.0
        )
    
    def _clean_defensive_stats(self, stats: DefensiveStats) -> DefensiveStats:
        """清洗防御属性"""
        return DefensiveStats(
            life=max(0, int(stats.life)) if stats.life else 0,
            energy_shield=max(0, int(stats.energy_shield)) if stats.energy_shield else 0,
            fire_resistance=max(-100, min(90, int(stats.fire_resistance))) if stats.fire_resistance else 75,
            cold_resistance=max(-100, min(90, int(stats.cold_resistance))) if stats.cold_resistance else 75,
            lightning_resistance=max(-100, min(90, int(stats.lightning_resistance))) if stats.lightning_resistance else 75,
            chaos_resistance=max(-100, min(90, int(stats.chaos_resistance))) if stats.chaos_resistance else -30,
            armour=max(0, int(stats.armour)) if stats.armour else 0,
            evasion=max(0, int(stats.evasion)) if stats.evasion else 0,
            block_chance=max(0.0, min(75.0, float(stats.block_chance))) if stats.block_chance else 0.0,
            spell_block_chance=max(0.0, min(75.0, float(stats.spell_block_chance))) if stats.spell_block_chance else 0.0
        )
    
    def _clean_string_list(self, string_list: List[str]) -> List[str]:
        """清洗字符串列表"""
        if not string_list:
            return []
        
        cleaned_list = []
        for item in string_list:
            cleaned_item = self._clean_string(item, max_length=100)
            if cleaned_item and cleaned_item not in cleaned_list:
                cleaned_list.append(cleaned_item)
        
        return cleaned_list[:20]  # 限制列表长度
    
    def _validate_build_basic(self, build: PoE2BuildData) -> bool:
        """基础验证构筑数据"""
        # 必需字段检查
        if not build.character_class or build.character_class == "Unknown":
            return False
        
        if build.level < 1 or build.level > 100:
            return False
        
        # 主技能检查
        if not build.main_skill_setup.main_skill:
            return False
        
        return True
    
    async def _remove_duplicates(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """去重处理"""
        logger.info("[Data Preprocessor] 开始去重处理")
        
        unique_builds = []
        seen_hashes = set()
        
        # 基于相似度哈希的快速去重
        for build in builds:
            if build.similarity_hash in seen_hashes:
                continue
            
            # 检查与已有构筑的相似度
            is_duplicate = False
            for existing_build in unique_builds:
                similarity = build.calculate_similarity_score(existing_build)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    # 保留质量更高的构筑
                    if build.data_quality.value > existing_build.data_quality.value:
                        unique_builds.remove(existing_build)
                        unique_builds.append(build)
                        seen_hashes.add(build.similarity_hash)
                    break
            
            if not is_duplicate:
                unique_builds.append(build)
                seen_hashes.add(build.similarity_hash)
        
        return unique_builds
    
    async def _impute_missing_values(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """缺失值插值"""
        logger.info("[Data Preprocessor] 开始缺失值插值")
        
        imputed_builds = []
        imputation_count = 0
        
        for build in builds:
            try:
                imputed_build = self._impute_single_build(build)
                if imputed_build != build:  # 检查是否有修改
                    imputation_count += 1
                imputed_builds.append(imputed_build)
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 插值失败 {build.character_name}: {e}")
                imputed_builds.append(build)  # 保留原始数据
        
        self.preprocessing_stats['missing_values_imputed'] = imputation_count
        return imputed_builds
    
    def _impute_single_build(self, build: PoE2BuildData) -> PoE2BuildData:
        """对单个构筑进行缺失值插值"""
        modified = False
        
        # 创建副本
        build_dict = asdict(build)
        
        # 插值生命值
        if build.defensive_stats.life == 0:
            imputed_life = self._impute_life_value(build)
            if imputed_life > 0:
                build_dict['defensive_stats']['life'] = imputed_life
                modified = True
        
        # 插值能量护盾
        if build.defensive_stats.energy_shield == 0:
            imputed_es = self._impute_energy_shield_value(build)
            if imputed_es > 0:
                build_dict['defensive_stats']['energy_shield'] = imputed_es
                modified = True
        
        # 插值DPS
        if build.offensive_stats.dps == 0:
            imputed_dps = self._impute_dps_value(build)
            if imputed_dps > 0:
                build_dict['offensive_stats']['dps'] = imputed_dps
                modified = True
        
        # 插值成本
        if build.total_cost == 0:
            imputed_cost = self._impute_cost_value(build)
            if imputed_cost > 0:
                build_dict['total_cost'] = imputed_cost
                modified = True
        
        # 如果有修改，重建对象
        if modified:
            return PoE2BuildData(**build_dict)
        else:
            return build
    
    def _impute_life_value(self, build: PoE2BuildData) -> int:
        """插值生命值"""
        # 基于职业和等级的统计数据插值
        if build.character_class in self.class_stats:
            class_life_stats = self.class_stats[build.character_class].get('life', {})
            if 'mean' in class_life_stats:
                base_life = class_life_stats['mean']
                # 根据等级调整
                level_factor = build.level / 85  # 85级为基准
                return int(base_life * level_factor)
        
        # 使用全局统计
        if 'life' in self.global_stats and 'mean' in self.global_stats['life']:
            return int(self.global_stats['life']['mean'])
        
        # 默认值
        return 5000
    
    def _impute_energy_shield_value(self, build: PoE2BuildData) -> int:
        """插值能量护盾值"""
        # ES通常与职业相关，某些职业更依赖ES
        es_heavy_classes = ['Witch', 'Sorceress']
        
        if build.character_class in es_heavy_classes:
            if build.character_class in self.class_stats:
                class_es_stats = self.class_stats[build.character_class].get('energy_shield', {})
                if 'mean' in class_es_stats:
                    return int(class_es_stats['mean'])
        
        # 非ES职业通常ES较低
        return 0
    
    def _impute_dps_value(self, build: PoE2BuildData) -> float:
        """插值DPS值"""
        # 基于主技能的统计数据
        if build.main_skill_setup.main_skill in self.skill_stats:
            skill_dps_stats = self.skill_stats[build.main_skill_setup.main_skill].get('dps', {})
            if 'mean' in skill_dps_stats:
                return skill_dps_stats['mean']
        
        # 基于职业统计
        if build.character_class in self.class_stats:
            class_dps_stats = self.class_stats[build.character_class].get('dps', {})
            if 'mean' in class_dps_stats:
                return class_dps_stats['mean']
        
        # 全局统计
        if 'dps' in self.global_stats and 'mean' in self.global_stats['dps']:
            return self.global_stats['dps']['mean']
        
        return 100000.0  # 默认值
    
    def _impute_cost_value(self, build: PoE2BuildData) -> float:
        """插值成本值"""
        # 基于构筑目标推断成本
        goal_cost_estimates = {
            BuildGoal.BUDGET_FRIENDLY: 3.0,
            BuildGoal.LEAGUE_START: 1.0,
            BuildGoal.CLEAR_SPEED: 10.0,
            BuildGoal.BOSS_KILLING: 15.0,
            BuildGoal.ENDGAME_CONTENT: 20.0,
            BuildGoal.BALANCED: 8.0
        }
        
        return goal_cost_estimates.get(build.build_goal, 5.0)
    
    async def _detect_and_handle_anomalies(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """异常值检测和处理"""
        logger.info("[Data Preprocessor] 开始异常值检测")
        
        filtered_builds = []
        anomaly_count = 0
        
        for build in builds:
            try:
                if self._is_anomaly(build):
                    # 尝试修正异常值
                    corrected_build = self._correct_anomaly(build)
                    if corrected_build:
                        filtered_builds.append(corrected_build)
                        anomaly_count += 1
                    # 否则跳过该构筑
                else:
                    filtered_builds.append(build)
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 异常检测失败 {build.character_name}: {e}")
                filtered_builds.append(build)  # 保留原始数据
        
        self.preprocessing_stats['anomalies_detected'] = anomaly_count
        return filtered_builds
    
    def _is_anomaly(self, build: PoE2BuildData) -> bool:
        """判断是否为异常值"""
        # 检查DPS异常
        if build.offensive_stats.dps > 0:
            if build.offensive_stats.dps > 100000000:  # 1亿DPS明显异常
                return True
            if build.offensive_stats.dps < 1000:  # 1000DPS过低
                return True
        
        # 检查生命值异常
        if build.defensive_stats.life > 0:
            if build.defensive_stats.life > 50000:  # 5万生命异常
                return True
            if build.defensive_stats.life < 1000:  # 1000生命过低
                return True
        
        # 检查等级异常
        if build.level > 100 or build.level < 1:
            return True
        
        # 检查成本异常
        if build.total_cost > 1000:  # 1000 divine成本异常高
            return True
        
        return False
    
    def _correct_anomaly(self, build: PoE2BuildData) -> Optional[PoE2BuildData]:
        """修正异常值"""
        build_dict = asdict(build)
        corrected = False
        
        # 修正DPS异常
        if build.offensive_stats.dps > 100000000:
            build_dict['offensive_stats']['dps'] = 1000000.0  # 设为合理值
            corrected = True
        elif 0 < build.offensive_stats.dps < 1000:
            build_dict['offensive_stats']['dps'] = 50000.0
            corrected = True
        
        # 修正生命值异常
        if build.defensive_stats.life > 50000:
            build_dict['defensive_stats']['life'] = 8000
            corrected = True
        elif 0 < build.defensive_stats.life < 1000:
            build_dict['defensive_stats']['life'] = 4000
            corrected = True
        
        # 修正等级异常
        if build.level > 100:
            build_dict['level'] = 95
            corrected = True
        elif build.level < 1:
            build_dict['level'] = 85
            corrected = True
        
        # 修正成本异常
        if build.total_cost > 1000:
            build_dict['total_cost'] = 50.0
            corrected = True
        
        if corrected:
            return PoE2BuildData(**build_dict)
        else:
            return None  # 无法修正，丢弃
    
    async def _normalize_data(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """数据标准化"""
        logger.info("[Data Preprocessor] 开始数据标准化")
        
        # 数据标准化主要是格式统一，数值范围已在清洗阶段处理
        normalized_builds = []
        
        for build in builds:
            try:
                normalized_build = self._normalize_single_build(build)
                normalized_builds.append(normalized_build)
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 标准化失败 {build.character_name}: {e}")
                normalized_builds.append(build)
        
        return normalized_builds
    
    def _normalize_single_build(self, build: PoE2BuildData) -> PoE2BuildData:
        """标准化单个构筑"""
        # 确保字符串字段格式一致
        build_dict = asdict(build)
        
        # 标准化职业名称格式
        build_dict['character_class'] = build.character_class.title()
        if build.ascendancy:
            build_dict['ascendancy'] = build.ascendancy.title()
        
        # 标准化技能名称格式
        if build.main_skill_setup.main_skill:
            build_dict['main_skill_setup']['main_skill'] = build.main_skill_setup.main_skill.title()
        
        # 标准化辅助宝石名称
        support_gems = []
        for gem in build.main_skill_setup.support_gems:
            support_gems.append(gem.title())
        build_dict['main_skill_setup']['support_gems'] = support_gems
        
        # 标准化关键天赋名称
        keystones = []
        for keystone in build.passive_keystones:
            keystones.append(keystone.title())
        build_dict['passive_keystones'] = keystones
        
        return PoE2BuildData(**build_dict)
    
    async def _engineer_features(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """特征工程"""
        logger.info("[Data Preprocessor] 开始特征工程")
        
        enhanced_builds = []
        feature_count = 0
        
        for build in builds:
            try:
                enhanced_build = self._engineer_single_build_features(build)
                enhanced_builds.append(enhanced_build)
                if enhanced_build != build:
                    feature_count += 1
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 特征工程失败 {build.character_name}: {e}")
                enhanced_builds.append(build)
        
        self.preprocessing_stats['features_engineered'] = feature_count
        return enhanced_builds
    
    def _engineer_single_build_features(self, build: PoE2BuildData) -> PoE2BuildData:
        """对单个构筑进行特征工程"""
        # 增强成功指标
        enhanced_metrics = self._calculate_enhanced_success_metrics(build)
        
        # 更新预算等级
        enhanced_budget_tier = self._determine_budget_tier(build.total_cost)
        
        # 生成增强标签
        enhanced_tags = self._generate_enhanced_tags(build)
        
        # 重新生成构筑描述(包含更多信息)
        enhanced_description = self._generate_enhanced_description(build)
        
        # 创建增强的构筑对象
        return replace(build,
                      success_metrics=enhanced_metrics,
                      budget_tier=enhanced_budget_tier,
                      tags=enhanced_tags,
                      build_description=enhanced_description)
    
    def _calculate_enhanced_success_metrics(self, build: PoE2BuildData) -> SuccessMetrics:
        """计算增强的成功指标"""
        metrics = SuccessMetrics()
        
        # 等级成就度
        metrics.level_achievement = min(build.level / 95.0, 1.0)  # 95级为优秀
        
        # 装备质量评估(基于成本)
        if build.total_cost > 0:
            # 成本效益曲线，20 divine为中等，50+为高端
            if build.total_cost <= 5:
                metrics.gear_quality_score = 0.3
            elif build.total_cost <= 15:
                metrics.gear_quality_score = 0.6
            elif build.total_cost <= 30:
                metrics.gear_quality_score = 0.8
            else:
                metrics.gear_quality_score = 1.0
        else:
            metrics.gear_quality_score = 0.1
        
        # 构筑完整度(基于可用数据)
        completeness_factors = []
        completeness_factors.append(1.0 if build.main_skill_setup.main_skill else 0.0)
        completeness_factors.append(1.0 if build.offensive_stats.dps > 0 else 0.0)
        completeness_factors.append(1.0 if build.defensive_stats.life > 0 else 0.0)
        completeness_factors.append(1.0 if len(build.main_skill_setup.support_gems) > 0 else 0.0)
        completeness_factors.append(1.0 if len(build.passive_keystones) > 0 else 0.0)
        
        metrics.build_completeness = sum(completeness_factors) / len(completeness_factors)
        
        # 流行度评估(基于排名)
        if build.popularity_rank > 0:
            # 排名越靠前分数越高，使用对数缩放
            metrics.popularity_score = max(0.0, 1.0 - (build.popularity_rank - 1) / 1000.0)
        else:
            metrics.popularity_score = 0.0
        
        # Meta符合度(基于技能流行度)
        if build.main_skill_setup.main_skill in self.skill_stats:
            skill_count = self.skill_stats[build.main_skill_setup.main_skill].get('count', 0)
            total_builds = self.global_stats.get('total_builds', 1)
            metrics.meta_alignment = skill_count / total_builds
        else:
            metrics.meta_alignment = 0.1
        
        # 成本效益
        if build.offensive_stats.dps > 0 and build.total_cost > 0:
            dps_per_divine = build.offensive_stats.dps / build.total_cost
            # 标准化到0-1范围，100k DPS per divine为满分
            metrics.cost_effectiveness = min(dps_per_divine / 100000, 1.0)
        else:
            metrics.cost_effectiveness = 0.5
        
        return metrics
    
    def _determine_budget_tier(self, cost: float) -> str:
        """确定预算等级"""
        if cost <= 0:
            return "unknown"
        elif cost <= 5:
            return "budget"
        elif cost <= 20:
            return "medium"
        else:
            return "expensive"
    
    def _generate_enhanced_tags(self, build: PoE2BuildData) -> List[str]:
        """生成增强标签"""
        tags = set(build.tags) if build.tags else set()
        
        # 添加性能标签
        if build.offensive_stats.dps > 0:
            if build.offensive_stats.dps > 5000000:
                tags.add("high_dps")
            elif build.offensive_stats.dps > 1000000:
                tags.add("medium_dps")
            else:
                tags.add("low_dps")
        
        # 添加防御标签
        ehp = build.defensive_stats.effective_health_pool()
        if ehp > 8000:
            tags.add("tanky")
        elif ehp > 5000:
            tags.add("balanced_defense")
        else:
            tags.add("glass_cannon")
        
        # 添加成本标签
        tags.add(f"budget_{build.budget_tier}")
        
        # 添加构筑目标标签
        tags.add(build.build_goal.value)
        
        # 添加数据质量标签
        tags.add(f"quality_{build.data_quality.value}")
        
        # 添加技能类型标签
        skill_tags = self._infer_skill_tags(build.main_skill_setup.main_skill)
        tags.update(skill_tags)
        
        return sorted(list(tags))
    
    def _infer_skill_tags(self, skill_name: str) -> Set[str]:
        """从技能名称推断标签"""
        tags = set()
        
        if not skill_name:
            return tags
        
        skill_lower = skill_name.lower()
        
        # 技能类型标签
        if any(word in skill_lower for word in ['arrow', 'shot', 'projectile']):
            tags.add("projectile")
        
        if any(word in skill_lower for word in ['fire', 'flame', 'burn', 'ignite']):
            tags.add("fire_damage")
        
        if any(word in skill_lower for word in ['ice', 'cold', 'freeze', 'glacial']):
            tags.add("cold_damage")
        
        if any(word in skill_lower for word in ['lightning', 'shock', 'spark', 'arc']):
            tags.add("lightning_damage")
        
        if any(word in skill_lower for word in ['minion', 'skeleton', 'zombie', 'summon']):
            tags.add("minion_build")
        
        if any(word in skill_lower for word in ['aura', 'curse', 'buff']):
            tags.add("support_skill")
        
        return tags
    
    def _generate_enhanced_description(self, build: PoE2BuildData) -> str:
        """生成增强的构筑描述"""
        parts = []
        
        # 基础信息
        class_info = f"{build.character_class}"
        if build.ascendancy:
            class_info += f" ({build.ascendancy})"
        parts.append(f"职业: {class_info}")
        
        parts.append(f"等级: {build.level}")
        
        # 技能信息
        if build.main_skill_setup.main_skill:
            skill_info = f"主技能: {build.main_skill_setup.main_skill}"
            if build.main_skill_setup.support_gems:
                supports = ", ".join(build.main_skill_setup.support_gems[:3])
                skill_info += f" + {supports}"
            parts.append(skill_info)
        
        # 属性信息
        if build.offensive_stats.dps > 0:
            parts.append(f"DPS: {build.offensive_stats.dps:,.0f}")
        
        ehp = build.defensive_stats.effective_health_pool()
        if ehp > 0:
            parts.append(f"有效生命: {ehp:,}")
        
        # 成本和性价比
        if build.total_cost > 0:
            cost_info = f"成本: {build.total_cost:.1f} divine"
            if build.success_metrics.cost_effectiveness > 0:
                cost_info += f" (性价比: {build.success_metrics.cost_effectiveness:.2f})"
            parts.append(cost_info)
        
        # 构筑目标和质量
        parts.append(f"目标: {build.build_goal.value}")
        parts.append(f"成功分数: {build.success_metrics.overall_score():.2f}")
        
        # 数据来源和质量
        parts.append(f"数据源: {build.data_source} ({build.data_quality.value})")
        
        return " | ".join(parts)
    
    async def _assess_and_upgrade_quality(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """评估和升级数据质量"""
        logger.info("[Data Preprocessor] 开始质量评估和升级")
        
        upgraded_builds = []
        upgrade_count = 0
        
        for build in builds:
            try:
                new_quality = self._assess_data_quality_enhanced(build)
                if new_quality != build.data_quality:
                    upgraded_build = replace(build, data_quality=new_quality)
                    upgraded_builds.append(upgraded_build)
                    upgrade_count += 1
                else:
                    upgraded_builds.append(build)
            except Exception as e:
                logger.warning(f"[Data Preprocessor] 质量评估失败 {build.character_name}: {e}")
                upgraded_builds.append(build)
        
        self.preprocessing_stats['quality_upgrades'] = upgrade_count
        return upgraded_builds
    
    def _assess_data_quality_enhanced(self, build: PoE2BuildData) -> DataQuality:
        """增强的数据质量评估"""
        score = 0
        max_score = 10
        
        # 基础信息完整性 (3分)
        if build.character_class and build.character_class != "Unknown":
            score += 1
        if build.ascendancy:
            score += 1
        if 1 <= build.level <= 100:
            score += 1
        
        # 技能信息完整性 (2分)
        if build.main_skill_setup.main_skill and build.main_skill_setup.main_skill != "Unknown":
            score += 1
        if len(build.main_skill_setup.support_gems) > 0:
            score += 1
        
        # 属性数据完整性 (3分)
        if build.offensive_stats.dps > 0:
            score += 1
        if build.defensive_stats.life > 0 or build.defensive_stats.energy_shield > 0:
            score += 1
        if build.defensive_stats.is_resistance_capped():
            score += 1
        
        # 构筑深度信息 (2分)
        if len(build.passive_keystones) > 0:
            score += 1
        if build.total_cost > 0:
            score += 1
        
        # 根据分数确定质量等级
        if score >= 9:
            return DataQuality.HIGH
        elif score >= 6:
            return DataQuality.MEDIUM
        elif score >= 3:
            return DataQuality.LOW
        else:
            return DataQuality.INVALID
    
    async def _final_validation(self, builds: List[PoE2BuildData]) -> List[PoE2BuildData]:
        """最终验证"""
        logger.info("[Data Preprocessor] 开始最终验证")
        
        valid_builds = []
        
        for build in builds:
            if self._final_validate_build(build):
                valid_builds.append(build)
        
        logger.info(f"[Data Preprocessor] 最终验证完成，{len(valid_builds)}/{len(builds)} 通过验证")
        return valid_builds
    
    def _final_validate_build(self, build: PoE2BuildData) -> bool:
        """最终验证单个构筑"""
        # 排除无效数据质量的构筑
        if build.data_quality == DataQuality.INVALID:
            return False
        
        # 确保基本字段存在
        if not build.character_class or build.character_class == "Unknown":
            return False
        
        if not build.main_skill_setup.main_skill or build.main_skill_setup.main_skill == "Unknown":
            return False
        
        # 确保有意义的属性数据
        if build.offensive_stats.dps <= 0 and build.defensive_stats.life <= 0:
            return False
        
        return True
    
    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """获取预处理统计信息"""
        stats = self.preprocessing_stats.copy()
        
        if stats['processing_start_time'] and stats['processing_end_time']:
            duration = stats['processing_end_time'] - stats['processing_start_time']
            stats['processing_duration_seconds'] = duration.total_seconds()
        
        # 计算处理效率
        if stats['input_builds'] > 0:
            stats['data_retention_rate'] = stats['cleaned_builds'] / stats['input_builds']
            stats['duplicate_rate'] = stats['duplicates_removed'] / stats['input_builds']
            stats['anomaly_rate'] = stats['anomalies_detected'] / stats['input_builds']
        
        return stats

# 测试函数
def test_data_preprocessing():
    """测试数据预处理功能"""
    import asyncio
    
    async def run_test():
        # 创建测试数据
        test_builds = [
            PoE2BuildData(
                character_name="Test Ranger 1",
                character_class="Ranger",
                ascendancy="Deadeye",
                level=85,
                main_skill_setup=SkillGemSetup(
                    main_skill="Lightning Arrow",
                    support_gems=["Pierce", "Lightning Penetration"]
                ),
                offensive_stats=OffensiveStats(dps=1500000),
                defensive_stats=DefensiveStats(life=6000, energy_shield=0),
                total_cost=12.5,
                data_quality=DataQuality.MEDIUM
            ),
            # 重复构筑(高相似度)
            PoE2BuildData(
                character_name="Test Ranger 2",
                character_class="Ranger",
                ascendancy="Deadeye",
                level=87,
                main_skill_setup=SkillGemSetup(
                    main_skill="Lightning Arrow",
                    support_gems=["Pierce", "Lightning Penetration"]
                ),
                offensive_stats=OffensiveStats(dps=1600000),
                defensive_stats=DefensiveStats(life=6200, energy_shield=0),
                total_cost=15.0,
                data_quality=DataQuality.LOW
            ),
            # 异常值构筑
            PoE2BuildData(
                character_name="Anomaly Build",
                character_class="Witch",
                level=200,  # 异常等级
                main_skill_setup=SkillGemSetup(main_skill="Fireball"),
                offensive_stats=OffensiveStats(dps=999999999),  # 异常DPS
                defensive_stats=DefensiveStats(life=0),  # 缺失生命值
                total_cost=0,  # 缺失成本
                data_quality=DataQuality.LOW
            )
        ]
        
        # 创建RAG数据模型
        test_data = RAGDataModel(
            builds=test_builds,
            collection_metadata={'test_source': 'unit_test'}
        )
        
        # 创建预处理器
        preprocessor = PoE2DataPreprocessor(
            enable_anomaly_detection=True,
            enable_missing_value_imputation=True,
            enable_feature_engineering=True,
            similarity_threshold=0.85
        )
        
        # 执行预处理
        print("=== 开始数据预处理测试 ===")
        processed_data = await preprocessor.preprocess_rag_data(test_data)
        
        # 显示结果
        print(f"\n=== 预处理结果 ===")
        print(f"输入构筑数: {len(test_data.builds)}")
        print(f"输出构筑数: {len(processed_data.builds)}")
        
        for i, build in enumerate(processed_data.builds):
            print(f"\n构筑 {i+1}: {build.character_name}")
            print(f"  职业: {build.character_class} ({build.ascendancy})")
            print(f"  等级: {build.level}")
            print(f"  主技能: {build.main_skill_setup.main_skill}")
            print(f"  DPS: {build.offensive_stats.dps:,.0f}")
            print(f"  生命: {build.defensive_stats.life}")
            print(f"  成本: {build.total_cost}")
            print(f"  数据质量: {build.data_quality.value}")
            print(f"  成功分数: {build.success_metrics.overall_score():.2f}")
        
        # 预处理统计
        stats = preprocessor.get_preprocessing_stats()
        print(f"\n=== 预处理统计 ===")
        print(f"数据保留率: {stats.get('data_retention_rate', 0):.2%}")
        print(f"去重数量: {stats['duplicates_removed']}")
        print(f"异常值检测: {stats['anomalies_detected']}")
        print(f"缺失值插值: {stats['missing_values_imputed']}")
        print(f"特征工程: {stats['features_engineered']}")
        print(f"质量升级: {stats['quality_upgrades']}")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_data_preprocessing()