"""
四大核心数据源集成模块
基于真实、可用的PoE2数据源构建智能推荐系统

🎯 **四大核心数据源 (Foundation)**:

1. **PoE2Scout API** (https://poe2scout.com)
   - 实时市场定价数据和物品价格分析
   - 模块: poe2scout.api_client

2. **PoE Ninja构筑爬虫** (https://poe.ninja/poe2/builds)  
   - Meta趋势分析和流行构筑数据爬取
   - 模块: ninja.scraper

3. **Path of Building 2数据** (GitHub/本地)
   - 官方游戏数据和精确DPS/EHP计算
   - 模块: pob2.data_extractor

4. **PoE2DB数据源** (https://poe2db.tw/cn/)
   - 完整游戏数据库和物品详情
   - 模块: poe2db.api_client

使用示例:
```python
from poe2build.data_sources import (
    get_poe2scout_client,
    get_ninja_scraper, 
    get_pob2_extractor,
    get_poe2db_client
)

# 获取四大数据源
scout = get_poe2scout_client()
ninja = get_ninja_scraper()  
pob2 = get_pob2_extractor()
poe2db = get_poe2db_client()
```
"""

# 基础数据源类
from .base_data_source import BaseDataSource

# 四大核心数据源导入
from .poe2scout.api_client import (
    PoE2ScoutClient,
    ItemPrice,
    CurrencyExchange,
    get_poe2scout_client
)

from .ninja.scraper import (
    NinjaMetaScraper,
    PopularBuild,
    SkillUsageStats,
    AscendancyTrend,
    get_ninja_scraper
)

from .pob2.data_extractor import (
    PoB2DataExtractor,
    SkillGem,
    PassiveNode,
    BaseItem,
    get_pob2_extractor
)

from .poe2db.api_client import (
    PoE2DBClient,
    ItemDetail,
    SkillDetail,
    AscendancyInfo,
    get_poe2db_client
)

# 导入动态数据爬虫系统
try:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from dynamic_data_crawlers import DynamicDataManager
    from pob2_github_downloader import PoB2GitHubDownloader  
    from poe2_realistic_data_system import PoE2RealisticDataSystem
    DYNAMIC_CRAWLERS_AVAILABLE = True
except ImportError:
    DYNAMIC_CRAWLERS_AVAILABLE = False

# 便捷函数：获取所有四大数据源
def get_all_four_sources(limit=None):
    """
    获取所有四大核心数据源的数据，集成动态爬虫系统
    
    Args:
        limit: 数据条数限制（可选）
    
    Returns:
        dict: 包含四大数据源数据的字典
    """
    result = {
        'poe2scout_data': [],
        'ninja_data': [],
        'pob2_data': {},
        'poe2db_data': []
    }
    
    # 使用动态爬虫系统获取实时数据
    if DYNAMIC_CRAWLERS_AVAILABLE:
        try:
            dynamic_manager = DynamicDataManager()
            dynamic_data = dynamic_manager.update_all_data()
            
            # 映射数据到标准格式
            result['poe2scout_data'] = dynamic_data.get('market_items', [])[:limit] if limit else dynamic_data.get('market_items', [])
            result['ninja_data'] = dynamic_data.get('meta_builds', [])[:limit] if limit else dynamic_data.get('meta_builds', [])
            result['poe2db_data'] = dynamic_data.get('skill_data', [])[:limit] if limit else dynamic_data.get('skill_data', [])
            
            # PoB2数据通过现有系统获取
            try:
                pob2_extractor = get_pob2_extractor()
                if pob2_extractor.is_available():
                    pob2_gems = pob2_extractor.get_skill_gems()
                    result['pob2_data']['skill_gems'] = list(pob2_gems.values())[:limit] if limit else list(pob2_gems.values())
            except Exception as e:
                print(f"PoB2数据获取失败: {e}")
                
        except Exception as e:
            print(f"动态数据获取失败: {e}")
            # 回退到原有方法
            return (
                get_poe2scout_client(),
                get_ninja_scraper(),
                get_pob2_extractor(), 
                get_poe2db_client()
            )
    else:
        # 回退到原有方法
        return (
            get_poe2scout_client(),
            get_ninja_scraper(),
            get_pob2_extractor(), 
            get_poe2db_client()
        )
    
    return result

def health_check_all_sources():
    """
    检查四大数据源的可用性，使用动态爬虫系统进行实时检查
    
    Returns:
        dict: 各数据源的健康状态
    """
    health_status = {
        'poe2scout': {'available': False, 'description': '未知状态'},
        'poe_ninja': {'available': False, 'description': '未知状态'},
        'path_of_building_2': {'available': False, 'info': {'source': 'unknown'}, 'description': '未知状态'},
        'poe2db': {'status': {'status': 'unknown'}, 'description': '未知状态'}
    }
    
    # 使用动态爬虫系统进行健康检查
    if DYNAMIC_CRAWLERS_AVAILABLE:
        try:
            dynamic_manager = DynamicDataManager()
            
            # PoE2Scout状态检查
            try:
                scout_items = dynamic_manager.scout_crawler.get_item_data()
                if scout_items:
                    health_status['poe2scout'] = {
                        'available': True, 
                        'description': f'API响应正常，获取到{len(scout_items)}个物品数据'
                    }
                else:
                    health_status['poe2scout'] = {
                        'available': False, 
                        'description': 'API无响应或数据为空'
                    }
            except Exception as e:
                health_status['poe2scout'] = {
                    'available': False, 
                    'description': f'连接失败: {str(e)[:50]}'
                }
            
            # PoE Ninja状态检查
            try:
                ninja_builds = dynamic_manager.ninja_crawler.crawl_meta_builds()
                if ninja_builds:
                    health_status['poe_ninja'] = {
                        'available': True,
                        'description': f'爬虫正常，获取到{len(ninja_builds)}个构筑数据'
                    }
                else:
                    health_status['poe_ninja'] = {
                        'available': False,
                        'description': '网页爬虫无法获取数据'
                    }
            except Exception as e:
                health_status['poe_ninja'] = {
                    'available': False,
                    'description': f'爬虫失败: {str(e)[:50]}'
                }
            
            # PoE2DB状态检查
            try:
                poe2db_skills = dynamic_manager.poe2db_crawler.crawl_skill_gems()
                if poe2db_skills:
                    health_status['poe2db'] = {
                        'status': {'status': 'healthy'},
                        'description': f'数据库连接正常，获取到{len(poe2db_skills)}个技能数据'
                    }
                else:
                    health_status['poe2db'] = {
                        'status': {'status': 'error'},
                        'description': '数据库无响应或数据为空'
                    }
            except Exception as e:
                health_status['poe2db'] = {
                    'status': {'status': 'error'},
                    'description': f'数据库连接失败: {str(e)[:50]}'
                }
                
        except Exception as e:
            print(f"动态健康检查失败: {e}")
    
    # PoB2状态检查（始终通过现有系统）
    try:
        pob2_extractor = get_pob2_extractor()
        if pob2_extractor.is_available():
            pob2_gems = pob2_extractor.get_skill_gems()
            if pob2_gems:
                cache_exists = Path("data_storage/pob2_cache/Gems.lua").exists()
                source_type = 'cache' if cache_exists else 'github'
                health_status['path_of_building_2'] = {
                    'available': True,
                    'info': {'source': source_type},
                    'description': f'PoB2集成正常，加载了{len(pob2_gems)}个技能宝石 (来源: {source_type})'
                }
            else:
                health_status['path_of_building_2'] = {
                    'available': False,
                    'info': {'source': 'unavailable'},
                    'description': 'PoB2数据加载失败'
                }
        else:
            health_status['path_of_building_2'] = {
                'available': False,
                'info': {'source': 'unavailable'},
                'description': 'PoB2数据源不可用'
            }
    except Exception as e:
        health_status['path_of_building_2'] = {
            'available': False,
            'info': {'source': 'error'},
            'description': f'PoB2检查失败: {str(e)[:50]}'
        }
    
    return health_status

# 导出所有组件
__all__ = [
    # 基础类
    'BaseDataSource',
    
    # PoE2Scout API
    'PoE2ScoutClient',
    'ItemPrice', 
    'CurrencyExchange',
    'get_poe2scout_client',
    
    # PoE Ninja爬虫
    'NinjaMetaScraper',
    'PopularBuild',
    'SkillUsageStats', 
    'AscendancyTrend',
    'get_ninja_scraper',
    
    # Path of Building 2
    'PoB2DataExtractor',
    'SkillGem',
    'PassiveNode',
    'BaseItem',
    'get_pob2_extractor',
    
    # PoE2DB
    'PoE2DBClient',
    'ItemDetail',
    'SkillDetail', 
    'AscendancyInfo',
    'get_poe2db_client',
    
    # 便捷函数
    'get_all_four_sources',
    'health_check_all_sources'
]

# 模块信息
__version__ = "2.0.0"
__description__ = "四大核心数据源集成模块 - PoE2智能构筑推荐系统"
__sources__ = [
    "https://poe2scout.com - 市场价格数据",
    "https://poe.ninja/poe2/builds - Meta趋势分析", 
    "Path of Building 2 (GitHub/本地) - 官方游戏数据",
    "https://poe2db.tw/cn/ - 完整游戏数据库"
]