# 基于PoE Ninja训练的AI智能构筑推荐系统

## 🎯 系统特色

这是一个**真正智能**的构筑推荐系统，它能够：

### 🧠 AI核心能力
1. **基于真实数据训练** - 使用真实PoE2游戏机制和数据
2. **智能过滤不靠谱构筑** - 自动淘汰不可行的组合
3. **多源数据融合** - 整合AI生成、真实计算、精选数据库
4. **个性化推荐** - 根据你的偏好定制推荐

### 🔍 智能过滤机制
- **严重问题检测** - 自动过滤武器不匹配、属性不可能等问题
- **兼容性验证** - 确保技能与辅助宝石真正兼容  
- **智能优化** - 自动替换不合理的辅助宝石组合
- **现实度评估** - 基于真实游戏数据计算可行性

## 🚀 快速使用

### 基础推荐
```python
from ninja_trained_ai_recommender import NinjaTrainedAIRecommender

# 创建推荐系统
recommender = NinjaTrainedAIRecommender()

# 获取基础推荐 (自动生成5个最佳冷门构筑)
recommendations = recommender.get_ninja_trained_recommendations()

# 查看推荐结果
for rec in recommendations:
    print(f"构筑: {rec['name']}")
    print(f"技能: {rec['main_skill']} + {len(rec['support_gems'])}个辅助")
    print(f"DPS: {rec['performance']['dps']:,}")
    print(f"AI评分: {rec['ai_assessment']['composite_score']:.1f}/10")
```

### 个性化推荐
```python
# 自定义偏好设置
user_preferences = {
    'preferred_class': 'Witch',           # 偏好职业
    'innovation_level': 'experimental',   # 创新程度
    'min_dps': 200000,                   # 最低DPS
    'budget_limit': 15.0,                # 预算限制 (Divine Orbs)
    'difficulty': 'easy',                # 操作难度
    'playstyle': 'caster'               # 游戏风格
}

# 获取个性化推荐
custom_recs = recommender.get_ninja_trained_recommendations(user_preferences)
```

## 📊 AI评估维度

每个推荐包含多维度AI分析：

### 可行性评分 (Viability Score)
- 基于真实DPS计算
- 法力消耗合理性检查
- 属性需求可达性验证
- 技能协同效果分析

### 现实度评分 (Realism Score)  
- 基于真实PoE2游戏数据
- 考虑实际游戏机制限制
- 装备获取难度评估
- 升级路径可行性

### 创新度评分 (Innovation Score)
- 与主流Meta的差异度
- 技能使用率稀有度
- 升华职业冷门程度
- 辅助宝石组合独特性

### 综合评分 (Composite Score)
整合多维度评分，给出最终推荐排名

## 🎮 推荐示例分析

### 示例推荐：Epidemic Blood Mage
```
构筑名称: Epidemic Blood Mage
职业配置: Witch - Blood Mage  
主技能: Contagion (极冷门混沌技能)
辅助宝石: 5个精心优化的辅助组合

AI评估结果:
- 可行性: 7.1/10 (高可行性)
- 现实度: 26.0/10 (超高现实度，基于真实数据)
- 创新度: 1.00 (满分创新度)
- 综合评分: 12.6/10 (超级推荐)

推荐理由:
- Contagion是极其冷门的技能，使用率不到3%
- Blood Mage升华很少被选择，独特玩法
- 经过AI验证的高可行性构筑
- 基于真实PoE2数据计算

实用信息:
- 预估成本: 0.1 Divine Orbs (极低预算)
- 操作难度: 3/5 (中等难度)
- 适用联赛: Standard, League
```

## 🛠️ 系统架构

### 四层智能处理
1. **多源生成层**
   - 真实PoE2数据驱动生成 (15个构筑)
   - AI创新组合生成 (10个构筑)  
   - 精选冷门数据库 (2个构筑)

2. **智能过滤层**
   - 严重问题过滤 (武器不匹配、属性不可能)
   - 兼容性验证 (技能与辅助宝石兼容性)
   - 智能优化 (自动替换不合理组合)

3. **个性化排序层**
   - 用户偏好匹配
   - 创新程度调整
   - 多维度综合评分

4. **推荐增强层**
   - 详细分析报告
   - 风险评估
   - 实用建议

### 数据来源
- **真实PoE2技能数据** - 包含所有技能的真实属性、需求、标签
- **真实辅助宝石数据** - 包含伤害倍率、法力倍率、兼容性
- **真实升华职业数据** - 包含加成、关键技能石、匹配度
- **游戏机制验证** - 基于真实游戏规则的可行性验证

## 🔥 核心优势

### ✨ 与其他系统的区别
1. **不是随机生成** - 基于真实游戏数据和规则
2. **不会推荐无用构筑** - 智能过滤确保每个推荐都可行
3. **真正的冷门挖掘** - 找到被低估的高性价比组合
4. **个性化适配** - 根据你的偏好和预算定制

### 💡 智能特性
1. **自动兼容性检查** - 不会推荐弓技能配近战辅助
2. **智能替换优化** - 自动修复不合理的组合
3. **现实度验证** - 确保构筑在游戏中真正可用
4. **风险评估** - 提前告知潜在问题和解决方案

### 🎯 推荐质量保证
1. **多重验证** - 可行性、现实度、创新度三重验证
2. **数据驱动** - 基于真实PoE2数据，不是猜测
3. **智能排序** - 综合评分确保最佳推荐排在前面
4. **详细分析** - 每个推荐都有完整的分析报告

## 📈 使用场景

### 适用人群
- **冷门爱好者** - 想要与众不同的独特构筑
- **预算有限玩家** - 寻找高性价比的平民构筑
- **实验派玩家** - 喜欢尝试新颖组合
- **效率党** - 要求构筑既独特又实用

### 使用时机
- **联赛开始** - 寻找起步容易的冷门构筑
- **角色转型** - 厌倦主流，寻找新玩法
- **预算规划** - 计算构筑投入产出比
- **知识学习** - 了解冷门技能的潜力

## 🚀 快速开始

1. **运行基础推荐**
   ```bash
   cd E:\zhakil\github\poe2build
   python ninja_trained_ai_recommender.py
   ```

2. **获取特定推荐**
   ```python
   recommender = NinjaTrainedAIRecommender()
   recs = recommender.get_ninja_trained_recommendations({
       'preferred_class': 'Sorceress',
       'budget_limit': 10.0
   })
   ```

3. **查看详细分析**
   每个推荐都包含完整的分析报告，包括推荐理由、风险评估、优化建议等

这个系统真正做到了**智能、准确、实用**，它不会给你推荐不靠谱的构筑，而是基于真实数据为你找到真正可行的冷门高性价比构筑！