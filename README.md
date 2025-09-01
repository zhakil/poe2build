# PoE2 智能构筑生成器

> 基于真实PoE2数据源的智能构筑推荐系统 - 集成PoB2计算引擎和RAG增强AI

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PoE2 Specific](https://img.shields.io/badge/PoE2%20Specific-100%25-orange)](docs/README.md)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/zhakil/poe2build)

## 项目概览

**PoE2智能构筑生成器** 是专为《流放之路2》设计的智能构筑推荐系统。集成**真实可用的PoE2数据源**，基于Path of Building Community (PoB2)计算引擎，使用RAG增强AI技术生成专业构筑方案。

### 核心特性
- **🤖 AI驱动推荐** - RAG增强的智能构筑生成
- **⚡ PoB2集成** - 基于Path of Building Community的精确计算
- **📊 真实数据源** - 集成poe2scout.com、poe2db.tw、poe.ninja
- **🖥️ 多模式支持** - CLI命令行 + Windows GUI应用
- **🛡️ PoE2专用** - 支持80%抗性上限、能量护盾等PoE2机制

### 数据源集成
- **[PoE2 Scout](https://poe2scout.com)** - PoE2市场和构筑数据
- **[PoE2DB](https://poe2db.tw)** - PoE2游戏数据库  
- **[poe.ninja PoE2专区](https://poe.ninja/poe2/builds)** - PoE2构筑分析

## 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11 (GUI模式), Linux/macOS (CLI模式)
- **内存**: 至少4GB RAM (推荐8GB+)
- **存储**: 至少2GB可用空间
- **网络**: 稳定互联网连接 (访问PoE2数据源)
- **可选**: Path of Building Community (PoB2) - 用于本地计算

## 快速开始

### 1. 项目设置

```bash
# 克隆项目
git clone https://github.com/zhakil/poe2build.git
cd poe2build

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件 (可选)
# 配置PoE2数据源URL、缓存设置等
```

### 3. 运行程序

```bash
# CLI模式 - 快速体验
python poe2_ai_orchestrator.py

# 交互式推荐
python poe2_ai_orchestrator.py --interactive

# GUI模式 (Windows)
python gui_main.py  # 需要完成GUI开发阶段
```

## 完整构建指南

**重要提示**: 必须严格按照以下顺序构建，每个阶段对应 `prompts/` 目录中的具体指导文件。

### 第一阶段: 项目基础架构 (阶段1-5)

#### 阶段1: 基础配置设置
```bash
# 指导文件: prompts/01_foundation_setup.txt
# 实现目标: 项目基础配置和依赖管理

# 创建文件:
# ├── pyproject.toml          # Python项目配置
# ├── requirements.txt        # 核心依赖
# ├── .env.example           # 环境变量模板  
# ├── .gitignore            # Git忽略规则
# └── .pre-commit-config.yaml # Git钩子配置

# 执行命令:
python -m pip install -e .
cp .env.example .env
```

#### 阶段2: 数据模型定义
```bash  
# 指导文件: prompts/02_data_models.txt
# 实现目标: PoE2专用数据模型

# 创建目录结构:
src/poe2build/models/
├── __init__.py
├── build.py              # PoE2Build, PoE2BuildStats模型
├── characters.py         # PoE2CharacterClass, PoE2Ascendancy
├── items.py              # PoE2Item, 装备槽位定义
├── market.py             # 市场数据和价格模型
└── skills.py             # 技能宝石和辅助宝石模型

# 验证命令:
python -c "from src.poe2build.models import *; print('Models loaded successfully')"
```

#### 阶段3: 接口定义
```bash
# 指导文件: prompts/03_interfaces.txt  
# 实现目标: 抽象接口和服务契约

# 创建接口:
# ├── IDataProvider          # 数据源提供者接口
# ├── ICalculationEngine     # 计算引擎接口
# ├── IAIRecommender        # AI推荐器接口
# └── IResilientService     # 弹性服务接口

# 实现位置: src/poe2build/interfaces/
```

#### 阶段4: API集成
```bash
# 指导文件: prompts/04_api_integration.txt
# 实现目标: 外部数据源集成

# 实现数据源:
src/poe2build/data_sources/
├── __init__.py
├── poe2_scout_api.py     # PoE2 Scout集成 (poe2scout.com)
├── poe2db_scraper.py     # PoE2DB集成 (poe2db.tw)
├── poe_ninja_api.py      # poe.ninja PoE2专区集成
└── base_data_source.py   # 数据源基类

# 测试命令:
python -c "
from src.poe2build.data_sources import *
print('Data sources loaded successfully')
"
```

#### 阶段5: PoB2集成
```bash
# 指导文件: prompts/05_pob2_integration.txt
# 实现目标: Path of Building Community集成

# 实现PoB2接口:
src/poe2build/pob2/
├── __init__.py
├── local_client.py       # PoB2本地客户端
├── build_importer.py     # PoB2构筑导入器
├── calculation_engine.py # PoB2计算引擎包装
└── build_generator.py    # PoB2构筑生成器

# 验证PoB2检测:
python -c "
from src.poe2build.pob2 import PoB2LocalClient
client = PoB2LocalClient()
print(f'PoB2 detected: {client.is_available()}')
"
```

### 第二阶段: 工具和弹性系统 (阶段24-25)

#### 阶段24: 弹性系统架构  
```bash
# 指导文件: prompts/24_resilience_system.txt
# 实现目标: 断路器、重试、缓存等弹性模式

# 实现弹性组件:
src/poe2build/resilience/
├── __init__.py
├── circuit_breaker.py    # 断路器模式
├── rate_limiter.py       # 速率限制器
├── retry_handler.py      # 重试处理器  
├── cache_manager.py      # 缓存管理器
└── fallback_provider.py  # 降级服务提供者

# 测试弹性功能:
python -c "
from src.poe2build.resilience import ResilientService
print('Resilience system loaded')
"
```

#### 阶段25: 工具函数和辅助模块
```bash
# 指导文件: prompts/25_utils_helpers.txt
# 实现目标: PoE2常量、验证工具、文本处理

# 实现工具模块:
src/poe2build/utils/
├── __init__.py
├── poe2_constants.py     # PoE2游戏常量和计算
├── data_validation.py    # 数据验证工具
├── text_processing.py    # PoE2文本处理  
├── math_helpers.py       # 数学计算辅助
├── file_helpers.py       # 文件操作辅助
├── network_helpers.py    # 网络请求辅助
├── logging_config.py     # 日志配置
└── performance_tools.py  # 性能分析工具

# 验证工具函数:
python -c "
from src.poe2build.utils.poe2_constants import PoE2Constants
print(f'Max resistance: {PoE2Constants.MAX_RESISTANCE}%')
"
```

### 第三阶段: RAG和AI系统 (阶段6-11)

#### 阶段6: PoB2计算器
```bash
# 指导文件: prompts/06_pob2_calculator.txt
# 实现目标: PoB2计算引擎集成

# 扩展PoB2功能:
# ├── DPS计算和统计分析
# ├── 构筑验证和优化
# └── 计算结果缓存

# 前置依赖: 阶段5 (PoB2集成)
```

#### 阶段7: RAG数据收集
```bash
# 指导文件: prompts/07_rag_collector.txt  
# 实现目标: 构筑数据收集和预处理

# 实现RAG数据收集:
src/poe2build/rag/
├── __init__.py
├── data_collector.py     # 数据收集器
├── build_scraper.py      # 构筑数据爬取
└── data_preprocessor.py  # 数据预处理

# 前置依赖: 阶段4 (API集成), 阶段24 (弹性系统)
```

#### 阶段8: RAG向量化
```bash
# 指导文件: prompts/08_rag_vectorizer.txt
# 实现目标: 构筑数据向量化和索引

# 扩展RAG系统:
src/poe2build/rag/
├── vectorizer.py         # 向量化引擎
├── index_builder.py      # 索引构建器
└── similarity_engine.py  # 相似性搜索

# 前置依赖: 阶段7 (RAG数据收集)
# 新增依赖: sentence-transformers, faiss-cpu
```

#### 阶段9: RAG AI引擎  
```bash
# 指导文件: prompts/09_rag_ai_engine.txt
# 实现目标: AI推荐引擎和知识增强

# 实现AI引擎:
src/poe2build/rag/
├── ai_engine.py          # AI推荐引擎
├── knowledge_base.py     # 知识库管理
└── recommendation.py     # 推荐算法

# 前置依赖: 阶段8 (RAG向量化)
```

#### 阶段10: AI协调器
```bash
# 指导文件: prompts/10_ai_orchestrator.txt
# 实现目标: 核心AI协调器

# 实现协调器:
src/poe2build/core/
├── __init__.py
├── ai_orchestrator.py    # 主协调器 (PoE2AIOrchestrator)
├── build_generator.py    # 构筑生成器
└── recommender.py        # 推荐引擎

# 前置依赖: 阶段1-9 (所有基础组件)
```

#### 阶段11: 主程序入口
```bash
# 指导文件: prompts/11_main_entry.txt
# 实现目标: CLI主程序和用户接口

# 创建主程序:
# ├── poe2_ai_orchestrator.py    # 主程序入口
# ├── CLI参数解析和交互模式
# └── 使用示例和帮助文档

# 前置依赖: 阶段10 (AI协调器)
# 测试运行:
python poe2_ai_orchestrator.py --help
```

### 第四阶段: 测试和质量保证 (阶段12)

#### 阶段12: 测试套件
```bash
# 指导文件: prompts/12_testing_suite.txt
# 实现目标: 完整测试框架

# 实现测试套件:
tests/
├── unit/                 # 单元测试 (70%)
├── integration/          # 集成测试 (20%)  
├── performance/          # 性能测试 (10%)
├── e2e/                  # 端到端测试
├── fixtures/             # 测试数据
└── conftest.py          # pytest配置

# 运行测试:
python -m pytest tests/ -v --cov=src/poe2build
```

### 第五阶段: 扩展功能 (阶段13-23) - 可选

#### Web架构 (阶段13-17)
```bash
# 指导文件: 
# ├── prompts/13_web_architecture.txt    # Web架构设计
# ├── prompts/14_fastapi_server.txt      # FastAPI服务器
# ├── prompts/15_frontend_ui.txt         # 前端UI界面
# ├── prompts/16_integration_testing.txt # 集成测试
# └── prompts/17_deployment_web.txt      # Web部署

# 适用场景: 需要Web界面的部署环境
# 前置依赖: 阶段1-12 (核心功能完成)
```

#### Windows GUI (阶段18-23)
```bash
# 指导文件:
# ├── prompts/18_windows_gui_architecture.txt  # GUI架构
# ├── prompts/19_gui_components.txt            # GUI组件
# ├── prompts/20_main_window.txt               # 主窗口
# ├── prompts/21_data_integration.txt          # 数据集成
# ├── prompts/22_windows_features.txt          # Windows特性
# └── prompts/23_packaging_distribution.txt    # 打包分发

# 适用场景: Windows桌面应用需求
# 前置依赖: 阶段1-12 (核心功能完成)
# 新增依赖: PyQt6, pyinstaller
```

### 构建验证检查点

每完成一个阶段，请运行以下验证命令：

```bash
# 基础验证 (阶段1-5完成后)
python -c "
import src.poe2build
from src.poe2build.models import *
from src.poe2build.data_sources import *
print('✅ 基础架构验证通过')
"

# 核心功能验证 (阶段6-11完成后)  
python poe2_ai_orchestrator.py --test-mode
python -c "
from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator
orchestrator = PoE2AIOrchestrator()
print('✅ 核心功能验证通过')
"

# 完整系统验证 (阶段12完成后)
python -m pytest tests/ --tb=short
python poe2_ai_orchestrator.py --interactive
```

## 项目结构

```
poe2build/
├── poe2_ai_orchestrator.py         # 主程序入口
├── pyproject.toml                   # Python项目配置
├── requirements.txt                 # 核心依赖
├── .env.example                     # 环境变量模板
├── CLAUDE.md                        # Claude Code指导文档
│
├── src/poe2build/                   # 源代码包
│   ├── __init__.py
│   ├── core/                        # 核心功能模块
│   │   ├── ai_orchestrator.py      # AI协调器
│   │   ├── build_generator.py      # 构筑生成器
│   │   └── recommender.py          # 推荐引擎
│   ├── models/                      # 数据模型
│   │   ├── build.py                # 构筑模型
│   │   ├── characters.py           # 角色模型
│   │   ├── items.py                # 物品模型
│   │   ├── market.py               # 市场模型
│   │   └── skills.py               # 技能模型
│   ├── data_sources/               # 数据源集成
│   ├── pob2/                       # PoB2集成
│   ├── rag/                        # RAG系统
│   ├── resilience/                 # 弹性架构
│   ├── utils/                      # 工具函数
│   └── config/                     # 配置管理
│
├── tests/                           # 测试套件
│   ├── unit/                       # 单元测试 (70%)
│   ├── integration/                # 集成测试 (20%)
│   ├── performance/                # 性能测试 (10%)
│   ├── e2e/                        # 端到端测试
│   └── fixtures/                   # 测试数据
│
├── prompts/                         # 构建指导文件
│   ├── 01_foundation_setup.txt     # 基础设置
│   ├── 02_data_models.txt          # 数据模型
│   ├── ...                         # 其他阶段指导
│   └── 23_packaging_distribution.txt # 打包分发
│
├── docs/                           # 项目文档
├── scripts/                        # 工具脚本
└── data/                           # 数据文件
```

## 使用示例

### CLI基础用法
```bash
# 生成弓手构筑推荐
python poe2_ai_orchestrator.py --class Ranger --style bow --budget 15divine

# 交互式模式
python poe2_ai_orchestrator.py --interactive

# 批量处理
python poe2_ai_orchestrator.py --batch builds_input.json --output results/
```

### Python API使用
```python
from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator

# 初始化AI协调器
orchestrator = PoE2AIOrchestrator()

# 构筑推荐请求
build_request = {
    'preferences': {
        'class': 'Ranger',
        'style': 'bow', 
        'goal': 'endgame_content',
        'budget': {'amount': 15, 'currency': 'divine'}
    }
}

# 生成推荐
recommendations = orchestrator.generate_build_recommendation(build_request)

# 显示结果
for build in recommendations['recommendations']:
    print(f"构筑: {build['build_name']}")
    print(f"预估DPS: {build['estimated_dps']:,}")
    print(f"预算: {build['cost_analysis']['total_cost']}")
```

## 技术栈

**核心依赖**:
- `requests>=2.31.0` - HTTP客户端
- `beautifulsoup4>=4.12.0` - HTML解析
- `pydantic>=2.0.0` - 数据验证
- `psutil>=5.9.0` - 系统进程监控

**RAG系统**:
- `sentence-transformers>=2.2.0` - 语义向量化
- `faiss-cpu>=1.7.0` - 向量检索

**开发工具**:
- `pytest` - 测试框架
- `black` - 代码格式化
- `mypy` - 类型检查

**可选组件**:
- `PyQt6` - Windows GUI
- `FastAPI` - Web服务器
- `aiohttp>=3.8.0` - 异步HTTP

## 开发指导

### 运行测试
```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行特定测试类型
python -m pytest tests/unit/ -v          # 单元测试
python -m pytest tests/integration/ -v   # 集成测试
python -m pytest tests/performance/ -v   # 性能测试

# 生成测试覆盖率报告
python -m pytest --cov=src/poe2build tests/
```

### 代码质量检查
```bash
# 代码格式化
black src/ tests/

# 类型检查
mypy src/poe2build

# 运行预提交钩子
pre-commit run --all-files
```

### 健康检查
```bash
# 验证数据源连接
python -c "from src.poe2build.core.ai_orchestrator import PoE2AIOrchestrator; PoE2AIOrchestrator().health_check()"

# 验证PoB2集成
python -c "from src.poe2build.pob2 import PoB2LocalClient; PoB2LocalClient().detect_installation()"
```

## 故障排除

### 常见问题

**1. 数据源连接失败**
```bash
# 检查网络连接
ping poe2scout.com
ping poe2db.tw
ping poe.ninja

# 检查防火墙设置
# 确保允许Python访问网络
```

**2. PoB2集成问题**
```bash
# 验证PoB2安装
# 检查Path of Building Community是否正确安装
# 确认版本兼容性 (推荐v2.35+)
```

**3. 内存不足**
```bash
# 减少RAG向量维度
# 调整缓存大小设置
# 分批处理大量数据
```

## 贡献指南

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 开发规范
- 遵循PEP 8代码风格
- 编写单元测试覆盖新功能
- 更新相关文档
- 确保所有测试通过

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 免责声明

本工具仅供《流放之路2》玩家学习和研究使用。请遵守游戏服务条款，理论构筑仅供参考。工具开发者不对使用本工具产生的任何后果承担责任。

---

**项目状态**: 🚧 积极开发中
**最后更新**: 2024-08-31
**版本**: 2.0.0