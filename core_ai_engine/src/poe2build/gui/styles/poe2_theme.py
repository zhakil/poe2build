"""
PoE2暗色主题样式定义

基于Path of Exile 2游戏UI设计的暗色主题，包含颜色定义、样式表和调色板。
"""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


class PoE2Theme:
    """PoE2暗色主题类"""
    
    # PoE2主题颜色定义
    COLORS = {
        # 主要背景色
        'background_primary': '#0f0f0f',      # 深黑主背景
        'background_secondary': '#1a1a1a',    # 次级背景
        'background_tertiary': '#2a2a2a',     # 第三级背景
        'background_quaternary': '#3a3a3a',   # 第四级背景
        
        # 文字颜色
        'text_primary': '#f5f5f5',            # 主要文字（更亮）
        'text_secondary': '#d0d0d0',          # 次级文字
        'text_tertiary': '#a0a0a0',           # 第三级文字
        'text_disabled': '#606060',           # 禁用文字
        'text_highlight': '#DAA520',          # 高亮文字（更准确的PoE金色）
        
        # PoE2特色颜色（更准确的游戏配色）
        'poe2_gold': '#DAA520',               # PoE2金色（稀有装备色）
        'poe2_blue': '#4169E1',               # PoE2蓝色（魔法装备色）
        'poe2_red': '#DC143C',                # PoE2红色（火焰伤害色）
        'poe2_green': '#32CD32',              # PoE2绿色（生命色）
        'poe2_purple': '#8A2BE2',             # PoE2紫色（混沌色）
        'poe2_orange': '#FF8C00',             # PoE2橙色（传奇装备色）
        'poe2_white': '#F8F8FF',              # PoE2白色（普通装备色）
        
        # 渐变和光效颜色
        'glow_gold': '#FFD700',               # 金色光效
        'glow_blue': '#87CEEB',               # 蓝色光效
        'glow_red': '#FF6B6B',                # 红色光效
        'shadow_dark': '#0a0a0a',             # 深阴影
        'shadow_medium': '#1f1f1f',           # 中等阴影
        
        # 边框和分割线
        'border_primary': '#4a4a4a',          # 主要边框
        'border_secondary': '#5a5a5a',        # 次级边框
        'border_hover': '#6a6a6a',            # 悬停边框
        'border_focus': '#d4af37',            # 焦点边框
        
        # 按钮颜色
        'button_primary': '#4a4a4a',          # 主按钮背景
        'button_primary_hover': '#5a5a5a',    # 主按钮悬停
        'button_primary_pressed': '#3a3a3a',  # 主按钮按下
        'button_hover': '#5a5a5a',            # 通用按钮悬停
        'button_accent': '#d4af37',           # 强调按钮背景
        'button_accent_hover': '#e6c547',     # 强调按钮悬停
        'button_accent_pressed': '#c19f2a',   # 强调按钮按下
        'poe2_gold_hover': '#e6c547',         # 金色悬停
        
        # 输入框颜色
        'input_background': '#2d2d2d',        # 输入框背景
        'input_border': '#4a4a4a',            # 输入框边框
        'input_border_focus': '#d4af37',      # 输入框焦点边框
        
        # 滚动条颜色
        'scrollbar_background': '#2d2d2d',    # 滚动条背景
        'scrollbar_handle': '#4a4a4a',        # 滚动条手柄
        'scrollbar_handle_hover': '#5a5a5a',  # 滚动条手柄悬停
        
        # 状态颜色
        'success': '#2ecc71',                 # 成功状态
        'warning': '#f39c12',                 # 警告状态
        'error': '#e74c3c',                   # 错误状态
        'info': '#4a90e2',                    # 信息状态
    }
    
    def __init__(self):
        self.palette = self._create_palette()
    
    def _create_palette(self) -> QPalette:
        """创建Qt调色板"""
        palette = QPalette()
        
        # 设置窗口颜色
        palette.setColor(QPalette.ColorRole.Window, QColor(self.COLORS['background_primary']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.COLORS['text_primary']))
        
        # 设置基础颜色
        palette.setColor(QPalette.ColorRole.Base, QColor(self.COLORS['background_secondary']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.COLORS['background_tertiary']))
        
        # 设置文字颜色
        palette.setColor(QPalette.ColorRole.Text, QColor(self.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(self.COLORS['text_highlight']))
        
        # 设置按钮颜色
        palette.setColor(QPalette.ColorRole.Button, QColor(self.COLORS['button_primary']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.COLORS['text_primary']))
        
        # 设置高亮颜色
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.COLORS['poe2_gold']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.COLORS['background_primary']))
        
        # 设置禁用状态颜色
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(self.COLORS['text_disabled']))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(self.COLORS['text_disabled']))
        
        return palette
    
    def get_palette(self) -> QPalette:
        """获取Qt调色板"""
        return self.palette
    
    def get_stylesheet(self) -> str:
        """获取完整的样式表"""
        return f"""
        /* 主窗口样式 */
        QMainWindow {{
            background-color: {self.COLORS['background_primary']};
            color: {self.COLORS['text_primary']};
        }}
        
        /* 菜单栏样式 */
        QMenuBar {{
            background-color: {self.COLORS['background_secondary']};
            border-bottom: 1px solid {self.COLORS['border_primary']};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.COLORS['button_primary_hover']};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {self.COLORS['button_primary_pressed']};
        }}
        
        /* 菜单样式 */
        QMenu {{
            background-color: {self.COLORS['background_secondary']};
            border: 1px solid {self.COLORS['border_primary']};
            padding: 4px;
            border-radius: 6px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            margin: 2px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.COLORS['button_primary_hover']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {self.COLORS['border_primary']};
            margin: 4px 8px;
        }}
        
        /* 状态栏样式 */
        QStatusBar {{
            background-color: {self.COLORS['background_secondary']};
            border-top: 1px solid {self.COLORS['border_primary']};
            color: {self.COLORS['text_secondary']};
        }}
        
        /* 工具栏样式 */
        QToolBar {{
            background-color: {self.COLORS['background_secondary']};
            border: none;
            spacing: 3px;
            padding: 4px;
        }}
        
        QToolBar::separator {{
            background-color: {self.COLORS['border_primary']};
            width: 1px;
            margin: 4px 8px;
        }}
        
        /* 按钮样式 */
        QPushButton {{
            background-color: {self.COLORS['button_primary']};
            border: 1px solid {self.COLORS['border_primary']};
            color: {self.COLORS['text_primary']};
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 500;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {self.COLORS['button_primary_hover']};
            border-color: {self.COLORS['border_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {self.COLORS['button_primary_pressed']};
        }}
        
        QPushButton:disabled {{
            background-color: {self.COLORS['background_tertiary']};
            color: {self.COLORS['text_disabled']};
            border-color: {self.COLORS['text_disabled']};
        }}
        
        /* 强调按钮样式 */
        QPushButton[accent="true"] {{
            background-color: {self.COLORS['button_accent']};
            color: {self.COLORS['background_primary']};
            font-weight: 600;
        }}
        
        QPushButton[accent="true"]:hover {{
            background-color: {self.COLORS['button_accent_hover']};
        }}
        
        QPushButton[accent="true"]:pressed {{
            background-color: {self.COLORS['button_accent_pressed']};
        }}
        
        /* 输入框样式 */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {self.COLORS['input_background']};
            border: 1px solid {self.COLORS['input_border']};
            color: {self.COLORS['text_primary']};
            padding: 8px;
            border-radius: 6px;
            selection-background-color: {self.COLORS['poe2_gold']};
            selection-color: {self.COLORS['background_primary']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {self.COLORS['input_border_focus']};
        }}
        
        /* 下拉框样式 */
        QComboBox {{
            background-color: {self.COLORS['input_background']};
            border: 1px solid {self.COLORS['input_border']};
            color: {self.COLORS['text_primary']};
            padding: 8px 12px;
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            border-color: {self.COLORS['border_hover']};
        }}
        
        QComboBox:focus {{
            border-color: {self.COLORS['input_border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border: 4px solid transparent;
            border-top: 6px solid {self.COLORS['text_primary']};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {self.COLORS['background_secondary']};
            border: 1px solid {self.COLORS['border_primary']};
            selection-background-color: {self.COLORS['button_primary_hover']};
            outline: none;
        }}
        
        /* 标签页样式 */
        QTabWidget::pane {{
            border: 1px solid {self.COLORS['border_primary']};
            background-color: {self.COLORS['background_primary']};
        }}
        
        QTabBar::tab {{
            background-color: {self.COLORS['background_secondary']};
            border: 1px solid {self.COLORS['border_primary']};
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.COLORS['background_primary']};
            border-bottom-color: {self.COLORS['background_primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {self.COLORS['button_primary_hover']};
        }}
        
        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {self.COLORS['scrollbar_background']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.COLORS['scrollbar_handle']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.COLORS['scrollbar_handle_hover']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {self.COLORS['scrollbar_background']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {self.COLORS['scrollbar_handle']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {self.COLORS['scrollbar_handle_hover']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* 分割器样式 */
        QSplitter::handle {{
            background-color: {self.COLORS['border_primary']};
        }}
        
        QSplitter::handle:vertical {{
            height: 3px;
        }}
        
        QSplitter::handle:horizontal {{
            width: 3px;
        }}
        
        /* 进度条样式 */
        QProgressBar {{
            background-color: {self.COLORS['background_secondary']};
            border: 1px solid {self.COLORS['border_primary']};
            border-radius: 6px;
            text-align: center;
            color: {self.COLORS['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {self.COLORS['poe2_gold']};
            border-radius: 5px;
        }}
        
        /* 分组框样式 */
        QGroupBox {{
            font-weight: 600;
            border: 1px solid {self.COLORS['border_primary']};
            border-radius: 6px;
            margin: 8px 0px;
            padding-top: 16px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {self.COLORS['text_highlight']};
        }}
        
        /* 列表和树视图样式 */
        QListView, QTreeView {{
            background-color: {self.COLORS['background_secondary']};
            border: 1px solid {self.COLORS['border_primary']};
            selection-background-color: {self.COLORS['poe2_gold']};
            selection-color: {self.COLORS['background_primary']};
            outline: none;
            border-radius: 6px;
        }}
        
        QListView::item, QTreeView::item {{
            padding: 4px;
            border-radius: 3px;
        }}
        
        QListView::item:hover, QTreeView::item:hover {{
            background-color: {self.COLORS['button_primary_hover']};
        }}
        
        /* 表格样式 */
        QTableView {{
            background-color: {self.COLORS['background_secondary']};
            alternate-background-color: {self.COLORS['background_tertiary']};
            border: 1px solid {self.COLORS['border_primary']};
            selection-background-color: {self.COLORS['poe2_gold']};
            selection-color: {self.COLORS['background_primary']};
            outline: none;
            gridline-color: {self.COLORS['border_primary']};
        }}
        
        QHeaderView::section {{
            background-color: {self.COLORS['background_tertiary']};
            border: none;
            border-right: 1px solid {self.COLORS['border_primary']};
            border-bottom: 1px solid {self.COLORS['border_primary']};
            padding: 8px;
            font-weight: 600;
        }}
        
        /* 工具提示样式 */
        QToolTip {{
            background-color: {self.COLORS['background_quaternary']};
            border: 2px solid {self.COLORS['poe2_gold']};
            color: {self.COLORS['text_primary']};
            padding: 10px 12px;
            border-radius: 8px;
            font-weight: 500;
        }}
        
        /* PoE2专用动画样式 */
        * {{
            selection-background-color: {self.COLORS['poe2_gold']};
            selection-color: {self.COLORS['background_primary']};
        }}
        
        /* 滚动区域样式增强 */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        
        /* 分组框增强样式 */
        QGroupBox[poe2_enhanced="true"] {{
            font-weight: 600;
            border: 2px solid {self.COLORS['poe2_gold']};
            border-radius: 8px;
            margin: 8px 0px;
            padding-top: 16px;
            background-color: {self.COLORS['background_secondary']};
        }}
        
        QGroupBox[poe2_enhanced="true"]::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {self.COLORS['poe2_gold']};
            background-color: {self.COLORS['background_primary']};
        }}
        
        /* 强调框架样式 */
        QFrame[poe2_card="true"] {{
            background-color: {self.COLORS['background_secondary']};
            border: 2px solid {self.COLORS['border_primary']};
            border-radius: 10px;
        }}
        
        QFrame[poe2_card="true"]:hover {{
            border-color: {self.COLORS['poe2_gold']};
            background-color: {self.COLORS['background_tertiary']};
        }}
        
        /* PoE2风格按钮增强 */
        QPushButton[poe2_style="primary"] {{
            background-color: {self.COLORS['background_tertiary']};
            border: 2px solid {self.COLORS['border_primary']};
            color: {self.COLORS['text_primary']};
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            min-height: 24px;
        }}
        
        QPushButton[poe2_style="primary"]:hover {{
            border-color: {self.COLORS['poe2_gold']};
            background-color: {self.COLORS['background_quaternary']};
        }}
        
        QPushButton[poe2_style="primary"]:pressed {{
            background-color: {self.COLORS['background_secondary']};
        }}
        
        QPushButton[poe2_style="accent"] {{
            background-color: {self.COLORS['poe2_gold']};
            border: 2px solid {self.COLORS['poe2_gold']};
            color: {self.COLORS['background_primary']};
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 700;
            min-height: 24px;
        }}
        
        QPushButton[poe2_style="accent"]:hover {{
            background-color: {self.COLORS['glow_gold']};
        }}
        
        QPushButton[poe2_style="accent"]:pressed {{
            background-color: {self.COLORS['poe2_gold']};
        }}
        
        /* PoE2风格输入框 */
        QLineEdit[poe2_enhanced="true"], QTextEdit[poe2_enhanced="true"] {{
            background-color: {self.COLORS['background_secondary']};
            border: 2px solid {self.COLORS['border_primary']};
            color: {self.COLORS['text_primary']};
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 13px;
        }}
        
        QLineEdit[poe2_enhanced="true"]:focus, QTextEdit[poe2_enhanced="true"]:focus {{
            border-color: {self.COLORS['poe2_gold']};
            background-color: {self.COLORS['background_tertiary']};
        }}
        
        /* 进度条增强样式 */
        QProgressBar[poe2_enhanced="true"] {{
            background-color: {self.COLORS['background_secondary']};
            border: 2px solid {self.COLORS['border_primary']};
            border-radius: 8px;
            text-align: center;
            color: {self.COLORS['text_primary']};
            font-weight: 600;
        }}
        
        QProgressBar[poe2_enhanced="true"]::chunk {{
            background-color: {self.COLORS['poe2_gold']};
            border-radius: 6px;
        }}
        """
    
    def get_color(self, color_name: str) -> str:
        """获取特定颜色值"""
        return self.COLORS.get(color_name, '#000000')
    
    def get_status_color(self, status: str) -> str:
        """根据状态获取颜色"""
        status_colors = {
            'success': self.COLORS['success'],
            'warning': self.COLORS['warning'], 
            'error': self.COLORS['error'],
            'info': self.COLORS['info'],
            'healthy': self.COLORS['success'],
            'unhealthy': self.COLORS['error'],
            'offline': self.COLORS['text_disabled'],
        }
        return status_colors.get(status.lower(), self.COLORS['text_primary'])
        
    def get_equipment_quality_color(self, quality: str) -> str:
        """根据装备品质获取颜色"""
        quality_colors = {
            'normal': self.COLORS['poe2_white'],
            'magic': self.COLORS['poe2_blue'],
            'rare': self.COLORS['poe2_gold'],
            'unique': self.COLORS['poe2_orange'],
            'legendary': self.COLORS['poe2_red']
        }
        return quality_colors.get(quality.lower(), self.COLORS['text_primary'])
        
    def get_damage_type_color(self, damage_type: str) -> str:
        """根据伤害类型获取颜色"""
        damage_colors = {
            'physical': self.COLORS['text_primary'],
            'fire': self.COLORS['poe2_red'],
            'cold': self.COLORS['poe2_blue'], 
            'lightning': self.COLORS['poe2_gold'],
            'chaos': self.COLORS['poe2_purple']
        }
        return damage_colors.get(damage_type.lower(), self.COLORS['text_primary'])
        
    def get_resistance_color(self, resistance_value: int) -> str:
        """根据抗性数值获取颜色"""
        if resistance_value >= 75:
            return self.COLORS['success']
        elif resistance_value >= 50:
            return self.COLORS['poe2_green']
        elif resistance_value >= 0:
            return self.COLORS['warning']
        else:
            return self.COLORS['error']
            
    def get_class_color(self, character_class: str) -> str:
        """根据角色职业获取颜色"""
        class_colors = {
            'witch': self.COLORS['poe2_purple'],
            'ranger': self.COLORS['poe2_green'],
            'warrior': self.COLORS['poe2_red'],
            'monk': self.COLORS['poe2_gold'],
            'sorceress': self.COLORS['poe2_blue'],
            'mercenary': self.COLORS['text_primary']
        }
        return class_colors.get(character_class.lower(), self.COLORS['text_primary'])
        
    def get_build_goal_color(self, goal: str) -> str:
        """根据构筑目标获取颜色"""
        goal_colors = {
            'league_start': self.COLORS['poe2_green'],
            'budget_friendly': self.COLORS['success'],
            'clear_speed': self.COLORS['poe2_blue'],
            'boss_killing': self.COLORS['poe2_red'],
            'endgame_content': self.COLORS['poe2_purple']
        }
        return goal_colors.get(goal.lower(), self.COLORS['text_primary'])
        
    def get_popularity_color(self, popularity: int) -> str:
        """根据流行度获取颜色"""
        if popularity >= 80:
            return self.COLORS['success']
        elif popularity >= 60:
            return self.COLORS['poe2_green']
        elif popularity >= 40:
            return self.COLORS['warning']
        else:
            return self.COLORS['error']
            
    def get_price_trend_color(self, trend: str) -> str:
        """根据价格趋势获取颜色"""
        if trend == 'up':
            return self.COLORS['success']
        elif trend == 'down':
            return self.COLORS['error']
        else:
            return self.COLORS['text_secondary']
            
    def get_service_status_color(self, status: str) -> str:
        """根据服务状态获取颜色"""
        status_colors = {
            'healthy': self.COLORS['success'],
            'warning': self.COLORS['warning'],
            'error': self.COLORS['error'],
            'unknown': self.COLORS['text_disabled'],
            'connected': self.COLORS['success'],
            'disconnected': self.COLORS['warning']
        }
        return status_colors.get(status.lower(), self.COLORS['text_disabled'])
        
    def apply_poe2_style_properties(self, widget, style_type: str = "default"):
        """为组件应用PoE2样式属性"""
        style_properties = {
            "enhanced_group": {"poe2_enhanced": "true"},
            "card_frame": {"poe2_card": "true"},
            "primary_button": {"poe2_style": "primary"},
            "accent_button": {"poe2_style": "accent"},
            "enhanced_input": {"poe2_enhanced": "true"},
            "enhanced_progress": {"poe2_enhanced": "true"},
            "enhanced_tab": {"poe2_enhanced": "true"},
            "enhanced_scroll": {"poe2_enhanced": "true"},
            "enhanced_list": {"poe2_enhanced": "true"}
        }
        
        properties = style_properties.get(style_type, {})
        for prop, value in properties.items():
            widget.setProperty(prop, value)
        widget.style().unpolish(widget)
        widget.style().polish(widget)