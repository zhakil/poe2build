# PoE2 Build Generator GUI

基于PyQt6的Path of Exile 2构筑生成器图形用户界面。

## 功能特性

### 🎯 核心功能
- **智能构筑生成**: AI驱动的构筑推荐系统
- **PoB2深度集成**: 无缝集成Path of Building Community
- **实时数据分析**: 整合poe2scout和ninja市场数据
- **响应式界面**: 现代化暗色PoE2主题设计

### 🎨 界面特性
- **暗色主题**: 基于PoE2游戏UI的专业暗色主题
- **响应式布局**: 支持不同分辨率和DPI缩放
- **多页面导航**: 欢迎页、构筑生成器、结果展示、设置页面
- **实时状态**: 显示后端连接和PoB2集成状态

## 安装要求

### 系统要求
- Windows 10/11, macOS 10.14+, 或 Linux
- Python 3.8+
- 至少2GB RAM
- 显示器分辨率: 1280x800或更高

### Python依赖
```bash
# 安装GUI依赖
pip install -r requirements-gui.txt

# 或手动安装核心依赖
pip install PyQt6 requests beautifulsoup4
```

## 快速启动

### 1. 使用启动脚本 (推荐)
```bash
python run_gui.py
```

### 2. 直接运行
```bash
cd src
python -m poe2build.gui.app
```

### 3. 作为模块导入
```python
from poe2build.gui.app import main
main()
```

## 项目结构

```
src/poe2build/gui/
├── __init__.py              # GUI包初始化
├── app.py                   # 主应用程序入口
├── main_window.py           # 主窗口框架
├── components/              # 可复用组件 (未来扩展)
├── pages/                   # 主要页面
│   ├── __init__.py
│   ├── welcome_page.py      # 欢迎页面
│   ├── build_generator_page.py  # 构筑生成器
│   ├── build_results_page.py   # 结果展示
│   └── settings_page.py     # 设置页面
├── widgets/                 # 自定义小部件
│   ├── __init__.py
│   └── navigation_bar.py    # 导航栏组件
└── styles/                  # 样式和主题
    ├── __init__.py
    └── poe2_theme.py        # PoE2暗色主题
```

## 使用指南

### 基本工作流程

1. **启动应用**: 运行`python run_gui.py`
2. **设置偏好**: 在"设置"页面配置PoB2路径和后端连接
3. **生成构筑**: 在"构筑生成器"页面输入偏好并生成AI推荐
4. **查看结果**: 在"构筑结果"页面查看详细推荐和PoB2数据
5. **导出构筑**: 将构筑导出到Path of Building Community

### 主要页面功能

#### 欢迎页 (Welcome Page)
- 功能概览和快速入口
- 系统状态显示
- 快捷操作按钮

#### 构筑生成器 (Build Generator)
- **基本设置**: 职业、专精、武器类型选择
- **高级设置**: PoB2集成、AI参数调整
- **预算设置**: 货币类型和预算限制
- **进度跟踪**: 实时显示生成进度

#### 构筑结果 (Build Results) 
- **构筑列表**: AI推荐的构筑卡片展示
- **详细信息**: 技能、装备、统计数据
- **PoB2集成**: 导入代码和精确计算
- **导出功能**: 保存和分享构筑

#### 设置页 (Settings)
- **常规设置**: 语言、启动选项
- **后端设置**: AI API配置和数据源
- **界面设置**: 主题、字体、显示选项
- **PoB2集成**: 路径设置和集成选项
- **高级设置**: 调试、性能、数据管理

## 主题系统

### PoE2暗色主题
- 基于Path of Exile 2游戏UI设计
- 专业暗色配色方案
- PoE2特色金色高亮
- 完整的组件样式覆盖

### 颜色规范
```python
# 主要颜色
背景色: #1a1a1a (主) / #2d2d2d (次) / #3a3a3a (第三级)
文字色: #f0f0f0 (主) / #c0c0c0 (次) / #707070 (禁用)
强调色: #d4af37 (PoE2金色)
状态色: #2ecc71 (成功) / #f39c12 (警告) / #e74c3c (错误)
```

## 开发说明

### 架构设计
- **MVC模式**: 分离界面、逻辑和数据
- **信号槽系统**: PyQt6事件驱动通信
- **模块化设计**: 页面和组件独立开发
- **主题系统**: 统一的样式管理

### 扩展指南
1. **添加新页面**: 继承`QWidget`并添加到主窗口
2. **自定义组件**: 在`widgets/`目录创建可复用组件
3. **样式定制**: 修改`poe2_theme.py`中的颜色和样式
4. **后端集成**: 通过`orchestrator`参数访问后端功能

### 调试技巧
```bash
# 启用调试模式
python run_gui.py --debug

# 查看PyQt6版本信息
python -c "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)"

# 测试主题渲染
python -c "from poe2build.gui.styles.poe2_theme import PoE2Theme; print('Theme loaded')"
```

## 故障排除

### 常见问题

#### 1. PyQt6导入失败
```bash
# 解决方案
pip install --upgrade PyQt6
# 或针对特定平台
pip install PyQt6-Qt6
```

#### 2. 界面显示异常
- 检查系统DPI设置
- 尝试不同的DPI缩放选项
- 确认显卡驱动程序正常

#### 3. 后端连接失败
- 检查网络连接
- 验证API端点配置
- 查看设置页面的连接测试结果

#### 4. PoB2集成问题
- 确认Path of Building Community已安装
- 手动设置PoB2安装路径
- 检查PoB2版本兼容性

### 日志和调试
- GUI日志: 控制台输出
- 错误报告: 自动显示错误对话框
- 状态信息: 状态栏实时显示

## 贡献指南

### 代码风格
- 遵循PEP 8规范
- 使用中文注释和文档字符串
- PyQt6命名约定 (驼峰式)
- 类型提示 (Python 3.8+)

### 提交规范
```
feat(gui): 添加新的构筑比较功能
fix(theme): 修复暗色主题按钮样式
docs(readme): 更新GUI使用指南
```

## 许可证

本项目基于MIT许可证开源。详见项目根目录的LICENSE文件。

## 致谢

- Path of Building Community项目
- PyQt6框架
- PoE2游戏社区和数据提供者

---

**注意**: 这是一个开发版本的GUI界面。部分高级功能可能需要完整的后端系统支持才能正常工作。