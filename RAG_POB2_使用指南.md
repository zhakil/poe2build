# RAG-PoB2高度集成推荐系统使用指南

## 🎯 系统概述

这是一个将RAG训练、四大数据源集成与Path of Building Community (PoE2)完美融合的智能构建推荐系统。

### ✨ 核心特性
- **RAG增强的智能推荐** - 基于真实游戏数据训练的AI推荐算法
- **四大数据源实时集成** - PoE2Scout + PoE Ninja + PoB2 + PoE2DB
- **自动PoB2检测** - 智能检测您的F盘安装路径: `F:\steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)`
- **完美PoB2适配** - 推荐结果可直接导入PoB2进行精确计算
- **智能构建代码生成** - 自动生成PoB2导入代码

## 🚀 快速开始

### 1. 运行完整测试
```bash
python test_complete_rag_pob2_integration.py
```

### 2. 使用集成推荐系统
```python
import asyncio
from rag_pob2_integrated_recommender import quick_recommendation

# 快速推荐
async def get_ranger_build():
    result = await quick_recommendation(
        character_class='Ranger',
        build_goal='clear_speed',
        budget_max=15.0
    )
    
    print(f"找到 {len(result.primary_recommendations)} 个推荐构建")
    for i, (build, score, pob2_result) in enumerate(result.primary_recommendations, 1):
        print(f"{i}. {build.metadata['main_skill']} - 分数: {score.total_score:.3f}")
        if pob2_result.import_code:
            print(f"   PoB2代码: {pob2_result.import_code[:50]}...")

# 运行
asyncio.run(get_ranger_build())
```

### 3. 使用详细推荐系统
```python
from rag_pob2_integrated_recommender import (
    create_integrated_recommender,
    IntegratedRecommendationRequest
)

async def detailed_recommendation():
    # 初始化系统
    recommender = await create_integrated_recommender()
    
    # 创建详细请求
    request = IntegratedRecommendationRequest(
        character_class='Witch',
        ascendancy='Infernalist',
        build_goal='boss_killing',
        budget_range=(10, 30),
        preferred_skills=['Fireball', 'Meteor'],
        skill_level='advanced',
        max_recommendations=8,
        generate_pob2_code=True,
        validate_with_pob2=True
    )
    
    # 生成推荐
    result = await recommender.generate_integrated_recommendations(request)
    
    # 显示结果
    recommender.display_recommendation_summary(result)

asyncio.run(detailed_recommendation())
```

## 🔧 系统组件

### 1. RAG训练系统
- **位置**: `core_ai_engine/src/poe2build/rag/`
- **功能**: 智能推荐算法、相似度搜索、知识库管理

### 2. PoB2集成组件
- **路径检测器**: `core_ai_engine/src/poe2build/pob2/path_detector.py`
- **数据适配器**: `core_ai_engine/src/poe2build/pob2/rag_pob2_adapter.py`
- **本地客户端**: `core_ai_engine/src/poe2build/pob2/local_client.py`

### 3. 导入代码生成器
- **位置**: `pob2_import_code_generator.py`
- **功能**: 生成完全兼容PoB2的导入代码

### 4. 集成推荐引擎
- **位置**: `rag_pob2_integrated_recommender.py`
- **功能**: 协调所有组件，提供端到端服务

## 📊 支持的功能

### 职业支持
- ✅ Witch (女巫)
- ✅ Ranger (游侠) 
- ✅ Warrior (战士)
- ✅ Monk (武僧)
- ✅ Mercenary (佣兵)
- ✅ Sorceress (女法师)

### 构建目标
- `clear_speed` - 快速清图
- `boss_killing` - Boss击杀
- `endgame_content` - 终极内容
- `league_start` - 赛季开荒
- `budget_friendly` - 预算友好

### 推荐算法
- `COLLABORATIVE_FILTERING` - 协同过滤
- `CONTENT_BASED` - 基于内容
- `KNOWLEDGE_BASED` - 基于知识
- `HYBRID` - 混合推荐 (推荐)

## 🛠️ PoB2集成特性

### 自动路径检测
系统会自动检测您的PoB2安装，支持的路径包括：
- `F:\steam\steamapps\common\Path of Exile 2\Path of Building Community (PoE2)` (您的安装位置)
- Steam默认路径
- Epic Games路径
- 自定义安装路径

### 完美数据转换
- ✅ 职业和升华自动匹配
- ✅ 技能宝石ID正确映射
- ✅ 装备属性精确转换
- ✅ 被动技能树路径优化
- ✅ PoB2 XML格式标准化

### 验证和兼容性
- 构建数据完整性验证
- PoB2格式兼容性检查
- 导入代码有效性测试
- 多重错误处理机制

## 📈 性能特性

### 缓存和优化
- 智能推荐结果缓存
- PoB2验证结果缓存
- 并行数据处理
- 渐进式降级策略

### 实时数据集成
- PoE2Scout市场数据 (10分钟更新)
- PoE Ninja构建趋势 (30分钟更新)
- PoE2DB游戏数据 (1小时更新)
- PoB2本地数据 (实时)

## 🧪 测试和验证

### 运行完整测试
```bash
python test_complete_rag_pob2_integration.py
```

测试包括：
1. 系统初始化测试
2. PoB2路径检测测试
3. RAG智能推荐测试
4. PoB2代码生成测试
5. 端到端工作流测试
6. 性能基准测试

### 单独组件测试
```bash
# 测试PoB2适配器
python -c "from core_ai_engine.src.poe2build.pob2.rag_pob2_adapter import test_rag_pob2_integration; test_rag_pob2_integration()"

# 测试代码生成器
python pob2_import_code_generator.py

# 测试路径检测
python -c "from core_ai_engine.src.poe2build.pob2.path_detector import PoB2PathDetector; print(PoB2PathDetector.detect())"
```

## 📋 使用示例

### 基础推荐
```python
# 获取游侠弓箭手构建
result = await quick_recommendation('Ranger', 'clear_speed', 15)
```

### 高级推荐
```python
# 详细配置推荐
request = IntegratedRecommendationRequest(
    character_class='Witch',
    ascendancy='Blood Mage', 
    build_goal='boss_killing',
    budget_range=(20, 50),
    preferred_skills=['Fireball', 'Meteor'],
    skill_level='expert',
    algorithm_type=AlgorithmType.HYBRID,
    max_recommendations=10
)
result = await recommender.generate_integrated_recommendations(request)
```

### 导入到PoB2
```python
# 获取推荐后，PoB2导入代码已自动生成
for build, score, pob2_validation in result.primary_recommendations:
    if pob2_validation.is_valid:
        print(f"PoB2导入代码: {pob2_validation.import_code}")
        # 直接复制这个代码到PoB2中导入
```

## ❓ 故障排除

### 常见问题

**Q: PoB2路径检测失败**
A: 确保PoB2安装在支持的路径，或手动指定路径

**Q: 推荐结果为空**
A: 检查网络连接，确保四大数据源可访问

**Q: PoB2代码无效**
A: 检查PoB2版本兼容性，确保使用最新版本

**Q: 系统初始化慢**
A: 首次运行需要下载和处理数据，请耐心等待

### 日志调试
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 未来计划

- [ ] 支持更多升华职业
- [ ] 增加装备推荐功能
- [ ] 实现构建对比分析
- [ ] 添加GUI界面
- [ ] 支持自定义算法权重
- [ ] 集成官方API (当可用时)

## 📞 获取帮助

如遇问题，请检查：
1. 系统组件是否正确初始化
2. PoB2是否正确安装和检测
3. 网络连接是否正常
4. 日志中是否有错误信息

---

🎉 **恭喜！** 您现在拥有了一个完整的RAG-PoB2集成推荐系统，可以提供智能、准确、可直接导入PoB2的构建推荐！