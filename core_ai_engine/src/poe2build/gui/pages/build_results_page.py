"""
构筑结果展示页面

显示AI生成的构筑推荐结果，包含构筑详情、PoB2数据和导出功能。
"""

from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QTabWidget, QGroupBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..styles.poe2_theme import PoE2Theme


class BuildResultCard(QFrame):
    """构筑结果卡片"""
    
    # 信号定义
    build_selected = pyqtSignal(dict)  # 构筑选择信号
    export_requested = pyqtSignal(dict)  # 导出请求信号
    
    def __init__(self, build_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.build_data = build_data
        self.theme = PoE2Theme()
        
        self._init_ui()
        self._setup_style()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        # 构筑名称
        build_name = self.build_data.get('build_name', '未命名构筑')
        title_label = QLabel(build_name)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        title_layout.addWidget(title_label)
        
        # RAG置信度
        confidence = self.build_data.get('rag_confidence', 0.0)
        confidence_label = QLabel(f"置信度: {confidence:.1%}")
        confidence_color = self._get_confidence_color(confidence)
        confidence_label.setStyleSheet(f"color: {confidence_color}; font-weight: 500;")
        title_layout.addWidget(confidence_label)
        
        layout.addLayout(title_layout)
        
        # 构筑基本信息
        info_layout = QGridLayout()
        
        class_name = self.build_data.get('character_class', '未知')
        ascendancy = self.build_data.get('ascendancy', '未指定')
        level = self.build_data.get('level', 'N/A')
        
        info_layout.addWidget(QLabel("职业:"), 0, 0)
        info_layout.addWidget(QLabel(class_name), 0, 1)
        info_layout.addWidget(QLabel("专精:"), 0, 2)
        info_layout.addWidget(QLabel(ascendancy), 0, 3)
        info_layout.addWidget(QLabel("等级:"), 1, 0)
        info_layout.addWidget(QLabel(str(level)), 1, 1)
        
        layout.addLayout(info_layout)
        
        # PoB2数据区域
        if 'pob2_stats' in self.build_data:
            self._add_pob2_stats(layout)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        view_button = QPushButton("查看详情")
        view_button.clicked.connect(lambda: self.build_selected.emit(self.build_data))
        button_layout.addWidget(view_button)
        
        export_button = QPushButton("导出到PoB2")
        export_button.setProperty("accent", True)
        export_button.clicked.connect(lambda: self.export_requested.emit(self.build_data))
        button_layout.addWidget(export_button)
        
        layout.addLayout(button_layout)
    
    def _add_pob2_stats(self, layout: QVBoxLayout):
        """添加PoB2统计数据"""
        pob2_stats = self.build_data['pob2_stats']
        
        # 统计数据网格
        stats_layout = QGridLayout()
        
        # DPS
        total_dps = pob2_stats.get('total_dps', 0)
        stats_layout.addWidget(QLabel("总DPS:"), 0, 0)
        stats_layout.addWidget(QLabel(f"{total_dps:,}"), 0, 1)
        
        # 有效血量池
        ehp = pob2_stats.get('effective_health_pool', 0)
        stats_layout.addWidget(QLabel("有效血量:"), 0, 2)
        stats_layout.addWidget(QLabel(f"{ehp:,}"), 0, 3)
        
        # 抗性
        resistances = pob2_stats.get('resistances', {})
        if resistances:
            fire_res = resistances.get('fire', 0)
            cold_res = resistances.get('cold', 0)
            lightning_res = resistances.get('lightning', 0)
            
            stats_layout.addWidget(QLabel("抗性:"), 1, 0)
            stats_layout.addWidget(QLabel(f"火: {fire_res}%"), 1, 1)
            stats_layout.addWidget(QLabel(f"冰: {cold_res}%"), 1, 2)
            stats_layout.addWidget(QLabel(f"电: {lightning_res}%"), 1, 3)
        
        layout.addLayout(stats_layout)
    
    def _get_confidence_color(self, confidence: float) -> str:
        """根据置信度获取颜色"""
        if confidence >= 0.8:
            return self.theme.get_color('success')
        elif confidence >= 0.6:
            return self.theme.get_color('warning')
        else:
            return self.theme.get_color('error')
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            BuildResultCard {{
                background-color: {self.theme.get_color('background_secondary')};
                border: 1px solid {self.theme.get_color('border_primary')};
                border-radius: 8px;
                margin: 4px;
            }}
            
            BuildResultCard:hover {{
                border-color: {self.theme.get_color('poe2_gold')};
            }}
        """)


class BuildResultsPage(QWidget):
    """构筑结果展示页面类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.theme = PoE2Theme()
        self.current_results: Dict[str, Any] = {}
        self.selected_build: Dict[str, Any] = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 页面标题
        title_label = QLabel("构筑推荐结果")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_highlight')};
                font-size: 24px;
                font-weight: 600;
                padding-bottom: 12px;
                border-bottom: 2px solid {self.theme.get_color('poe2_gold')};
            }}
        """)
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：构筑列表
        self._create_results_list(splitter)
        
        # 右侧：构筑详情
        self._create_build_details(splitter)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 初始显示空状态
        self._show_empty_state()
    
    def _create_results_list(self, parent):
        """创建结果列表区域"""
        # 左侧容器
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        
        # 列表标题
        list_title = QLabel("AI推荐构筑")
        list_title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0;
            }}
        """)
        left_layout.addWidget(list_title)
        
        # 滚动区域
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 结果容器
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_scroll.setWidget(self.results_container)
        
        left_layout.addWidget(self.results_scroll)
        parent.addWidget(left_widget)
    
    def _create_build_details(self, parent):
        """创建构筑详情区域"""
        # 右侧容器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(12)
        
        # 详情标题
        details_title = QLabel("构筑详情")
        details_title.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_primary')};
                font-size: 16px;
                font-weight: 600;
                padding: 8px 0;
            }}
        """)
        right_layout.addWidget(details_title)
        
        # 标签页容器
        self.details_tabs = QTabWidget()
        
        # 概览标签页
        self.overview_tab = self._create_overview_tab()
        self.details_tabs.addTab(self.overview_tab, "概览")
        
        # 技能标签页
        self.skills_tab = self._create_skills_tab()
        self.details_tabs.addTab(self.skills_tab, "技能")
        
        # 装备标签页
        self.equipment_tab = self._create_equipment_tab()
        self.details_tabs.addTab(self.equipment_tab, "装备")
        
        # PoB2数据标签页
        self.pob2_tab = self._create_pob2_tab()
        self.details_tabs.addTab(self.pob2_tab, "PoB2数据")
        
        right_layout.addWidget(self.details_tabs)
        
        # 操作按钮区域
        self._create_detail_actions(right_layout)
        
        parent.addWidget(right_widget)
    
    def _create_overview_tab(self) -> QWidget:
        """创建概览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.overview_content = QLabel("请选择一个构筑以查看详情")
        self.overview_content.setWordWrap(True)
        self.overview_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.overview_content.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_secondary')};
                padding: 16px;
                background-color: {self.theme.get_color('background_secondary')};
                border-radius: 6px;
            }}
        """)
        
        layout.addWidget(self.overview_content)
        return widget
    
    def _create_skills_tab(self) -> QWidget:
        """创建技能标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.skills_tree = QTreeWidget()
        self.skills_tree.setHeaderLabels(["技能", "等级", "品质"])
        
        layout.addWidget(self.skills_tree)
        return widget
    
    def _create_equipment_tab(self) -> QWidget:
        """创建装备标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.equipment_tree = QTreeWidget()
        self.equipment_tree.setHeaderLabels(["部位", "装备", "主要属性"])
        
        layout.addWidget(self.equipment_tree)
        return widget
    
    def _create_pob2_tab(self) -> QWidget:
        """创建PoB2数据标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PoB2导入代码
        self.pob2_code = QTextEdit()
        self.pob2_code.setReadOnly(True)
        self.pob2_code.setMaximumHeight(100)
        
        # 复制按钮
        copy_button = QPushButton("复制PoB2代码")
        copy_button.clicked.connect(self._copy_pob2_code)
        
        layout.addWidget(QLabel("PoB2导入代码:"))
        layout.addWidget(self.pob2_code)
        layout.addWidget(copy_button)
        
        # 详细统计
        self.pob2_stats_tree = QTreeWidget()
        self.pob2_stats_tree.setHeaderLabels(["属性", "数值"])
        
        layout.addWidget(QLabel("详细统计:"))
        layout.addWidget(self.pob2_stats_tree)
        
        return widget
    
    def _create_detail_actions(self, layout: QVBoxLayout):
        """创建详情操作按钮"""
        button_layout = QHBoxLayout()
        
        # 导出按钮
        export_button = QPushButton("导出到PoB2")
        export_button.setProperty("accent", True)
        export_button.clicked.connect(self._export_current_build)
        button_layout.addWidget(export_button)
        
        # 保存按钮
        save_button = QPushButton("保存构筑")
        save_button.clicked.connect(self._save_current_build)
        button_layout.addWidget(save_button)
        
        # 分享按钮
        share_button = QPushButton("分享构筑")
        share_button.clicked.connect(self._share_current_build)
        button_layout.addWidget(share_button)
        
        layout.addLayout(button_layout)
    
    def display_build_results(self, results_data: Dict[str, Any]):
        """显示构筑结果"""
        self.current_results = results_data
        
        # 清空现有结果
        self._clear_results()
        
        # 显示新结果
        recommendations = results_data.get('recommendations', [])
        
        if not recommendations:
            self._show_empty_state()
            return
        
        # 添加构筑卡片
        for i, build in enumerate(recommendations):
            card = BuildResultCard(build)
            card.build_selected.connect(self._on_build_selected)
            card.export_requested.connect(self._export_build)
            self.results_layout.addWidget(card)
        
        # 自动选择第一个构筑
        if recommendations:
            self._on_build_selected(recommendations[0])
    
    def _clear_results(self):
        """清空结果显示"""
        # 移除所有卡片
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _show_empty_state(self):
        """显示空状态"""
        empty_label = QLabel("暂无构筑结果\\n\\n请先在构筑生成器页面生成AI推荐")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.get_color('text_disabled')};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        self.results_layout.addWidget(empty_label)
    
    def _on_build_selected(self, build_data: Dict[str, Any]):
        """处理构筑选择"""
        self.selected_build = build_data
        self._update_build_details(build_data)
    
    def _update_build_details(self, build_data: Dict[str, Any]):
        """更新构筑详情显示"""
        # 更新概览
        overview_text = self._generate_overview_text(build_data)
        self.overview_content.setText(overview_text)
        
        # 更新技能树
        self._update_skills_display(build_data)
        
        # 更新装备
        self._update_equipment_display(build_data)
        
        # 更新PoB2数据
        self._update_pob2_display(build_data)
    
    def _generate_overview_text(self, build_data: Dict[str, Any]) -> str:
        """生成概览文本"""
        name = build_data.get('build_name', '未命名构筑')
        class_name = build_data.get('character_class', '未知')
        ascendancy = build_data.get('ascendancy', '未指定')
        description = build_data.get('description', '无描述')
        
        return f"""
        <h2>{name}</h2>
        <p><b>职业:</b> {class_name}</p>
        <p><b>专精:</b> {ascendancy}</p>
        <p><b>描述:</b></p>
        <p>{description}</p>
        """
    
    def _update_skills_display(self, build_data: Dict[str, Any]):
        """更新技能显示"""
        self.skills_tree.clear()
        
        skills = build_data.get('skills', {})
        
        # 主技能组
        if 'main_skills' in skills:
            main_item = QTreeWidgetItem(self.skills_tree, ["主技能"])
            for skill in skills['main_skills']:
                skill_item = QTreeWidgetItem(main_item, [
                    skill.get('name', ''),
                    str(skill.get('level', '')),
                    str(skill.get('quality', ''))
                ])
        
        # 辅助技能
        if 'support_skills' in skills:
            support_item = QTreeWidgetItem(self.skills_tree, ["辅助技能"])
            for skill in skills['support_skills']:
                skill_item = QTreeWidgetItem(support_item, [
                    skill.get('name', ''),
                    str(skill.get('level', '')),
                    str(skill.get('quality', ''))
                ])
        
        self.skills_tree.expandAll()
    
    def _update_equipment_display(self, build_data: Dict[str, Any]):
        """更新装备显示"""
        self.equipment_tree.clear()
        
        equipment = build_data.get('equipment', {})
        
        for slot, item in equipment.items():
            if item:
                main_stats = ', '.join(item.get('main_stats', []))
                QTreeWidgetItem(self.equipment_tree, [
                    slot,
                    item.get('name', ''),
                    main_stats
                ])
    
    def _update_pob2_display(self, build_data: Dict[str, Any]):
        """更新PoB2数据显示"""
        # 更新导入代码
        pob2_data = build_data.get('pob2_data', {})
        import_codes = pob2_data.get('import_codes', [])
        
        if import_codes:
            self.pob2_code.setText(import_codes[0])
        else:
            self.pob2_code.setText("无PoB2导入代码")
        
        # 更新统计树
        self.pob2_stats_tree.clear()
        
        if 'calculated_stats' in pob2_data:
            stats = pob2_data['calculated_stats']
            for key, value in stats.items():
                QTreeWidgetItem(self.pob2_stats_tree, [
                    key.replace('_', ' ').title(),
                    str(value)
                ])
    
    def _copy_pob2_code(self):
        """复制PoB2代码"""
        # TODO: 实现复制功能
        pass
    
    def _export_current_build(self):
        """导出当前构筑"""
        if self.selected_build:
            self._export_build(self.selected_build)
    
    def _export_build(self, build_data: Dict[str, Any]):
        """导出构筑"""
        # TODO: 实现导出功能
        print(f"导出构筑: {build_data.get('build_name')}")
    
    def _save_current_build(self):
        """保存当前构筑"""
        # TODO: 实现保存功能
        pass
    
    def _share_current_build(self):
        """分享当前构筑"""
        # TODO: 实现分享功能
        pass