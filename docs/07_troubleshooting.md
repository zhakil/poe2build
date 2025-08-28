# 故障排除指南

## 📖 概述

本指南提供PoE2智能构筑生成器常见问题的诊断和解决方案，帮助开发者和用户快速定位和解决问题。

## 🔍 快速诊断

### 系统健康检查

```python
# health_check.py
import requests
import time
import psutil
from poe2_real_data_sources import PoE2RealDataOrchestrator

def quick_health_check():
    """快速系统健康检查"""
    print("=== PoE2系统健康检查 ===")
    
    # 1. 基本系统资源
    print(f"CPU使用率: {psutil.cpu_percent()}%")
    print(f"内存使用率: {psutil.virtual_memory().percent}%")
    print(f"磁盘使用率: {psutil.disk_usage('/').percent}%")
    
    # 2. 网络连接测试
    test_urls = [
        "https://poe2scout.com",
        "https://poe2db.tw", 
        "https://poe.ninja"
    ]
    
    print("\n网络连接测试:")
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{url}: {status}")
        except Exception as e:
            print(f"{url}: ❌ {str(e)[:50]}...")
    
    # 3. PoE2系统测试
    print("\nPoE2系统测试:")
    try:
        orchestrator = PoE2RealDataOrchestrator()
        print("系统初始化: ✅")
        
        # 测试推荐生成
        test_request = {
            'game': 'poe2',
            'preferences': {'class': 'Ranger', 'style': 'bow'}
        }
        
        start_time = time.time()
        result = orchestrator.create_poe2_build_recommendation(test_request)
        end_time = time.time()
        
        if result and 'recommendations' in result:
            print(f"推荐生成: ✅ ({end_time - start_time:.2f}s)")
            print(f"推荐数量: {len(result['recommendations'])}")
        else:
            print("推荐生成: ❌ 无结果")
            
    except Exception as e:
        print(f"系统测试: ❌ {str(e)}")

if __name__ == "__main__":
    quick_health_check()
```

### 诊断命令

```bash
# 运行健康检查
python health_check.py

# 检查Python环境
python -c "import sys; print(f'Python版本: {sys.version}')"
python -c "from poe2_real_data_sources import *; print('模块导入成功')"

# 检查网络连接
ping -c 3 poe2scout.com
ping -c 3 poe2db.tw
ping -c 3 poe.ninja

# 检查端口占用
netstat -tlnp | grep :8080
```

## ❌ 常见错误及解决方案

### 1. 导入错误

#### 错误信息
```
ModuleNotFoundError: No module named 'requests'
ImportError: No module named 'poe2_real_data_sources'
```

#### 原因分析
- 依赖包未安装
- Python环境问题
- 模块路径问题

#### 解决方案
```bash
# 1. 检查虚拟环境
which python
pip list | grep requests

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查Python路径
python -c "import sys; print('\n'.join(sys.path))"

# 4. 重新安装项目
pip install -e .
```

### 2. 网络连接错误

#### 错误信息
```
requests.exceptions.ConnectionError: HTTPSConnectionPool
requests.exceptions.Timeout: HTTPSConnectionPool
SSL: CERTIFICATE_VERIFY_FAILED
```

#### 原因分析
- 网络连接问题
- 防火墙阻止
- SSL证书问题
- DNS解析问题

#### 诊断和解决
```python
# network_debug.py
import requests
import socket
import ssl
from urllib.parse import urlparse

def diagnose_network_issue(url: str):
    """诊断网络连接问题"""
    print(f"诊断URL: {url}")
    parsed = urlparse(url)
    host = parsed.hostname
    port = 443 if parsed.scheme == 'https' else 80
    
    # 1. DNS解析测试
    try:
        ip = socket.gethostbyname(host)
        print(f"✅ DNS解析: {host} -> {ip}")
    except Exception as e:
        print(f"❌ DNS解析失败: {e}")
        return
    
    # 2. 端口连接测试
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print(f"✅ 端口连接: {host}:{port}")
    except Exception as e:
        print(f"❌ 端口连接失败: {e}")
        return
    
    # 3. SSL证书测试 (HTTPS)
    if parsed.scheme == 'https':
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port)) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    print(f"✅ SSL证书: {cert['subject']}")
        except Exception as e:
            print(f"❌ SSL证书问题: {e}")
    
    # 4. HTTP请求测试
    try:
        response = requests.get(url, timeout=10, verify=True)
        print(f"✅ HTTP请求: 状态码 {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误: {e}")
        print("尝试解决方案:")
        print("  1. 更新requests和certifi包: pip install -U requests certifi")
        print("  2. 检查系统时间是否正确")
        print("  3. 临时跳过SSL验证 (不推荐): requests.get(url, verify=False)")
    except requests.exceptions.Timeout as e:
        print(f"❌ 请求超时: {e}")
        print("尝试解决方案:")
        print("  1. 增加超时时间: requests.get(url, timeout=30)")
        print("  2. 检查网络连接稳定性")
        print("  3. 使用代理: requests.get(url, proxies={'https': 'proxy_url'})")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

# 使用示例
if __name__ == "__main__":
    for url in ["https://poe2scout.com", "https://poe2db.tw", "https://poe.ninja"]:
        diagnose_network_issue(url)
        print("-" * 50)
```

### 3. 数据解析错误

#### 错误信息
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
AttributeError: 'NoneType' object has no attribute 'find_all'
KeyError: 'builds'
```

#### 原因分析
- API返回格式变化
- 网页结构更新
- 数据为空或格式错误

#### 调试工具
```python
# data_debug.py
import requests
from bs4 import BeautifulSoup
import json

class PoE2DataDebugger:
    """PoE2数据调试工具"""
    
    def debug_api_response(self, url: str, expected_format: str = "json"):
        """调试API响应"""
        print(f"调试URL: {url}")
        
        try:
            response = requests.get(url, timeout=15)
            print(f"状态码: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"响应大小: {len(response.content)} bytes")
            
            # 保存原始响应
            with open(f"debug_response_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("原始响应已保存到文件")
            
            # 尝试JSON解析
            if expected_format == "json":
                try:
                    data = response.json()
                    print("✅ JSON解析成功")
                    print(f"顶级键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    return data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print("响应内容预览:")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            
            # 尝试HTML解析
            elif expected_format == "html":
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    print("✅ HTML解析成功")
                    
                    # 查找常见的数据容器
                    tables = soup.find_all('table')
                    divs = soup.find_all('div', class_=lambda x: x and 'build' in x.lower())
                    
                    print(f"找到 {len(tables)} 个表格")
                    print(f"找到 {len(divs)} 个可能的构筑容器")
                    
                    return soup
                except Exception as e:
                    print(f"❌ HTML解析失败: {e}")
            
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def analyze_data_structure(self, data, max_depth=3, current_depth=0):
        """分析数据结构"""
        indent = "  " * current_depth
        
        if isinstance(data, dict):
            print(f"{indent}Dict ({len(data)} keys):")
            for key, value in list(data.items())[:5]:  # 只显示前5个键
                print(f"{indent}  {key}: {type(value).__name__}")
                if current_depth < max_depth:
                    self.analyze_data_structure(value, max_depth, current_depth + 1)
        
        elif isinstance(data, list):
            print(f"{indent}List ({len(data)} items):")
            if data and current_depth < max_depth:
                print(f"{indent}  [0]: {type(data[0]).__name__}")
                self.analyze_data_structure(data[0], max_depth, current_depth + 1)
        
        else:
            preview = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
            print(f"{indent}{type(data).__name__}: {preview}")

# 使用示例
debugger = PoE2DataDebugger()
data = debugger.debug_api_response("https://poe2scout.com", "html")
if data:
    debugger.analyze_data_structure(data)
```

### 4. 缓存问题

#### 错误信息
```
Redis connection failed
Cache hit rate too low
Memory usage too high
```

#### 诊断和解决
```python
# cache_debug.py
import time
import tracemalloc
from poe2_real_data_sources import PoE2RealDataProvider

class CacheDebugger:
    """缓存调试工具"""
    
    def __init__(self, data_provider: PoE2RealDataProvider):
        self.provider = data_provider
    
    def diagnose_cache_performance(self):
        """诊断缓存性能"""
        print("=== 缓存性能诊断 ===")
        
        # 1. 缓存大小检查
        cache_size = len(self.provider.cache)
        print(f"缓存项数量: {cache_size}")
        
        # 2. 内存使用检查
        tracemalloc.start()
        
        # 模拟缓存操作
        test_keys = [f"test_key_{i}" for i in range(100)]
        test_data = {"test": "data", "timestamp": time.time()}
        
        for key in test_keys:
            self.provider._set_cache(key, test_data)
        
        current, peak = tracemalloc.get_traced_memory()
        print(f"当前内存使用: {current / 1024 / 1024:.2f} MB")
        print(f"峰值内存使用: {peak / 1024 / 1024:.2f} MB")
        tracemalloc.stop()
        
        # 3. 缓存命中率测试
        hits = 0
        misses = 0
        
        for key in test_keys:
            if self.provider._get_from_cache(key, 3600):
                hits += 1
            else:
                misses += 1
        
        hit_rate = hits / (hits + misses) * 100 if (hits + misses) > 0 else 0
        print(f"缓存命中率: {hit_rate:.1f}%")
        
        # 4. 缓存清理测试
        old_size = len(self.provider.cache)
        # 模拟过期数据
        expired_data = {"timestamp": time.time() - 7200}  # 2小时前
        self.provider._set_cache("expired_key", expired_data)
        
        # 检查过期处理
        result = self.provider._get_from_cache("expired_key", 3600)  # 1小时TTL
        if result is None:
            print("✅ 过期缓存正确处理")
        else:
            print("❌ 过期缓存未正确清理")
    
    def fix_cache_issues(self):
        """修复缓存问题"""
        print("=== 缓存问题修复 ===")
        
        # 1. 清理所有缓存
        self.provider.cache.clear()
        print("✅ 缓存已清理")
        
        # 2. 重新初始化缓存系统
        self.provider.cache = {}
        print("✅ 缓存系统已重新初始化")

# 使用示例
from poe2_real_data_sources import PoE2ScoutAPI
scout = PoE2ScoutAPI()
cache_debugger = CacheDebugger(scout)
cache_debugger.diagnose_cache_performance()
```

### 5. 计算错误

#### 错误信息
```
DPS calculation returned negative value
ZeroDivisionError in defense calculation
Energy shield calculation overflow
```

#### 调试和验证
```python
# calculation_debug.py
from poe2_real_data_sources import PoE2RealBuildCalculator, PoE2DBScraper

class CalculationDebugger:
    """计算调试工具"""
    
    def __init__(self):
        self.poe2db = PoE2DBScraper()
        self.calculator = PoE2RealBuildCalculator(self.poe2db)
    
    def validate_calculation_inputs(self, build_config: dict) -> dict:
        """验证计算输入"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # 检查必需字段
        required_fields = ['main_skill', 'level']
        for field in required_fields:
            if field not in build_config:
                validation['errors'].append(f"缺少必需字段: {field}")
                validation['valid'] = False
        
        # 检查数值范围
        if 'level' in build_config:
            level = build_config['level']
            if not isinstance(level, int) or level < 1 or level > 100:
                validation['errors'].append(f"等级值无效: {level}")
                validation['valid'] = False
            elif level < 10:
                validation['warnings'].append(f"等级较低: {level}")
        
        # 检查技能名称
        if 'main_skill' in build_config:
            skill = build_config['main_skill']
            if not isinstance(skill, str) or len(skill) == 0:
                validation['errors'].append("技能名称无效")
                validation['valid'] = False
        
        return validation
    
    def debug_calculation_steps(self, build_config: dict):
        """调试计算步骤"""
        print("=== 计算步骤调试 ===")
        
        # 1. 输入验证
        validation = self.validate_calculation_inputs(build_config)
        if not validation['valid']:
            print("❌ 输入验证失败:")
            for error in validation['errors']:
                print(f"  - {error}")
            return None
        
        if validation['warnings']:
            print("⚠️ 输入警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # 2. 逐步计算
        try:
            print("\n步骤1: DPS计算...")
            dps_result = self.calculator._calculate_poe2_dps(
                build_config.get('main_skill', 'Lightning Arrow'),
                build_config.get('weapon', 'Lightning Bow'),
                build_config.get('level', 85),
                build_config.get('items', {})
            )
            print(f"  总DPS: {dps_result['total_dps']:,}")
            
            print("\n步骤2: 防御计算...")
            defense_result = self.calculator._calculate_poe2_defenses(
                build_config.get('level', 85),
                build_config.get('items', {})
            )
            print(f"  火焰抗性: {defense_result['fire_resistance']}%")
            
            print("\n步骤3: 生存能力计算...")
            surv_result = self.calculator._calculate_poe2_survivability(
                build_config.get('level', 85),
                build_config.get('items', {}),
                defense_result
            )
            print(f"  总EHP: {surv_result['total_ehp']:,}")
            
            return {
                'dps': dps_result,
                'defenses': defense_result,
                'survivability': surv_result
            }
            
        except Exception as e:
            print(f"❌ 计算过程出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_calculation_tests(self):
        """运行计算测试用例"""
        print("=== 计算测试用例 ===")
        
        test_cases = [
            {
                'name': '标准弓箭手',
                'config': {
                    'main_skill': 'Lightning Arrow',
                    'weapon': 'Lightning Bow',
                    'level': 85,
                    'items': {}
                }
            },
            {
                'name': '高级法师',
                'config': {
                    'main_skill': 'Fireball',
                    'weapon': 'Fire Staff',
                    'level': 95,
                    'items': {
                        'armor': {'energy_shield': 500}
                    }
                }
            },
            {
                'name': '边界测试 - 最低等级',
                'config': {
                    'main_skill': 'Basic Attack',
                    'weapon': 'Basic Weapon',
                    'level': 1,
                    'items': {}
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n测试: {test_case['name']}")
            result = self.debug_calculation_steps(test_case['config'])
            
            if result:
                # 验证结果合理性
                dps = result['dps']['total_dps']
                ehp = result['survivability']['total_ehp']
                
                if dps <= 0:
                    print(f"  ❌ DPS异常: {dps}")
                elif dps < 10000:
                    print(f"  ⚠️ DPS较低: {dps:,}")
                else:
                    print(f"  ✅ DPS正常: {dps:,}")
                
                if ehp <= 0:
                    print(f"  ❌ EHP异常: {ehp}")
                elif ehp < 5000:
                    print(f"  ⚠️ EHP较低: {ehp:,}")
                else:
                    print(f"  ✅ EHP正常: {ehp:,}")

# 使用示例
calc_debugger = CalculationDebugger()
calc_debugger.run_calculation_tests()
```

## 📊 性能问题诊断

### 1. 响应时间过慢

#### 诊断工具
```python
# performance_debug.py
import time
import psutil
import threading
from functools import wraps

def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 开始监控
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 结束监控
        end_time = time.time()
        end_cpu = psutil.cpu_percent()
        end_memory = psutil.virtual_memory().percent
        
        # 输出性能数据
        execution_time = end_time - start_time
        cpu_usage = end_cpu - start_cpu
        memory_usage = end_memory - start_memory
        
        print(f"函数: {func.__name__}")
        print(f"执行时间: {execution_time:.2f}s")
        print(f"CPU使用: {cpu_usage:+.1f}%")
        print(f"内存使用: {memory_usage:+.1f}%")
        
        if execution_time > 10:
            print("⚠️ 执行时间过长")
        if cpu_usage > 50:
            print("⚠️ CPU使用率过高")
        if memory_usage > 20:
            print("⚠️ 内存使用增长过多")
        
        return result
    return wrapper

# 性能测试
@performance_monitor
def test_recommendation_performance():
    from poe2_real_data_sources import PoE2RealDataOrchestrator
    
    orchestrator = PoE2RealDataOrchestrator()
    request = {
        'game': 'poe2',
        'preferences': {'class': 'Ranger', 'style': 'bow'}
    }
    
    return orchestrator.create_poe2_build_recommendation(request)

if __name__ == "__main__":
    test_recommendation_performance()
```

### 2. 内存泄漏检测

```python
# memory_debug.py
import gc
import tracemalloc
import time
from poe2_real_data_sources import PoE2RealDataOrchestrator

def memory_leak_test():
    """内存泄漏测试"""
    print("=== 内存泄漏检测 ===")
    
    # 启动内存追踪
    tracemalloc.start()
    
    # 基准内存使用
    gc.collect()  # 强制垃圾回收
    baseline_current, baseline_peak = tracemalloc.get_traced_memory()
    print(f"基准内存: {baseline_current / 1024 / 1024:.2f} MB")
    
    # 执行多次操作
    orchestrator = PoE2RealDataOrchestrator()
    test_request = {
        'game': 'poe2',
        'preferences': {'class': 'Ranger', 'style': 'bow'}
    }
    
    for i in range(10):
        print(f"执行第 {i+1} 次...")
        result = orchestrator.create_poe2_build_recommendation(test_request)
        
        # 记录内存使用
        current, peak = tracemalloc.get_traced_memory()
        print(f"  内存使用: {current / 1024 / 1024:.2f} MB")
        
        # 每5次强制垃圾回收
        if i % 5 == 4:
            gc.collect()
            after_gc_current, _ = tracemalloc.get_traced_memory()
            print(f"  GC后内存: {after_gc_current / 1024 / 1024:.2f} MB")
    
    # 最终内存使用
    final_current, final_peak = tracemalloc.get_traced_memory()
    print(f"\n最终内存: {final_current / 1024 / 1024:.2f} MB")
    print(f"峰值内存: {final_peak / 1024 / 1024:.2f} MB")
    print(f"内存增长: {(final_current - baseline_current) / 1024 / 1024:.2f} MB")
    
    # 内存泄漏警告
    if final_current > baseline_current * 2:
        print("⚠️ 可能存在内存泄漏")
        
        # 显示最大内存消耗者
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        print("\n内存使用TOP 10:")
        for stat in top_stats[:10]:
            print(f"  {stat}")
    
    tracemalloc.stop()

if __name__ == "__main__":
    memory_leak_test()
```

## 🛠️ 自动化故障排除

### 自动诊断脚本

```python
# auto_diagnosis.py
import os
import sys
import subprocess
import json
from datetime import datetime

class PoE2AutoDiagnosis:
    """PoE2自动诊断系统"""
    
    def __init__(self):
        self.diagnosis_report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'test_results': {},
            'recommendations': []
        }
    
    def collect_system_info(self):
        """收集系统信息"""
        print("收集系统信息...")
        
        # Python版本
        self.diagnosis_report['system_info']['python_version'] = sys.version
        
        # 操作系统
        self.diagnosis_report['system_info']['os'] = os.name
        self.diagnosis_report['system_info']['platform'] = sys.platform
        
        # 环境变量
        relevant_env_vars = [key for key in os.environ.keys() if 'POE2' in key]
        self.diagnosis_report['system_info']['env_vars'] = {
            key: os.environ[key] for key in relevant_env_vars
        }
        
        # 依赖包版本
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            self.diagnosis_report['system_info']['packages'] = result.stdout
        except:
            self.diagnosis_report['system_info']['packages'] = "无法获取包信息"
    
    def run_system_tests(self):
        """运行系统测试"""
        print("运行系统测试...")
        
        tests = [
            ('模块导入测试', self._test_module_import),
            ('网络连接测试', self._test_network_connectivity),
            ('数据源测试', self._test_data_sources),
            ('计算引擎测试', self._test_calculation_engine),
            ('性能测试', self._test_performance)
        ]
        
        for test_name, test_func in tests:
            print(f"  执行: {test_name}")
            try:
                result = test_func()
                self.diagnosis_report['test_results'][test_name] = {
                    'status': 'passed' if result else 'failed',
                    'details': result
                }
            except Exception as e:
                self.diagnosis_report['test_results'][test_name] = {
                    'status': 'error',
                    'error': str(e)
                }
    
    def _test_module_import(self):
        """测试模块导入"""
        try:
            from poe2_real_data_sources import (
                PoE2RealDataOrchestrator,
                PoE2ScoutAPI,
                PoE2DBScraper,
                PoE2NinjaScraper
            )
            return "所有模块导入成功"
        except ImportError as e:
            return f"模块导入失败: {e}"
    
    def _test_network_connectivity(self):
        """测试网络连接"""
        import requests
        
        urls = [
            "https://poe2scout.com",
            "https://poe2db.tw",
            "https://poe.ninja"
        ]
        
        results = {}
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                results[url] = f"状态码: {response.status_code}"
            except Exception as e:
                results[url] = f"连接失败: {e}"
        
        return results
    
    def _test_data_sources(self):
        """测试数据源"""
        from poe2_real_data_sources import PoE2RealDataOrchestrator
        
        try:
            orchestrator = PoE2RealDataOrchestrator()
            
            # 测试各个数据源
            scout_data = orchestrator.poe2_scout.get_market_data()
            db_data = orchestrator.poe2db.get_skill_data()
            ninja_data = orchestrator.poe2_ninja.get_popular_builds()
            
            return {
                'scout': f"状态: {scout_data.get('status', 'unknown')}",
                'poe2db': f"技能数量: {len(db_data.get('skills', []))}",
                'ninja': f"构筑数量: {len(ninja_data) if isinstance(ninja_data, list) else 0}"
            }
        except Exception as e:
            return f"数据源测试失败: {e}"
    
    def _test_calculation_engine(self):
        """测试计算引擎"""
        from poe2_real_data_sources import PoE2RealDataOrchestrator
        
        try:
            orchestrator = PoE2RealDataOrchestrator()
            test_config = {
                'main_skill': 'Lightning Arrow',
                'weapon': 'Lightning Bow',
                'level': 85
            }
            
            result = orchestrator.calculator.calculate_poe2_build(test_config)
            dps = result['dps']['total_dps']
            ehp = result['survivability']['total_ehp']
            
            return f"DPS: {dps:,}, EHP: {ehp:,}"
        except Exception as e:
            return f"计算引擎测试失败: {e}"
    
    def _test_performance(self):
        """性能测试"""
        import time
        from poe2_real_data_sources import PoE2RealDataOrchestrator
        
        try:
            orchestrator = PoE2RealDataOrchestrator()
            test_request = {
                'game': 'poe2',
                'preferences': {'class': 'Ranger', 'style': 'bow'}
            }
            
            start_time = time.time()
            result = orchestrator.create_poe2_build_recommendation(test_request)
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result and 'recommendations' in result
            
            return {
                'execution_time': f"{execution_time:.2f}s",
                'success': success,
                'recommendations': len(result.get('recommendations', [])) if success else 0
            }
        except Exception as e:
            return f"性能测试失败: {e}"
    
    def generate_recommendations(self):
        """生成修复建议"""
        print("生成修复建议...")
        
        # 基于测试结果生成建议
        for test_name, test_result in self.diagnosis_report['test_results'].items():
            if test_result['status'] == 'failed':
                if '模块导入' in test_name:
                    self.diagnosis_report['recommendations'].append(
                        "模块导入失败 - 请运行: pip install -r requirements.txt"
                    )
                elif '网络连接' in test_name:
                    self.diagnosis_report['recommendations'].append(
                        "网络连接问题 - 请检查网络连接和防火墙设置"
                    )
                elif '数据源' in test_name:
                    self.diagnosis_report['recommendations'].append(
                        "数据源问题 - 请检查外部API服务状态"
                    )
                elif '计算引擎' in test_name:
                    self.diagnosis_report['recommendations'].append(
                        "计算引擎问题 - 请检查数据输入格式"
                    )
                elif '性能' in test_name:
                    self.diagnosis_report['recommendations'].append(
                        "性能问题 - 请优化网络连接或增加系统资源"
                    )
            elif test_result['status'] == 'error':
                self.diagnosis_report['recommendations'].append(
                    f"{test_name} - 出现异常，请查看详细错误信息"
                )
    
    def save_report(self, filename: str = None):
        """保存诊断报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"poe2_diagnosis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.diagnosis_report, f, indent=2, ensure_ascii=False)
        
        print(f"诊断报告已保存: {filename}")
        return filename
    
    def print_summary(self):
        """打印诊断摘要"""
        print("\n" + "="*50)
        print("PoE2 系统诊断报告")
        print("="*50)
        
        # 测试结果汇总
        total_tests = len(self.diagnosis_report['test_results'])
        passed_tests = sum(1 for r in self.diagnosis_report['test_results'].values() if r['status'] == 'passed')
        failed_tests = sum(1 for r in self.diagnosis_report['test_results'].values() if r['status'] == 'failed')
        error_tests = sum(1 for r in self.diagnosis_report['test_results'].values() if r['status'] == 'error')
        
        print(f"测试总数: {total_tests}")
        print(f"通过: {passed_tests}, 失败: {failed_tests}, 错误: {error_tests}")
        
        # 系统状态
        if failed_tests == 0 and error_tests == 0:
            print("✅ 系统状态: 正常")
        elif failed_tests > 0 or error_tests > 0:
            print("❌ 系统状态: 存在问题")
        
        # 修复建议
        if self.diagnosis_report['recommendations']:
            print("\n修复建议:")
            for i, rec in enumerate(self.diagnosis_report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        print("="*50)
    
    def run_full_diagnosis(self):
        """运行完整诊断"""
        print("开始PoE2系统诊断...")
        
        self.collect_system_info()
        self.run_system_tests()
        self.generate_recommendations()
        
        self.print_summary()
        report_file = self.save_report()
        
        return report_file

# 使用示例
if __name__ == "__main__":
    diagnoser = PoE2AutoDiagnosis()
    diagnoser.run_full_diagnosis()
```

## 📞 获取帮助

### 日志收集

```bash
# 收集完整日志
python auto_diagnosis.py > diagnosis.log 2>&1

# 收集系统信息
python -c "import sys, os; print(f'Python: {sys.version}'); print(f'OS: {os.name}')" > system_info.txt

# 收集网络信息
ping -c 3 poe2scout.com >> network_info.txt
ping -c 3 poe2db.tw >> network_info.txt
ping -c 3 poe.ninja >> network_info.txt
```

### 问题报告模板

```markdown
## PoE2构筑生成器问题报告

### 环境信息
- 操作系统: [Windows 10/Linux/Mac]
- Python版本: [3.8/3.9/3.10/3.11]
- 项目版本: [2.0.0]

### 问题描述
[详细描述遇到的问题]

### 重现步骤
1. 
2. 
3. 

### 期望结果
[描述期望的行为]

### 实际结果
[描述实际发生的情况]

### 错误信息
```
[粘贴错误信息和堆栈跟踪]
```

### 诊断信息
[粘贴auto_diagnosis.py的输出]

### 额外信息
[任何其他相关信息]
```

### 联系方式

1. **GitHub Issues**: https://github.com/zhakil/poe2build/issues
2. **诊断报告**: 运行 `python auto_diagnosis.py` 并附上报告
3. **社区讨论**: 在项目讨论区寻求帮助

---

**总结**: 这个故障排除指南提供了全面的问题诊断和解决方案。通过自动诊断工具和详细的调试指南，可以快速定位和解决大部分常见问题。