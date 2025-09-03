#!/usr/bin/env python3
"""
动态数据爬虫系统
从四大数据源实时获取PoE2动态数据
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import re
from pathlib import Path

@dataclass
class MarketItem:
    """市场物品数据"""
    name: str
    type: str
    price_chaos: float
    price_divine: float
    league: str
    confidence: float
    listings: int
    trend: str  # "rising", "stable", "falling"
    last_updated: datetime

@dataclass
class SkillData:
    """技能数据"""
    name: str
    gem_type: str  # skill, support, meta
    damage_type: str
    mana_cost: int
    tags: List[str]
    description: str
    requirements: Dict[str, int]
    stats: List[str]

@dataclass
class MetaBuildData:
    """完整的Meta构筑数据"""
    name: str
    character_class: str
    ascendancy: str
    main_skill: str
    support_gems: List[str]
    popularity: float
    average_level: int
    key_items: List[str]
    estimated_dps: Optional[int]
    
    # 新增详细数据
    passive_tree: Dict[str, Any]  # 天赋树分配
    equipment: Dict[str, Dict]    # 装备配置
    flask_setup: List[Dict]       # 药剂配置
    aura_setup: List[str]        # 光环配置
    defense_stats: Dict[str, int] # 防御属性
    offense_stats: Dict[str, int] # 输出属性
    movement_stats: Dict[str, int] # 移动属性
    cost_analysis: Dict[str, float] # 成本分析
    playstyle: str               # 游戏风格
    difficulty_rating: int       # 难度评级 (1-5)
    league_suitability: List[str] # 适合的联赛
    pros_cons: Dict[str, List[str]] # 优缺点
    leveling_guide: List[Dict]   # 升级指南
    endgame_scaling: Dict[str, str] # 终局扩展性

class PoE2ScoutCrawler:
    """PoE2Scout API爬虫"""
    
    def __init__(self, cache_dir: str = "data_storage/market_cache"):
        self.base_url = "https://poe2scout.com"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PoE2BuildGenerator/1.0 (Educational Purpose)',
            'Accept': 'application/json'
        })
        
    def get_item_data(self, league: str = "Rise of the Abyssal") -> List[MarketItem]:
        """获取市场物品数据"""
        try:
            # 使用可用的API端点，添加必需的league参数
            params = {'league': league}
            response = self.session.get(f"{self.base_url}/api/items", params=params, timeout=15)
            
            if response.status_code == 200:
                raw_data = response.json()
                items = []
                
                # API直接返回物品数组
                if isinstance(raw_data, list):
                    for item_data in raw_data:
                        try:
                            # 从价格日志中获取最新价格
                            price_logs = item_data.get('priceLogs', [])
                            latest_price = 0
                            if price_logs:
                                for log in price_logs:
                                    if log and isinstance(log, dict) and 'price' in log:
                                        latest_price = log['price']
                                        break
                            
                            item = MarketItem(
                                name=item_data.get('name', ''),
                                type=item_data.get('type', ''),
                                price_chaos=float(latest_price),
                                price_divine=float(latest_price / 300) if latest_price > 300 else 0,  # 大概汇率
                                league=league,
                                confidence=0.8,  # 默认置信度
                                listings=1,  # 默认
                                trend='stable',
                                last_updated=datetime.now()
                            )
                            items.append(item)
                        except (ValueError, KeyError, TypeError):
                            continue
                
                # 缓存数据
                cache_file = self.cache_dir / f"scout_items_{league}.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump([asdict(item) for item in items], f, default=str, indent=2)
                
                print(f"PoE2Scout: 获取到 {len(items)} 个物品数据")
                return items
                
            else:
                print(f"PoE2Scout API失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"PoE2Scout爬虫异常: {e}")
            return []

class PoE2DBCrawler:
    """PoE2DB网站爬虫"""
    
    def __init__(self, cache_dir: str = "data_storage/poe2db_cache"):
        self.base_url = "https://poe2db.tw/us"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_skill_gems(self) -> List[SkillData]:
        """爬取技能宝石数据"""
        try:
            response = self.session.get(f"{self.base_url}/Skill_Gems", timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                skills = []
                
                # 查找技能表格
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')[1:]  # 跳过表头
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            try:
                                skill_name = cells[0].get_text(strip=True)
                                gem_type = self._determine_gem_type(cells[1].get_text(strip=True))
                                mana_cost = self._extract_number(cells[2].get_text(strip=True))
                                description = cells[3].get_text(strip=True)
                                
                                skill = SkillData(
                                    name=skill_name,
                                    gem_type=gem_type,
                                    damage_type=self._determine_damage_type(description),
                                    mana_cost=mana_cost,
                                    tags=self._extract_tags(description),
                                    description=description,
                                    requirements={},
                                    stats=[]
                                )
                                skills.append(skill)
                                
                            except Exception:
                                continue
                
                # 缓存数据
                cache_file = self.cache_dir / "skill_gems.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump([asdict(skill) for skill in skills], f, default=str, indent=2)
                
                print(f"PoE2DB: 获取到 {len(skills)} 个技能数据")
                return skills
                
            else:
                print(f"PoE2DB访问失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"PoE2DB爬虫异常: {e}")
            return []
    
    def _determine_gem_type(self, text: str) -> str:
        """判断宝石类型"""
        text = text.lower()
        if 'support' in text:
            return 'support'
        elif 'meta' in text:
            return 'meta'
        else:
            return 'skill'
    
    def _determine_damage_type(self, description: str) -> str:
        """判断伤害类型"""
        description = description.lower()
        if any(word in description for word in ['fire', 'burn', 'ignite']):
            return 'fire'
        elif any(word in description for word in ['cold', 'freeze', 'chill']):
            return 'cold'
        elif any(word in description for word in ['lightning', 'shock', 'spark']):
            return 'lightning'
        elif any(word in description for word in ['chaos', 'poison', 'withered']):
            return 'chaos'
        elif any(word in description for word in ['physical', 'bleed', 'impale']):
            return 'physical'
        else:
            return 'elemental'
    
    def _extract_tags(self, description: str) -> List[str]:
        """提取技能标签"""
        tags = []
        description_lower = description.lower()
        
        tag_keywords = {
            'bow': ['bow', 'arrow'],
            'melee': ['melee', 'strike', 'slam'],
            'spell': ['spell', 'cast', 'magic'],
            'projectile': ['projectile', 'pierce'],
            'area': ['area', 'explosion', 'blast'],
            'minion': ['minion', 'summon', 'skeleton']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _extract_number(self, text: str) -> int:
        """从文本中提取数字"""
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0

class PoENinjaCrawler:
    """PoE Ninja爬虫"""
    
    def __init__(self, cache_dir: str = "data_storage/ninja_cache"):
        self.base_url = "https://poe.ninja"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_meta_builds(self) -> List[MetaBuildData]:
        """爬取Meta构筑数据"""
        try:
            # 尝试API访问
            api_success = False
            builds = []
            
            # 尝试不同的联赛
            for league in ['Affliction', 'Standard', 'Hardcore']:
                try:
                    api_url = f"https://poe.ninja/api/data/buildsoverview?league={league}"
                    response = self.session.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and 'builds' in data:
                            api_success = True
                            # 处理API数据
                            for build_data in data['builds'][:20]:
                                build = MetaBuildData(
                                    name=build_data.get('name', 'Unknown Build'),
                                    character_class=build_data.get('class', 'Unknown'),
                                    ascendancy=build_data.get('ascendancy', 'Unknown'),
                                    main_skill=build_data.get('mainSkill', 'Unknown'),
                                    support_gems=build_data.get('supportGems', []),
                                    popularity=float(build_data.get('popularity', 0.1)),
                                    average_level=int(build_data.get('level', 90)),
                                    key_items=build_data.get('keyItems', []),
                                    estimated_dps=build_data.get('dps')
                                )
                                builds.append(build)
                            break
                except:
                    continue
            
            # 如果API失败，使用独特构筑数据库
            if not api_success:
                print("PoE Ninja API不可用，使用独特构筑数据库")
                try:
                    import sys
                    from pathlib import Path
                    project_root = Path(__file__).parent
                    sys.path.insert(0, str(project_root))
                    
                    from unique_builds_database import UniqueBuildDatabase
                    
                    unique_db = UniqueBuildDatabase()
                    unique_builds = unique_db.builds
                    
                    for unique_build in unique_builds:
                        build = MetaBuildData(
                            name=unique_build.name,
                            character_class=unique_build.character_class,
                            ascendancy=unique_build.ascendancy,
                            main_skill=unique_build.main_skill,
                            support_gems=unique_build.support_gems,
                            popularity=unique_build.popularity_score,
                            average_level=85,
                            key_items=list(unique_build.equipment.keys()),
                            estimated_dps=unique_build.offense_stats.get('total_dps', 500000),
                            
                            # 扩展的完整数据
                            passive_tree=unique_build.passive_tree,
                            equipment=unique_build.equipment,
                            flask_setup=unique_build.flask_setup,
                            aura_setup=unique_build.aura_setup,
                            defense_stats=unique_build.defense_stats,
                            offense_stats=unique_build.offense_stats,
                            movement_stats=unique_build.movement_stats,
                            cost_analysis=unique_build.cost_analysis,
                            playstyle=unique_build.playstyle,
                            difficulty_rating=unique_build.difficulty_rating,
                            league_suitability=unique_build.league_suitability,
                            pros_cons=unique_build.pros_cons,
                            leveling_guide=unique_build.leveling_guide,
                            endgame_scaling=unique_build.endgame_scaling
                        )
                        builds.append(build)
                        
                except ImportError:
                    print("独特构筑数据库不可用，尝试AI推荐引擎")
                    try:
                        from ai_build_recommender import AIBuildRecommender
                        ai_recommender = AIBuildRecommender()
                        ai_builds = ai_recommender.generate_unique_combinations(count=3)
                        
                        for ai_build in ai_builds:
                            build = MetaBuildData(
                                name=ai_build.name,
                                character_class=ai_build.character_class,
                                ascendancy=ai_build.ascendancy,
                                main_skill=ai_build.skill_combination.main_skill,
                                support_gems=ai_build.skill_combination.support_gems,
                                popularity=1.0 - ai_build.innovation_score,  # 创新度越高，流行度越低
                                average_level=85,
                                key_items=["AI Generated Equipment"],
                                estimated_dps=int(ai_build.estimated_performance.get('dps', 500000)),
                                
                                # AI生成的完整数据
                                passive_tree=ai_build.passive_allocation,
                                equipment=ai_build.equipment_strategy,
                                flask_setup=[],
                                aura_setup=[],
                                defense_stats={"effective_health_pool": int(ai_build.estimated_performance.get('survivability', 7000))},
                                offense_stats={"total_dps": int(ai_build.estimated_performance.get('dps', 500000))},
                                movement_stats={},
                                cost_analysis=ai_build.cost_prediction,
                                playstyle=f"AI Generated: {ai_build.defense_approach}",
                                difficulty_rating=ai_build.difficulty_factors.get('mechanical_complexity', 3),
                                league_suitability=["Standard", "League"],
                                pros_cons={"pros": ai_build.why_unique, "cons": ai_build.potential_issues},
                                leveling_guide=[],
                                endgame_scaling={}
                            )
                            builds.append(build)
                        
                        print(f"AI推荐引擎提供了 {len(ai_builds)} 个创新构筑")
                        
                    except ImportError:
                        print("AI推荐引擎不可用，使用基础模拟数据")
                    # 基础备用数据
                    basic_builds = [
                        {"name": "Lightning Monk", "class": "Monk", "ascendancy": "Invoker", "skill": "Lightning Strike", "popularity": 0.15},
                        {"name": "Ice Sorceress", "class": "Sorceress", "ascendancy": "Stormweaver", "skill": "Glacial Cascade", "popularity": 0.12}
                    ]
                    
                    for mock_data in basic_builds:
                        build = MetaBuildData(
                            name=mock_data["name"],
                            character_class=mock_data["class"], 
                            ascendancy=mock_data["ascendancy"],
                            main_skill=mock_data["skill"],
                            support_gems=["Added Lightning Damage", "Elemental Focus"],
                            popularity=mock_data["popularity"],
                            average_level=85,
                            key_items=["Unique Weapon", "Life Flask"],
                            estimated_dps=500000,
                            
                            # 默认空数据
                            passive_tree={},
                            equipment={},
                            flask_setup=[],
                            aura_setup=[],
                            defense_stats={},
                            offense_stats={},
                            movement_stats={},
                            cost_analysis={},
                            playstyle="Unknown",
                            difficulty_rating=3,
                            league_suitability=["Standard"],
                            pros_cons={"pros": [], "cons": []},
                            leveling_guide=[],
                            endgame_scaling={}
                        )
                        builds.append(build)
            
            # 缓存数据
            cache_file = self.cache_dir / "meta_builds.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(build) for build in builds], f, default=str, indent=2)
            
            source = "API" if api_success else "Mock Data"
            print(f"PoE Ninja: 获取到 {len(builds)} 个Meta构筑 (来源: {source})")
            return builds
                
        except Exception as e:
            print(f"PoE Ninja爬虫异常: {e}")
            return []
    
    def _extract_build_name(self, element) -> str:
        """提取构筑名称"""
        # 根据实际HTML结构实现
        text = element.get_text(strip=True)
        return text[:50] if text else ""
    
    def _extract_class(self, element) -> str:
        """提取职业"""
        return "Unknown"  # 需要根据实际结构实现
    
    def _extract_ascendancy(self, element) -> str:
        """提取升华职业"""
        return "Unknown"  # 需要根据实际结构实现
    
    def _extract_main_skill(self, element) -> str:
        """提取主技能"""
        return "Unknown"  # 需要根据实际结构实现
    
    def _extract_support_gems(self, element) -> List[str]:
        """提取辅助宝石"""
        return []  # 需要根据实际结构实现

class DynamicDataManager:
    """动态数据管理器"""
    
    def __init__(self):
        self.scout_crawler = PoE2ScoutCrawler()
        self.poe2db_crawler = PoE2DBCrawler()
        self.ninja_crawler = PoENinjaCrawler()
        
    def update_all_data(self, league: str = "Rise of the Abyssal"):
        """更新所有动态数据"""
        print("=== 开始更新动态数据 ===")
        start_time = time.time()
        
        # 1. 更新市场数据
        print("\n1. 更新市场数据...")
        market_items = self.scout_crawler.get_item_data(league)
        
        # 2. 更新技能数据
        print("\n2. 更新技能数据...")
        skill_data = self.poe2db_crawler.crawl_skill_gems()
        
        # 3. 更新Meta数据
        print("\n3. 更新Meta数据...")
        meta_builds = self.ninja_crawler.crawl_meta_builds()
        
        elapsed = time.time() - start_time
        print(f"\n=== 动态数据更新完成 ===")
        print(f"用时: {elapsed:.1f}秒")
        print(f"市场物品: {len(market_items)}")
        print(f"技能数据: {len(skill_data)}")
        print(f"Meta构筑: {len(meta_builds)}")
        
        return {
            'market_items': market_items,
            'skill_data': skill_data,
            'meta_builds': meta_builds,
            'updated_at': datetime.now(),
            'league': league
        }

def main():
    """运行动态数据爬虫"""
    manager = DynamicDataManager()
    data = manager.update_all_data()
    return data

if __name__ == "__main__":
    data = main()