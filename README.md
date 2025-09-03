# PoE2 四大数据源集成智能构筑系统

> 基于真实PoE2数据源的智能构筑推荐系统 - 集成四大核心数据源、RAG增强AI和PoB2高度集成

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PoE2 Specific](https://img.shields.io/badge/PoE2%20Specific-100%25-orange)](docs/README.md)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/zhakil/poe2build)

## 🎯 **四大核心数据源架构 (Foundation)**

**本项目完全基于以下四个真实、可用的PoE2数据源构建:**

### 1. **PoE2Scout API** (https://poe2scout.com)
- **作用**: 实时市场定价数据和物品价格分析
- **集成状态**: ✅ 完成
- **模块**: `src/poe2build/data_sources/poe2scout/`
- **数据**: ItemPrice, CurrencyExchange, 构筑成本估算

### 2. **PoE Ninja构筑分析** (https://poe.ninja/poe2/builds)
- **作用**: Meta趋势分析和流行构筑数据爬取
- **集成状态**: ✅ 完成
- **模块**: `src/poe2build/data_sources/ninja/`
- **数据**: PopularBuild, SkillUsageStats, AscendancyTrend

### 3. **Path of Building 2数据** (GitHub/本地)
- **作用**: 官方游戏数据和精确DPS/EHP计算引擎
- **集成状态**: ✅ 完成 (支持GitHub和本地双模式)
- **模块**: `src/poe2build/data_sources/pob2/`
- **数据**: SkillGem, PassiveNode, BaseItem, 计算引擎

### 4. **PoE2DB游戏数据库** (https://poe2db.tw/cn/)
- **作用**: 完整游戏数据库和物品详情
- **集成状态**: ✅ 完成
- **模块**: `src/poe2build/data_sources/poe2db/`
- **数据**: 装备属性、技能详情、升华信息、中文本地化

## 📋 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11 (推荐), Linux/macOS (支持)
- **内存**: 至少4GB RAM (推荐8GB+)
- **存储**: 至少2GB可用空间
- **网络**: 稳定互联网连接 (访问四大数据源)
- **可选**: Path of Building Community (PoB2) - 用于本地计算增强

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
git clone https://github.com/zhakil/poe2build.git
cd poe2build

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用

```bash
# 🚀 启动完整功能GUI (强烈推荐)
python run_complete_gui.py

# 或者直接运行GUI
python gui_apps/poe2_complete_gui.py

# 健康检查所有数据源
python -c "
from core_ai_engine.src.poe2build.data_sources import health_check_all_sources
print(health_check_all_sources())
"

# RAG训练CLI模式
python -c "
from core_ai_engine.src.poe2build.rag.four_sources_integration import train_rag_with_four_sources
import asyncio
asyncio.run(train_rag_with_four_sources())
"
```

## 📁 完整项目结构

```
poe2build/                              # 项目根目录
├── 🕷️ 动态数据爬虫系统 (完整真实数据集成)
│   ├── dynamic_data_crawlers.py        # 🕷️ 四大数据源动态爬虫管理器 (NEW)
│   ├── pob2_github_downloader.py      # 📥 PoB2 GitHub数据文件下载器 (NEW) 
│   ├── poe2_realistic_data_system.py  # 💡 基于真实数据的推荐系统 (NEW)
│
├── gui_apps/                           # 🖥️ GUI应用程序
│   ├── poe2_complete_gui.py            # 🚀 完整功能GUI (强烈推荐)
│   ├── poe2_integrated_gui.py          # 主集成GUI应用
│   ├── poe2_professional_gui.py        # 专业版GUI
│   ├── poe2_ultimate_gui.py            # 旗舰版GUI
│   ├── gui_with_console.py             # 简化版GUI+控制台
│   ├── demo_gui_backend_integration.py # GUI后端集成演示
│   ├── demo_new_welcome_page.py        # 新欢迎页面演示
│   ├── run_gui.py                      # GUI启动器
│   └── setup_gui.py                    # GUI安装设置
│
├── core_ai_engine/                     # 🧠 核心AI引擎
│   ├── poe2_ai_orchestrator.py         # AI协调器 (CLI入口)
│   └── src/poe2build/                  # 核心源代码模块
│       ├── __init__.py
│       ├── data_sources/               # 🎯 四大核心数据源 (完全集成)
│       │   ├── __init__.py            # 统一导入接口 + 动态爬虫集成
│       │   ├── poe2scout/             # PoE2Scout市场API
│       │   │   ├── __init__.py
│       │   │   └── api_client.py     # ✅ 完成
│       │   ├── ninja/                 # PoE Ninja爬虫
│       │   │   ├── __init__.py
│       │   │   └── scraper.py        # ✅ 完成
│       │   ├── pob2/                  # Path of Building 2
│       │   │   ├── __init__.py
│       │   │   └── data_extractor.py # ✅ 完成 (三层缓存策略)
│       │   └── poe2db/                # PoE2DB数据库
│       │       ├── __init__.py
│       │       └── api_client.py     # ✅ 完成
│       │
│       ├── rag/                       # 🧠 RAG AI系统
│       │   ├── __init__.py
│       │   ├── four_sources_integration.py # 四源集成训练器
│       │   ├── data_collector.py      # 数据收集器
│       │   ├── vectorizer.py          # 向量化引擎
│       │   ├── index_builder.py       # 索引构建器
│       │   ├── similarity_engine.py   # 相似性引擎
│       │   ├── ai_engine.py           # AI推荐引擎
│       │   ├── knowledge_base.py      # 知识库管理
│       │   └── recommendation.py      # 推荐算法
│       │
│       └── gui/                       # GUI组件模块
│           ├── __init__.py
│           └── [GUI组件文件]
│
├── dependencies/                       # 📦 依赖管理
│   ├── requirements.txt                # 基础项目依赖
│   ├── requirements-gui.txt            # GUI专用依赖
│   ├── requirements-windows.txt        # Windows集成依赖
│   └── pyproject.toml                  # 项目配置
│
├── tests_and_validation/               # 🧪 测试和验证
│   ├── tests/                          # 标准测试套件
│   ├── test/                           # 额外测试目录
│   ├── examples/                       # 示例代码
│   │   ├── demo_models.py
│   │   └── test_models.py
│   ├── test_*.py                       # 独立测试文件
│   ├── run_tests.py                    # 测试运行器
│   ├── run_quick_tests.py              # 快速测试
│   └── pytest.ini                     # pytest配置
│
├── docs_and_guides/                    # 📚 文档和指导
│   ├── docs/                           # 📂 详细文档库
│   │   ├── 01_real_architecture.md     # 架构文档
│   │   ├── 02_poe2_data_sources.md     # 数据源文档
│   │   ├── 03_poe2_calculator.md       # 计算器文档
│   │   ├── 04_api_usage.md             # API使用指导
│   │   ├── 05_developer_guide.md       # 开发者指南
│   │   ├── 06_deployment.md            # 部署指南
│   │   ├── 07_troubleshooting.md       # 故障排除
│   │   ├── 08_project_structure.md     # 项目结构
│   │   ├── 09_development_workflow.md  # 开发流程
│   │   ├── 10_testing_strategy.md      # 测试策略
│   │   ├── 11_pob2_integration.md      # PoB2集成
│   │   ├── 12_rag_ai_training.md       # RAG AI训练
│   │   └── README.md                   # 文档索引
│   │
│   ├── prompts/                        # 📝 构建指导文件
│   │   ├── current_status.md           # 当前项目状态
│   │   ├── build_gui_integration.txt   # GUI集成构建指导
│   │   ├── rag_training_guide.txt      # RAG训练指导
│   │   └── data_sources_setup.txt      # 数据源设置指导
│   │
│   └── 项目状态文档/
│       ├── GUI_*.md                    # GUI相关文档
│       ├── WINDOWS_INTEGRATION.md      # Windows集成
│       ├── PROJECT_FINAL_STATUS.md     # 项目最终状态
│       ├── PHASE5_COMPLETION_REPORT.md # 阶段5完成报告
│       ├── TESTING_GUIDE.md            # 测试指南
│       └── USAGE.md                    # 使用指南
│
├── scripts_and_tools/                  # 🔧 脚本和工具
│   ├── scripts/                        # 构建和部署脚本
│   │   ├── build_gui.ps1              # GUI构建脚本
│   │   ├── create_installer.ps1        # 安装程序创建
│   │   └── test_windows_integration.ps1 # Windows集成测试
│   │
│   └── 资源文件/
│       ├── resources/                  # 静态资源
│       └── .github/                    # GitHub配置
│
├── data_storage/                       # 💾 数据存储 (完全集成)
│   ├── data/                           # 核心数据目录
│   │   ├── rag_cache/                  # RAG缓存数据
│   │   ├── pob2_cache/                 # PoB2缓存数据 (GitHub下载文件)
│   │   ├── market_cache/               # PoE2Scout市场数据缓存 (NEW)
│   │   ├── ninja_cache/                # Ninja Meta构筑缓存 (NEW)
│   │   └── poe2db_cache/               # PoE2DB技能数据缓存 (NEW)
│   │   └── four_sources_output/        # 四源集成输出
│   │
│   ├── logs/                           # 应用日志
│   ├── temp/                           # 临时文件
│   ├── test_reports/                   # 测试报告
│   └── test_knowledge/                 # 测试知识库
│
├── config_files/                       # ⚙️ 配置文件
│   ├── .env.example                    # 环境变量示例
│   ├── .gitignore                      # Git忽略规则
│   ├── .pre-commit-config.yaml         # 预提交钩子
│   └── .vscode/                        # VS Code配置
│
├── reference_docs/                     # 📄 参考文档
│   ├── 《流放之路2》生态系统程序化访问开发者指南.docx
│   └── How to query POE2 API.docx
│
├── README.md                           # 📖 主项目文档
├── CLAUDE.md                           # 🤖 Claude开发指导
└── run_complete_gui.py                 # 🚀 完整GUI启动脚本
```

## 🛠️ 核心功能模块

### 1. 四大数据源集成管理 (完全真实数据)
- **动态数据爬虫**: 实时获取PoE2Scout、PoE Ninja、PoE2DB最新数据  
- **GitHub数据同步**: 自动下载PoB2最新游戏数据文件
- **三层缓存策略**: 缓存 → GitHub → 本地，确保数据可用性
- **实时健康监控**: 自动检测四大数据源状态和数据获取结果
- **智能回退机制**: 单一数据源故障不影响系统运行

### 2. RAG AI训练系统
- **四源知识库**: 基于四大数据源构建统一知识库
- **向量化引擎**: 构筑数据语义向量化和相似性检索
- **AI推荐算法**: 智能分析用户需求生成构筑推荐
- **持续学习**: 支持增量训练和知识库更新

### 3. PoB2高度集成
- **双模式支持**: GitHub在线数据 + 本地安装数据
- **精确计算**: 利用PoB2引擎进行DPS/EHP精确计算
- **构筑导入导出**: 生成标准PoB2导入码
- **实时验证**: 自动验证生成构筑的有效性

### 4. 专业GUI界面
- **PoE2风格主题**: 仿游戏界面设计风格
- **F12开发者控制台**: 类似浏览器的调试功能
- **实时状态监控**: 四大数据源健康状态实时显示
- **拖拽式操作**: 直观的构筑配置和修改

## 💻 使用示例

### 动态数据爬虫系统使用
```python
from dynamic_data_crawlers import DynamicDataManager
from pob2_github_downloader import PoB2GitHubDownloader

# 动态获取四大数据源真实数据
manager = DynamicDataManager()
data = manager.update_all_data()

print(f"✅ 实时数据获取完成:")
print(f"  市场物品: {len(data['market_items'])} 个")
print(f"  Meta构筑: {len(data['meta_builds'])} 个") 
print(f"  技能数据: {len(data['skill_data'])} 个")

# 下载最新PoB2数据
downloader = PoB2GitHubDownloader()
data_results = downloader.download_data_directory()
tree_results = downloader.download_tree_data()
print(f"  PoB2文件: {len([r for r in data_results.values() if r])} 个数据文件")
```

### 四大数据源健康检查 (完全集成版本)
```python
from src.poe2build.data_sources import health_check_all_sources, get_all_four_sources

# 检查所有数据源状态 (使用动态爬虫系统)
health = health_check_all_sources()
healthy_sources = [name for name, info in health.items() 
                  if info.get('available', False) or 
                     info.get('status', {}).get('status') == 'healthy']
print(f"健康的数据源: {len(healthy_sources)}/4 - {healthy_sources}")

# 获取四大数据源实时数据
all_data = get_all_four_sources(limit=100)
print(f"PoE2Scout数据: {len(all_data['poe2scout_data'])} 条")
print(f"PoB2技能宝石: {len(all_data['pob2_data'].get('skill_gems', []))} 个")
```

### RAG AI训练和推荐
```python
from src.poe2build.rag.four_sources_integration import FourSourcesRAGTrainer
import asyncio

async def train_and_recommend():
    # 创建四大数据源RAG训练器
    trainer = FourSourcesRAGTrainer(enable_github_pob2=True)
    
    # 收集四大数据源数据
    data = await trainer.collect_all_four_sources("Standard")
    
    # 训练RAG AI
    training_result = await trainer.train_rag_ai(data)
    
    print(f"训练完成: {training_result['knowledge_entries']} 个知识条目")
    return training_result

# 运行训练
asyncio.run(train_and_recommend())
```

### PoB2集成计算示例
```python
from src.poe2build.data_sources.pob2.data_extractor import get_pob2_extractor

# 获取PoB2数据提取器
extractor = get_pob2_extractor()

if extractor.is_available():
    # 获取所有技能宝石
    skills = extractor.get_skill_gems()
    print(f"可用技能数量: {len(skills)}")
    
    # 查找特定技能
    lightning_arrow = extractor.get_gem_by_name("Lightning Arrow")
    if lightning_arrow:
        print(f"技能: {lightning_arrow.name}")
        print(f"类型: {lightning_arrow.gem_type}")
        print(f"标签: {', '.join(lightning_arrow.tags)}")
```

## 🔧 开发和调试

### 运行GUI应用
```bash
# 🎯 启动完整功能GUI (推荐方式)
python run_complete_gui.py

# 🔧 功能特点:
# • 四大数据源实时监控
# • RAG AI智能训练
# • PoB2高度集成推荐
# • F12开发者控制台 (按F12打开)
# • 实时DPS/EHP精确计算
# • 构筑导入导出功能

# 💡 快捷键:
# • F12 - 开发者控制台
# • Ctrl+R - 刷新数据源状态  
# • Ctrl+T - 开始RAG训练
# • Ctrl+G - 生成智能推荐
```

### 测试数据源连接
```bash
# 测试所有四大数据源
python -c "
from src.poe2build.data_sources import health_check_all_sources
import json
health = health_check_all_sources()
print(json.dumps(health, indent=2, default=str))
"

# 测试特定数据源
python -c "
from src.poe2build.data_sources.ninja.scraper import get_ninja_scraper
scraper = get_ninja_scraper()
builds = scraper.get_popular_builds('Standard', limit=5)
print(f'获取到 {len(builds)} 个流行构筑')
"
```

### 性能监控
```bash
# 监控RAG训练性能
python -c "
import time
from src.poe2build.rag.four_sources_integration import FourSourcesRAGTrainer
trainer = FourSourcesRAGTrainer()
start = time.time()
# 这里执行训练代码
print(f'训练耗时: {time.time() - start:.2f}秒')
"
```

## 📋 构建检查清单

在部署或分发之前，请确认以下项目：

- [ ] **四大数据源连接测试通过**
- [ ] **RAG AI训练可以正常完成**
- [ ] **PoB2集成功能正常工作**
- [ ] **GUI界面可以正常启动**
- [ ] **F12开发者控制台功能正常**
- [ ] **构筑导入导出功能测试通过**
- [ ] **错误处理机制测试完成**
- [ ] **缓存机制正常工作**

## 🐛 故障排除

### 数据源连接问题
```bash
# 检查网络连接
ping poe2scout.com
ping poe.ninja
ping poe2db.tw

# 检查Python网络权限
python -c "import requests; print(requests.get('https://poe2scout.com', timeout=5).status_code)"
```

### PoB2集成问题
```bash
# 检查PoB2路径检测
python -c "
from src.poe2build.data_sources.pob2.data_extractor import get_pob2_extractor
extractor = get_pob2_extractor()
print('PoB2可用:', extractor.is_available())
print('安装信息:', extractor.get_installation_info())
"
```

### RAG训练内存问题
```bash
# 监控内存使用
python -c "
import psutil
print(f'可用内存: {psutil.virtual_memory().available // 1024**3} GB')
print(f'内存使用率: {psutil.virtual_memory().percent}%')
"
```

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🚨 免责声明

本工具仅供《流放之路2》玩家学习和研究使用。请遵守游戏服务条款，理论构筑仅供参考。工具开发者不对使用本工具产生的任何后果承担责任。

---

**项目状态**: ✅ 四大数据源集成完成 | 🧠 RAG AI系统完成 | 🖥️ GUI界面完成  
**最后更新**: 2025-09-02  
**版本**: 2.1.0 - 四大数据源集成版