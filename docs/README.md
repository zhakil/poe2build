# PoE2 智能构筑生成器 - 技术文档

## 📖 文档概览

本文档库包含基于**真实PoE2数据源**的智能构筑生成器的完整技术文档。所有内容都专门针对Path of Exile 2，不依赖假设的API端点。

## 🎯 核心原则

- **✅ 真实可用**: 所有API和数据源都基于实际存在的PoE2服务
- **🎮 PoE2专用**: 100%专注于Path of Exile 2的特有机制和数据
- **📊 验证有效**: 所有代码示例和集成都经过实际测试验证
- **🔄 持续更新**: 随着PoE2发展不断更新和改进

## 📚 文档导航

### 🏗️ 核心架构文档
- **[01. 弹性架构设计](01_real_architecture.md)** - 基于Interface-based的弹性模块化架构
- **[02. PoE2数据源集成](02_poe2_data_sources.md)** - 详细的PoE2专用数据源集成指南
- **[11. PoB2集成架构](11_pob2_integration.md)** - Path of Building Community集成设计和实现
- **[12. RAG-AI训练系统](12_rag_ai_training.md)** - 基于ninja.poe2数据的RAG智能训练架构

### 📋 项目规划文档
- **[08. 项目结构设计](08_project_structure.md)** - 完整的项目文件结构和组织规范
- **[09. 开发流程规范](09_development_workflow.md)** - 标准化开发流程和工作规范
- **[10. 测试策略指南](10_testing_strategy.md)** - 全面的测试策略和质量保证

### 🚀 使用指南
- **[04. API使用指南](04_api_usage.md)** - 完整的使用示例和快速开始
- **[05. 开发者指南](05_developer_guide.md)** - 扩展开发和贡献指南

### 🛠️ 运维文档
- **[06. 部署指南](06_deployment.md)** - 生产环境部署和运维
- **[07. 故障排除](07_troubleshooting.md)** - 常见问题和解决方案

## 🔗 真实PoE2数据源

本项目集成的所有数据源都是**真实可用**的PoE2专用服务：

### 1. [PoE2 Scout](https://poe2scout.com) ✅
- **用途**: PoE2专用市场和构筑数据
- **状态**: 真实可用，专门针对PoE2
- **文档**: [PoE2数据源集成](02_poe2_data_sources.md#poe2-scout)

### 2. [PoE2DB](https://poe2db.tw) ✅  
- **用途**: PoE2游戏数据数据库
- **状态**: 真实可用，从PoE2客户端提取数据
- **文档**: [PoE2数据源集成](02_poe2_data_sources.md#poe2db)

### 3. [poe.ninja PoE2专区](https://poe.ninja/poe2/builds) ✅
- **用途**: PoE2构筑分析和Meta数据
- **状态**: 真实可用，poe.ninja的PoE2专门页面
- **文档**: [PoE2数据源集成](02_poe2_data_sources.md#poe2-ninja)

## 🎮 PoE2核心机制支持

本系统完整支持Path of Exile 2的独有游戏机制：

- **能量护盾系统**: PoE2的核心防御机制
- **80%抗性上限**: PoE2的最大抗性机制
- **新技能系统**: PoE2的技能宝石和支撑宝石机制
- **升华职业**: PoE2的新升华职业系统
- **装备系统**: PoE2的装备词缀和制作系统

详见: [PoE2计算引擎](03_poe2_calculator.md)

## 🚀 快速开始

### 最简单的开始方式

```bash
# 克隆项目
git clone https://github.com/zhakil/poe2build.git
cd poe2build

# 安装依赖
pip install -r requirements.txt

# 运行PoE2 AI推荐系统
python poe2_ai_orchestrator.py
```

### 代码示例

```python
from poe2_ai_orchestrator import PoE2AIOrchestrator

# 初始化AI推荐系统
orchestrator = PoE2AIOrchestrator()

# 检查PoB2集成状态
health = orchestrator.health_check()
print(f"PoB2可用: {'✅' if health['pob2_available'] else '❌'}")

# PoE2构筑请求
request = {
    'preferences': {
        'class': 'Ranger', 
        'style': 'bow',
        'pob2_integration': {
            'calculate_stats': True,
            'generate_import_code': True
        }
    }
}

# 获取RAG增强的AI构筑推荐
result = orchestrator.generate_build_recommendation(request)

print(f"基于 {result.get('rag_context', {}).get('similar_builds_found', 0)} 个相似构筑生成推荐")

for build in result['recommendations']:
    print(f"推荐构筑: {build['build_name']}")
    print(f"RAG置信度: {build.get('rag_confidence', 0):.3f}")
    if 'pob2_stats' in build:
        print(f"PoB2计算DPS: {build['pob2_stats']['total_dps']:,}")
        print(f"导入代码: {build.get('pob2_import_code', 'N/A')[:50]}...")
    if 'rag_context' in build:
        inspiration = build['rag_context'].get('inspiration_build', {})
        print(f"灵感来源: {inspiration.get('name', 'N/A')} (排名: {inspiration.get('rank', 'N/A')})")
```

更多示例见: [API使用指南](04_api_usage.md)

## 📊 文档状态

| 文档 | 状态 | 最后更新 | 验证状态 |
|------|------|----------|----------|
| 弹性架构设计 | ✅ 完成 | 2025-01 | ✅ 已验证 |
| PoE2数据源集成 | ✅ 完成 | 2025-01 | ✅ 已测试 |
| PoE2计算引擎 | ✅ 完成 | 2025-01 | ✅ 已验证 |
| API使用指南 | ✅ 完成 | 2025-01 | ✅ 已测试 |
| 开发者指南 | ✅ 完成 | 2025-01 | ✅ 已审核 |
| 部署指南 | ✅ 完成 | 2025-01 | ✅ 已验证 |
| 故障排除 | ✅ 完成 | 2025-01 | ✅ 已测试 |
| PoB2集成架构 | ✅ 完成 | 2025-01 | ✅ 已设计 |
| 项目结构设计 | ✅ 完成 | 2025-01 | ✅ 已规划 |
| 开发流程规范 | ✅ 完成 | 2025-01 | ✅ 已制定 |
| 测试策略指南 | ✅ 完成 | 2025-01 | ✅ 已设计 |
| RAG-AI训练系统 | ✅ 完成 | 2025-01 | ✅ 已设计 |

## 🤝 文档贡献

我们欢迎对PoE2文档的贡献：

1. **📝 内容改进**: 帮助改善文档的准确性和清晰度
2. **🔍 错误报告**: 发现并报告文档中的错误或过时信息
3. **💡 新增内容**: 添加新的PoE2功能或用例的文档
4. **🌐 翻译**: 帮助将文档翻译成其他语言

### 文档更新流程

```bash
# 1. Fork项目
git fork https://github.com/zhakil/poe2build

# 2. 创建文档分支
git checkout -b docs/improve-poe2-docs

# 3. 编辑文档
# 编辑 docs/ 目录下的相关文件

# 4. 测试文档中的代码示例
python poe2_real_data_sources.py

# 5. 提交PR
git commit -m "改进PoE2文档: 添加新示例"
git push origin docs/improve-poe2-docs
```

## 📞 获取帮助

如果你在使用文档时遇到问题：

1. **📖 查阅相关文档**: 先查看对应的专题文档
2. **🔍 搜索Issues**: 在GitHub Issues中搜索类似问题  
3. **❓ 提出问题**: 在Issues中提出新问题
4. **💬 社区讨论**: 参与社区讨论获取帮助

## 🏷️ 版本说明

### v2.0.0 - 弹性模块化架构版本

- ✅ **弹性架构**: 基于Interface-based的弹性模块化设计
- ✅ **断路器模式**: 实现Circuit Breaker防止级联故障
- ✅ **智能限流**: 指数退避策略保护社区资源
- ✅ **未来就绪**: 为官方API迁移做好准备
- ✅ **完整规划**: 详细的项目结构、开发流程和测试策略

### 主要变更

1. **数据源更新**:
   - ❌ 移除: 假设的 `api.poe2.ninja`
   - ❌ 移除: 假设的 `trade.poe2.com`  
   - ❌ 移除: 不存在的 `PoB2_CLI.exe`
   - ✅ 添加: 真实的 PoE2 Scout 集成
   - ✅ 添加: 真实的 PoE2DB 集成
   - ✅ 添加: 真实的 poe.ninja PoE2专区集成

2. **架构全面升级**:
   - ✅ **弹性设计**: Interface-based模块化架构
   - ✅ **断路器保护**: 防止级联故障的自动恢复机制
   - ✅ **智能限流**: Rate Limiting + 指数退避策略
   - ✅ **"生态公民"理念**: 尊重社区资源的API使用方式
   - ✅ **未来兼容**: 为GGG官方OAuth API做好迁移准备

3. **开发流程标准化**:
   - ✅ **项目结构设计**: 企业级文件组织和模块划分
   - ✅ **标准开发流程**: TDD、CI/CD、代码审查完整流程
   - ✅ **测试策略**: 单元、集成、性能、E2E全覆盖测试
   - ✅ **质量保证**: 自动化质量检查和持续集成

---

**🚀 快速开始**: 
- 📋 **项目规划**: 从 [项目结构设计](08_project_structure.md) 了解完整的项目组织
- 🏗️ **架构理解**: 阅读 [弹性架构设计](01_real_architecture.md) 掌握核心设计理念
- ⚡ **立即使用**: 查看 [API使用指南](04_api_usage.md) 快速上手体验