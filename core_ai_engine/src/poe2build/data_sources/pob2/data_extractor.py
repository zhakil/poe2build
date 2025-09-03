r"""
Path of Building 2数据提取器 - 游戏数据解析
支持本地安装和GitHub项目两种数据源

数据源选项:
1. 本地安装: F:\steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)\
2. GitHub项目: https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2

从PoB2数据源提取技能、天赋树、装备数据
"""

import os
import re
import json
import glob
import requests
import tempfile
import shutil
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging
from urllib.parse import urljoin


@dataclass
class SkillGem:
    """技能宝石数据"""
    name: str
    internal_id: str
    base_type: str
    tags: List[str]
    gem_type: str  # "active", "support", "meta"
    required_level: int
    stat_text: List[str]
    quality_stats: List[str]
    base_effectiveness: float
    mana_cost: Optional[int]
    cooldown: Optional[float]
    damage_multiplier: float


@dataclass
class PassiveNode:
    """天赋节点数据"""
    node_id: int
    name: str
    icon: str
    description: List[str]
    stats: List[str]
    class_start_index: Optional[int]
    is_keystone: bool
    is_notable: bool
    position: Dict[str, float]  # x, y coordinates


@dataclass
class BaseItem:
    """基础物品数据"""
    name: str
    internal_id: str
    base_type: str
    item_class: str
    tags: List[str]
    implicit_mods: List[str]
    requirements: Dict[str, int]  # level, str, dex, int
    weapon_type: Optional[str]
    armour_type: Optional[str]


class PoB2DataExtractor:
    """Path of Building 2数据提取器 - 支持本地安装和GitHub项目"""
    
    # GitHub项目信息  
    GITHUB_REPO = "PathOfBuildingCommunity/PathOfBuilding-PoE2"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/main/src/Data"
    GITHUB_TREE_BASE = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/main/src/TreeData"
    
    # 本地安装路径
    COMMON_POB2_PATHS = [
        r"F:\steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)",
        r"C:\Program Files (x86)\Steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)",
        r"D:\Steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)",
        r"C:\Steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)",
        # 添加更多可能的安装路径
        r"C:\Users\*\Documents\My Games\Path of Building Community (PoE2)",
    ]
    
    def __init__(self, pob2_path: Optional[str] = None, use_github: bool = True):
        """
        初始化数据提取器
        
        Args:
            pob2_path: 自定义PoB2安装路径
            use_github: 优先使用GitHub数据源
        """
        # 首先初始化日志
        self.logger = logging.getLogger(__name__)
        
        self.use_github = use_github
        self.pob2_path = pob2_path or self._detect_pob2_installation()
        self.data_path = None
        
        if self.pob2_path:
            self.data_path = os.path.join(self.pob2_path, "Data")
        
        # GitHub数据缓存
        self._github_cache_dir = None
        if self.use_github:
            self._setup_github_cache()
        
        # HTTP会话用于GitHub请求
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PoE2BuildGenerator/1.0 (Educational Purpose)'
        })
            
        # 缓存
        self._gems_cache: Optional[Dict[str, SkillGem]] = None
        self._passives_cache: Optional[Dict[int, PassiveNode]] = None
        self._items_cache: Optional[Dict[str, BaseItem]] = None
    
    def _setup_github_cache(self):
        """设置GitHub数据缓存目录"""
        try:
            cache_base = tempfile.gettempdir()
            self._github_cache_dir = os.path.join(cache_base, "poe2build_pob2_cache")
            os.makedirs(self._github_cache_dir, exist_ok=True)
            self.logger.info(f"GitHub缓存目录: {self._github_cache_dir}")
        except Exception as e:
            self.logger.warning(f"无法创建GitHub缓存目录: {e}")
            self._github_cache_dir = None
    
    def _download_github_file(self, filename: str) -> Optional[str]:
        """从GitHub下载数据文件"""
        url = f"{self.GITHUB_RAW_BASE}/{filename}"
        cache_file = None
        
        if self._github_cache_dir:
            cache_file = os.path.join(self._github_cache_dir, filename)
            # 检查缓存是否存在且未过期（1小时）
            if os.path.exists(cache_file):
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 3600:  # 1小时
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            self.logger.info(f"使用缓存的GitHub文件: {filename}")
                            return f.read()
                    except Exception as e:
                        self.logger.warning(f"读取缓存文件失败: {e}")
        
        try:
            self.logger.info(f"从GitHub下载: {filename}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            
            # 缓存到本地
            if cache_file:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"已缓存GitHub文件: {filename}")
                except Exception as e:
                    self.logger.warning(f"缓存文件失败: {e}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"从GitHub下载文件失败 {filename}: {e}")
            return None
        
    def _detect_pob2_installation(self) -> Optional[str]:
        """自动检测PoB2安装路径"""
        for path_template in self.COMMON_POB2_PATHS:
            # 处理通配符路径
            if '*' in path_template:
                matching_paths = glob.glob(path_template)
                for path in matching_paths:
                    if os.path.exists(path) and self._validate_pob2_installation(path):
                        self.logger.info(f"检测到PoB2安装路径: {path}")
                        return path
            else:
                if os.path.exists(path_template) and self._validate_pob2_installation(path_template):
                    self.logger.info(f"检测到PoB2安装路径: {path_template}")
                    return path_template
        
        self.logger.warning("未找到Path of Building 2安装路径")
        return None
    
    def _validate_pob2_installation(self, path: str) -> bool:
        """验证PoB2安装路径的有效性"""
        # 检查基本文件存在性
        required_files = [
            "Data/Gems.lua",
            "Data/Global.lua",
            "Data/SkillStatMap.lua"
        ]
        
        valid_count = 0
        for file_path in required_files:
            full_path = os.path.join(path, file_path)
            if os.path.exists(full_path):
                valid_count += 1
                self.logger.info(f"PoB2文件检查: {file_path} ✅")
            else:
                self.logger.warning(f"PoB2文件检查: {file_path} ❌")
        
        # 至少要有2个核心文件存在才认为有效
        is_valid = valid_count >= 2
        if is_valid:
            self.logger.info(f"PoB2安装路径验证成功: {path}")
        else:
            self.logger.warning(f"PoB2安装路径验证失败: {path}")
            
        return is_valid
    
    def is_available(self) -> bool:
        """检查PoB2数据是否可用"""
        if self.use_github:
            # GitHub数据总是可用的（除非网络问题）
            return True
        else:
            # 本地安装检查
            return self.pob2_path is not None and self.data_path is not None
    
    def _parse_lua_table(self, content: str) -> Dict[str, Any]:
        """解析Lua表格数据"""
        try:
            # 移除Lua注释
            content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
            
            # 提取表格内容
            table_match = re.search(r'=\s*{(.+)}', content, re.DOTALL)
            if not table_match:
                return {}
            
            table_content = table_match.group(1)
            
            # 简单的Lua->Python转换
            # 这里使用正则表达式进行基本转换，实际项目可能需要更完整的Lua解析器
            
            # 转换布尔值
            table_content = re.sub(r'\btrue\b', 'True', table_content)
            table_content = re.sub(r'\bfalse\b', 'False', table_content)
            table_content = re.sub(r'\bnil\b', 'None', table_content)
            
            # 处理Lua字符串
            table_content = re.sub(r'(\w+)\s*=', r'"\1":', table_content)
            
            # 简单的表格项提取
            items = {}
            
            # 匹配形如 ["key"] = { ... } 的项目
            pattern = r'\["([^"]+)"\]\s*=\s*{([^}]*)}'
            matches = re.finditer(pattern, table_content, re.DOTALL)
            
            for match in matches:
                key = match.group(1)
                value_content = match.group(2)
                
                # 解析值内容
                item_data = self._parse_lua_item_data(value_content)
                items[key] = item_data
                
            return items
            
        except Exception as e:
            self.logger.error(f"解析Lua表格失败: {e}")
            return {}
    
    def _parse_lua_item_data(self, content: str) -> Dict[str, Any]:
        """解析Lua项目数据"""
        data = {}
        
        # 简单的键值对提取
        patterns = [
            (r'name\s*=\s*"([^"]*)"', 'name'),
            (r'baseTypeName\s*=\s*"([^"]*)"', 'baseTypeName'),
            (r'type\s*=\s*"([^"]*)"', 'type'),
            (r'level\s*=\s*(\d+)', 'level'),
            (r'manaMultiplier\s*=\s*([\d.]+)', 'manaMultiplier'),
            (r'manaCost\s*=\s*(\d+)', 'manaCost'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, content)
            if match:
                value = match.group(1)
                # 尝试转换数字
                try:
                    if '.' in value:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                except ValueError:
                    data[key] = value
        
        # 处理标签
        tags_match = re.search(r'tags\s*=\s*{([^}]*)}', content)
        if tags_match:
            tags_content = tags_match.group(1)
            tags = re.findall(r'(\w+)\s*=\s*true', tags_content)
            data['tags'] = tags
        
        # 处理统计数据
        stats_matches = re.finditer(r'stats\s*=\s*{([^}]*)}', content)
        for match in stats_matches:
            stats_content = match.group(1)
            stats = re.findall(r'"([^"]*)"', stats_content)
            data['stats'] = stats
        
        return data
    
    def get_skill_gems(self, force_refresh: bool = False) -> Dict[str, SkillGem]:
        """
        获取技能宝石数据
        
        Args:
            force_refresh: 强制刷新缓存
            
        Returns:
            技能宝石字典 {internal_id: SkillGem}
        """
        if self._gems_cache and not force_refresh:
            return self._gems_cache
        
        if not self.is_available():
            return {}
        
        # 获取文件内容 - 三层回退：缓存 → GitHub → 本地
        content = None
        
        # 1. 先尝试从下载缓存读取
        cache_file = Path("data_storage/pob2_cache/Gems.lua")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logger.info("从缓存加载Gems.lua")
            except Exception as e:
                self.logger.warning(f"读取缓存Gems.lua失败: {e}")
        
        # 2. 缓存不可用时，从GitHub获取
        if not content:
            self.logger.info("尝试从GitHub获取Gems.lua")
            content = self._download_github_file("Gems.lua")
        
        # 3. GitHub也不可用时，尝试本地文件
        if not content and not self.use_github and self.data_path:
            gems_file = os.path.join(self.data_path, "Gems.lua")
            try:
                with open(gems_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logger.info("从本地文件加载Gems.lua")
            except Exception as e:
                self.logger.error(f"读取本地Gems.lua失败: {e}")
        
        if not content:
            self.logger.error("所有数据源都不可用")
            return {}
        
        try:
            # 解析Lua数据
            gem_data = self._parse_lua_table(content)
            
            gems = {}
            for internal_id, data in gem_data.items():
                gem = SkillGem(
                    name=data.get('name', 'Unknown'),
                    internal_id=internal_id,
                    base_type=data.get('baseTypeName', ''),
                    tags=data.get('tags', []),
                    gem_type=self._determine_gem_type(data),
                    required_level=data.get('level', 1),
                    stat_text=data.get('stats', []),
                    quality_stats=data.get('qualityStats', []),
                    base_effectiveness=data.get('baseEffectiveness', 1.0),
                    mana_cost=data.get('manaCost'),
                    cooldown=data.get('cooldown'),
                    damage_multiplier=data.get('manaMultiplier', 1.0)
                )
                gems[internal_id] = gem
            
            self._gems_cache = gems
            self.logger.info(f"加载了 {len(gems)} 个技能宝石")
            return gems
            
        except Exception as e:
            self.logger.error(f"读取技能宝石数据失败: {e}")
            return {}
    
    def _determine_gem_type(self, gem_data: Dict[str, Any]) -> str:
        """确定宝石类型"""
        tags = gem_data.get('tags', [])
        
        if 'support' in tags:
            return 'support'
        elif 'aura' in tags:
            return 'aura'
        elif any(tag in tags for tag in ['spell', 'attack', 'minion']):
            return 'active'
        else:
            return 'meta'
    
    def get_passive_tree(self, force_refresh: bool = False) -> Dict[int, PassiveNode]:
        """
        获取天赋树数据
        
        Args:
            force_refresh: 强制刷新缓存
            
        Returns:
            天赋节点字典 {node_id: PassiveNode}
        """
        if self._passives_cache and not force_refresh:
            return self._passives_cache
        
        if not self.is_available():
            return {}
        
        # 支持下载缓存、GitHub和本地模式
        content = None
        
        # 1. 首先尝试从下载缓存读取
        cache_file = Path("data_storage/pob2_cache/PassiveTree.lua")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.info("从下载缓存读取PassiveTree.lua")
            except Exception as e:
                self.logger.warning(f"读取缓存PassiveTree.lua失败: {e}")
        
        # 2. 尝试GitHub模式
        if not content and self.use_github:
            try:
                content = self._download_github_file("PassiveTree.lua")
                if not content:
                    self.logger.error("GitHub模式下无法获取PassiveTree.lua")
            except Exception as e:
                self.logger.error(f"从GitHub下载PassiveTree.lua失败: {e}")
        
        # 3. 尝试本地文件
        if not content and not self.use_github:
            passive_file = os.path.join(self.data_path, "PassiveTree.lua")
            try:
                with open(passive_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"读取本地PassiveTree.lua失败: {e}")
        
        # 如果仍然没有内容，返回空
        if not content:
            self.logger.error("无法从任何数据源获取PassiveTree.lua")
            return {}
        
        try:
            
            # 解析天赋树数据
            tree_data = self._parse_lua_table(content)
            
            nodes = {}
            for node_id_str, data in tree_data.items():
                try:
                    node_id = int(node_id_str)
                    node = PassiveNode(
                        node_id=node_id,
                        name=data.get('name', ''),
                        icon=data.get('icon', ''),
                        description=data.get('description', []),
                        stats=data.get('stats', []),
                        class_start_index=data.get('classStartIndex'),
                        is_keystone=data.get('isKeystone', False),
                        is_notable=data.get('isNotable', False),
                        position={'x': data.get('x', 0), 'y': data.get('y', 0)}
                    )
                    nodes[node_id] = node
                except ValueError:
                    continue
            
            self._passives_cache = nodes
            self.logger.info(f"加载了 {len(nodes)} 个天赋节点")
            return nodes
            
        except Exception as e:
            self.logger.error(f"读取天赋树数据失败: {e}")
            return {}
    
    def get_base_items(self, force_refresh: bool = False) -> Dict[str, BaseItem]:
        """
        获取基础物品数据
        
        Args:
            force_refresh: 强制刷新缓存
            
        Returns:
            基础物品字典 {internal_id: BaseItem}
        """
        if self._items_cache and not force_refresh:
            return self._items_cache
        
        if not self.is_available():
            return {}
        
        # 获取文件内容 - 三层回退：缓存 → GitHub → 本地
        content = None
        
        # 1. 先尝试从下载缓存读取
        cache_file = Path("data_storage/pob2_cache/Bases.lua")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logger.info("从缓存加载Bases.lua")
            except Exception as e:
                self.logger.warning(f"读取缓存Bases.lua失败: {e}")
        
        # 2. 缓存不可用时，从GitHub获取
        if not content:
            self.logger.info("尝试从GitHub获取Bases.lua")
            content = self._download_github_file("Bases.lua")
        
        # 3. GitHub也不可用时，尝试本地文件
        if not content and not self.use_github and self.data_path:
            bases_file = os.path.join(self.data_path, "Bases.lua")
            try:
                with open(bases_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logger.info("从本地文件加载Bases.lua")
            except Exception as e:
                self.logger.error(f"读取本地Bases.lua失败: {e}")
        
        if not content:
            self.logger.error("所有数据源都不可用")
            return {}
        
        try:
            # 解析基础物品数据
            item_data = self._parse_lua_table(content)
            
            items = {}
            for internal_id, data in item_data.items():
                item = BaseItem(
                    name=data.get('name', 'Unknown'),
                    internal_id=internal_id,
                    base_type=data.get('baseTypeName', ''),
                    item_class=data.get('type', ''),
                    tags=data.get('tags', []),
                    implicit_mods=data.get('implicitMods', []),
                    requirements=self._parse_requirements(data),
                    weapon_type=data.get('weaponType'),
                    armour_type=data.get('armourType')
                )
                items[internal_id] = item
            
            self._items_cache = items
            self.logger.info(f"加载了 {len(items)} 个基础物品")
            return items
            
        except Exception as e:
            self.logger.error(f"读取基础物品数据失败: {e}")
            return {}
    
    def _parse_requirements(self, item_data: Dict[str, Any]) -> Dict[str, int]:
        """解析物品需求"""
        requirements = {}
        
        req_level = item_data.get('reqLevel')
        if req_level:
            requirements['level'] = req_level
        
        req_str = item_data.get('reqStr')
        if req_str:
            requirements['str'] = req_str
            
        req_dex = item_data.get('reqDex')
        if req_dex:
            requirements['dex'] = req_dex
            
        req_int = item_data.get('reqInt')
        if req_int:
            requirements['int'] = req_int
        
        return requirements
    
    def search_gems_by_tag(self, tag: str) -> List[SkillGem]:
        """按标签搜索技能宝石"""
        gems = self.get_skill_gems()
        return [gem for gem in gems.values() if tag.lower() in [t.lower() for t in gem.tags]]
    
    def search_gems_by_name(self, name_pattern: str) -> List[SkillGem]:
        """按名称模式搜索技能宝石"""
        gems = self.get_skill_gems()
        pattern = re.compile(name_pattern, re.IGNORECASE)
        return [gem for gem in gems.values() if pattern.search(gem.name)]
    
    def get_gem_by_name(self, name: str) -> Optional[SkillGem]:
        """按名称获取特定技能宝石"""
        gems = self.get_skill_gems()
        for gem in gems.values():
            if gem.name.lower() == name.lower():
                return gem
        return None
    
    def get_installation_info(self) -> Dict[str, Any]:
        """获取PoB2数据源信息"""
        if self.use_github:
            return {
                'available': True,
                'source': 'GitHub',
                'repository': self.GITHUB_REPO,
                'base_url': self.GITHUB_RAW_BASE,
                'cache_dir': self._github_cache_dir
            }
        else:
            return {
                'available': self.is_available(),
                'source': 'Local',
                'path': self.pob2_path,
                'data_path': self.data_path
            }


# 全局实例
_extractor = None

def get_pob2_extractor() -> PoB2DataExtractor:
    """获取全局PoB2数据提取器实例"""
    global _extractor
    if _extractor is None:
        _extractor = PoB2DataExtractor()
    return _extractor