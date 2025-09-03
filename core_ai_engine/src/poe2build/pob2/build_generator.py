"""
PoB2构筑生成器 - AI驱动的Path of Building Community (PoE2)构筑创建
"""

import base64
import gzip
import json
import time
from typing import Dict, List, Optional, Union
import logging
import copy

from .local_client import PoB2LocalClient
from .calculation_engine import PoB2CalculationEngine
from .build_importer import PoB2BuildImporter

logger = logging.getLogger(__name__)


class PoB2BuildGenerator:
    """AI驱动的PoB2构筑生成器"""
    
    def __init__(self, pob2_client: Optional[PoB2LocalClient] = None):
        self.pob2_client = pob2_client or PoB2LocalClient()
        self.calculation_engine = PoB2CalculationEngine(self.pob2_client)
        self.build_importer = PoB2BuildImporter()
        
        # 构筑模板和数据
        self.build_templates = self._load_build_templates()
        self.skill_database = self._load_skill_database()
        self.item_database = self._load_item_database()
        
        # 市场和Meta数据缓存
        self.market_data: Dict = {}
        self.meta_trends: Dict = {}
    
    def generate_build_recommendation(self, user_request: Dict) -> Dict:
        """基于用户需求生成构筑推荐"""
        
        try:
            logger.info("开始生成AI构筑推荐")
            
            # 1. 分析用户需求
            build_requirements = self._analyze_user_requirements(user_request)
            logger.debug(f"构筑需求分析: {build_requirements}")
            
            # 2. 获取市场数据和Meta趋势
            self._fetch_external_data()
            
            # 3. AI生成构筑候选方案
            build_candidates = self._generate_build_candidates(build_requirements)
            logger.info(f"生成了 {len(build_candidates)} 个候选构筑")
            
            # 4. PoB2验证和计算
            validated_builds = self._validate_builds_with_pob2(build_candidates, build_requirements)
            logger.info(f"PoB2验证通过 {len(validated_builds)} 个构筑")
            
            # 5. 根据性能排序
            ranked_builds = self._rank_builds_by_performance(validated_builds, build_requirements)
            
            return {
                'success': True,
                'recommendations': ranked_builds,
                'generation_metadata': {
                    'candidates_generated': len(build_candidates),
                    'pob2_validated': len(validated_builds),
                    'market_data_timestamp': self.market_data.get('timestamp'),
                    'meta_data_timestamp': self.meta_trends.get('timestamp'),
                    'generation_time': time.time()
                }
            }
            
        except Exception as e:
            logger.error(f"构筑生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': []
            }
    
    def _analyze_user_requirements(self, user_request: Dict) -> Dict:
        """分析用户需求"""
        
        preferences = user_request.get('preferences', {})
        
        requirements = {
            'character_class': preferences.get('class', 'Ranger'),
            'ascendancy': preferences.get('ascendancy', ''),
            'build_style': preferences.get('style', 'bow'),
            'build_goal': preferences.get('goal', 'endgame_content'),
            'budget': preferences.get('budget', {'amount': 10, 'currency': 'divine'}),
            'level_target': preferences.get('level', 90),
            'defensive_focus': preferences.get('defensive_focus', 'balanced'),
            'offensive_focus': preferences.get('offensive_focus', 'dps'),
            'playstyle': preferences.get('playstyle', 'aggressive'),
            'pob2_integration': preferences.get('pob2_integration', {
                'generate_import_code': True,
                'calculate_stats': True,
                'validate_build': True
            })
        }
        
        # 根据构筑目标调整参数
        if requirements['build_goal'] == 'boss_killing':
            requirements['defensive_focus'] = 'tanky'
            requirements['offensive_focus'] = 'single_target'
        elif requirements['build_goal'] == 'mapping':
            requirements['defensive_focus'] = 'balanced'
            requirements['offensive_focus'] = 'aoe'
        elif requirements['build_goal'] == 'league_start':
            requirements['budget']['amount'] = min(requirements['budget']['amount'], 5)
        
        return requirements
    
    def _fetch_external_data(self):
        """获取外部数据（市场价格、Meta趋势等）"""
        
        try:
            # 模拟市场数据获取
            self.market_data = {
                'timestamp': time.time(),
                'currency_rates': {
                    'divine': 1.0,
                    'exalted': 0.15,
                    'chaos': 0.01
                },
                'popular_items': {
                    'weapons': ['Harbinger Bow', 'Thicket Bow', 'Imperial Bow'],
                    'armour': ['Assassin\'s Garb', 'Glorious Plate', 'Widowsilk Robe']
                }
            }
            
            # 模拟Meta趋势数据
            self.meta_trends = {
                'timestamp': time.time(),
                'popular_skills': {
                    'Ranger': ['Lightning Arrow', 'Explosive Shot', 'Poison Concoction'],
                    'Sorceress': ['Spark', 'Firewall', 'Lightning Bolt'],
                    'Witch': ['Summon Skeletons', 'Raise Zombie', 'Bone Spear'],
                    'Warrior': ['Earthquake', 'Ground Slam', 'Shield Charge'],
                    'Monk': ['Falling Thunder', 'Ice Strike', 'Tempest Bell'],
                    'Mercenary': ['Gas Arrow', 'Fragmentation Rounds', 'High Velocity Rounds']
                },
                'ascendancy_popularity': {
                    'Deadeye': 0.35,
                    'Pathfinder': 0.28,
                    'Chronomancer': 0.25,
                    'Stormweaver': 0.30
                }
            }
            
        except Exception as e:
            logger.warning(f"获取外部数据失败: {e}")
    
    def _generate_build_candidates(self, requirements: Dict) -> List[Dict]:
        """生成构筑候选方案"""
        
        candidates = []
        character_class = requirements['character_class']
        build_style = requirements['build_style']
        
        # 获取匹配的构筑模板
        base_templates = self._get_matching_templates(character_class, build_style)
        
        for template in base_templates:
            # 创建多个变种
            variants = self._create_build_variants(template, requirements)
            candidates.extend(variants)
        
        # 如果没有找到匹配模板，创建基础构筑
        if not candidates:
            candidates.append(self._create_basic_build(requirements))
        
        return candidates[:5]  # 限制候选数量
    
    def _get_matching_templates(self, character_class: str, build_style: str) -> List[Dict]:
        """获取匹配的构筑模板"""
        
        matching_templates = []
        
        for template in self.build_templates:
            if (template.get('character', {}).get('class') == character_class and
                build_style in template.get('styles', [])):
                matching_templates.append(template)
        
        return matching_templates
    
    def _create_build_variants(self, template: Dict, requirements: Dict) -> List[Dict]:
        """基于模板创建构筑变种"""
        
        variants = []
        budget = requirements['budget']['amount']
        
        # 预算版本变种
        for budget_multiplier in [0.7, 1.0, 1.5]:
            adjusted_budget = budget * budget_multiplier
            variant = self._adapt_build_for_budget(template, adjusted_budget, requirements)
            if variant:
                variants.append(variant)
        
        return variants
    
    def _adapt_build_for_budget(self, template: Dict, budget: float, requirements: Dict) -> Optional[Dict]:
        """根据预算调整构筑"""
        
        build = copy.deepcopy(template)
        
        # 更新构筑元数据
        build['metadata'] = {
            'build_name': f"{template.get('name', '未命名构筑')} (预算: {budget:.1f} Divine)",
            'description': f"基于{template.get('name', '模板')}适配的构筑",
            'budget': budget,
            'target_level': requirements['level_target'],
            'build_goal': requirements['build_goal']
        }
        
        # 根据预算调整装备
        build['items'] = self._select_items_for_budget(template.get('items', {}), budget)
        
        # 根据Meta趋势调整技能
        build = self._apply_meta_adjustments(build, requirements)
        
        return build
    
    def _create_basic_build(self, requirements: Dict) -> Dict:
        """创建基础构筑（没有匹配模板时）"""
        
        character_class = requirements['character_class']
        
        # 基础构筑结构
        basic_build = {
            'version': '3_0',
            'metadata': {
                'build_name': f"{character_class} {requirements['build_style'].title()} Build",
                'description': 'AI生成的基础构筑',
                'budget': requirements['budget']['amount'],
                'target_level': requirements['level_target']
            },
            'character': {
                'class': character_class,
                'ascendancy': requirements.get('ascendancy', ''),
                'level': requirements['level_target']
            },
            'skills': self._get_default_skills_for_class(character_class, requirements['build_style']),
            'items': self._get_default_items_for_class(character_class),
            'passive_tree': self._get_default_passive_tree(character_class),
            'config': self._get_default_config()
        }
        
        return basic_build
    
    def _get_default_skills_for_class(self, character_class: str, build_style: str) -> List[Dict]:
        """获取职业的默认技能配置"""
        
        popular_skills = self.meta_trends.get('popular_skills', {}).get(character_class, [])
        
        if not popular_skills:
            # 备选技能配置
            skill_defaults = {
                'Ranger': ['Lightning Arrow', 'Explosive Shot'],
                'Sorceress': ['Spark', 'Firewall'],
                'Witch': ['Summon Skeletons', 'Raise Zombie'],
                'Warrior': ['Earthquake', 'Ground Slam'],
                'Monk': ['Falling Thunder', 'Ice Strike'],
                'Mercenary': ['Gas Arrow', 'Fragmentation Rounds']
            }
            popular_skills = skill_defaults.get(character_class, ['基础攻击'])
        
        skills = []
        
        # 主技能
        main_skill = popular_skills[0] if popular_skills else '基础攻击'
        skills.append({
            'id': 'main',
            'slot': 'weapon',
            'main_skill': {
                'name': main_skill,
                'level': 20,
                'quality': 20
            },
            'support_gems': self._get_default_supports_for_skill(main_skill)
        })
        
        # 辅助技能
        if len(popular_skills) > 1:
            skills.append({
                'id': 'aura',
                'slot': 'helmet',
                'main_skill': {
                    'name': popular_skills[1],
                    'level': 20,
                    'quality': 0
                },
                'support_gems': []
            })
        
        return skills
    
    def _get_default_supports_for_skill(self, skill_name: str) -> List[Dict]:
        """获取技能的默认辅助宝石"""
        
        # 通用辅助宝石
        common_supports = [
            {'name': 'Elemental Damage with Attacks Support', 'level': 20, 'quality': 20},
            {'name': 'Added Lightning Damage Support', 'level': 20, 'quality': 20},
            {'name': 'Faster Attacks Support', 'level': 20, 'quality': 20},
            {'name': 'Critical Strike Multiplier Support', 'level': 20, 'quality': 0}
        ]
        
        return common_supports[:3]  # 限制辅助宝石数量
    
    def _get_default_items_for_class(self, character_class: str) -> Dict:
        """获取职业的默认装备"""
        
        # 基础装备模板
        item_templates = {
            'Ranger': {
                'main_hand': {'name': 'Thicket Bow', 'type': 'Bow', 'rarity': 'rare'},
                'body_armour': {'name': 'Assassin\'s Garb', 'type': 'Evasion', 'rarity': 'rare'},
                'helmet': {'name': 'Leather Cap', 'type': 'Evasion', 'rarity': 'rare'},
                'gloves': {'name': 'Leather Gloves', 'type': 'Evasion', 'rarity': 'rare'},
                'boots': {'name': 'Leather Boots', 'type': 'Evasion', 'rarity': 'rare'},
                'belt': {'name': 'Leather Belt', 'type': 'Belt', 'rarity': 'rare'},
                'ring_1': {'name': 'Iron Ring', 'type': 'Ring', 'rarity': 'rare'},
                'ring_2': {'name': 'Iron Ring', 'type': 'Ring', 'rarity': 'rare'},
                'amulet': {'name': 'Amber Amulet', 'type': 'Amulet', 'rarity': 'rare'}
            },
            'Sorceress': {
                'main_hand': {'name': 'Long Staff', 'type': 'Staff', 'rarity': 'rare'},
                'body_armour': {'name': 'Widowsilk Robe', 'type': 'Energy Shield', 'rarity': 'rare'},
                'helmet': {'name': 'Leather Cap', 'type': 'Energy Shield', 'rarity': 'rare'},
                'gloves': {'name': 'Wool Gloves', 'type': 'Energy Shield', 'rarity': 'rare'},
                'boots': {'name': 'Wool Shoes', 'type': 'Energy Shield', 'rarity': 'rare'},
                'belt': {'name': 'Chain Belt', 'type': 'Belt', 'rarity': 'rare'},
                'ring_1': {'name': 'Sapphire Ring', 'type': 'Ring', 'rarity': 'rare'},
                'ring_2': {'name': 'Sapphire Ring', 'type': 'Ring', 'rarity': 'rare'},
                'amulet': {'name': 'Lapis Amulet', 'type': 'Amulet', 'rarity': 'rare'}
            }
        }
        
        return item_templates.get(character_class, item_templates['Ranger'])
    
    def _get_default_passive_tree(self, character_class: str) -> Dict:
        """获取默认的天赋树配置"""
        
        return {
            'class_id': '0',
            'ascendancy_name': '',
            'allocated_nodes': [1, 2, 3, 4, 5],  # 示例节点ID
            'mastery_effects': {}
        }
    
    def _get_default_config(self) -> Dict:
        """获取默认计算配置"""
        
        return {
            'enemyLevel': 84,
            'conditionStationary': True,
            'conditionMoving': False,
            'buffOnslaught': False,
            'conditionEnemyMoving': False
        }
    
    def _select_items_for_budget(self, template_items: Dict, budget: float) -> Dict:
        """根据预算选择装备"""
        
        # 简化的预算分配逻辑
        if budget < 5:
            # 低预算：基础装备
            for slot, item in template_items.items():
                item['rarity'] = 'magic'
        elif budget < 15:
            # 中等预算：稀有装备
            for slot, item in template_items.items():
                item['rarity'] = 'rare'
        else:
            # 高预算：可能包含传奇装备
            key_slots = ['main_hand', 'body_armour']
            for slot in key_slots:
                if slot in template_items and budget > 20:
                    template_items[slot]['rarity'] = 'unique'
        
        return template_items
    
    def _apply_meta_adjustments(self, build: Dict, requirements: Dict) -> Dict:
        """根据Meta趋势调整构筑"""
        
        character_class = requirements['character_class']
        popular_skills = self.meta_trends.get('popular_skills', {}).get(character_class, [])
        
        # 如果有流行技能，尝试替换主技能
        if popular_skills and build.get('skills'):
            for skill_group in build['skills']:
                main_skill = skill_group.get('main_skill')
                if main_skill and main_skill.get('name') not in popular_skills:
                    # 替换为更流行的技能
                    skill_group['main_skill']['name'] = popular_skills[0]
        
        return build
    
    def _validate_builds_with_pob2(self, build_candidates: List[Dict], requirements: Dict) -> List[Dict]:
        """使用PoB2验证构筑候选方案"""
        
        validated_builds = []
        
        for i, candidate in enumerate(build_candidates):
            logger.debug(f"验证构筑候选 {i+1}/{len(build_candidates)}")
            
            pob2_result = self._validate_with_pob2(candidate, requirements)
            
            if pob2_result['valid']:
                # 添加PoB2计算结果到构筑数据
                candidate['pob2_stats'] = pob2_result['calculated_stats']
                candidate['pob2_import_code'] = pob2_result.get('import_code', '')
                candidate['validation_status'] = 'valid'
                validated_builds.append(candidate)
            else:
                logger.warning(f"构筑候选 {i+1} PoB2验证失败: {pob2_result.get('error', '未知错误')}")
        
        return validated_builds
    
    def _validate_with_pob2(self, build_config: Dict, requirements: Dict) -> Dict:
        """使用PoB2验证和计算构筑"""
        
        if not self.calculation_engine.is_available():
            return {
                'valid': False,
                'error': 'PoB2不可用',
                'fallback_used': True
            }
        
        try:
            # 1. 生成PoB2导入代码
            import_code = self._generate_pob2_import_code(build_config)
            
            # 2. 使用计算引擎进行计算
            calculation_config = requirements.get('pob2_integration', {})
            calculation_result = self.calculation_engine.calculate_build_stats(build_config, calculation_config)
            
            if calculation_result['success']:
                return {
                    'valid': True,
                    'calculated_stats': calculation_result['stats'],
                    'import_code': import_code,
                    'calculation_method': calculation_result.get('calculation_method', 'PoB2_Local')
                }
            else:
                return {
                    'valid': False,
                    'error': calculation_result.get('error', '计算失败'),
                    'fallback': calculation_result.get('fallback')
                }
                
        except Exception as e:
            logger.error(f"PoB2验证过程异常: {e}")
            return {
                'valid': False,
                'error': str(e),
                'fallback_used': True
            }
    
    def _generate_pob2_import_code(self, build_config: Dict) -> str:
        """生成PoB2可导入的构筑代码"""
        
        try:
            # 构建PoB2格式的构筑数据
            pob2_build = {
                'version': build_config.get('version', '3_0'),
                'character': build_config.get('character', {}),
                'skills': self._convert_skills_to_pob2_format(build_config.get('skills', [])),
                'items': self._convert_items_to_pob2_format(build_config.get('items', {})),
                'passive_tree': build_config.get('passive_tree', {}),
                'config': build_config.get('config', {})
            }
            
            # 编码为PoB2导入字符串
            json_data = json.dumps(pob2_build, separators=(',', ':')).encode('utf-8')
            compressed_data = gzip.compress(json_data)
            import_code = base64.b64encode(compressed_data).decode('utf-8')
            
            return import_code
            
        except Exception as e:
            logger.error(f"生成PoB2导入代码失败: {e}")
            return ''
    
    def _convert_skills_to_pob2_format(self, skills: List[Dict]) -> List[Dict]:
        """转换技能数据为PoB2格式"""
        
        pob2_skills = []
        
        for skill in skills:
            pob2_skill = {
                'id': skill.get('id', ''),
                'slot': skill.get('slot', ''),
                'main_skill': skill.get('main_skill', {}),
                'support_gems': skill.get('support_gems', [])
            }
            pob2_skills.append(pob2_skill)
        
        return pob2_skills
    
    def _convert_items_to_pob2_format(self, items: Dict) -> Dict:
        """转换装备数据为PoB2格式"""
        
        return items  # 假设格式已经兼容
    
    def _rank_builds_by_performance(self, validated_builds: List[Dict], requirements: Dict) -> List[Dict]:
        """根据性能指标排序构筑"""
        
        def calculate_score(build: Dict) -> float:
            stats = build.get('pob2_stats', {})
            
            # 根据构筑目标调整权重
            goal = requirements.get('build_goal', 'balanced')
            
            if goal == 'boss_killing':
                # Boss击杀优先考虑单体DPS和生存能力
                score = (
                    stats.get('total_dps', 0) * 0.6 +
                    stats.get('effective_health_pool', 0) * 0.3 +
                    (stats.get('fire_resistance', 0) + stats.get('cold_resistance', 0) + 
                     stats.get('lightning_resistance', 0)) * 0.1
                )
            elif goal == 'mapping':
                # 地图优先考虑清图速度和移动
                score = (
                    stats.get('total_dps', 0) * 0.5 +
                    stats.get('movement_speed', 100) * 10 +
                    stats.get('effective_health_pool', 0) * 0.2
                )
            else:
                # 平衡构筑
                score = (
                    stats.get('total_dps', 0) * 0.4 +
                    stats.get('effective_health_pool', 0) * 0.4 +
                    (stats.get('fire_resistance', 0) + stats.get('cold_resistance', 0) + 
                     stats.get('lightning_resistance', 0)) * 0.2
                )
            
            return score
        
        # 排序并添加排名信息
        ranked_builds = sorted(validated_builds, key=calculate_score, reverse=True)
        
        for i, build in enumerate(ranked_builds):
            build['rank'] = i + 1
            build['performance_score'] = calculate_score(build)
        
        return ranked_builds
    
    def _load_build_templates(self) -> List[Dict]:
        """加载构筑模板数据"""
        
        # 简化的模板数据
        templates = [
            {
                'name': 'Lightning Arrow Deadeye',
                'character': {'class': 'Ranger', 'ascendancy': 'Deadeye'},
                'styles': ['bow', 'lightning', 'projectile'],
                'skills': [
                    {
                        'id': 'main',
                        'main_skill': {'name': 'Lightning Arrow', 'level': 20},
                        'support_gems': [
                            {'name': 'Elemental Damage with Attacks Support', 'level': 20},
                            {'name': 'Added Lightning Damage Support', 'level': 20}
                        ]
                    }
                ]
            }
        ]
        
        return templates
    
    def _load_skill_database(self) -> Dict:
        """加载技能数据库"""
        
        return {
            'Lightning Arrow': {
                'type': 'projectile',
                'element': 'lightning',
                'damage_type': 'attack'
            },
            'Spark': {
                'type': 'projectile',
                'element': 'lightning', 
                'damage_type': 'spell'
            }
        }
    
    def _load_item_database(self) -> Dict:
        """加载装备数据库"""
        
        return {
            'Thicket Bow': {
                'type': 'Bow',
                'base_dps': 150,
                'price_range': {'min': 1, 'max': 10}
            },
            'Harbinger Bow': {
                'type': 'Bow', 
                'base_dps': 200,
                'price_range': {'min': 5, 'max': 50}
            }
        }
    
    def export_build_to_file(self, build_data: Dict, file_path: str, format: str = 'xml') -> bool:
        """导出构筑到文件"""
        
        try:
            if format == 'xml':
                xml_content = self.calculation_engine._build_data_to_xml(build_data)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
            elif format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(build_data, f, indent=2, ensure_ascii=False)
            elif format == 'pob':
                import_code = self._generate_pob2_import_code(build_data)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(import_code)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            logger.info(f"构筑导出成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"构筑导出失败: {e}")
            return False