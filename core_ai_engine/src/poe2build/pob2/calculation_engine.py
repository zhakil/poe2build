"""
PoB2计算引擎包装器 - 调用Path of Building Community (PoE2)进行精确计算
"""

import subprocess
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import threading

from .local_client import PoB2LocalClient
from .build_importer import PoB2BuildImporter

logger = logging.getLogger(__name__)


class PoB2CalculationEngine:
    """PoB2计算引擎包装器"""
    
    def __init__(self, pob2_client: Optional[PoB2LocalClient] = None):
        self.pob2_client = pob2_client or PoB2LocalClient()
        self.build_importer = PoB2BuildImporter()
        self.calculation_timeout = 30  # 30秒超时
        self.temp_files: List[Path] = []
        
    def is_available(self) -> bool:
        """检查计算引擎是否可用"""
        return self.pob2_client.is_available()
    
    def calculate_build_stats(self, build_data: Dict, config: Optional[Dict] = None) -> Dict:
        """
        计算构筑统计数据
        
        Args:
            build_data: 构筑数据
            config: 计算配置 (敌人等级, Boss遭遇等)
            
        Returns:
            Dict: 计算结果
        """
        
        if not self.is_available():
            return self._get_fallback_calculation(build_data)
        
        try:
            # 应用计算配置
            if config:
                build_data = self._apply_calculation_config(build_data, config)
            
            # 生成临时构筑文件
            temp_build_file = self._create_temp_build_file(build_data)
            
            # 执行PoB2计算
            calculation_result = self._execute_pob2_calculation(temp_build_file)
            
            # 解析计算结果
            parsed_stats = self._parse_calculation_result(calculation_result)
            
            return {
                'success': True,
                'stats': parsed_stats,
                'calculation_method': 'PoB2_Local',
                'engine_version': self.pob2_client.version_info,
                'calculation_time': calculation_result.get('calculation_time', 0)
            }
            
        except Exception as e:
            logger.error(f"PoB2计算失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': self._get_fallback_calculation(build_data)
            }
        finally:
            self._cleanup_temp_files()
    
    def _apply_calculation_config(self, build_data: Dict, config: Dict) -> Dict:
        """应用计算配置到构筑数据"""
        
        # 深拷贝构筑数据
        import copy
        modified_build = copy.deepcopy(build_data)
        
        # 更新配置部分
        if 'config' not in modified_build:
            modified_build['config'] = {}
        
        # 应用常用配置选项
        config_mapping = {
            'enemy_level': 'enemyLevel',
            'boss_encounter': 'conditionBossEncounter', 
            'player_stationary': 'conditionStationary',
            'moving': 'conditionMoving',
            'onslaught': 'buffOnslaught',
            'enemy_moving': 'conditionEnemyMoving',
            'power_charges': 'PowerCharges',
            'frenzy_charges': 'FrenzyCharges',
            'endurance_charges': 'EnduranceCharges'
        }
        
        for config_key, pob2_key in config_mapping.items():
            if config_key in config:
                modified_build['config'][pob2_key] = config[config_key]
        
        # 应用药剂配置
        if 'active_flasks' in config:
            for flask in config['active_flasks']:
                modified_build['config'][f'flask{flask}'] = True
        
        # 应用Buff配置
        if 'active_buffs' in config:
            for buff in config['active_buffs']:
                modified_build['config'][f'condition{buff}'] = True
        
        return modified_build
    
    def _create_temp_build_file(self, build_data: Dict) -> Path:
        """创建临时构筑文件"""
        
        # 生成PoB2 XML格式
        xml_content = self._build_data_to_xml(build_data)
        
        # 创建临时文件
        temp_file = self.pob2_client.create_temp_build_file(xml_content, 'xml')
        self.temp_files.append(temp_file)
        
        return temp_file
    
    def _build_data_to_xml(self, build_data: Dict) -> str:
        """将构筑数据转换为PoB2 XML格式"""
        
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_parts.append('<PathOfBuilding>')
        
        # Build信息
        character = build_data.get('character', {})
        xml_parts.append(f'<Build level="{character.get("level", 90)}" '
                        f'targetVersion="3_0" '
                        f'className="{character.get("class", "")}" '
                        f'ascendClassName="{character.get("ascendancy", "")}" '
                        f'mainSocketGroup="1" '
                        f'viewMode="TREE"/>')
        
        # 技能配置
        xml_parts.append('<Skills>')
        xml_parts.append('<SkillSet id="1">')
        
        for i, skill in enumerate(build_data.get('skills', []), 1):
            main_skill = skill.get('main_skill', {})
            if main_skill.get('name'):
                xml_parts.append(f'<Gem level="{main_skill.get("level", 1)}" '
                                f'quality="{main_skill.get("quality", 0)}" '
                                f'skillId="{main_skill["name"]}" '
                                f'enabled="true"/>')
                
                # 添加辅助宝石
                for support in skill.get('support_gems', []):
                    xml_parts.append(f'<Gem level="{support.get("level", 1)}" '
                                    f'quality="{support.get("quality", 0)}" '
                                    f'skillId="{support["name"]}" '
                                    f'support="true" '
                                    f'enabled="true"/>')
        
        xml_parts.append('</SkillSet>')
        xml_parts.append('</Skills>')
        
        # 装备配置
        xml_parts.append('<Items>')
        
        slot_mapping = {
            'main_hand': 'Weapon 1',
            'off_hand': 'Weapon 2',
            'helmet': 'Helmet',
            'body_armour': 'Body Armour',
            'gloves': 'Gloves',
            'boots': 'Boots',
            'belt': 'Belt',
            'ring_1': 'Ring 1',
            'ring_2': 'Ring 2',
            'amulet': 'Amulet'
        }
        
        items = build_data.get('items', {})
        for slot, pob_slot in slot_mapping.items():
            item = items.get(slot)
            if item and item.get('name'):
                xml_parts.append(f'<Item slot="{pob_slot}" '
                                f'name="{item["name"]}" '
                                f'type="{item.get("type", "")}" '
                                f'rarity="{item.get("rarity", "normal")}">')
                if item.get('text'):
                    xml_parts.append(item['text'])
                xml_parts.append('</Item>')
        
        xml_parts.append('</Items>')
        
        # 天赋树配置
        passive_tree = build_data.get('passive_tree', {})
        if passive_tree.get('allocated_nodes'):
            nodes_str = ','.join(map(str, passive_tree['allocated_nodes']))
            xml_parts.append(f'<Tree classId="{passive_tree.get("class_id", "0")}" '
                            f'ascendClassName="{passive_tree.get("ascendancy_name", "")}">')
            xml_parts.append(nodes_str)
            xml_parts.append('</Tree>')
        
        # 配置选项
        config = build_data.get('config', {})
        if config:
            xml_parts.append('<Config>')
            for key, value in config.items():
                xml_parts.append(f'<Input name="{key}" value="{value}"/>')
            xml_parts.append('</Config>')
        
        xml_parts.append('</PathOfBuilding>')
        
        return '\\n'.join(xml_parts)
    
    def _execute_pob2_calculation(self, build_file: Path) -> Dict:
        """执行PoB2计算"""
        
        start_time = time.time()
        
        try:
            # PoB2命令行参数
            cmd = [
                str(self.pob2_client.executable_path),
                '--calculate',
                '--input', str(build_file),
                '--output', 'json'
            ]
            
            logger.debug(f"执行PoB2计算命令: {cmd}")
            
            # 执行计算
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.calculation_timeout,
                cwd=self.pob2_client.installation_path
            )
            
            calculation_time = time.time() - start_time
            
            if result.returncode == 0:
                # 解析JSON输出
                try:
                    output_data = json.loads(result.stdout)
                    output_data['calculation_time'] = calculation_time
                    return output_data
                except json.JSONDecodeError as e:
                    # 可能是文本格式输出，尝试解析
                    return self._parse_text_output(result.stdout, calculation_time)
            else:
                raise subprocess.CalledProcessError(
                    result.returncode, 
                    cmd, 
                    result.stdout, 
                    result.stderr
                )
                
        except subprocess.TimeoutExpired:
            raise Exception(f"PoB2计算超时 (>{self.calculation_timeout}s)")
        except Exception as e:
            raise Exception(f"PoB2计算执行失败: {e}")
    
    def _parse_text_output(self, output_text: str, calculation_time: float) -> Dict:
        """解析文本格式的PoB2输出"""
        
        # 基础正则表达式模式
        import re
        
        patterns = {
            'total_dps': r'Total DPS:\\s*(\\d+(?:,\\d{3})*(?:\\.\\d+)?)',
            'average_hit': r'Average Hit:\\s*(\\d+(?:,\\d{3})*(?:\\.\\d+)?)',
            'crit_chance': r'Crit Chance:\\s*(\\d+(?:\\.\\d+)?)%',
            'crit_multiplier': r'Crit Multiplier:\\s*(\\d+(?:\\.\\d+)?)%',
            'total_life': r'Total Life:\\s*(\\d+(?:,\\d{3})*)',
            'energy_shield': r'Energy Shield:\\s*(\\d+(?:,\\d{3})*)',
            'fire_resist': r'Fire Resistance:\\s*(-?\\d+)%',
            'cold_resist': r'Cold Resistance:\\s*(-?\\d+)%',
            'lightning_resist': r'Lightning Resistance:\\s*(-?\\d+)%',
            'chaos_resist': r'Chaos Resistance:\\s*(-?\\d+)%'
        }
        
        parsed_data = {'calculation_time': calculation_time}
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output_text)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    parsed_data[key] = float(value_str)
                except ValueError:
                    parsed_data[key] = value_str
        
        return {'stats': parsed_data}
    
    def _parse_calculation_result(self, calculation_result: Dict) -> Dict:
        """解析PoB2计算结果"""
        
        # 如果已经有解析后的stats，直接返回
        if 'stats' in calculation_result:
            return calculation_result['stats']
        
        # 标准化统计数据格式
        stats = calculation_result.get('output', {})
        
        return {
            # 攻击数据
            'total_dps': self._safe_get_numeric(stats, 'TotalDPS', 0),
            'average_hit': self._safe_get_numeric(stats, 'AverageHit', 0),
            'crit_chance': self._safe_get_numeric(stats, 'CritChance', 0),
            'crit_multiplier': self._safe_get_numeric(stats, 'CritMultiplier', 150),
            'attack_rate': self._safe_get_numeric(stats, 'AttackRate', 1),
            'accuracy': self._safe_get_numeric(stats, 'Accuracy', 90),
            
            # 防御数据
            'total_life': self._safe_get_numeric(stats, 'Life', 0),
            'total_energy_shield': self._safe_get_numeric(stats, 'EnergyShield', 0),
            'effective_health_pool': self._safe_get_numeric(stats, 'TotalEHP', 0),
            'life_regen': self._safe_get_numeric(stats, 'LifeRegen', 0),
            'es_recharge': self._safe_get_numeric(stats, 'EnergyShieldRecharge', 0),
            
            # 抗性数据
            'fire_resistance': self._safe_get_numeric(stats, 'FireResist', 0),
            'cold_resistance': self._safe_get_numeric(stats, 'ColdResist', 0),
            'lightning_resistance': self._safe_get_numeric(stats, 'LightningResist', 0),
            'chaos_resistance': self._safe_get_numeric(stats, 'ChaosResist', 0),
            
            # 其他数据
            'movement_speed': self._safe_get_numeric(stats, 'MovementSpeed', 100),
            'block_chance': self._safe_get_numeric(stats, 'BlockChance', 0),
            'dodge_chance': self._safe_get_numeric(stats, 'DodgeChance', 0),
            
            # 元数据
            'calculation_timestamp': time.time(),
            'pob2_version': self.pob2_client.version_info.get('version', 'unknown'),
            'calculation_time': calculation_result.get('calculation_time', 0)
        }
    
    def _safe_get_numeric(self, data: Dict, key: str, default: float = 0) -> float:
        """安全获取数值类型数据"""
        try:
            value = data.get(key, default)
            if isinstance(value, str):
                # 移除逗号并转换为数值
                value = value.replace(',', '')
                return float(value)
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def _get_fallback_calculation(self, build_data: Dict) -> Dict:
        """获取后备计算结果（当PoB2不可用时）"""
        
        logger.warning("使用后备计算方法（PoB2不可用）")
        
        # 基础估算逻辑
        character = build_data.get('character', {})
        level = character.get('level', 90)
        
        # 基础血量估算
        base_life = 50 + (level - 1) * 12  # 基础血量增长
        estimated_life = base_life * 2.5  # 假设天赋和装备加成
        
        # 基础DPS估算
        estimated_dps = level * 1000  # 简单的等级基础DPS
        
        return {
            'success': False,
            'fallback_used': True,
            'stats': {
                'total_dps': estimated_dps,
                'total_life': estimated_life,
                'total_energy_shield': 0,
                'effective_health_pool': estimated_life,
                'fire_resistance': 75,
                'cold_resistance': 75,
                'lightning_resistance': 75,
                'chaos_resistance': 0,
                'calculation_method': 'Fallback_Estimation'
            }
        }
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        if hasattr(self.pob2_client, 'cleanup_temp_files'):
            self.pob2_client.cleanup_temp_files(self.temp_files)
        else:
            for temp_file in self.temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception as e:
                    logger.debug(f"清理临时文件失败 {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def batch_calculate(self, build_list: List[Dict], config: Optional[Dict] = None) -> List[Dict]:
        """批量计算多个构筑"""
        
        results = []
        
        for i, build_data in enumerate(build_list):
            logger.info(f"计算构筑 {i+1}/{len(build_list)}")
            
            try:
                result = self.calculate_build_stats(build_data, config)
                result['build_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"构筑 {i+1} 计算失败: {e}")
                results.append({
                    'success': False,
                    'build_index': i,
                    'error': str(e)
                })
        
        return results
    
    def compare_builds(self, build_1: Dict, build_2: Dict, config: Optional[Dict] = None) -> Dict:
        """比较两个构筑的性能"""
        
        calc_1 = self.calculate_build_stats(build_1, config)
        calc_2 = self.calculate_build_stats(build_2, config)
        
        if not (calc_1['success'] and calc_2['success']):
            return {
                'success': False,
                'error': '构筑计算失败，无法比较'
            }
        
        stats_1 = calc_1['stats']
        stats_2 = calc_2['stats']
        
        comparison = {
            'success': True,
            'build_1_stats': stats_1,
            'build_2_stats': stats_2,
            'comparison': {}
        }
        
        # 关键数据比较
        key_stats = [
            'total_dps', 'total_life', 'total_energy_shield', 
            'effective_health_pool', 'fire_resistance', 'cold_resistance',
            'lightning_resistance', 'chaos_resistance'
        ]
        
        for stat in key_stats:
            value_1 = stats_1.get(stat, 0)
            value_2 = stats_2.get(stat, 0)
            
            if value_1 > 0 or value_2 > 0:
                comparison['comparison'][stat] = {
                    'build_1': value_1,
                    'build_2': value_2,
                    'difference': value_2 - value_1,
                    'percentage_change': ((value_2 - value_1) / value_1 * 100) if value_1 > 0 else 0
                }
        
        return comparison