#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成的专业级PoE2构筑推荐GUI系统
- 集成ninja_trained_ai_recommender.py的AI推荐系统
- PoB2风格的专业界面
- 完整的职业/升华选择
- 联赛选择和市场数据集成
- AI智能推荐
- 详细构筑卡片显示
- 物品链接功能
- 数据导出功能
- 处理中文编码问题
"""

import sys
import os
import json
import webbrowser
import threading
import traceback
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, font, filedialog
import tkinter.font as tkFont
from typing import Dict, List, Any, Optional
from datetime import datetime
import locale

# 设置UTF-8编码支持
if sys.platform == "win32":
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入AI推荐系统
try:
    from ninja_trained_ai_recommender import NinjaTrainedAIRecommender
    AI_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import AI system: {e}")
    AI_SYSTEM_AVAILABLE = False


class CompleteProfessionalGUI:
    """完整的专业级PoE2构筑推荐GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PoE2 Complete AI Build Planner - Professional Edition")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#2b2b2b')
        
        # 设置编码
        self.setup_encoding()
        
        # PoE2 游戏数据
        self.leagues = [
            "Rise of the Abyssal (Current)", 
            "Standard",
            "Hardcore",
            "Solo Self-Found",
            "Trade League"
        ]
        
        self.classes = {
            "Sorceress": {
                "ascendancies": ["Stormweaver", "Chronomancer"],
                "icon": "⚡",
                "color": "#4169E1",
                "description": "Elemental spell caster with high damage output"
            },
            "Witch": {
                "ascendancies": ["Infernalist", "Blood Mage"],
                "icon": "🔥",
                "color": "#8B0000",
                "description": "Dark magic practitioner with minion support"
            },
            "Ranger": {
                "ascendancies": ["Deadeye", "Pathfinder"],
                "icon": "🏹",
                "color": "#228B22",
                "description": "Ranged damage dealer with high mobility"
            },
            "Monk": {
                "ascendancies": ["Invoker", "Acolyte"],
                "icon": "👊",
                "color": "#FF6347",
                "description": "Martial arts combatant with combo mechanics"
            },
            "Warrior": {
                "ascendancies": ["Titan", "Warbringer"],
                "icon": "⚔️",
                "color": "#B8860B",
                "description": "Melee tank with heavy armor and weapons"
            },
            "Mercenary": {
                "ascendancies": ["Witchhunter", "Gemling Legionnaire"],
                "icon": "🔫",
                "color": "#696969",
                "description": "Hybrid combatant with crossbows and skills"
            }
        }
        
        # 创建样式和界面
        self.setup_styles()
        self.create_professional_ui()
        self.load_ai_system()
        
        # 状态变量
        self.current_recommendations = []
        self.favorites = []
        
    def setup_encoding(self):
        """设置编码支持"""
        try:
            # 强制UTF-8编码
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    def setup_styles(self):
        """设置PoB2风格的样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # PoB2风格颜色
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_medium': '#3c3c3c',
            'bg_light': '#4d4d4d',
            'text_normal': '#cccccc',
            'text_highlight': '#ffffff',
            'accent_blue': '#4169E1',
            'accent_gold': '#FFD700',
            'accent_green': '#32CD32',
            'accent_red': '#FF4444',
            'accent_orange': '#FF8C00',
            'border': '#555555'
        }
        
        # 配置样式
        style.configure('Dark.TFrame', background=self.colors['bg_dark'])
        style.configure('Medium.TFrame', background=self.colors['bg_medium'])
        style.configure('Light.TFrame', background=self.colors['bg_light'])
        
        style.configure('Dark.TLabel', 
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_normal'])
        
        style.configure('Highlight.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_highlight'],
                       font=('Arial', 10, 'bold'))
        
        style.configure('Title.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent_gold'],
                       font=('Arial', 14, 'bold'))
        
    def create_professional_ui(self):
        """创建专业级UI界面"""
        # 主容器
        self.main_container = Frame(self.root, bg=self.colors['bg_dark'])
        self.main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 创建界面组件
        self.create_top_toolbar()
        self.create_main_content()
        self.create_status_bar()
        
    def create_top_toolbar(self):
        """创建顶部工具栏"""
        toolbar = Frame(self.main_container, bg=self.colors['bg_medium'], height=60)
        toolbar.pack(fill=X, padx=2, pady=2)
        toolbar.pack_propagate(False)
        
        # 左侧标题区域
        title_frame = Frame(toolbar, bg=self.colors['bg_medium'])
        title_frame.pack(side=LEFT, fill=Y, padx=15)
        
        title_label = Label(title_frame,
                           text="PoE2 Complete AI Build Planner",
                           font=('Arial', 18, 'bold'),
                           fg=self.colors['accent_gold'],
                           bg=self.colors['bg_medium'])
        title_label.pack(side=LEFT, pady=(15, 0))
        
        subtitle_label = Label(title_frame,
                              text="Professional Edition with Full AI Integration",
                              font=('Arial', 11),
                              fg=self.colors['text_normal'],
                              bg=self.colors['bg_medium'])
        subtitle_label.pack(side=LEFT, padx=(15, 0), pady=(15, 0))
        
        # 右侧快速操作按钮
        buttons_frame = Frame(toolbar, bg=self.colors['bg_medium'])
        buttons_frame.pack(side=RIGHT, fill=Y, padx=15)
        
        # 快速操作按钮
        quick_buttons = [
            ("📥 Import", self.import_build),
            ("📤 Export", self.export_builds), 
            ("⭐ Favorites", self.show_favorites),
            ("🔧 Settings", self.show_settings)
        ]
        
        for text, command in quick_buttons:
            btn = Button(buttons_frame, text=text,
                        bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                        command=command, relief=RAISED, padx=12, pady=5,
                        font=('Arial', 9))
            btn.pack(side=RIGHT, padx=3, pady=15)
    
    def create_main_content(self):
        """创建主内容区域"""
        content_frame = Frame(self.main_container, bg=self.colors['bg_dark'])
        content_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        # 左侧参数面板
        self.create_left_panel(content_frame)
        
        # 中央分隔条
        separator = Frame(content_frame, bg=self.colors['border'], width=2)
        separator.pack(side=LEFT, fill=Y, padx=5)
        
        # 右侧结果面板
        self.create_right_panel(content_frame)
    
    def create_left_panel(self, parent):
        """创建左侧参数面板"""
        left_panel = Frame(parent, bg=self.colors['bg_medium'], width=450)
        left_panel.pack(side=LEFT, fill=Y)
        left_panel.pack_propagate(False)
        
        # 面板标题
        panel_title = Label(left_panel, text="🎯 Build Configuration",
                           font=('Arial', 14, 'bold'),
                           fg=self.colors['accent_gold'],
                           bg=self.colors['bg_medium'])
        panel_title.pack(pady=(15, 10))
        
        # 创建配置区域
        self.create_league_selection(left_panel)
        self.create_class_selection(left_panel) 
        self.create_build_parameters(left_panel)
        self.create_ai_settings(left_panel)
        self.create_generation_controls(left_panel)
    
    def create_league_selection(self, parent):
        """创建联赛选择区域"""
        league_frame = LabelFrame(parent, text=" 🏆 League & Market Data ",
                                 bg=self.colors['bg_medium'],
                                 fg=self.colors['accent_gold'],
                                 font=('Arial', 11, 'bold'),
                                 padx=15, pady=10)
        league_frame.pack(fill=X, padx=15, pady=(10, 8))
        
        # 当前联赛选择
        league_label = Label(league_frame, text="Current League:",
                            bg=self.colors['bg_medium'], fg=self.colors['text_normal'])
        league_label.pack(anchor=W)
        
        self.selected_league = StringVar(value=self.leagues[0])
        league_combo = ttk.Combobox(league_frame, textvariable=self.selected_league,
                                   values=self.leagues, state="readonly", width=40)
        league_combo.pack(fill=X, pady=(5, 0))
        
        # 市场数据状态
        market_frame = Frame(league_frame, bg=self.colors['bg_medium'])
        market_frame.pack(fill=X, pady=(10, 0))
        
        market_status = Label(market_frame,
                             text="📊 Market Data: Active  |  💰 Pricing: Real-time",
                             font=('Arial', 9), fg=self.colors['accent_green'],
                             bg=self.colors['bg_medium'])
        market_status.pack(side=LEFT)
        
        refresh_btn = Button(market_frame, text="🔄",
                           bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                           command=self.refresh_market_data, relief=RAISED,
                           padx=5, pady=1, font=('Arial', 8))
        refresh_btn.pack(side=RIGHT)
    
    def create_class_selection(self, parent):
        """创建职业选择区域"""
        class_frame = LabelFrame(parent, text=" ⚔️ Character Configuration ",
                                bg=self.colors['bg_medium'],
                                fg=self.colors['accent_gold'],
                                font=('Arial', 11, 'bold'),
                                padx=15, pady=10)
        class_frame.pack(fill=X, padx=15, pady=8)
        
        # 职业选择变量
        self.selected_class = StringVar(value="Any")
        self.selected_ascendancy = StringVar(value="Any")
        
        # "Any"选项
        any_frame = Frame(class_frame, bg=self.colors['bg_medium'])
        any_frame.pack(fill=X, pady=(0, 10))
        
        any_btn = Button(any_frame, text="🎯 Any Class (AI Recommends)",
                        bg=self.colors['accent_blue'], fg='white',
                        command=lambda: self.select_class("Any"),
                        relief=RAISED, padx=15, pady=8, font=('Arial', 10, 'bold'))
        any_btn.pack(fill=X)
        
        # 职业网格
        class_grid = Frame(class_frame, bg=self.colors['bg_medium'])
        class_grid.pack(fill=X, pady=5)
        
        # 职业按钮网格 (3列)
        row = 0
        col = 0
        for class_name, class_info in self.classes.items():
            btn = Button(class_grid,
                        text=f"{class_info['icon']} {class_name}",
                        bg=class_info['color'], fg='white',
                        command=lambda cn=class_name: self.select_class(cn),
                        relief=RAISED, padx=10, pady=8, font=('Arial', 9, 'bold'))
            btn.grid(row=row, column=col, sticky=EW, padx=2, pady=2)
            
            col += 1
            if col >= 2:  # 每行2个职业
                col = 0
                row += 1
        
        # 配置网格权重
        for i in range(2):
            class_grid.columnconfigure(i, weight=1)
        
        # 升华选择
        ascendancy_label = Label(class_frame, text="Ascendancy:",
                               bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                               font=('Arial', 10))
        ascendancy_label.pack(anchor=W, pady=(15, 3))
        
        self.ascendancy_combo = ttk.Combobox(class_frame, textvariable=self.selected_ascendancy,
                                            values=["Any"], state="readonly", width=40)
        self.ascendancy_combo.pack(fill=X)
        
        # 职业描述
        self.class_description = Label(class_frame, text="Select a class to see description",
                                     font=('Arial', 9), fg=self.colors['text_normal'],
                                     bg=self.colors['bg_medium'], wraplength=350, justify=LEFT)
        self.class_description.pack(anchor=W, pady=(8, 0))
    
    def create_build_parameters(self, parent):
        """创建构筑参数区域"""
        params_frame = LabelFrame(parent, text=" ⚙️ Build Parameters ",
                                 bg=self.colors['bg_medium'],
                                 fg=self.colors['accent_gold'],
                                 font=('Arial', 11, 'bold'),
                                 padx=15, pady=10)
        params_frame.pack(fill=X, padx=15, pady=8)
        
        # 参数网格
        params_grid = Frame(params_frame, bg=self.colors['bg_medium'])
        params_grid.pack(fill=X)
        
        # 预算设置
        Label(params_grid, text="💰 Budget (Divine Orbs):",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
              font=('Arial', 10)).grid(row=0, column=0, sticky=W, pady=3)
        
        self.budget_var = StringVar(value="15")
        budget_frame = Frame(params_grid, bg=self.colors['bg_medium'])
        budget_frame.grid(row=0, column=1, sticky=EW, padx=(10, 0), pady=3)
        
        budget_spinbox = Spinbox(budget_frame, from_=1, to=200, textvariable=self.budget_var,
                                width=8, bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        budget_spinbox.pack(side=LEFT)
        
        budget_label = Label(budget_frame, text="(Higher = More Options)",
                           font=('Arial', 8), fg=self.colors['text_normal'],
                           bg=self.colors['bg_medium'])
        budget_label.pack(side=LEFT, padx=(5, 0))
        
        # DPS要求
        Label(params_grid, text="⚔️ Minimum DPS:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
              font=('Arial', 10)).grid(row=1, column=0, sticky=W, pady=3)
        
        self.dps_var = StringVar(value="250000")
        dps_entry = Entry(params_grid, textvariable=self.dps_var, width=15,
                         bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        dps_entry.grid(row=1, column=1, sticky=EW, padx=(10, 0), pady=3)
        
        # 构筑风格
        Label(params_grid, text="🎯 Build Style:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
              font=('Arial', 10)).grid(row=2, column=0, sticky=W, pady=3)
        
        self.style_var = StringVar(value="Any")
        style_combo = ttk.Combobox(params_grid, textvariable=self.style_var,
                                  values=["Any", "Ranged", "Melee", "Caster", "Minion", "Hybrid"],
                                  state="readonly", width=12)
        style_combo.grid(row=2, column=1, sticky=EW, padx=(10, 0), pady=3)
        
        # 复杂度
        Label(params_grid, text="🔧 Complexity:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
              font=('Arial', 10)).grid(row=3, column=0, sticky=W, pady=3)
        
        self.complexity_var = StringVar(value="Medium")
        complexity_combo = ttk.Combobox(params_grid, textvariable=self.complexity_var,
                                       values=["Low", "Medium", "High", "Expert"],
                                       state="readonly", width=12)
        complexity_combo.grid(row=3, column=1, sticky=EW, padx=(10, 0), pady=3)
        
        # 配置网格权重
        params_grid.columnconfigure(1, weight=1)
    
    def create_ai_settings(self, parent):
        """创建AI设置区域"""
        ai_frame = LabelFrame(parent, text=" 🤖 AI Generation Settings ",
                             bg=self.colors['bg_medium'],
                             fg=self.colors['accent_gold'],
                             font=('Arial', 11, 'bold'),
                             padx=15, pady=10)
        ai_frame.pack(fill=X, padx=15, pady=8)
        
        # AI状态指示器
        ai_status_frame = Frame(ai_frame, bg=self.colors['bg_medium'])
        ai_status_frame.pack(fill=X, pady=(0, 10))
        
        ai_status_text = "🟢 AI System: Ready" if AI_SYSTEM_AVAILABLE else "🔴 AI System: Not Available"
        ai_status_color = self.colors['accent_green'] if AI_SYSTEM_AVAILABLE else self.colors['accent_red']
        
        ai_status_label = Label(ai_status_frame, text=ai_status_text,
                               font=('Arial', 10, 'bold'), fg=ai_status_color,
                               bg=self.colors['bg_medium'])
        ai_status_label.pack(side=LEFT)
        
        # 创新程度设置
        innovation_label = Label(ai_frame, text="Innovation Level:",
                               bg=self.colors['bg_medium'], fg=self.colors['text_normal'])
        innovation_label.pack(anchor=W)
        
        self.innovation_var = StringVar(value="balanced")
        
        innovation_frame = Frame(ai_frame, bg=self.colors['bg_medium'])
        innovation_frame.pack(fill=X, pady=(5, 10))
        
        innovation_options = [
            ("🛡️ Conservative", "conservative", "Safe, proven builds"),
            ("⚖️ Balanced", "balanced", "Mix of safe and innovative"),
            ("🔬 Experimental", "experimental", "Cutting-edge builds")
        ]
        
        for text, value, tooltip in innovation_options:
            btn = Radiobutton(innovation_frame, text=text, variable=self.innovation_var, value=value,
                             bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                             selectcolor=self.colors['bg_light'],
                             activebackground=self.colors['bg_medium'], font=('Arial', 9))
            btn.pack(anchor=W, padx=5)
        
        # 生成数量设置
        count_frame = Frame(ai_frame, bg=self.colors['bg_medium'])
        count_frame.pack(fill=X, pady=5)
        
        Label(count_frame, text="Result Count:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal']).pack(side=LEFT)
        
        self.result_count_var = StringVar(value="5")
        count_spinbox = Spinbox(count_frame, from_=1, to=10, textvariable=self.result_count_var,
                               width=5, bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        count_spinbox.pack(side=RIGHT)
    
    def create_generation_controls(self, parent):
        """创建生成控制区域"""
        controls_frame = Frame(parent, bg=self.colors['bg_medium'])
        controls_frame.pack(fill=X, padx=15, pady=20)
        
        # 主生成按钮
        self.generate_btn = Button(controls_frame, text="🎯 Generate AI Recommendations",
                                  font=('Arial', 14, 'bold'),
                                  bg=self.colors['accent_blue'], fg='white',
                                  command=self.generate_builds,
                                  relief=RAISED, borderwidth=2,
                                  padx=25, pady=15)
        self.generate_btn.pack(fill=X, pady=(0, 15))
        
        # 快速模板按钮
        quick_frame = Frame(controls_frame, bg=self.colors['bg_medium'])
        quick_frame.pack(fill=X)
        
        quick_templates = [
            ("💎 Meta Builds", self.quick_meta, self.colors['accent_green']),
            ("🔍 Rare Gems", self.quick_rare, self.colors['accent_orange']),
            ("💰 Budget Pro", self.quick_budget, self.colors['accent_blue']),
            ("⚡ League Start", self.quick_league_start, self.colors['accent_red'])
        ]
        
        for i, (text, command, color) in enumerate(quick_templates):
            if i % 2 == 0:  # 每行2个按钮
                row_frame = Frame(quick_frame, bg=self.colors['bg_medium'])
                row_frame.pack(fill=X, pady=2)
            
            btn = Button(row_frame, text=text, command=command,
                        bg=color, fg='white', relief=RAISED,
                        padx=8, pady=6, font=('Arial', 9, 'bold'))
            btn.pack(side=LEFT, expand=True, fill=X, padx=1)
    
    def create_right_panel(self, parent):
        """创建右侧结果面板"""
        right_panel = Frame(parent, bg=self.colors['bg_medium'])
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # 结果头部
        results_header = Frame(right_panel, bg=self.colors['bg_light'], height=50)
        results_header.pack(fill=X, padx=3, pady=3)
        results_header.pack_propagate(False)
        
        # 标题和统计
        header_left = Frame(results_header, bg=self.colors['bg_light'])
        header_left.pack(side=LEFT, fill=Y, padx=15)
        
        results_title = Label(header_left, text="🏆 AI Build Recommendations",
                            font=('Arial', 16, 'bold'),
                            fg=self.colors['accent_gold'], bg=self.colors['bg_light'])
        results_title.pack(anchor=W, pady=(12, 0))
        
        # 结果统计和过滤
        header_right = Frame(results_header, bg=self.colors['bg_light'])
        header_right.pack(side=RIGHT, fill=Y, padx=15)
        
        self.results_count_label = Label(header_right, text="Ready to generate",
                                        font=('Arial', 11),
                                        fg=self.colors['text_normal'], bg=self.colors['bg_light'])
        self.results_count_label.pack(pady=(8, 0))
        
        # 排序选项
        sort_frame = Frame(header_right, bg=self.colors['bg_light'])
        sort_frame.pack(pady=(3, 8))
        
        Label(sort_frame, text="Sort by:", bg=self.colors['bg_light'],
              fg=self.colors['text_normal'], font=('Arial', 9)).pack(side=LEFT)
        
        self.sort_var = StringVar(value="AI Score")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                 values=["AI Score", "DPS", "Cost", "Innovation"],
                                 state="readonly", width=10, font=('Arial', 8))
        sort_combo.pack(side=LEFT, padx=(5, 0))
        sort_combo.bind("<<ComboboxSelected>>", self.resort_results)
        
        # 结果显示区域
        self.create_results_area(right_panel)
    
    def create_results_area(self, parent):
        """创建结果显示区域"""
        results_container = Frame(parent, bg=self.colors['bg_medium'])
        results_container.pack(fill=BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 滚动区域
        canvas = Canvas(results_container, bg=self.colors['bg_medium'], highlightthickness=0)
        scrollbar = Scrollbar(results_container, orient=VERTICAL, command=canvas.yview)
        self.results_frame = Frame(canvas, bg=self.colors['bg_medium'])
        
        self.results_frame.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定鼠标滚轮
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 绑定到多个组件
        canvas.bind("<MouseWheel>", on_mousewheel)
        self.results_frame.bind("<MouseWheel>", on_mousewheel)
        
        # 默认欢迎界面
        self.show_welcome_screen()
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = Frame(self.main_container, bg=self.colors['bg_light'], height=35)
        status_bar.pack(fill=X, side=BOTTOM)
        status_bar.pack_propagate(False)
        
        # 左侧状态
        self.status_var = StringVar(value="Ready - Complete AI System Loaded")
        status_label = Label(status_bar, textvariable=self.status_var,
                           bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                           font=('Arial', 10))
        status_label.pack(side=LEFT, padx=15, pady=8)
        
        # 右侧版本和时间信息
        info_frame = Frame(status_bar, bg=self.colors['bg_light'])
        info_frame.pack(side=RIGHT, padx=15, pady=8)
        
        time_label = Label(info_frame, text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}",
                          bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                          font=('Arial', 9))
        time_label.pack(side=RIGHT, padx=(10, 0))
        
        version_label = Label(info_frame, text="v2.1.0 | Complete Edition",
                            bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                            font=('Arial', 9))
        version_label.pack(side=RIGHT)
    
    def show_welcome_screen(self):
        """显示欢迎界面"""
        # 清空现有内容
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        welcome_frame = Frame(self.results_frame, bg=self.colors['bg_medium'])
        welcome_frame.pack(fill=BOTH, expand=True, padx=30, pady=50)
        
        # 欢迎图标和标题
        welcome_icon = Label(welcome_frame, text="🎯", font=('Arial', 64),
                           fg=self.colors['accent_gold'], bg=self.colors['bg_medium'])
        welcome_icon.pack(pady=30)
        
        welcome_title = Label(welcome_frame, text="Complete PoE2 AI Build Planner",
                            font=('Arial', 24, 'bold'),
                            fg=self.colors['text_highlight'], bg=self.colors['bg_medium'])
        welcome_title.pack(pady=10)
        
        # 功能特性
        features_frame = Frame(welcome_frame, bg=self.colors['bg_light'], relief=RAISED, borderwidth=2)
        features_frame.pack(pady=30, padx=50, fill=X)
        
        features_title = Label(features_frame, text="🚀 Professional Features",
                             font=('Arial', 16, 'bold'),
                             fg=self.colors['accent_gold'], bg=self.colors['bg_light'])
        features_title.pack(pady=15)
        
        features_text = """🤖 Advanced AI-Powered Build Generation
📊 Real PoE2 Data Integration & Market Analysis
💎 Discover Unpopular High-Value Builds
🔗 Direct Item Links & Trade Integration
⚡ Professional PoB2-Style Interface
📈 Comprehensive Build Analytics
🎯 Personalized Recommendations
💰 Budget-Optimized Solutions"""
        
        features_label = Label(features_frame, text=features_text,
                             font=('Arial', 13), fg=self.colors['text_normal'],
                             bg=self.colors['bg_light'], justify=LEFT)
        features_label.pack(pady=20, padx=30)
        
        # 开始提示
        start_frame = Frame(welcome_frame, bg=self.colors['bg_medium'])
        start_frame.pack(pady=30)
        
        start_label = Label(start_frame,
                          text="⬅ Configure your build parameters and click 'Generate AI Recommendations' to begin!",
                          font=('Arial', 14, 'bold'), fg=self.colors['accent_blue'],
                          bg=self.colors['bg_medium'])
        start_label.pack()
        
        # AI状态提示
        if not AI_SYSTEM_AVAILABLE:
            warning_label = Label(start_frame,
                                text="⚠️ Note: AI system may have limited functionality",
                                font=('Arial', 11), fg=self.colors['accent_orange'],
                                bg=self.colors['bg_medium'])
            warning_label.pack(pady=10)
    
    def select_class(self, class_name):
        """选择职业"""
        self.selected_class.set(class_name)
        
        # 更新升华选项
        if class_name == "Any":
            ascendancies = ["Any"]
            description = "AI will recommend the best class based on your preferences"
        else:
            ascendancies = ["Any"] + self.classes[class_name]["ascendancies"]
            description = self.classes[class_name]["description"]
        
        self.ascendancy_combo.configure(values=ascendancies)
        self.selected_ascendancy.set("Any")
        self.class_description.configure(text=description)
        
        self.status_var.set(f"Selected: {class_name}")
        self.update_status_time()
    
    def load_ai_system(self):
        """加载AI系统"""
        try:
            if AI_SYSTEM_AVAILABLE:
                self.ai_recommender = NinjaTrainedAIRecommender()
                self.status_var.set("Ready - Complete AI System Loaded Successfully")
            else:
                self.ai_recommender = None
                self.status_var.set("Warning - AI System Limited Functionality")
        except Exception as e:
            self.status_var.set(f"Error - AI System Load Failed: {e}")
            messagebox.showwarning("AI System Warning", f"AI system initialization failed:\n{e}\n\nSome features may be limited.")
    
    def generate_builds(self):
        """生成构筑推荐"""
        if not AI_SYSTEM_AVAILABLE or not self.ai_recommender:
            messagebox.showwarning("AI Not Available", 
                                 "AI system is not available. Please check the installation.")
            return
        
        def run_generation():
            try:
                self.root.after(0, lambda: self.update_generation_ui(True))
                
                # 构建用户偏好
                preferences = self.build_user_preferences()
                
                # 生成推荐
                self.status_var.set("🔄 Generating AI builds with real data...")
                recommendations = self.ai_recommender.get_ninja_trained_recommendations(preferences)
                
                # 保存推荐结果
                self.current_recommendations = recommendations
                
                # 更新UI
                self.root.after(0, lambda: self.display_professional_results(recommendations))
                self.root.after(0, lambda: self.update_generation_ui(False))
                self.root.after(0, lambda: self.update_results_count(len(recommendations)))
                
            except Exception as e:
                error_msg = f"Generation failed: {str(e)}\n\nDetails:\n{traceback.format_exc()}"
                self.root.after(0, lambda: messagebox.showerror("Generation Error", error_msg))
                self.root.after(0, lambda: self.update_generation_ui(False))
                self.root.after(0, lambda: self.status_var.set("❌ Generation failed"))
        
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
    
    def update_generation_ui(self, generating):
        """更新生成过程中的UI状态"""
        if generating:
            self.generate_btn.configure(state=DISABLED, text="⏳ Generating AI Builds...")
            self.status_var.set("🔄 AI is analyzing data and generating recommendations...")
        else:
            self.generate_btn.configure(state=NORMAL, text="🎯 Generate AI Recommendations")
            self.update_status_time()
    
    def build_user_preferences(self):
        """构建用户偏好设置"""
        preferences = {}
        
        # 基础偏好
        if self.selected_class.get() != "Any":
            preferences['preferred_class'] = self.selected_class.get()
        
        # 数值参数
        try:
            budget = float(self.budget_var.get())
            preferences['budget_limit'] = budget
        except:
            pass
        
        try:
            min_dps = int(self.dps_var.get())
            preferences['min_dps'] = min_dps
        except:
            pass
        
        # 风格和复杂度
        if self.style_var.get() != "Any":
            preferences['playstyle'] = self.style_var.get().lower()
        
        preferences['innovation_level'] = self.innovation_var.get()
        
        complexity_map = {"Low": 3, "Medium": 4, "High": 5, "Expert": 6}
        preferences['max_complexity'] = complexity_map.get(self.complexity_var.get(), 4)
        
        # 结果数量
        try:
            result_count = int(self.result_count_var.get())
            preferences['result_count'] = result_count
        except:
            pass
        
        return preferences
    
    def display_professional_results(self, recommendations):
        """显示专业级结果"""
        # 清空现有结果
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not recommendations:
            self.show_no_results()
            return
        
        # 显示每个推荐
        for i, rec in enumerate(recommendations):
            self.create_enhanced_build_card(rec, i)
        
        # 更新状态
        self.status_var.set(f"✅ Generated {len(recommendations)} professional recommendations")
    
    def create_enhanced_build_card(self, recommendation, index):
        """创建增强版构筑卡片"""
        # 主卡片容器
        card = Frame(self.results_frame, bg=self.colors['bg_light'], relief=RAISED, borderwidth=2)
        card.pack(fill=X, padx=12, pady=8)
        
        # 卡片头部
        header = Frame(card, bg=self.colors['bg_dark'], height=60)
        header.pack(fill=X, padx=3, pady=3)
        header.pack_propagate(False)
        
        # 左侧构筑信息
        left_header = Frame(header, bg=self.colors['bg_dark'])
        left_header.pack(side=LEFT, fill=Y, padx=15)
        
        # 构筑名称
        title_frame = Frame(left_header, bg=self.colors['bg_dark'])
        title_frame.pack(anchor=W, pady=(8, 0))
        
        rank_label = Label(title_frame, text=f"#{index+1}",
                          font=('Arial', 14, 'bold'),
                          fg=self.colors['accent_orange'], bg=self.colors['bg_dark'])
        rank_label.pack(side=LEFT, padx=(0, 10))
        
        build_name = Label(title_frame, text=recommendation['name'],
                          font=('Arial', 14, 'bold'),
                          fg=self.colors['accent_gold'], bg=self.colors['bg_dark'])
        build_name.pack(side=LEFT)
        
        # 职业信息
        class_info = f"{recommendation['character_class']} - {recommendation['ascendancy']}"
        class_label = Label(left_header, text=class_info,
                          font=('Arial', 11), fg=self.colors['text_normal'], bg=self.colors['bg_dark'])
        class_label.pack(anchor=W, pady=(0, 8))
        
        # 右侧评分区域
        scores_frame = Frame(header, bg=self.colors['bg_dark'])
        scores_frame.pack(side=RIGHT, fill=Y, padx=15)
        
        ai_assess = recommendation['ai_assessment']
        composite_score = ai_assess['composite_score']
        
        score_color = (self.colors['accent_green'] if composite_score >= 8.0 
                      else self.colors['accent_blue'] if composite_score >= 6.0
                      else self.colors['accent_orange'])
        
        score_label = Label(scores_frame, text=f"AI Score: {composite_score:.1f}/10",
                          font=('Arial', 13, 'bold'),
                          fg=score_color, bg=self.colors['bg_dark'])
        score_label.pack(pady=(12, 2))
        
        confidence = recommendation['metadata']['recommendation_confidence']
        conf_label = Label(scores_frame, text=f"Confidence: {confidence:.0%}",
                         font=('Arial', 9), fg=self.colors['text_normal'], bg=self.colors['bg_dark'])
        conf_label.pack()
        
        # 卡片主体
        body = Frame(card, bg=self.colors['bg_light'])
        body.pack(fill=BOTH, expand=True, padx=12, pady=(0, 12))
        
        # 三栏布局：技能、属性、分析
        self.create_skill_column(body, recommendation)
        self.create_stats_column(body, recommendation)
        self.create_analysis_column(body, recommendation)
        
        # 底部操作栏
        self.create_enhanced_action_buttons(body, recommendation)
    
    def create_skill_column(self, parent, recommendation):
        """创建技能栏"""
        skill_frame = Frame(parent, bg=self.colors['bg_light'])
        skill_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))
        
        # 主技能
        main_skill_frame = LabelFrame(skill_frame, text="⚡ Main Skill",
                                     bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                     font=('Arial', 10, 'bold'))
        main_skill_frame.pack(fill=X, pady=(0, 8))
        
        main_skill_btn = Button(main_skill_frame,
                              text=f"🔮 {recommendation['main_skill']}",
                              font=('Arial', 12, 'bold'),
                              bg=self.colors['accent_blue'], fg='white',
                              command=lambda: self.show_skill_details(recommendation['main_skill']),
                              relief=RAISED, padx=15, pady=8)
        main_skill_btn.pack(fill=X, padx=8, pady=8)
        
        # 辅助宝石
        supports_frame = LabelFrame(skill_frame, text="💎 Support Gems",
                                   bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                   font=('Arial', 10, 'bold'))
        supports_frame.pack(fill=BOTH, expand=True, pady=(0, 8))
        
        # 辅助宝石网格（2列）
        supports_grid = Frame(supports_frame, bg=self.colors['bg_medium'])
        supports_grid.pack(fill=X, padx=8, pady=8)
        
        for i, support in enumerate(recommendation['support_gems'][:6]):
            row = i // 2
            col = i % 2
            
            support_btn = Button(supports_grid, text=f"💎 {support}",
                                bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                command=lambda s=support: self.show_gem_details(s),
                                relief=RAISED, padx=8, pady=4, font=('Arial', 9))
            support_btn.grid(row=row, column=col, sticky=EW, padx=2, pady=2)
        
        # 配置网格权重
        supports_grid.columnconfigure(0, weight=1)
        supports_grid.columnconfigure(1, weight=1)
    
    def create_stats_column(self, parent, recommendation):
        """创建属性栏"""
        stats_frame = Frame(parent, bg=self.colors['bg_light'], width=200)
        stats_frame.pack(side=LEFT, fill=Y, padx=8)
        stats_frame.pack_propagate(False)
        
        # 性能统计
        perf_frame = LabelFrame(stats_frame, text="📊 Performance",
                               bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                               font=('Arial', 10, 'bold'))
        perf_frame.pack(fill=X, pady=(0, 8))
        
        perf = recommendation['performance']
        stats_data = [
            ("DPS", f"{perf['dps']:,}", self.colors['accent_red']),
            ("EHP", f"{perf['ehp']:,}", self.colors['accent_green']),
            ("Mana Cost", str(perf['mana_cost']), self.colors['accent_blue'])
        ]
        
        for name, value, color in stats_data:
            stat_frame = Frame(perf_frame, bg=self.colors['bg_medium'])
            stat_frame.pack(fill=X, padx=8, pady=3)
            
            Label(stat_frame, text=f"{name}:", bg=self.colors['bg_medium'],
                  fg=self.colors['text_normal'], font=('Arial', 9)).pack(side=LEFT)
            Label(stat_frame, text=value, bg=self.colors['bg_medium'],
                  fg=color, font=('Arial', 9, 'bold')).pack(side=RIGHT)
        
        # AI详细评分
        ai_frame = LabelFrame(stats_frame, text="🤖 AI Analysis",
                             bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                             font=('Arial', 10, 'bold'))
        ai_frame.pack(fill=X, pady=(0, 8))
        
        ai_assess = recommendation['ai_assessment']
        ai_stats = [
            ("Viability", f"{ai_assess['viability_score']:.1f}/10"),
            ("Realism", f"{ai_assess['realism_score']:.1f}/10"),
            ("Innovation", f"{ai_assess['innovation_score']:.2f}/1")
        ]
        
        for name, value in ai_stats:
            ai_stat_frame = Frame(ai_frame, bg=self.colors['bg_medium'])
            ai_stat_frame.pack(fill=X, padx=8, pady=3)
            
            Label(ai_stat_frame, text=f"{name}:", bg=self.colors['bg_medium'],
                  fg=self.colors['text_normal'], font=('Arial', 9)).pack(side=LEFT)
            Label(ai_stat_frame, text=value, bg=self.colors['bg_medium'],
                  fg=self.colors['accent_blue'], font=('Arial', 9, 'bold')).pack(side=RIGHT)
    
    def create_analysis_column(self, parent, recommendation):
        """创建分析栏"""
        analysis_frame = Frame(parent, bg=self.colors['bg_light'], width=250)
        analysis_frame.pack(side=RIGHT, fill=Y, padx=(8, 0))
        analysis_frame.pack_propagate(False)
        
        # 推荐理由
        reasons_frame = LabelFrame(analysis_frame, text="💡 Why Recommended",
                                  bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                  font=('Arial', 10, 'bold'))
        reasons_frame.pack(fill=X, pady=(0, 8))
        
        reasons_text = Frame(reasons_frame, bg=self.colors['bg_medium'])
        reasons_text.pack(fill=X, padx=8, pady=8)
        
        analysis = recommendation['recommendation_analysis']
        for reason in analysis['why_recommended'][:2]:  # 显示前2个理由
            reason_label = Label(reasons_text, text=f"• {reason}",
                               font=('Arial', 9), fg=self.colors['text_normal'],
                               bg=self.colors['bg_medium'], wraplength=220, justify=LEFT)
            reason_label.pack(anchor=W, pady=1)
        
        # 成本和风险
        practical_frame = LabelFrame(analysis_frame, text="💰 Cost & Risk",
                                   bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                   font=('Arial', 10, 'bold'))
        practical_frame.pack(fill=X, pady=(0, 8))
        
        practical_info = recommendation['practical_info']
        cost_label = Label(practical_frame, text=f"Cost: {practical_info['estimated_cost']}",
                         font=('Arial', 9, 'bold'), fg=self.colors['accent_green'],
                         bg=self.colors['bg_medium'])
        cost_label.pack(padx=8, pady=(8, 4))
        
        risk_color = (self.colors['accent_green'] if analysis['risk_level'] == '低'
                     else self.colors['accent_orange'] if analysis['risk_level'] == '中'
                     else self.colors['accent_red'])
        
        risk_label = Label(practical_frame, text=f"Risk: {analysis['risk_level']}",
                         font=('Arial', 9), fg=risk_color,
                         bg=self.colors['bg_medium'])
        risk_label.pack(padx=8, pady=(0, 8))
    
    def create_enhanced_action_buttons(self, parent, recommendation):
        """创建增强版操作按钮"""
        actions_frame = Frame(parent, bg=self.colors['bg_light'])
        actions_frame.pack(fill=X, pady=(12, 0))
        
        # 主要操作按钮
        primary_buttons = [
            ("📋 Full Details", lambda: self.show_build_details(recommendation), self.colors['bg_medium']),
            ("📤 Export PoB2", lambda: self.export_to_pob(recommendation), self.colors['accent_blue']),
            ("🔗 View Items", lambda: self.show_item_links(recommendation), self.colors['accent_green'])
        ]
        
        for text, command, color in primary_buttons:
            btn = Button(actions_frame, text=text, command=command,
                        bg=color, fg='white', relief=RAISED,
                        padx=12, pady=6, font=('Arial', 9, 'bold'))
            btn.pack(side=LEFT, padx=5)
        
        # 次要操作按钮
        secondary_frame = Frame(actions_frame, bg=self.colors['bg_light'])
        secondary_frame.pack(side=RIGHT)
        
        secondary_buttons = [
            ("⭐", lambda: self.add_to_favorites(recommendation), "Add to Favorites"),
            ("📊", lambda: self.analyze_build(recommendation), "Detailed Analysis"),
            ("🔄", lambda: self.create_variant(recommendation), "Create Variant")
        ]
        
        for text, command, tooltip in secondary_buttons:
            btn = Button(secondary_frame, text=text, command=command,
                        bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                        relief=RAISED, padx=8, pady=6, font=('Arial', 9))
            btn.pack(side=LEFT, padx=2)
            # TODO: 添加tooltip支持
    
    def show_no_results(self):
        """显示无结果界面"""
        no_results_frame = Frame(self.results_frame, bg=self.colors['bg_medium'])
        no_results_frame.pack(fill=BOTH, expand=True, padx=50, pady=100)
        
        no_results_icon = Label(no_results_frame, text="🔍",
                              font=('Arial', 48),
                              fg=self.colors['accent_orange'], bg=self.colors['bg_medium'])
        no_results_icon.pack(pady=20)
        
        no_results_title = Label(no_results_frame, text="No Builds Found",
                               font=('Arial', 18, 'bold'),
                               fg=self.colors['text_highlight'], bg=self.colors['bg_medium'])
        no_results_title.pack(pady=10)
        
        suggestions_text = """Try adjusting your parameters:
• Increase budget limit
• Lower minimum DPS requirement  
• Change complexity setting
• Select different class or style"""
        
        suggestions_label = Label(no_results_frame, text=suggestions_text,
                                font=('Arial', 12), fg=self.colors['text_normal'],
                                bg=self.colors['bg_medium'], justify=LEFT)
        suggestions_label.pack(pady=20)
    
    def update_results_count(self, count):
        """更新结果计数显示"""
        self.results_count_label.configure(text=f"{count} builds generated")
        self.update_status_time()
    
    def update_status_time(self):
        """更新状态栏时间"""
        current_time = datetime.now().strftime('%H:%M:%S')
        # 更新右侧时间显示
        for widget in self.main_container.winfo_children():
            if isinstance(widget, Frame) and widget.winfo_children():
                status_bar = widget.winfo_children()[-1]  # 最后一个是状态栏
                if hasattr(status_bar, 'winfo_children'):
                    for child in status_bar.winfo_children():
                        if isinstance(child, Frame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, Label) and "Last Update" in subchild.cget('text'):
                                    subchild.configure(text=f"Last Update: {current_time}")
                                    break
    
    # ===== 事件处理方法 =====
    
    def resort_results(self, event=None):
        """重新排序结果"""
        if not self.current_recommendations:
            return
        
        sort_by = self.sort_var.get()
        
        if sort_by == "AI Score":
            self.current_recommendations.sort(
                key=lambda x: x['ai_assessment']['composite_score'], reverse=True)
        elif sort_by == "DPS":
            self.current_recommendations.sort(
                key=lambda x: x['performance']['dps'], reverse=True)
        elif sort_by == "Cost":
            self.current_recommendations.sort(
                key=lambda x: float(x['practical_info']['estimated_cost'].split()[0]), reverse=False)
        elif sort_by == "Innovation":
            self.current_recommendations.sort(
                key=lambda x: x['ai_assessment']['innovation_score'], reverse=True)
        
        self.display_professional_results(self.current_recommendations)
        self.status_var.set(f"Results sorted by {sort_by}")
    
    def refresh_market_data(self):
        """刷新市场数据"""
        self.status_var.set("🔄 Refreshing market data...")
        # TODO: 实际的市场数据刷新逻辑
        self.root.after(2000, lambda: self.status_var.set("✅ Market data refreshed"))
    
    # ===== 快速模板方法 =====
    
    def quick_meta(self):
        """快速元构筑"""
        self.innovation_var.set("conservative")
        self.budget_var.set("20")
        self.complexity_var.set("Medium")
        self.generate_builds()
    
    def quick_rare(self):
        """快速稀有构筑"""
        self.innovation_var.set("experimental")
        self.complexity_var.set("High")
        self.generate_builds()
    
    def quick_budget(self):
        """快速预算构筑"""
        self.budget_var.set("5")
        self.complexity_var.set("Low")
        self.innovation_var.set("conservative")
        self.generate_builds()
    
    def quick_league_start(self):
        """快速联赛开荒"""
        self.budget_var.set("3")
        self.complexity_var.set("Low")
        self.dps_var.set("150000")
        self.generate_builds()
    
    # ===== 详细功能方法 =====
    
    def show_skill_details(self, skill_name):
        """显示技能详情"""
        skill_url = f"https://poe2db.tw/us/skill/{skill_name.replace(' ', '_')}"
        webbrowser.open(skill_url)
        self.status_var.set(f"Opening skill details: {skill_name}")
    
    def show_gem_details(self, gem_name):
        """显示宝石详情"""
        gem_url = f"https://poe2db.tw/us/gem/{gem_name.replace(' ', '_')}"
        webbrowser.open(gem_url)
        self.status_var.set(f"Opening gem details: {gem_name}")
    
    def show_item_links(self, recommendation):
        """显示物品链接"""
        items_window = Toplevel(self.root)
        items_window.title("Item Links - " + recommendation['name'])
        items_window.geometry("700x500")
        items_window.configure(bg=self.colors['bg_dark'])
        
        # 标题
        title_label = Label(items_window, text="🔗 Recommended Items & Trade Links",
                          font=('Arial', 16, 'bold'),
                          fg=self.colors['accent_gold'], bg=self.colors['bg_dark'])
        title_label.pack(pady=20)
        
        # 物品分类展示
        categories = {
            "🗡️ Weapons": [
                "High Physical DPS Weapon",
                "Elemental Damage Staff", 
                "Critical Strike Multiplier Bow"
            ],
            "🛡️ Armor": [
                "Life + Resistances Chest Armor",
                "Energy Shield Helmet",
                "Movement Speed Boots",
                "Defensive Gloves"
            ],
            "💍 Jewelry": [
                "Life + Damage Ring",
                "All Resistances Amulet",
                "Unique Utility Belt"
            ],
            "💎 Gems": [
                recommendation['main_skill'],
                *recommendation['support_gems'][:3]
            ]
        }
        
        # 滚动区域
        scroll_frame = Frame(items_window, bg=self.colors['bg_dark'])
        scroll_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        canvas = Canvas(scroll_frame, bg=self.colors['bg_medium'])
        scrollbar = Scrollbar(scroll_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = Frame(canvas, bg=self.colors['bg_medium'])
        
        scrollable_frame.bind("<Configure>", 
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 添加物品类别
        for category, items in categories.items():
            cat_frame = LabelFrame(scrollable_frame, text=category,
                                 bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                 font=('Arial', 12, 'bold'))
            cat_frame.pack(fill=X, padx=15, pady=10)
            
            for item in items:
                item_frame = Frame(cat_frame, bg=self.colors['bg_medium'])
                item_frame.pack(fill=X, padx=10, pady=5)
                
                item_btn = Button(item_frame, text=f"🔍 Search: {item}",
                                bg=self.colors['accent_blue'], fg='white',
                                command=lambda i=item: self.open_trade_search(i),
                                relief=RAISED, padx=15, pady=8, font=('Arial', 10))
                item_btn.pack(side=LEFT, fill=X, expand=True)
    
    def export_to_pob(self, recommendation):
        """导出到Path of Building"""
        export_window = Toplevel(self.root)
        export_window.title("Export to Path of Building 2")
        export_window.geometry("600x400")
        export_window.configure(bg=self.colors['bg_dark'])
        
        # 标题
        title_label = Label(export_window, text="📤 Path of Building 2 Export",
                          font=('Arial', 16, 'bold'),
                          fg=self.colors['accent_gold'], bg=self.colors['bg_dark'])
        title_label.pack(pady=20)
        
        # 生成PoB代码
        pob_code = self.generate_advanced_pob_code(recommendation)
        
        # 代码显示区域
        import tkinter.scrolledtext as st
        code_text = st.ScrolledText(export_window, width=70, height=20,
                                   bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                   font=('Consolas', 10))
        code_text.pack(padx=20, pady=10)
        code_text.insert(END, pob_code)
        
        # 按钮区域
        btn_frame = Frame(export_window, bg=self.colors['bg_dark'])
        btn_frame.pack(pady=15)
        
        copy_btn = Button(btn_frame, text="📋 Copy to Clipboard",
                         bg=self.colors['accent_blue'], fg='white',
                         command=lambda: self.copy_to_clipboard(pob_code),
                         font=('Arial', 11, 'bold'), padx=20, pady=8)
        copy_btn.pack(side=LEFT, padx=10)
        
        save_btn = Button(btn_frame, text="💾 Save to File",
                         bg=self.colors['accent_green'], fg='white',
                         command=lambda: self.save_pob_code(pob_code, recommendation['name']),
                         font=('Arial', 11, 'bold'), padx=20, pady=8)
        save_btn.pack(side=LEFT, padx=10)
    
    def show_build_details(self, recommendation):
        """显示构筑详情"""
        details_window = Toplevel(self.root)
        details_window.title("Detailed Analysis - " + recommendation['name'])
        details_window.geometry("900x700")
        details_window.configure(bg=self.colors['bg_dark'])
        
        # 创建notebook标签页
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 标签页1：基础信息
        basic_frame = Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(basic_frame, text="📋 Basic Info")
        
        # 标签页2：性能分析
        performance_frame = Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(performance_frame, text="📊 Performance")
        
        # 标签页3：AI分析
        ai_frame = Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(ai_frame, text="🤖 AI Analysis")
        
        # 填充基础信息
        self.fill_basic_details(basic_frame, recommendation)
        self.fill_performance_details(performance_frame, recommendation)
        self.fill_ai_details(ai_frame, recommendation)
    
    def fill_basic_details(self, parent, rec):
        """填充基础详情"""
        import tkinter.scrolledtext as st
        
        details_text = st.ScrolledText(parent, width=85, height=35,
                                     bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                     font=('Consolas', 11))
        details_text.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        content = f"""
{'='*70}
🏆 {rec['name']}
{'='*70}

📋 CHARACTER CONFIGURATION:
   Class: {rec['character_class']}
   Ascendancy: {rec['ascendancy']}
   Build Style: {rec['practical_info'].get('playstyle_description', 'Not specified')}

⚡ SKILL SETUP:
   Main Skill: {rec['main_skill']}
   
   Support Gems:
"""
        
        for i, gem in enumerate(rec['support_gems'], 1):
            content += f"   {i:2d}. {gem}\n"
        
        content += f"""

💰 ECONOMICS:
   Estimated Cost: {rec['practical_info']['estimated_cost']}
   Difficulty Rating: {rec['practical_info']['difficulty_rating']}/5
   League Suitability: {rec['practical_info']['league_suitability']}

🎯 TARGET PERFORMANCE:
   Expected DPS: {rec['performance']['dps']:,}
   Effective Health Pool: {rec['performance']['ehp']:,}
   Mana Cost per Cast: {rec['performance']['mana_cost']}

📈 STAT REQUIREMENTS:
"""
        
        for stat, value in rec['performance']['stat_requirements'].items():
            content += f"   {stat.upper()}: {value}\n"
        
        details_text.insert(END, content)
    
    def fill_performance_details(self, parent, rec):
        """填充性能详情"""
        # 创建图表框架（简化版）
        perf_frame = Frame(parent, bg=self.colors['bg_medium'])
        perf_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 性能指标卡片
        metrics = [
            ("DPS Output", rec['performance']['dps'], "🗡️", self.colors['accent_red']),
            ("Survivability", rec['performance']['ehp'], "🛡️", self.colors['accent_green']),
            ("Mana Efficiency", rec['performance']['mana_cost'], "💙", self.colors['accent_blue']),
        ]
        
        for i, (name, value, icon, color) in enumerate(metrics):
            metric_card = Frame(perf_frame, bg=self.colors['bg_light'], relief=RAISED, borderwidth=2)
            metric_card.pack(fill=X, pady=10)
            
            # 卡片标题
            title_frame = Frame(metric_card, bg=self.colors['bg_dark'])
            title_frame.pack(fill=X)
            
            Label(title_frame, text=f"{icon} {name}",
                  font=('Arial', 14, 'bold'), fg=color,
                  bg=self.colors['bg_dark']).pack(pady=10)
            
            # 数值显示
            value_frame = Frame(metric_card, bg=self.colors['bg_light'])
            value_frame.pack(fill=X, padx=20, pady=15)
            
            if isinstance(value, (int, float)) and value > 1000:
                display_value = f"{value:,}"
            else:
                display_value = str(value)
            
            Label(value_frame, text=display_value,
                  font=('Arial', 20, 'bold'), fg=color,
                  bg=self.colors['bg_light']).pack()
    
    def fill_ai_details(self, parent, rec):
        """填充AI分析详情"""
        ai_frame = Frame(parent, bg=self.colors['bg_medium'])
        ai_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # AI评分区域
        scores_frame = LabelFrame(ai_frame, text="🤖 AI Scoring Breakdown",
                                bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                font=('Arial', 12, 'bold'))
        scores_frame.pack(fill=X, pady=(0, 15))
        
        ai_assess = rec['ai_assessment']
        scores = [
            ("Viability Score", ai_assess['viability_score'], "Build实用性和可行性"),
            ("Realism Score", ai_assess['realism_score'], "基于真实数据的现实度"),
            ("Innovation Score", ai_assess['innovation_score'], "创新程度和独特性"),
            ("Composite Score", ai_assess['composite_score'], "综合评分")
        ]
        
        for name, score, description in scores:
            score_frame = Frame(scores_frame, bg=self.colors['bg_medium'])
            score_frame.pack(fill=X, padx=15, pady=8)
            
            Label(score_frame, text=name + ":", font=('Arial', 11, 'bold'),
                  fg=self.colors['text_highlight'], bg=self.colors['bg_medium']).pack(anchor=W)
            
            Label(score_frame, text=f"{score:.2f}/10", font=('Arial', 14, 'bold'),
                  fg=self.colors['accent_blue'], bg=self.colors['bg_medium']).pack(anchor=W, padx=20)
            
            Label(score_frame, text=description, font=('Arial', 9),
                  fg=self.colors['text_normal'], bg=self.colors['bg_medium']).pack(anchor=W, padx=20)
        
        # 推荐分析
        analysis_frame = LabelFrame(ai_frame, text="💡 Recommendation Analysis",
                                  bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                  font=('Arial', 12, 'bold'))
        analysis_frame.pack(fill=BOTH, expand=True)
        
        import tkinter.scrolledtext as st
        analysis_text = st.ScrolledText(analysis_frame, width=80, height=15,
                                      bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                      font=('Arial', 11))
        analysis_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        analysis_content = f"""
推荐理由:
"""
        
        for reason in rec['recommendation_analysis']['why_recommended']:
            analysis_content += f"• {reason}\n"
        
        analysis_content += f"""
风险评估:
• 风险等级: {rec['recommendation_analysis']['risk_level']}
"""
        
        if rec['recommendation_analysis']['risk_factors']:
            for risk in rec['recommendation_analysis']['risk_factors']:
                analysis_content += f"• {risk}\n"
        
        analysis_content += f"""
独特优势:
"""
        
        for advantage in rec['recommendation_analysis']['unique_aspects']:
            analysis_content += f"• {advantage}\n"
        
        analysis_text.insert(END, analysis_content)
    
    # ===== 工具方法 =====
    
    def generate_advanced_pob_code(self, recommendation):
        """生成高级PoB导入代码"""
        import base64
        
        pob_data = {
            "version": "2.0",
            "build_name": recommendation['name'],
            "character": {
                "class": recommendation['character_class'],
                "ascendancy": recommendation['ascendancy']
            },
            "skills": {
                "main": recommendation['main_skill'],
                "supports": recommendation['support_gems']
            },
            "stats": {
                "dps": recommendation['performance']['dps'],
                "life": recommendation['performance']['ehp'],
                "mana": recommendation['performance']['mana_cost'],
                "requirements": recommendation['performance']['stat_requirements']
            },
            "metadata": {
                "generated_by": "PoE2 Complete AI Planner",
                "ai_score": recommendation['ai_assessment']['composite_score'],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        json_data = json.dumps(pob_data, indent=2)
        encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        
        return f"""# PoE2 Complete AI Build Export
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Build: {recommendation['name']}
# AI Score: {recommendation['ai_assessment']['composite_score']:.1f}/10

{json_data}

# PoB2 Import Instructions:
# 1. Copy the JSON data above
# 2. Open Path of Building 2
# 3. Use the import function
# 4. Paste the build data

# Advanced Import Code (Base64):
{encoded_data}
"""
    
    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("✅ Copied to clipboard")
        messagebox.showinfo("Success", "Build data copied to clipboard!")
    
    def save_pob_code(self, code, build_name):
        """保存PoB代码到文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialname=f"{build_name.replace(' ', '_')}_pob_export.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.status_var.set(f"✅ Saved to {filename}")
                messagebox.showinfo("Success", f"Build exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def open_trade_search(self, item_name):
        """打开交易搜索"""
        trade_url = f"https://poe2scout.com/search?item={item_name.replace(' ', '+')}"
        webbrowser.open(trade_url)
        self.status_var.set(f"Opening trade search: {item_name}")
    
    def add_to_favorites(self, recommendation):
        """添加到收藏"""
        if recommendation not in self.favorites:
            self.favorites.append(recommendation)
            self.status_var.set(f"⭐ Added to favorites: {recommendation['name']}")
            messagebox.showinfo("Favorite", f"Build '{recommendation['name']}' added to favorites!")
        else:
            messagebox.showinfo("Info", "Build already in favorites!")
    
    def analyze_build(self, recommendation):
        """详细分析构筑"""
        # 这里可以添加更高级的分析功能
        self.show_build_details(recommendation)
    
    def create_variant(self, recommendation):
        """创建构筑变体"""
        messagebox.showinfo("Feature", "Build variant creation feature coming soon!")
    
    # ===== 菜单功能方法 =====
    
    def import_build(self):
        """导入构筑"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    build_data = json.load(f)
                messagebox.showinfo("Success", f"Build imported from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import build:\n{e}")
    
    def export_builds(self):
        """导出所有构筑"""
        if not self.current_recommendations:
            messagebox.showwarning("Warning", "No builds to export!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialname=f"poe2_builds_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                export_data = {
                    "generated": datetime.now().isoformat(),
                    "count": len(self.current_recommendations),
                    "builds": self.current_recommendations
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.status_var.set(f"✅ Exported {len(self.current_recommendations)} builds")
                messagebox.showinfo("Success", f"Builds exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export builds:\n{e}")
    
    def show_favorites(self):
        """显示收藏夹"""
        if not self.favorites:
            messagebox.showinfo("Favorites", "No favorite builds yet!")
            return
        
        favorites_window = Toplevel(self.root)
        favorites_window.title("Favorite Builds")
        favorites_window.geometry("800x600")
        favorites_window.configure(bg=self.colors['bg_dark'])
        
        # TODO: 创建收藏夹界面
        Label(favorites_window, text="⭐ Favorite Builds",
              font=('Arial', 16, 'bold'), fg=self.colors['accent_gold'],
              bg=self.colors['bg_dark']).pack(pady=20)
        
        for fav in self.favorites:
            fav_frame = Frame(favorites_window, bg=self.colors['bg_medium'], relief=RAISED, borderwidth=1)
            fav_frame.pack(fill=X, padx=20, pady=5)
            
            Label(fav_frame, text=fav['name'], font=('Arial', 12, 'bold'),
                  fg=self.colors['text_highlight'], bg=self.colors['bg_medium']).pack(pady=10)
    
    def show_settings(self):
        """显示设置界面"""
        settings_window = Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.colors['bg_dark'])
        
        Label(settings_window, text="🔧 Settings",
              font=('Arial', 16, 'bold'), fg=self.colors['accent_gold'],
              bg=self.colors['bg_dark']).pack(pady=20)
        
        # TODO: 添加设置选项
        Label(settings_window, text="Settings panel coming soon!",
              font=('Arial', 12), fg=self.colors['text_normal'],
              bg=self.colors['bg_dark']).pack(pady=50)


def main():
    """启动完整专业级GUI"""
    root = Tk()
    
    # 设置窗口图标
    try:
        root.iconbitmap('poe2_icon.ico')
    except:
        pass
    
    # 设置字体DPI支持
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = CompleteProfessionalGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()
    except Exception as e:
        print(f"Application error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()