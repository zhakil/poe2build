# API使用指南

## 📖 概述

本文档提供基于**真实PoE2数据源**的API完整使用指南。所有示例都基于实际可用的代码和数据源，可以直接运行和测试。

## 🚀 快速开始

### 最简单的使用方式

```python
# 1. 导入核心模块
from poe2_real_data_sources import PoE2RealDataOrchestrator

# 2. 初始化系统
orchestrator = PoE2RealDataOrchestrator()

# 3. 创建PoE2构筑请求
request = {
    'game': 'poe2',
    'mode': 'standard',
    'preferences': {
        'class': 'Ranger',
        'style': 'bow',
        'budget': {'amount': 10, 'currency': 'divine'}
    }
}

# 4. 获取推荐结果
result = orchestrator.create_poe2_build_recommendation(request)

# 5. 查看结果
print(f"推荐构筑: {result['recommendations'][0]['build_name']}")
print(f"总DPS: {result['recommendations'][0]['stats']['dps']['total_dps']:,}")
```

### 运行结果示例

```
=== PoE2构筑推荐结果 ===
游戏版本: Path of Exile 2
数据源: {'market': 'poe2scout', 'builds': 'poe2ninja', 'skills': 'poe2db', 'calculation': 'poe2_real_calculator'}
推荐数量: 2

--- PoE2推荐 1 ---
构筑名称: PoE2 Meta Lightning Arrow
职业: Ranger (Deadeye)
总DPS: 468,430
生命值: 11,757
能量护盾: 3,527
总EHP: 15,284
预估成本: 28 divine
```

## 🔧 核心API组件

### 1. PoE2数据协调器

```python
class PoE2RealDataOrchestrator:
    """PoE2系统的核心入口点"""
    
    def __init__(self):
        # 初始化所有真实PoE2数据源
        self.poe2_scout = PoE2ScoutAPI()      # 市场数据
        self.poe2db = PoE2DBScraper()         # 游戏数据  
        self.poe2_ninja = PoE2NinjaScraper()  # 构筑数据
        self.calculator = PoE2RealBuildCalculator(self.poe2db)
    
    def create_poe2_build_recommendation(self, user_request: Dict) -> Dict:
        """生成PoE2构筑推荐 - 主要API方法"""
        pass
```

### 使用示例

```python
# 高级配置示例
orchestrator = PoE2RealDataOrchestrator()

# 详细的用户请求
advanced_request = {
    'game': 'poe2',
    'mode': 'standard',  # 或 'hardcore'
    'preferences': {
        'class': 'Sorceress',           # 职业偏好
        'ascendancy': 'Chronomancer',   # 升华偏好
        'style': 'fire',                # 构筑风格
        'goal': 'boss_killing',         # 目标: clear_speed, boss_killing, balanced
        'budget': {                     # 预算限制
            'amount': 20,
            'currency': 'divine',
            'strict': True              # 严格预算控制
        },
        'level_target': 90,             # 目标等级
        'league': 'standard'            # 联盟
    },
    'requirements': {                   # 构筑要求
        'min_dps': 1000000,            # 最低DPS
        'min_ehp': 10000,              # 最低EHP
        'max_complexity': 'intermediate' # 复杂度: beginner, intermediate, advanced
    }
}

# 获取推荐
result = orchestrator.create_poe2_build_recommendation(advanced_request)

# 详细结果处理
for i, rec in enumerate(result['recommendations']):
    print(f"\n=== PoE2推荐 {i+1} ===")
    print(f"构筑: {rec['build_name']}")
    print(f"职业: {rec['class']} ({rec.get('ascendancy', 'Unknown')})")
    print(f"等级: {rec['level']}")
    
    # DPS信息
    dps = rec['stats']['dps']
    print(f"总DPS: {dps['total_dps']:,}")
    print(f"每击伤害: {dps['damage_per_hit']:,}")
    print(f"攻击速度: {dps['attack_speed']}")
    print(f"暴击率: {dps['crit_chance']}%")
    
    # 防御信息
    defense = rec['stats']['defenses']
    print(f"火焰抗性: {defense['fire_resistance']}%")
    print(f"冰霜抗性: {defense['cold_resistance']}%")
    print(f"闪电抗性: {defense['lightning_resistance']}%")
    print(f"混沌抗性: {defense['chaos_resistance']}%")
    
    # 生存能力
    surv = rec['stats']['survivability']
    print(f"生命值: {surv['total_life']:,}")
    print(f"能量护盾: {surv['total_energy_shield']:,}")
    print(f"总EHP: {surv['total_ehp']:,}")
    
    # 成本分析
    cost = rec['estimated_cost']
    print(f"预估成本: {cost['amount']} {cost['currency']}")
    print(f"流行度: {rec['popularity_score']*100:.1f}%")
```

## 📊 单独使用数据源API

### 1. PoE2 Scout API

```python
from poe2_real_data_sources import PoE2ScoutAPI

# 初始化PoE2 Scout
scout = PoE2ScoutAPI()

# 获取市场数据
market_data = scout.get_market_data()
print(f"数据状态: {market_data['status']}")
print(f"数据源: {market_data['source']}")

# 获取构筑数据  
builds = scout.get_build_data("popular")
print(f"获取到 {len(builds)} 个流行构筑")

for build in builds[:3]:  # 显示前3个
    print(f"- {build['name']} ({build['class']})")
```

### 2. PoE2DB API

```python
from poe2_real_data_sources import PoE2DBScraper

# 初始化PoE2DB
poe2db = PoE2DBScraper()

# 获取技能数据
skills_result = poe2db.get_skill_data()
print(f"技能数据状态: {skills_result['status']}")
print(f"获取到 {len(skills_result['skills'])} 个技能")

# 查看技能详情
for skill in skills_result['skills'][:5]:
    print(f"技能: {skill['name']}")
    print(f"  类型: {skill['type']}")
    print(f"  基础伤害: {skill['base_damage']}")
    print(f"  法力消耗: {skill['mana_cost']}")

# 获取物品数据
items_result = poe2db.get_item_data("weapons")
print(f"\n物品数据状态: {items_result['status']}")
print(f"获取到 {len(items_result['items'])} 个武器")

for item in items_result['items'][:3]:
    print(f"武器: {item['name']}")
    print(f"  类型: {item['type']}")
    print(f"  基础伤害: {item['base_damage']}")
    print(f"  等级需求: {item['level_req']}")
```

### 3. poe.ninja PoE2专区API

```python
from poe2_real_data_sources import PoE2NinjaScraper

# 初始化poe.ninja PoE2专区
ninja = PoE2NinjaScraper()

# 获取流行构筑
builds = ninja.get_popular_builds("standard")
print(f"ninja获取到 {len(builds)} 个构筑")

for build in builds:
    print(f"构筑: {build['name']}")
    print(f"职业: {build['class']}")
    print(f"等级: {build['level']}")
    print(f"流行度: {build.get('popularity', 0)*100:.1f}%")
```

## ⚙️ PoE2计算引擎API

### 独立使用计算引擎

```python
from poe2_real_data_sources import PoE2RealBuildCalculator, PoE2DBScraper

# 初始化计算引擎
poe2db = PoE2DBScraper()
calculator = PoE2RealBuildCalculator(poe2db)

# 构筑配置
build_config = {
    'main_skill': 'Lightning Arrow',
    'weapon': 'Lightning Bow', 
    'level': 85,
    'items': {
        'weapon': {'base_damage': 200, 'attack_speed': 1.5},
        'armor': {'energy_shield': 300, 'life': 80},
        'jewelry': {'resistance_bonus': 20}
    }
}

# 执行计算
result = calculator.calculate_poe2_build(build_config)

# 查看计算结果
print(f"构筑名称: {result['build_name']}")
print(f"主技能: {result['main_skill']}")
print(f"武器: {result['weapon']}")
print(f"等级: {result['level']}")

# DPS详情
dps = result['dps']
print(f"\nDPS分析:")
print(f"总DPS: {dps['total_dps']:,}")
print(f"技能贡献: {dps['skill_dps']:,}")
print(f"武器贡献: {dps['weapon_contribution']:,}")

# 防御详情
defenses = result['defenses']
print(f"\n防御分析:")
print(f"护甲: {defenses['armor']:,}")
print(f"闪避: {defenses['evasion']:,}")
print(f"火焰抗性: {defenses['fire_resistance']}%")

# 生存能力
surv = result['survivability']
print(f"\n生存能力:")
print(f"总生命: {surv['total_life']:,}")
print(f"能量护盾: {surv['total_energy_shield']:,}")
print(f"总EHP: {surv['total_ehp']:,}")
```

### 批量计算示例

```python
def batch_calculate_builds(calculator, build_configs: List[Dict]) -> List[Dict]:
    """批量计算多个构筑"""
    results = []
    
    for i, config in enumerate(build_configs):
        print(f"计算构筑 {i+1}/{len(build_configs)}: {config['main_skill']}")
        
        try:
            result = calculator.calculate_poe2_build(config)
            results.append(result)
        except Exception as e:
            print(f"计算失败: {e}")
            results.append(None)
    
    return results

# 批量构筑配置
build_configs = [
    {'main_skill': 'Lightning Arrow', 'weapon': 'Lightning Bow', 'level': 85},
    {'main_skill': 'Fireball', 'weapon': 'Fire Staff', 'level': 87},
    {'main_skill': 'Ice Spear', 'weapon': 'Ice Wand', 'level': 82}
]

# 执行批量计算
results = batch_calculate_builds(calculator, build_configs)

# 对比分析
print("\n=== 构筑对比 ===")
for result in results:
    if result:
        name = result['build_name']
        dps = result['dps']['total_dps']
        ehp = result['survivability']['total_ehp']
        print(f"{name}: DPS={dps:,}, EHP={ehp:,}")
```

## 🛠️ 高级API使用

### 自定义数据源

```python
class CustomPoE2DataSource(PoE2RealDataProvider):
    """自定义PoE2数据源示例"""
    
    def __init__(self, custom_url: str):
        super().__init__()
        self.base_url = custom_url
    
    def get_custom_data(self, query: str) -> Dict:
        """自定义数据获取方法"""
        try:
            response = self.session.get(f"{self.base_url}/api/{query}")
            return response.json()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# 使用自定义数据源
custom_source = CustomPoE2DataSource("https://my-poe2-api.com")
custom_data = custom_source.get_custom_data("builds")
```

### 扩展计算引擎

```python
class ExtendedPoE2Calculator(PoE2RealBuildCalculator):
    """扩展的PoE2计算引擎"""
    
    def calculate_custom_metric(self, build_config: Dict) -> float:
        """计算自定义指标"""
        base_result = self.calculate_poe2_build(build_config)
        
        dps = base_result['dps']['total_dps']
        ehp = base_result['survivability']['total_ehp']
        
        # 自定义效率指标
        efficiency = (dps * ehp) / 1000000000  # DPS*EHP效率
        
        return efficiency
    
    def compare_builds(self, build_configs: List[Dict]) -> Dict:
        """对比多个构筑"""
        comparisons = []
        
        for config in build_configs:
            result = self.calculate_poe2_build(config)
            efficiency = self.calculate_custom_metric(config)
            
            comparisons.append({
                'name': result['build_name'],
                'dps': result['dps']['total_dps'],
                'ehp': result['survivability']['total_ehp'],
                'efficiency': efficiency
            })
        
        # 按效率排序
        comparisons.sort(key=lambda x: x['efficiency'], reverse=True)
        
        return {
            'best_build': comparisons[0],
            'all_builds': comparisons,
            'ranking_metric': 'efficiency'
        }

# 使用扩展计算器
extended_calc = ExtendedPoE2Calculator(poe2db)
comparison = extended_calc.compare_builds(build_configs)
print(f"最佳构筑: {comparison['best_build']['name']}")
```

## 🔍 错误处理和调试

### API错误处理

```python
def safe_build_recommendation(orchestrator, request: Dict) -> Dict:
    """安全的构筑推荐调用"""
    try:
        result = orchestrator.create_poe2_build_recommendation(request)
        
        if result['status'] == 'success':
            print(f"成功获取 {len(result['recommendations'])} 个推荐")
            return result
        else:
            print(f"推荐生成失败: {result.get('message', 'Unknown error')}")
            return None
            
    except requests.RequestException as e:
        print(f"网络错误: {e}")
        # 使用离线数据
        return get_offline_recommendations(request)
        
    except Exception as e:
        print(f"未知错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_offline_recommendations(request: Dict) -> Dict:
    """离线推荐备案"""
    return {
        'status': 'offline',
        'recommendations': [{
            'build_name': 'Offline Recommendation',
            'class': request['preferences'].get('class', 'Unknown'),
            'stats': {'dps': {'total_dps': 1000000}},
            'estimated_cost': {'amount': 5, 'currency': 'divine'}
        }],
        'message': '使用离线数据'
    }
```

### 调试工具

```python
class PoE2APIDebugger:
    """PoE2 API调试工具"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.debug_log = []
    
    def debug_request(self, request: Dict) -> Dict:
        """调试API请求"""
        debug_info = {
            'request': request,
            'timestamp': time.time(),
            'data_sources_status': {},
            'calculation_details': {}
        }
        
        # 检查数据源状态
        try:
            market_data = self.orchestrator.poe2_scout.get_market_data()
            debug_info['data_sources_status']['poe2_scout'] = market_data['status']
        except Exception as e:
            debug_info['data_sources_status']['poe2_scout'] = f'error: {str(e)}'
        
        try:
            builds_data = self.orchestrator.poe2_ninja.get_popular_builds()
            debug_info['data_sources_status']['poe2_ninja'] = f'success: {len(builds_data)} builds'
        except Exception as e:
            debug_info['data_sources_status']['poe2_ninja'] = f'error: {str(e)}'
        
        # 执行请求
        try:
            result = self.orchestrator.create_poe2_build_recommendation(request)
            debug_info['result'] = 'success'
            debug_info['recommendations_count'] = len(result.get('recommendations', []))
        except Exception as e:
            debug_info['result'] = f'error: {str(e)}'
        
        self.debug_log.append(debug_info)
        return debug_info
    
    def print_debug_report(self):
        """打印调试报告"""
        print("=== PoE2 API调试报告 ===")
        
        for i, debug_info in enumerate(self.debug_log):
            print(f"\n--- 请求 {i+1} ---")
            print(f"时间: {time.ctime(debug_info['timestamp'])}")
            print(f"请求类型: {debug_info['request'].get('preferences', {}).get('class', 'Unknown')}")
            print(f"结果: {debug_info['result']}")
            
            print("数据源状态:")
            for source, status in debug_info['data_sources_status'].items():
                print(f"  {source}: {status}")

# 使用调试器
debugger = PoE2APIDebugger(orchestrator)
debug_info = debugger.debug_request(request)
debugger.print_debug_report()
```

## 📈 性能优化技巧

### 缓存优化

```python
# 启用缓存的推荐调用
def cached_recommendation(orchestrator, request: Dict, cache_duration: int = 1800) -> Dict:
    """带缓存的推荐调用"""
    import hashlib
    
    # 生成请求哈希
    request_str = json.dumps(request, sort_keys=True)
    request_hash = hashlib.md5(request_str.encode()).hexdigest()
    
    # 检查缓存
    cached_result = orchestrator.poe2_scout._get_from_cache(f"recommendation_{request_hash}", cache_duration)
    if cached_result:
        print("使用缓存结果")
        return cached_result
    
    # 生成新推荐
    result = orchestrator.create_poe2_build_recommendation(request)
    
    # 存储缓存
    orchestrator.poe2_scout._set_cache(f"recommendation_{request_hash}", result)
    
    return result
```

### 并发处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_recommendations(orchestrator, requests: List[Dict]) -> List[Dict]:
    """并行处理多个推荐请求"""
    
    def process_single_request(request):
        return orchestrator.create_poe2_build_recommendation(request)
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_single_request, request)
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks)
    
    return results

# 使用示例
requests = [
    {'game': 'poe2', 'preferences': {'class': 'Ranger', 'style': 'bow'}},
    {'game': 'poe2', 'preferences': {'class': 'Sorceress', 'style': 'fire'}},
    {'game': 'poe2', 'preferences': {'class': 'Warrior', 'style': 'melee'}}
]

# 并行执行
# results = asyncio.run(parallel_recommendations(orchestrator, requests))
```

## 📋 完整使用示例

### 端到端示例应用

```python
def create_poe2_build_app():
    """创建完整的PoE2构筑推荐应用"""
    
    # 初始化系统
    print("初始化PoE2构筑推荐系统...")
    orchestrator = PoE2RealDataOrchestrator()
    
    # 用户交互
    def get_user_preferences():
        print("\n=== PoE2构筑推荐 ===")
        
        # 获取用户输入
        user_class = input("选择职业 (Ranger/Sorceress/Warrior): ") or "Ranger"
        build_style = input("构筑风格 (bow/fire/melee): ") or "bow"
        budget = int(input("预算 (神圣石数量): ") or "10")
        
        return {
            'game': 'poe2',
            'mode': 'standard',
            'preferences': {
                'class': user_class,
                'style': build_style,
                'budget': {'amount': budget, 'currency': 'divine'}
            }
        }
    
    # 生成推荐
    def generate_recommendations(request):
        print("正在生成PoE2构筑推荐...")
        
        try:
            result = orchestrator.create_poe2_build_recommendation(request)
            return result
        except Exception as e:
            print(f"生成推荐时出错: {e}")
            return None
    
    # 显示结果
    def display_recommendations(result):
        if not result or not result.get('recommendations'):
            print("没有找到合适的构筑推荐")
            return
        
        print(f"\n找到 {len(result['recommendations'])} 个推荐构筑:")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n--- 推荐 {i} ---")
            print(f"构筑名称: {rec['build_name']}")
            print(f"职业: {rec['class']} ({rec.get('ascendancy', 'Unknown')})")
            print(f"等级: {rec['level']}")
            print(f"DPS: {rec['stats']['dps']['total_dps']:,}")
            print(f"生命: {rec['stats']['survivability']['total_life']:,}")
            print(f"能量护盾: {rec['stats']['survivability']['total_energy_shield']:,}")
            print(f"总EHP: {rec['stats']['survivability']['total_ehp']:,}")
            print(f"预估成本: {rec['estimated_cost']['amount']} {rec['estimated_cost']['currency']}")
            print(f"流行度: {rec['popularity_score']*100:.1f}%")
    
    # 主程序循环
    while True:
        try:
            # 获取用户偏好
            request = get_user_preferences()
            
            # 生成推荐
            result = generate_recommendations(request)
            
            # 显示结果
            display_recommendations(result)
            
            # 继续询问
            continue_choice = input("\n是否继续 (y/n): ").lower()
            if continue_choice != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"程序错误: {e}")
            continue

# 运行应用
if __name__ == "__main__":
    create_poe2_build_app()
```

---

**下一步**: 查看 [开发者指南](05_developer_guide.md) 了解如何扩展和贡献这个PoE2项目。