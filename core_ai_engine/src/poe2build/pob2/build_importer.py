"""
PoB2构筑导入器 - 解析和处理Path of Building Community (PoE2)构筑格式
"""

import base64
import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import re

logger = logging.getLogger(__name__)


class PoB2BuildImporter:
    """PoB2构筑导入器，支持多种构筑格式"""
    
    def __init__(self):
        self.supported_formats = ['.xml', '.pob', 'import_code']
        
    def import_build(self, source: Union[str, Path]) -> Dict:
        """
        导入构筑数据
        
        Args:
            source: 构筑文件路径、导入代码字符串或XML字符串
            
        Returns:
            Dict: 解析后的构筑数据
        """
        
        try:
            # 判断输入类型
            if isinstance(source, (str, Path)) and Path(source).exists():
                # 文件路径
                return self._import_from_file(Path(source))
            elif isinstance(source, str):
                # 字符串内容 (导入代码或XML)
                return self._import_from_string(source)
            else:
                raise ValueError("不支持的输入格式")
                
        except Exception as e:
            logger.error(f"导入构筑失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def _import_from_file(self, file_path: Path) -> Dict:
        """从文件导入构筑"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"构筑文件不存在: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.xml':
            return self._parse_xml_file(file_path)
        elif file_extension == '.pob':
            return self._parse_pob_file(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")
    
    def _import_from_string(self, content: str) -> Dict:
        """从字符串导入构筑"""
        
        content = content.strip()
        
        # 检测是否为Base64编码的导入代码
        if self._is_pob_import_code(content):
            return self._parse_import_code(content)
        elif content.startswith('<?xml') or content.startswith('<PathOfBuilding'):
            return self._parse_xml_string(content)
        else:
            # 尝试解析为JSON格式
            try:
                json_data = json.loads(content)
                return self._parse_json_data(json_data)
            except json.JSONDecodeError:
                raise ValueError("无法识别的构筑格式")
    
    def _is_pob_import_code(self, content: str) -> bool:
        """检测是否为PoB导入代码"""
        try:
            # PoB导入代码通常是长的Base64字符串
            if len(content) < 100:
                return False
            
            # 尝试Base64解码
            decoded = base64.b64decode(content)
            
            # 检查是否为gzip压缩的数据
            try:
                decompressed = gzip.decompress(decoded)
                return True
            except:
                # 可能是未压缩的JSON数据
                try:
                    json.loads(decoded.decode('utf-8'))
                    return True
                except:
                    return False
                    
        except:
            return False
    
    def _parse_import_code(self, import_code: str) -> Dict:
        """解析PoB导入代码"""
        
        try:
            # Base64解码
            decoded_data = base64.b64decode(import_code)
            
            # 尝试gzip解压
            try:
                decompressed_data = gzip.decompress(decoded_data)
                build_data = json.loads(decompressed_data.decode('utf-8'))
            except:
                # 可能未压缩，直接解析JSON
                build_data = json.loads(decoded_data.decode('utf-8'))
            
            return {
                'success': True,
                'format': 'import_code',
                'data': self._normalize_build_data(build_data)
            }
            
        except Exception as e:
            raise ValueError(f"导入代码解析失败: {e}")
    
    def _parse_xml_file(self, file_path: Path) -> Dict:
        """解析XML格式的构筑文件"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        return self._parse_xml_string(xml_content)
    
    def _parse_xml_string(self, xml_content: str) -> Dict:
        """解析XML字符串"""
        
        try:
            root = ET.fromstring(xml_content)
            
            if root.tag != 'PathOfBuilding':
                raise ValueError("不是有效的PathOfBuilding XML文件")
            
            build_data = self._extract_xml_build_data(root)
            
            return {
                'success': True,
                'format': 'xml',
                'data': self._normalize_build_data(build_data)
            }
            
        except ET.ParseError as e:
            raise ValueError(f"XML解析错误: {e}")
    
    def _parse_pob_file(self, file_path: Path) -> Dict:
        """解析.pob格式文件（通常是导入代码）"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        return self._parse_import_code(content)
    
    def _parse_json_data(self, json_data: Dict) -> Dict:
        """解析JSON格式构筑数据"""
        
        return {
            'success': True,
            'format': 'json',
            'data': self._normalize_build_data(json_data)
        }
    
    def _extract_xml_build_data(self, root: ET.Element) -> Dict:
        """从XML元素中提取构筑数据"""
        
        build_data = {
            'version': root.get('version', '3_0'),
            'character': {},
            'skills': [],
            'items': {},
            'passive_tree': {},
            'config': {}
        }
        
        # 提取角色信息
        build_elem = root.find('Build')
        if build_elem is not None:
            build_data['character'] = {
                'class': build_elem.get('className', ''),
                'ascendancy': build_elem.get('ascendClassName', ''),
                'level': int(build_elem.get('level', 1))
            }
        
        # 提取技能信息
        skills_elem = root.find('Skills')
        if skills_elem is not None:
            for skill_group in skills_elem.findall('SkillSet'):
                skill_data = self._extract_skill_group(skill_group)
                if skill_data:
                    build_data['skills'].append(skill_data)
        
        # 提取装备信息
        items_elem = root.find('Items')
        if items_elem is not None:
            build_data['items'] = self._extract_items_data(items_elem)
        
        # 提取天赋树信息
        tree_elem = root.find('Tree')
        if tree_elem is not None:
            build_data['passive_tree'] = self._extract_passive_tree(tree_elem)
        
        # 提取配置信息
        config_elem = root.find('Config')
        if config_elem is not None:
            build_data['config'] = self._extract_config_data(config_elem)
        
        return build_data
    
    def _extract_skill_group(self, skill_group: ET.Element) -> Optional[Dict]:
        """提取技能组数据"""
        
        skill_data = {
            'id': skill_group.get('id', ''),
            'slot': skill_group.get('slot', ''),
            'main_skill': None,
            'support_gems': []
        }
        
        # 提取主技能和辅助宝石
        for gem in skill_group.findall('Gem'):
            gem_data = {
                'name': gem.get('skillId', ''),
                'level': int(gem.get('level', 1)),
                'quality': int(gem.get('quality', 0)),
                'enabled': gem.get('enabled', '1') == '1'
            }
            
            if gem.get('support', '0') == '0':
                skill_data['main_skill'] = gem_data
            else:
                skill_data['support_gems'].append(gem_data)
        
        return skill_data if skill_data['main_skill'] else None
    
    def _extract_items_data(self, items_elem: ET.Element) -> Dict:
        """提取装备数据"""
        
        items_data = {}
        
        # 装备槽位映射
        slot_mapping = {
            'Weapon 1': 'main_hand',
            'Weapon 2': 'off_hand', 
            'Helmet': 'helmet',
            'Body Armour': 'body_armour',
            'Gloves': 'gloves',
            'Boots': 'boots',
            'Belt': 'belt',
            'Ring 1': 'ring_1',
            'Ring 2': 'ring_2',
            'Amulet': 'amulet'
        }
        
        for item in items_elem.findall('Item'):
            slot = item.get('slot', '')
            if slot in slot_mapping:
                items_data[slot_mapping[slot]] = self._extract_item_data(item)
        
        return items_data
    
    def _extract_item_data(self, item: ET.Element) -> Dict:
        """提取单个装备数据"""
        
        return {
            'name': item.get('name', ''),
            'type': item.get('type', ''),
            'rarity': item.get('rarity', 'normal'),
            'text': item.text or ''
        }
    
    def _extract_passive_tree(self, tree_elem: ET.Element) -> Dict:
        """提取天赋树数据"""
        
        passive_tree = {
            'class_id': tree_elem.get('classId', ''),
            'ascendancy_name': tree_elem.get('ascendClassName', ''),
            'nodes': []
        }
        
        # 提取已分配的天赋点
        nodes_text = tree_elem.text or ''
        if nodes_text:
            # 解析天赋节点ID列表
            node_ids = [int(x) for x in nodes_text.split(',') if x.strip().isdigit()]
            passive_tree['nodes'] = node_ids
        
        return passive_tree
    
    def _extract_config_data(self, config_elem: ET.Element) -> Dict:
        """提取配置数据"""
        
        config_data = {}
        
        for input_elem in config_elem.findall('Input'):
            name = input_elem.get('name', '')
            value = input_elem.get('value', '')
            if name:
                config_data[name] = value
        
        return config_data
    
    def _normalize_build_data(self, raw_data: Dict) -> Dict:
        """标准化构筑数据格式"""
        
        normalized = {
            'version': raw_data.get('version', '3_0'),
            'metadata': {
                'build_name': raw_data.get('build_name', '未命名构筑'),
                'description': raw_data.get('description', ''),
                'author': raw_data.get('author', ''),
                'created_date': raw_data.get('created_date', ''),
                'poe2_version': raw_data.get('poe2_version', '1.0')
            },
            'character': {
                'class': raw_data.get('character', {}).get('class', ''),
                'ascendancy': raw_data.get('character', {}).get('ascendancy', ''),
                'level': raw_data.get('character', {}).get('level', 90)
            },
            'skills': self._normalize_skills_data(raw_data.get('skills', [])),
            'items': self._normalize_items_data(raw_data.get('items', {})),
            'passive_tree': self._normalize_passive_tree_data(raw_data.get('passive_tree', {})),
            'config': self._normalize_config_data(raw_data.get('config', {}))
        }
        
        return normalized
    
    def _normalize_skills_data(self, skills_data: List) -> List[Dict]:
        """标准化技能数据"""
        
        normalized_skills = []
        
        for skill in skills_data:
            if isinstance(skill, dict) and skill.get('main_skill'):
                normalized_skill = {
                    'id': skill.get('id', ''),
                    'slot': skill.get('slot', ''),
                    'main_skill': {
                        'name': skill['main_skill'].get('name', ''),
                        'level': skill['main_skill'].get('level', 1),
                        'quality': skill['main_skill'].get('quality', 0)
                    },
                    'support_gems': []
                }
                
                for support in skill.get('support_gems', []):
                    normalized_skill['support_gems'].append({
                        'name': support.get('name', ''),
                        'level': support.get('level', 1),
                        'quality': support.get('quality', 0)
                    })
                
                normalized_skills.append(normalized_skill)
        
        return normalized_skills
    
    def _normalize_items_data(self, items_data: Dict) -> Dict:
        """标准化装备数据"""
        
        normalized_items = {}
        
        standard_slots = [
            'main_hand', 'off_hand', 'helmet', 'body_armour', 
            'gloves', 'boots', 'belt', 'ring_1', 'ring_2', 'amulet'
        ]
        
        for slot in standard_slots:
            if slot in items_data:
                item = items_data[slot]
                normalized_items[slot] = {
                    'name': item.get('name', ''),
                    'type': item.get('type', ''),
                    'rarity': item.get('rarity', 'normal'),
                    'text': item.get('text', '')
                }
        
        return normalized_items
    
    def _normalize_passive_tree_data(self, tree_data: Dict) -> Dict:
        """标准化天赋树数据"""
        
        return {
            'class_id': tree_data.get('class_id', ''),
            'ascendancy_name': tree_data.get('ascendancy_name', ''),
            'allocated_nodes': tree_data.get('nodes', []),
            'mastery_effects': tree_data.get('mastery_effects', {})
        }
    
    def _normalize_config_data(self, config_data: Dict) -> Dict:
        """标准化配置数据"""
        
        default_config = {
            'enemy_level': 84,
            'boss_encounter': False,
            'player_stationary': True,
            'conditionStationary': True,
            'conditionMoving': False,
            'buffOnslaught': False,
            'conditionEnemyMoving': False
        }
        
        default_config.update(config_data)
        return default_config
    
    def validate_build_data(self, build_data: Dict) -> Dict:
        """验证构筑数据完整性"""
        
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # 验证必需字段
        required_fields = ['character', 'skills', 'items', 'passive_tree']
        
        for field in required_fields:
            if field not in build_data:
                validation_result['errors'].append(f"缺少必需字段: {field}")
                validation_result['valid'] = False
        
        # 验证角色信息
        if 'character' in build_data:
            char_data = build_data['character']
            if not char_data.get('class'):
                validation_result['warnings'].append("角色职业未指定")
            if char_data.get('level', 0) < 1 or char_data.get('level', 0) > 100:
                validation_result['warnings'].append("角色等级异常")
        
        # 验证技能配置
        if 'skills' in build_data:
            skills = build_data['skills']
            if not skills:
                validation_result['warnings'].append("没有配置技能")
            else:
                for skill in skills:
                    if not skill.get('main_skill', {}).get('name'):
                        validation_result['warnings'].append("发现未命名的主技能")
        
        # 验证装备配置
        if 'items' in build_data:
            items = build_data['items']
            essential_slots = ['main_hand', 'body_armour']
            for slot in essential_slots:
                if slot not in items or not items[slot].get('name'):
                    validation_result['warnings'].append(f"缺少关键装备槽位: {slot}")
        
        return validation_result
    
    def get_build_summary(self, build_data: Dict) -> Dict:
        """生成构筑摘要信息"""
        
        summary = {
            'build_name': build_data.get('metadata', {}).get('build_name', '未知构筑'),
            'character_class': build_data.get('character', {}).get('class', '未知'),
            'ascendancy': build_data.get('character', {}).get('ascendancy', '无'),
            'level': build_data.get('character', {}).get('level', 0),
            'main_skills': [],
            'key_items': {},
            'passive_points_used': len(build_data.get('passive_tree', {}).get('allocated_nodes', []))
        }
        
        # 提取主要技能
        for skill in build_data.get('skills', []):
            main_skill = skill.get('main_skill', {})
            if main_skill.get('name'):
                summary['main_skills'].append({
                    'name': main_skill['name'],
                    'level': main_skill.get('level', 1),
                    'support_count': len(skill.get('support_gems', []))
                })
        
        # 提取关键装备
        items = build_data.get('items', {})
        key_slots = ['main_hand', 'off_hand', 'body_armour', 'helmet']
        for slot in key_slots:
            if slot in items and items[slot].get('name'):
                summary['key_items'][slot] = items[slot]['name']
        
        return summary