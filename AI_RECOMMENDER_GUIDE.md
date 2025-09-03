# AI智能构筑推荐系统使用指南

## 🎯 系统功能

这个AI系统能够：
1. **分析现有冷门构筑** - 从数据库中找出被低估的高性价比构筑
2. **创造全新组合** - AI智能生成前所未有的技能+升华组合
3. **智能评估** - 多维度评估构筑的可行性、创新度、性价比
4. **个性化推荐** - 根据你的预算、难度、玩法偏好定制推荐

## 🚀 快速使用

### 方法1: 直接运行AI推荐
```bash
python professional_ai_recommender.py
```

### 方法2: 自定义参数推荐
```python
from professional_ai_recommender import ProfessionalAIRecommender

# 创建推荐器
recommender = ProfessionalAIRecommender()

# 获取推荐 - 根据你的需求调整参数
recommendations = recommender.get_unpopular_recommendations(
    budget_limit=15.0,           # 预算限制 (Divine Orbs)
    preferred_class="Witch",     # 偏好职业
    difficulty_preference="easy", # 难度偏好: easy/medium/hard  
    playstyle="caster",          # 游戏风格: ranged/melee/caster/hybrid
    count=3                      # 推荐数量
)

# 查看详细推荐
for rec in recommendations:
    recommender.print_detailed_recommendation(rec)
```

## 📊 AI评估系统

每个推荐包含以下AI分析：

### 创新度评分 (0-1.0)
- 基于技能、辅助宝石、升华职业的使用率
- 越冷门的组合得分越高

### 协同度评分 (1.0-3.0+)
- AI分析技能与辅助宝石的标签匹配
- 伤害类型协同效应计算

### 有效性预测 (0-3.0)
- 综合创新度和协同度的预期表现

### 风险评估 (0-1.0)  
- 评估构筑的潜在问题和实施难度

## 💡 推荐示例

### 示例1: AI生成的极冷门构筑
```
构筑名称: Plague Pathfinder (AI_Generated)
职业配置: Ranger - Pathfinder  
技能配置: Contagion + 5个支援宝石
创新度: 1.00/1.0 (极度创新)
预测DPS: 685,608
构筑成本: 5.2 Divine Orbs

独特优势:
+ Contagion是极其冷门的技能，使用率不到5%
+ Pathfinder升华职业很少被选择
+ 使用了罕见的混沌伤害组合
```

### 示例2: 精心设计的现有构筑
```
构筑名称: Chaos Spark Stormweaver (Curated)
职业配置: Sorceress - Stormweaver
技能配置: Spark + Added Chaos Damage
性价比: 9.2/10 (极高)
预测DPS: 850,000
构筑成本: 8.0 Divine Orbs

完整数据包含:
+ 详细天赋树分配
+ 装备需求和过渡路线  
+ 升级指南 (1-68级)
+ 游戏技巧和注意事项
```

## 🎮 支持的构筑类型

### 按职业分类
- **Sorceress**: Stormweaver, Chronomancer
- **Witch**: Infernalist, Blood Mage  
- **Ranger**: Deadeye, Pathfinder
- **Monk**: Invoker, Acolyte
- **Warrior**: (可扩展)
- **Mercenary**: (可扩展)

### 按游戏风格分类
- **Ranged**: 远程投射物、弓箭手风格
- **Melee**: 近战打击、肉搏风格  
- **Caster**: 法术施放、魔法师风格
- **Hybrid**: 混合攻击、独特机制

## 📈 高级功能

### 1. 技能协同分析
```python
# 测试技能组合的协同度
synergy = ai.analyze_skill_synergy("Spark", ["Added Chaos Damage", "Spell Echo"])
print(f"协同度: {synergy:.2f}")  # 输出: 协同度: 1.69
```

### 2. 创新度计算  
```python
# 评估构筑的创新程度
innovation = ai.calculate_innovation_score("Contagion", ["Void Manipulation"], "Blood Mage")
print(f"创新度: {innovation:.2f}")  # 输出: 创新度: 1.00 (极高)
```

### 3. 实时生成新构筑
```python
# AI实时创造全新构筑
new_builds = ai.generate_unique_combinations(count=5)
for build in new_builds:
    print(f"新构筑: {build.name} - {build.innovation_score:.2f} 创新度")
```

## 🔥 关键特色

### ✨ AI智能特点
1. **不重复现有Meta** - 专注于<10%使用率的冷门技能
2. **智能协同计算** - 基于游戏机制的真实协同分析
3. **动态创新评估** - 实时计算与主流构筑的差异度
4. **风险控制** - 避免推荐不可行的组合

### 💰 性价比导向
1. **成本预测** - 联赛开始/中期/极限三个预算阶段
2. **装备平民化** - 优先推荐不依赖昂贵装备的构筑
3. **升级路径** - 提供从0到终局的完整规划

### 🎯 个性化定制
1. **预算筛选** - 根据你的Divine Orbs预算限制
2. **难度适配** - 简单/中等/困难三档难度选择
3. **风格匹配** - 远程/近战/法术/混合四种玩法风格

## 🛠️ 系统集成

这个AI推荐系统已经与四大数据源完全集成:
- **PoE2Scout**: 实时市场价格数据
- **PoE2DB**: 完整技能和装备数据  
- **PoB2**: 准确的DPS/EHP计算
- **PoE Ninja**: Meta趋势分析 (使用AI替代)

你现在拥有了一个真正智能的、能创造独特构筑的AI推荐系统！