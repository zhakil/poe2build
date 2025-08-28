"""PoB2数据格式转换器 - 构筑数据与PoB2格式互转"""

import base64
import zlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import re
from datetime import datetime

from ..models.build import PoE2Build, PoE2BuildStats
from ..models.characters import PoE2CharacterClass, PoE2Ascendancy
from ..models.skills import PoE2Skill


@dataclass
class PoB2ImportCode:
    """PoB2导入代码数据结构"""
    raw_code: str
    decoded_xml: str
    build_data: Dict[str, Any]
    version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_code': self.raw_code,
            'decoded_xml': self.decoded_xml,
            'build_data': self.build_data,
            'version': self.version
        }


class PoB2DataConverter:
    """PoB2数据格式转换器"""
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.PoB2DataConverter")
        
        # PoE2职业映射
        self.class_mapping = {
            PoE2CharacterClass.WITCH: {'id': 0, 'name': 'Witch'},
            PoE2CharacterClass.MONK: {'id': 1, 'name': 'Monk'},
            PoE2CharacterClass.RANGER: {'id': 2, 'name': 'Ranger'},
            PoE2CharacterClass.MERCENARY: {'id': 3, 'name': 'Mercenary'},
            PoE2CharacterClass.WARRIOR: {'id': 4, 'name': 'Warrior'},
            PoE2CharacterClass.SORCERESS: {'id': 5, 'name': 'Sorceress'}
        }
        
        # 反向映射
        self.id_to_class = {v['id']: k for k, v in self.class_mapping.items()}
        self.name_to_class = {v['name'].lower(): k for k, v in self.class_mapping.items()}
    
    def build_to_pob2_code(self, build: PoE2Build) -> str:
        """将PoE2Build转换为PoB2导入代码"""
        try:
            # 创建XML根元素
            root = ET.Element("PathOfBuilding")
            
            # 添加版本信息
            root.set("version", "2.0")
            root.set("gameVersion", "2.0.0")
            
            # 添加构筑信息
            build_elem = ET.SubElement(root, "Build")
            build_elem.set("level", str(build.level))
            build_elem.set("targetVersion", "2_0")
            
            # 添加角色信息
            char_elem = ET.SubElement(build_elem, "Character")
            class_info = self.class_mapping.get(build.character_class)
            if class_info:
                char_elem.set("class", class_info['name'])
                char_elem.set("classId", str(class_info['id']))
            
            if build.ascendancy:
                char_elem.set("ascendClass", build.ascendancy.value)
            
            char_elem.set("level", str(build.level))
            
            # 添加技能信息
            if build.main_skill_gem or build.support_gems:
                skills_elem = ET.SubElement(build_elem, "Skills")
                
                # 主技能
                if build.main_skill_gem:
                    skill_elem = ET.SubElement(skills_elem, "Skill")
                    skill_elem.set("slot", "Weapon 1")
                    skill_elem.set("mainActiveSkillCalcs", "1")
                    
                    gem_elem = ET.SubElement(skill_elem, "Gem")
                    gem_elem.set("nameSpec", build.main_skill_gem)
                    gem_elem.set("level", "20")
                    gem_elem.set("quality", "0")
                    gem_elem.set("enabled", "true")
                
                # 辅助技能
                if build.support_gems:
                    for i, support_gem in enumerate(build.support_gems):
                        if i < 5:  # 最多5个辅助宝石
                            gem_elem = ET.SubElement(skills_elem, "Gem")
                            gem_elem.set("nameSpec", support_gem)
                            gem_elem.set("level", "20")
                            gem_elem.set("quality", "0")
                            gem_elem.set("enabled", "true")
            
            # 添加物品信息
            if build.key_items:
                items_elem = ET.SubElement(build_elem, "Items")
                
                # 武器槽
                weapon_slot = ET.SubElement(items_elem, "Slot")
                weapon_slot.set("name", "Weapon 1")
                
                for item_name in build.key_items[:1]:  # 只取第一个作为武器
                    item_elem = ET.SubElement(weapon_slot, "Item")
                    item_elem.set("id", "1")
                    
                    # 简化的物品数据
                    item_elem.text = f"Rarity: Rare\n{item_name}\nLevel: 68"
            
            # 添加天赋树信息
            if build.passive_keystones:
                tree_elem = ET.SubElement(build_elem, "Tree")
                tree_elem.set("activeSpec", "1")
                
                spec_elem = ET.SubElement(tree_elem, "Spec")
                spec_elem.set("title", "Default")
                
                # 天赋节点（简化处理）
                for i, keystone in enumerate(build.passive_keystones):
                    node_elem = ET.SubElement(spec_elem, "Node")
                    node_elem.set("id", str(1000 + i))  # 虚拟节点ID
                    node_elem.set("name", keystone)
            
            # 添加配置
            config_elem = ET.SubElement(build_elem, "Config")
            
            # 基础配置
            ET.SubElement(config_elem, "Input", name="resistancePenalty", number="0")
            ET.SubElement(config_elem, "Input", name="enemyLevel", number="84")
            ET.SubElement(config_elem, "Input", name="enemyResists", number="0")
            
            # 如果有统计数据，添加相关配置
            if build.stats:
                if build.stats.life > 0:
                    ET.SubElement(config_elem, "Input", name="conditionFullLife", boolean="true")
                if build.stats.energy_shield > 0:
                    ET.SubElement(config_elem, "Input", name="conditionFullEnergyShield", boolean="true")
            
            # 添加笔记
            notes_elem = ET.SubElement(build_elem, "Notes")
            notes_text = f"构筑名称: {build.name}\n"
            if build.notes:
                notes_text += f"说明: {build.notes}\n"
            if build.source_url:
                notes_text += f"来源: {build.source_url}\n"
            notes_text += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            notes_elem.text = notes_text
            
            # 转换为格式化的XML字符串
            xml_str = self._format_xml(root)
            
            # 压缩和编码
            compressed = zlib.compress(xml_str.encode('utf-8'))
            encoded = base64.b64encode(compressed).decode('ascii')
            
            self._logger.info(f"成功生成PoB2导入代码，长度: {len(encoded)}")
            return encoded
            
        except Exception as e:
            self._logger.error(f"生成PoB2导入代码失败: {e}")
            raise
    
    def pob2_code_to_build(self, import_code: str) -> Optional[PoE2Build]:
        """将PoB2导入代码转换为PoE2Build"""
        try:
            # 解码和解压缩
            decoded_data = self.decode_pob2_code(import_code)
            if not decoded_data:
                return None
            
            # 解析XML
            root = ET.fromstring(decoded_data.decoded_xml)
            build_elem = root.find('.//Build')
            
            if build_elem is None:
                self._logger.error("PoB2代码中未找到Build元素")
                return None
            
            # 提取基础信息
            level = int(build_elem.get('level', '1'))
            
            # 提取角色信息
            char_elem = build_elem.find('Character')
            character_class = PoE2CharacterClass.WITCH  # 默认值
            ascendancy = None
            
            if char_elem is not None:
                class_name = char_elem.get('class', '').lower()
                if class_name in self.name_to_class:
                    character_class = self.name_to_class[class_name]
                
                ascend_name = char_elem.get('ascendClass', '')
                if ascend_name:
                    try:
                        ascendancy = PoE2Ascendancy(ascend_name)
                    except ValueError:
                        self._logger.warning(f"未知的升华职业: {ascend_name}")
            
            # 提取技能信息
            main_skill_gem = None
            support_gems = []
            
            skills_elem = build_elem.find('Skills')
            if skills_elem is not None:
                # 主技能
                skill_elem = skills_elem.find('.//Skill[@mainActiveSkillCalcs="1"]')
                if skill_elem is not None:
                    gem_elem = skill_elem.find('Gem')
                    if gem_elem is not None:
                        main_skill_gem = gem_elem.get('nameSpec', '')
                
                # 辅助宝石
                for gem_elem in skills_elem.findall('.//Gem'):
                    gem_name = gem_elem.get('nameSpec', '')
                    if gem_name and gem_name != main_skill_gem:
                        support_gems.append(gem_name)
            
            # 提取物品信息
            key_items = []
            items_elem = build_elem.find('Items')
            if items_elem is not None:
                for item_elem in items_elem.findall('.//Item'):
                    item_text = item_elem.text or ""
                    # 简单解析物品名称
                    lines = item_text.split('\n')
                    if len(lines) > 1:
                        key_items.append(lines[1].strip())
            
            # 提取天赋信息
            passive_keystones = []
            tree_elem = build_elem.find('Tree')
            if tree_elem is not None:
                for node_elem in tree_elem.findall('.//Node'):
                    node_name = node_elem.get('name', '')
                    if node_name:
                        passive_keystones.append(node_name)
            
            # 提取笔记
            notes = ""
            notes_elem = build_elem.find('Notes')
            if notes_elem is not None and notes_elem.text:
                notes = notes_elem.text.strip()
            
            # 从笔记中提取构筑名称
            build_name = "Imported PoB2 Build"
            if notes:
                name_match = re.search(r'构筑名称:\s*(.+)', notes)
                if name_match:
                    build_name = name_match.group(1).strip()
            
            # 创建PoE2Build实例
            build = PoE2Build(
                name=build_name,
                character_class=character_class,
                level=level,
                ascendancy=ascendancy,
                main_skill_gem=main_skill_gem,
                support_gems=support_gems,
                key_items=key_items,
                passive_keystones=passive_keystones,
                notes=notes,
                pob2_code=import_code,
                source_url="imported_from_pob2",
                created_by="PoB2Import"
            )
            
            self._logger.info(f"成功从PoB2代码导入构筑: {build_name}")
            return build
            
        except Exception as e:
            self._logger.error(f"从PoB2代码导入构筑失败: {e}")
            return None
    
    def decode_pob2_code(self, import_code: str) -> Optional[PoB2ImportCode]:
        """解码PoB2导入代码"""
        try:
            # 清理导入代码
            cleaned_code = re.sub(r'[^A-Za-z0-9+/=]', '', import_code.strip())
            
            # Base64解码
            compressed_data = base64.b64decode(cleaned_code)
            
            # 解压缩
            xml_data = zlib.decompress(compressed_data)
            xml_str = xml_data.decode('utf-8')
            
            # 解析XML获取基础信息
            root = ET.fromstring(xml_str)
            version = root.get('version', '')
            
            # 转换为字典格式便于处理
            build_data = self._xml_to_dict(root)
            
            return PoB2ImportCode(
                raw_code=import_code,
                decoded_xml=xml_str,
                build_data=build_data,
                version=version
            )
            
        except Exception as e:
            self._logger.error(f"解码PoB2导入代码失败: {e}")
            return None
    
    def validate_pob2_code(self, import_code: str) -> bool:
        """验证PoB2导入代码的有效性"""
        try:
            decoded = self.decode_pob2_code(import_code)
            if not decoded:
                return False
            
            # 检查必要的XML元素
            root = ET.fromstring(decoded.decoded_xml)
            
            # 检查根元素
            if root.tag != "PathOfBuilding":
                return False
            
            # 检查Build元素
            build_elem = root.find('.//Build')
            if build_elem is None:
                return False
            
            # 检查角色信息
            char_elem = build_elem.find('Character')
            if char_elem is None:
                return False
            
            self._logger.info("PoB2导入代码验证通过")
            return True
            
        except Exception as e:
            self._logger.error(f"验证PoB2导入代码失败: {e}")
            return False
    
    def extract_build_stats(self, import_code: str) -> Optional[PoE2BuildStats]:
        """从PoB2导入代码中提取构筑统计数据"""
        try:
            decoded = self.decode_pob2_code(import_code)
            if not decoded:
                return None
            
            root = ET.fromstring(decoded.decoded_xml)
            
            # 查找计算结果元素
            calcs_elem = root.find('.//Calcs')
            if calcs_elem is None:
                self._logger.warning("PoB2代码中未找到计算结果，返回默认统计数据")
                return self._create_default_stats()
            
            # 提取DPS数据
            total_dps = 0.0
            for output in calcs_elem.findall('.//Output[@name="TotalDPS"]'):
                try:
                    total_dps = float(output.get('val', '0'))
                    break
                except ValueError:
                    pass
            
            # 提取生命值
            life = 0.0
            for output in calcs_elem.findall('.//Output[@name="Life"]'):
                try:
                    life = float(output.get('val', '0'))
                    break
                except ValueError:
                    pass
            
            # 提取能量护盾
            energy_shield = 0.0
            for output in calcs_elem.findall('.//Output[@name="EnergyShield"]'):
                try:
                    energy_shield = float(output.get('val', '0'))
                    break
                except ValueError:
                    pass
            
            # 提取抗性
            fire_res = self._extract_resistance(calcs_elem, "FireResist")
            cold_res = self._extract_resistance(calcs_elem, "ColdResist")
            lightning_res = self._extract_resistance(calcs_elem, "LightningResist")
            chaos_res = self._extract_resistance(calcs_elem, "ChaosResist")
            
            # 计算有效生命值
            ehp = life + energy_shield * 0.5
            
            stats = PoE2BuildStats(
                total_dps=total_dps,
                effective_health_pool=ehp,
                life=life,
                energy_shield=energy_shield,
                fire_resistance=fire_res,
                cold_resistance=cold_res,
                lightning_resistance=lightning_res,
                chaos_resistance=chaos_res
            )
            
            self._logger.info(f"成功提取构筑统计数据: DPS={total_dps}, EHP={ehp}")
            return stats
            
        except Exception as e:
            self._logger.error(f"提取构筑统计数据失败: {e}")
            return self._create_default_stats()
    
    def _extract_resistance(self, calcs_elem: ET.Element, resist_name: str) -> int:
        """提取抗性值"""
        for output in calcs_elem.findall(f'.//Output[@name="{resist_name}"]'):
            try:
                value = float(output.get('val', '0'))
                return int(max(-100, min(80, value)))  # PoE2抗性范围
            except ValueError:
                pass
        return 75  # 默认抗性值
    
    def _create_default_stats(self) -> PoE2BuildStats:
        """创建默认统计数据"""
        return PoE2BuildStats(
            total_dps=100000.0,
            effective_health_pool=5000.0,
            life=4000.0,
            energy_shield=1000.0,
            fire_resistance=75,
            cold_resistance=75,
            lightning_resistance=75,
            chaos_resistance=-30
        )
    
    def _format_xml(self, elem: ET.Element) -> str:
        """格式化XML"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _xml_to_dict(self, elem: ET.Element) -> Dict[str, Any]:
        """将XML元素转换为字典"""
        result = {}
        
        # 添加属性
        if elem.attrib:
            result['@attributes'] = elem.attrib
        
        # 添加文本内容
        if elem.text and elem.text.strip():
            result['#text'] = elem.text.strip()
        
        # 添加子元素
        for child in elem:
            child_data = self._xml_to_dict(child)
            
            if child.tag in result:
                # 如果已存在同名元素，转换为列表
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def generate_minimal_pob2_code(self, character_class: PoE2CharacterClass, 
                                  level: int = 1, 
                                  main_skill: Optional[str] = None) -> str:
        """生成最小的PoB2导入代码"""
        try:
            # 创建最小XML结构
            root = ET.Element("PathOfBuilding")
            root.set("version", "2.0")
            root.set("gameVersion", "2.0.0")
            
            build_elem = ET.SubElement(root, "Build")
            build_elem.set("level", str(level))
            
            # 角色信息
            char_elem = ET.SubElement(build_elem, "Character")
            class_info = self.class_mapping.get(character_class)
            if class_info:
                char_elem.set("class", class_info['name'])
                char_elem.set("classId", str(class_info['id']))
            char_elem.set("level", str(level))
            
            # 主技能（如果提供）
            if main_skill:
                skills_elem = ET.SubElement(build_elem, "Skills")
                skill_elem = ET.SubElement(skills_elem, "Skill")
                skill_elem.set("slot", "Weapon 1")
                skill_elem.set("mainActiveSkillCalcs", "1")
                
                gem_elem = ET.SubElement(skill_elem, "Gem")
                gem_elem.set("nameSpec", main_skill)
                gem_elem.set("level", "1")
                gem_elem.set("enabled", "true")
            
            # 转换为代码
            xml_str = self._format_xml(root)
            compressed = zlib.compress(xml_str.encode('utf-8'))
            encoded = base64.b64encode(compressed).decode('ascii')
            
            self._logger.info(f"生成最小PoB2代码: 职业={character_class.value}, 等级={level}")
            return encoded
            
        except Exception as e:
            self._logger.error(f"生成最小PoB2代码失败: {e}")
            raise