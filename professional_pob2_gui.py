#!/usr/bin/env python3
"""
专业级PoE2构筑推荐GUI - 模仿PoB2风格
包含完整构筑信息、物品图标、链接、赛季选择等
"""

import sys
import os
import json
import webbrowser
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, font
import tkinter.font as tkFont
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class PoE2ProfessionalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PoE2 AI Build Planner - Professional Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')  # PoB2风格深色背景
        
        # PoE2 游戏数据
        self.leagues = [
            "Rise of the Abyssal (Current)",
            "Standard", 
            "Hardcore",
            "Solo Self-Found"
        ]
        
        self.classes = {
            "Sorceress": {
                "ascendancies": ["Stormweaver", "Chronomancer"],
                "icon": "⚡",
                "color": "#4169E1"
            },
            "Witch": {
                "ascendancies": ["Infernalist", "Blood Mage"],
                "icon": "🔥",
                "color": "#8B0000"
            },
            "Ranger": {
                "ascendancies": ["Deadeye", "Pathfinder"],
                "icon": "🏹",
                "color": "#228B22"
            },
            "Monk": {
                "ascendancies": ["Invoker", "Acolyte"],
                "icon": "⚡",
                "color": "#FF6347"
            },
            "Warrior": {
                "ascendancies": ["Titan", "Warbringer"],
                "icon": "⚔️",
                "color": "#B8860B"
            },
            "Mercenary": {
                "ascendancies": ["Witchhunter", "Gemling Legionnaire"],
                "icon": "🔫", 
                "color": "#696969"
            }
        }
        
        # 创建样式
        self.setup_styles()
        self.create_professional_ui()
        self.load_ai_system()
        
    def setup_styles(self):
        """设置PoB2风格的样式"""
        style = ttk.Style()
        
        # 配置主题色调
        style.theme_use('clam')
        
        # 定义PoB2风格颜色
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
        
        style.configure('Professional.TButton',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_highlight'],
                       borderwidth=1,
                       relief='raised')
        
        style.configure('Accent.TButton',
                       background=self.colors['accent_blue'],
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        
    def create_professional_ui(self):
        """创建专业级UI界面"""
        # 主容器
        self.main_container = Frame(self.root, bg=self.colors['bg_dark'])
        self.main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 顶部工具栏
        self.create_top_toolbar()
        
        # 主内容区域
        content_frame = Frame(self.main_container, bg=self.colors['bg_dark'])
        content_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        # 左侧参数面板
        self.create_left_panel(content_frame)
        
        # 右侧结果面板
        self.create_right_panel(content_frame)
        
        # 底部状态栏
        self.create_status_bar()
    
    def create_top_toolbar(self):
        """创建顶部工具栏"""
        toolbar = Frame(self.main_container, bg=self.colors['bg_medium'], height=50)
        toolbar.pack(fill=X, padx=2, pady=2)
        toolbar.pack_propagate(False)
        
        # 标题区域
        title_frame = Frame(toolbar, bg=self.colors['bg_medium'])
        title_frame.pack(side=LEFT, fill=Y, padx=10)
        
        title_label = Label(title_frame, 
                           text="PoE2 AI Build Planner",
                           font=('Arial', 16, 'bold'),
                           fg=self.colors['accent_gold'],
                           bg=self.colors['bg_medium'])
        title_label.pack(side=LEFT, pady=15)
        
        subtitle_label = Label(title_frame,
                              text="Professional Edition",
                              font=('Arial', 10),
                              fg=self.colors['text_normal'],
                              bg=self.colors['bg_medium'])
        subtitle_label.pack(side=LEFT, padx=(10, 0), pady=15)
        
        # 快速操作按钮区域
        buttons_frame = Frame(toolbar, bg=self.colors['bg_medium'])
        buttons_frame.pack(side=RIGHT, fill=Y, padx=10)
        
        # 导入/导出按钮
        import_btn = Button(buttons_frame, text="📥 Import Build", 
                           bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                           border=1, relief=RAISED, padx=10)
        import_btn.pack(side=RIGHT, padx=5, pady=12)
        
        export_btn = Button(buttons_frame, text="📤 Export Build",
                           bg=self.colors['bg_light'], fg=self.colors['text_normal'], 
                           border=1, relief=RAISED, padx=10)
        export_btn.pack(side=RIGHT, padx=5, pady=12)
    
    def create_left_panel(self, parent):
        """创建左侧参数面板"""
        left_panel = Frame(parent, bg=self.colors['bg_medium'], width=400)
        left_panel.pack(side=LEFT, fill=Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # 赛季选择区域
        self.create_league_selection(left_panel)
        
        # 职业选择区域  
        self.create_class_selection(left_panel)
        
        # 构筑参数区域
        self.create_build_parameters(left_panel)
        
        # AI设置区域
        self.create_ai_settings(left_panel)
        
        # 生成按钮
        self.create_generation_controls(left_panel)
    
    def create_league_selection(self, parent):
        """创建赛季选择区域"""
        league_frame = LabelFrame(parent, text=" 🏆 League Selection ",
                                 bg=self.colors['bg_medium'], 
                                 fg=self.colors['accent_gold'],
                                 font=('Arial', 11, 'bold'),
                                 padx=10, pady=10)
        league_frame.pack(fill=X, padx=10, pady=(10, 5))
        
        # 当前赛季
        current_league_label = Label(league_frame, text="Current League:",
                                    bg=self.colors['bg_medium'],
                                    fg=self.colors['text_normal'])
        current_league_label.pack(anchor=W)
        
        self.selected_league = StringVar(value=self.leagues[0])
        league_combo = ttk.Combobox(league_frame, textvariable=self.selected_league,
                                   values=self.leagues, state="readonly", width=35)
        league_combo.pack(fill=X, pady=(5, 0))
        
        # 联赛信息显示
        info_label = Label(league_frame, 
                          text="🔄 Active | ⚡ Real-time market data",
                          font=('Arial', 9),
                          fg=self.colors['accent_green'],
                          bg=self.colors['bg_medium'])
        info_label.pack(anchor=W, pady=(5, 0))
    
    def create_class_selection(self, parent):
        """创建职业选择区域"""
        class_frame = LabelFrame(parent, text=" ⚔️ Character Class ",
                                bg=self.colors['bg_medium'],
                                fg=self.colors['accent_gold'], 
                                font=('Arial', 11, 'bold'),
                                padx=10, pady=10)
        class_frame.pack(fill=X, padx=10, pady=5)
        
        # 职业选择网格
        self.selected_class = StringVar(value="Any")
        self.selected_ascendancy = StringVar(value="Any")
        
        # 职业按钮网格
        class_grid = Frame(class_frame, bg=self.colors['bg_medium'])
        class_grid.pack(fill=X, pady=5)
        
        # "Any"选项
        any_btn = Button(class_grid, text="🎯 Any Class",
                        bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                        command=lambda: self.select_class("Any"),
                        relief=RAISED, padx=5, pady=3)
        any_btn.grid(row=0, column=0, columnspan=3, sticky=EW, padx=1, pady=1)
        
        # 职业按钮
        row = 1
        col = 0
        for class_name, class_info in self.classes.items():
            btn = Button(class_grid,
                        text=f"{class_info['icon']} {class_name}",
                        bg=class_info['color'], fg='white',
                        command=lambda cn=class_name: self.select_class(cn),
                        relief=RAISED, padx=5, pady=3, font=('Arial', 9))
            btn.grid(row=row, column=col, sticky=EW, padx=1, pady=1)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # 配置网格权重
        for i in range(3):
            class_grid.columnconfigure(i, weight=1)
        
        # 升华选择
        ascendancy_label = Label(class_frame, text="Ascendancy:",
                               bg=self.colors['bg_medium'],
                               fg=self.colors['text_normal'])
        ascendancy_label.pack(anchor=W, pady=(10, 0))
        
        self.ascendancy_combo = ttk.Combobox(class_frame, textvariable=self.selected_ascendancy,
                                            values=["Any"], state="readonly", width=35)
        self.ascendancy_combo.pack(fill=X, pady=(5, 0))
    
    def create_build_parameters(self, parent):
        """创建构筑参数区域"""
        params_frame = LabelFrame(parent, text=" ⚙️ Build Parameters ",
                                 bg=self.colors['bg_medium'],
                                 fg=self.colors['accent_gold'],
                                 font=('Arial', 11, 'bold'), 
                                 padx=10, pady=10)
        params_frame.pack(fill=X, padx=10, pady=5)
        
        # 参数网格
        params_grid = Frame(params_frame, bg=self.colors['bg_medium'])
        params_grid.pack(fill=X)
        
        # 预算设置
        Label(params_grid, text="💰 Budget (Divine):",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal']).grid(row=0, column=0, sticky=W, pady=2)
        
        self.budget_var = StringVar(value="15")
        budget_spinbox = Spinbox(params_grid, from_=1, to=100, textvariable=self.budget_var,
                                width=10, bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        budget_spinbox.grid(row=0, column=1, sticky=EW, padx=(10, 0), pady=2)
        
        # DPS要求
        Label(params_grid, text="⚔️ Min DPS:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal']).grid(row=1, column=0, sticky=W, pady=2)
        
        self.dps_var = StringVar(value="200000")
        dps_entry = Entry(params_grid, textvariable=self.dps_var, width=12,
                         bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        dps_entry.grid(row=1, column=1, sticky=EW, padx=(10, 0), pady=2)
        
        # 难度设置
        Label(params_grid, text="🎯 Complexity:",
              bg=self.colors['bg_medium'], fg=self.colors['text_normal']).grid(row=2, column=0, sticky=W, pady=2)
        
        self.complexity_var = StringVar(value="Medium")
        complexity_combo = ttk.Combobox(params_grid, textvariable=self.complexity_var,
                                       values=["Low", "Medium", "High"], state="readonly", width=10)
        complexity_combo.grid(row=2, column=1, sticky=EW, padx=(10, 0), pady=2)
        
        # 配置网格权重
        params_grid.columnconfigure(1, weight=1)
    
    def create_ai_settings(self, parent):
        """创建AI设置区域"""
        ai_frame = LabelFrame(parent, text=" 🤖 AI Settings ",
                             bg=self.colors['bg_medium'],
                             fg=self.colors['accent_gold'],
                             font=('Arial', 11, 'bold'),
                             padx=10, pady=10)
        ai_frame.pack(fill=X, padx=10, pady=5)
        
        # 创新程度设置
        innovation_label = Label(ai_frame, text="Innovation Level:",
                               bg=self.colors['bg_medium'], fg=self.colors['text_normal'])
        innovation_label.pack(anchor=W)
        
        innovation_frame = Frame(ai_frame, bg=self.colors['bg_medium'])
        innovation_frame.pack(fill=X, pady=(5, 10))
        
        self.innovation_var = StringVar(value="balanced")
        
        # 创新程度选项按钮
        innovation_options = [
            ("🛡️ Conservative", "conservative", self.colors['accent_green']),
            ("⚖️ Balanced", "balanced", self.colors['accent_blue']),
            ("🔬 Experimental", "experimental", self.colors['accent_red'])
        ]
        
        for i, (text, value, color) in enumerate(innovation_options):
            btn = Radiobutton(innovation_frame, text=text, variable=self.innovation_var, value=value,
                             bg=self.colors['bg_medium'], fg=color, selectcolor=self.colors['bg_light'],
                             activebackground=self.colors['bg_medium'], font=('Arial', 9))
            btn.pack(anchor=W, padx=5)
        
        # AI数据源指示器
        sources_label = Label(ai_frame, 
                             text="📊 Data Sources: Real PoE2 Data + AI Analysis",
                             font=('Arial', 9), fg=self.colors['accent_green'],
                             bg=self.colors['bg_medium'])
        sources_label.pack(anchor=W, pady=(5, 0))
    
    def create_generation_controls(self, parent):
        """创建生成控制区域"""
        controls_frame = Frame(parent, bg=self.colors['bg_medium'])
        controls_frame.pack(fill=X, padx=10, pady=20)
        
        # 主生成按钮
        self.generate_btn = Button(controls_frame, text="🎯 Generate AI Builds",
                                  font=('Arial', 12, 'bold'),
                                  bg=self.colors['accent_blue'], fg='white',
                                  command=self.generate_builds,
                                  relief=RAISED, borderwidth=2,
                                  padx=20, pady=10)
        self.generate_btn.pack(fill=X, pady=(0, 10))
        
        # 快速选项按钮
        quick_frame = Frame(controls_frame, bg=self.colors['bg_medium'])
        quick_frame.pack(fill=X)
        
        quick_btns = [
            ("💎 High Value", self.quick_high_value),
            ("🔍 Ultra Rare", self.quick_ultra_rare),
            ("💰 Budget Builds", self.quick_budget)
        ]
        
        for text, command in quick_btns:
            btn = Button(quick_frame, text=text, command=command,
                        bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                        relief=RAISED, padx=5, pady=3, font=('Arial', 9))
            btn.pack(side=LEFT, expand=True, fill=X, padx=1)
    
    def create_right_panel(self, parent):
        """创建右侧结果面板"""
        right_panel = Frame(parent, bg=self.colors['bg_medium'])
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # 结果标题栏
        results_header = Frame(right_panel, bg=self.colors['bg_light'], height=40)
        results_header.pack(fill=X, padx=2, pady=2)
        results_header.pack_propagate(False)
        
        header_label = Label(results_header, text="🏆 Build Recommendations",
                           font=('Arial', 14, 'bold'),
                           fg=self.colors['accent_gold'],
                           bg=self.colors['bg_light'])
        header_label.pack(side=LEFT, padx=15, pady=10)
        
        # 结果计数
        self.results_count_label = Label(results_header, text="Ready to generate",
                                        font=('Arial', 10),
                                        fg=self.colors['text_normal'],
                                        bg=self.colors['bg_light'])
        self.results_count_label.pack(side=RIGHT, padx=15, pady=10)
        
        # 结果显示区域
        self.create_results_area(right_panel)
    
    def create_results_area(self, parent):
        """创建结果显示区域"""
        # 主结果容器
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
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # 默认欢迎界面
        self.show_welcome_screen()
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = Frame(self.main_container, bg=self.colors['bg_light'], height=30)
        status_bar.pack(fill=X, side=BOTTOM)
        status_bar.pack_propagate(False)
        
        self.status_var = StringVar(value="Ready - AI System Loaded")
        status_label = Label(status_bar, textvariable=self.status_var,
                           bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                           font=('Arial', 9))
        status_label.pack(side=LEFT, padx=10, pady=5)
        
        # 版本信息
        version_label = Label(status_bar, text="v2.0.0 | AI-Powered",
                            bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                            font=('Arial', 9))
        version_label.pack(side=RIGHT, padx=10, pady=5)
    
    def show_welcome_screen(self):
        """显示欢迎界面"""
        # 清空现有内容
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        welcome_frame = Frame(self.results_frame, bg=self.colors['bg_medium'])
        welcome_frame.pack(fill=BOTH, expand=True, padx=20, pady=50)
        
        # 欢迎图标
        welcome_icon = Label(welcome_frame, text="🎯", font=('Arial', 48),
                           fg=self.colors['accent_gold'], bg=self.colors['bg_medium'])
        welcome_icon.pack(pady=20)
        
        # 欢迎标题
        welcome_title = Label(welcome_frame, text="PoE2 AI Build Planner",
                            font=('Arial', 20, 'bold'),
                            fg=self.colors['text_highlight'], bg=self.colors['bg_medium'])
        welcome_title.pack(pady=10)
        
        # 功能介绍
        features_text = """🤖 AI-Powered Build Generation
📊 Real PoE2 Data Integration  
💎 Unpopular High-Value Builds
🔗 Direct Item Links
⚡ Professional Interface"""
        
        features_label = Label(welcome_frame, text=features_text,
                             font=('Arial', 12), fg=self.colors['text_normal'],
                             bg=self.colors['bg_medium'], justify=CENTER)
        features_label.pack(pady=20)
        
        # 开始提示
        start_label = Label(welcome_frame, 
                          text="Configure your parameters and click 'Generate AI Builds' to start!",
                          font=('Arial', 11), fg=self.colors['accent_blue'],
                          bg=self.colors['bg_medium'])
        start_label.pack(pady=10)
    
    def select_class(self, class_name):
        """选择职业"""
        self.selected_class.set(class_name)
        
        # 更新升华选项
        if class_name == "Any":
            ascendancies = ["Any"]
        else:
            ascendancies = ["Any"] + self.classes[class_name]["ascendancies"]
        
        self.ascendancy_combo.configure(values=ascendancies)
        self.selected_ascendancy.set("Any")
        
        self.status_var.set(f"Selected: {class_name}")
    
    def load_ai_system(self):
        """加载AI系统"""
        try:
            from ninja_trained_ai_recommender import NinjaTrainedAIRecommender
            self.ai_recommender = NinjaTrainedAIRecommender()
            self.status_var.set("Ready - AI System Loaded Successfully")
        except Exception as e:
            self.status_var.set(f"Warning - AI System Load Failed: {e}")
            messagebox.showwarning("Warning", f"Could not load AI system: {e}")
    
    def generate_builds(self):
        """生成构筑推荐"""
        def run_generation():
            try:
                self.status_var.set("🔄 Generating AI Builds...")
                self.generate_btn.configure(state=DISABLED, text="⏳ Generating...")
                
                # 构建用户偏好
                preferences = self.build_user_preferences()
                
                # 生成推荐
                recommendations = self.ai_recommender.get_ninja_trained_recommendations(preferences)
                
                # 显示结果
                self.root.after(0, lambda: self.display_professional_results(recommendations))
                self.root.after(0, lambda: self.generate_btn.configure(state=NORMAL, text="🎯 Generate AI Builds"))
                self.root.after(0, lambda: self.status_var.set(f"✅ Generated {len(recommendations)} builds"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {e}"))
                self.root.after(0, lambda: self.generate_btn.configure(state=NORMAL, text="🎯 Generate AI Builds"))
                self.root.after(0, lambda: self.status_var.set(f"❌ Generation failed"))
        
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
    
    def build_user_preferences(self):
        """构建用户偏好设置"""
        preferences = {}
        
        # 职业偏好
        if self.selected_class.get() != "Any":
            preferences['preferred_class'] = self.selected_class.get()
        
        # 预算设置
        try:
            budget = float(self.budget_var.get())
            preferences['budget_limit'] = budget
        except:
            pass
        
        # DPS要求
        try:
            min_dps = int(self.dps_var.get())
            preferences['min_dps'] = min_dps
        except:
            pass
        
        # AI设置
        preferences['innovation_level'] = self.innovation_var.get()
        
        # 复杂度映射
        complexity_map = {"Low": 3, "Medium": 4, "High": 5}
        preferences['max_complexity'] = complexity_map.get(self.complexity_var.get(), 4)
        
        return preferences
    
    def display_professional_results(self, recommendations):
        """显示专业级结果"""
        # 清空现有结果
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # 更新结果计数
        self.results_count_label.configure(text=f"{len(recommendations)} builds generated")
        
        # 显示每个推荐
        for i, rec in enumerate(recommendations):
            self.create_build_card(rec, i)
    
    def create_build_card(self, recommendation, index):
        """创建构筑卡片 - PoB2风格"""
        # 主卡片容器
        card = Frame(self.results_frame, bg=self.colors['bg_light'], relief=RAISED, borderwidth=1)
        card.pack(fill=X, padx=10, pady=5)
        
        # 卡片头部
        header = Frame(card, bg=self.colors['bg_dark'], height=50)
        header.pack(fill=X, padx=2, pady=2)
        header.pack_propagate(False)
        
        # 构筑名称和职业
        title_frame = Frame(header, bg=self.colors['bg_dark'])
        title_frame.pack(side=LEFT, fill=Y, padx=10)
        
        build_name = Label(title_frame, text=f"#{index+1} {recommendation['name']}",
                          font=('Arial', 12, 'bold'),
                          fg=self.colors['accent_gold'], bg=self.colors['bg_dark'])
        build_name.pack(anchor=W, pady=(8, 0))
        
        class_info = f"{recommendation['character_class']} - {recommendation['ascendancy']}"
        class_label = Label(title_frame, text=class_info,
                          font=('Arial', 10), fg=self.colors['text_normal'], bg=self.colors['bg_dark'])
        class_label.pack(anchor=W, pady=(0, 8))
        
        # AI评分区域
        scores_frame = Frame(header, bg=self.colors['bg_dark'])
        scores_frame.pack(side=RIGHT, fill=Y, padx=10)
        
        ai_assess = recommendation['ai_assessment']
        composite_score = ai_assess['composite_score']
        
        score_label = Label(scores_frame, text=f"AI Score: {composite_score:.1f}/10",
                          font=('Arial', 11, 'bold'),
                          fg=self.colors['accent_green'] if composite_score > 8 else self.colors['accent_blue'],
                          bg=self.colors['bg_dark'])
        score_label.pack(pady=(12, 0))
        
        # 卡片主体内容
        body = Frame(card, bg=self.colors['bg_light'])
        body.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 左侧技能信息
        skill_frame = Frame(body, bg=self.colors['bg_light'])
        skill_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        self.create_skill_section(skill_frame, recommendation)
        
        # 右侧性能信息
        stats_frame = Frame(body, bg=self.colors['bg_light'], width=250)
        stats_frame.pack(side=RIGHT, fill=Y)
        stats_frame.pack_propagate(False)
        
        self.create_stats_section(stats_frame, recommendation)
        
        # 底部操作按钮
        actions_frame = Frame(body, bg=self.colors['bg_light'])
        actions_frame.pack(fill=X, pady=(10, 0))
        
        self.create_action_buttons(actions_frame, recommendation)
    
    def create_skill_section(self, parent, recommendation):
        """创建技能区域"""
        # 主技能
        main_skill_frame = Frame(parent, bg=self.colors['bg_medium'], relief=SUNKEN, borderwidth=1)
        main_skill_frame.pack(fill=X, pady=5)
        
        main_skill_label = Label(main_skill_frame, text="⚡ Main Skill",
                               font=('Arial', 10, 'bold'),
                               fg=self.colors['accent_gold'], bg=self.colors['bg_medium'])
        main_skill_label.pack(anchor=W, padx=10, pady=5)
        
        # 主技能按钮 (可点击查看详情)
        main_skill_btn = Button(main_skill_frame, 
                              text=f"🔮 {recommendation['main_skill']}",
                              font=('Arial', 11, 'bold'),
                              bg=self.colors['accent_blue'], fg='white',
                              command=lambda: self.show_skill_details(recommendation['main_skill']),
                              relief=RAISED, padx=10, pady=5)
        main_skill_btn.pack(fill=X, padx=10, pady=(0, 10))
        
        # 辅助宝石
        supports_label = Label(parent, text="💎 Support Gems",
                             font=('Arial', 10, 'bold'),
                             fg=self.colors['text_highlight'], bg=self.colors['bg_light'])
        supports_label.pack(anchor=W, pady=(10, 5))
        
        # 辅助宝石网格
        supports_grid = Frame(parent, bg=self.colors['bg_light'])
        supports_grid.pack(fill=X)
        
        for i, support in enumerate(recommendation['support_gems'][:6]):  # 最多显示6个
            row = i // 2
            col = i % 2
            
            support_btn = Button(supports_grid, text=f"💎 {support}",
                                bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                                command=lambda s=support: self.show_gem_details(s),
                                relief=RAISED, padx=5, pady=2, font=('Arial', 9))
            support_btn.grid(row=row, column=col, sticky=EW, padx=2, pady=2)
        
        # 配置网格权重
        supports_grid.columnconfigure(0, weight=1)
        supports_grid.columnconfigure(1, weight=1)
    
    def create_stats_section(self, parent, recommendation):
        """创建属性区域"""
        # 性能统计
        perf_frame = LabelFrame(parent, text=" 📊 Performance ",
                               bg=self.colors['bg_light'], fg=self.colors['accent_gold'],
                               font=('Arial', 10, 'bold'))
        perf_frame.pack(fill=X, pady=5)
        
        perf = recommendation['performance']
        stats = [
            ("DPS", f"{perf['dps']:,}", self.colors['accent_red']),
            ("EHP", f"{perf['ehp']:,}", self.colors['accent_green']),
            ("Mana", str(perf['mana_cost']), self.colors['accent_blue'])
        ]
        
        for name, value, color in stats:
            stat_frame = Frame(perf_frame, bg=self.colors['bg_light'])
            stat_frame.pack(fill=X, padx=5, pady=2)
            
            Label(stat_frame, text=f"{name}:", bg=self.colors['bg_light'],
                  fg=self.colors['text_normal'], font=('Arial', 9)).pack(side=LEFT)
            Label(stat_frame, text=value, bg=self.colors['bg_light'],
                  fg=color, font=('Arial', 9, 'bold')).pack(side=RIGHT)
        
        # AI评估详情
        ai_frame = LabelFrame(parent, text=" 🤖 AI Analysis ",
                             bg=self.colors['bg_light'], fg=self.colors['accent_gold'],
                             font=('Arial', 10, 'bold'))
        ai_frame.pack(fill=X, pady=5)
        
        ai_assess = recommendation['ai_assessment']
        ai_stats = [
            ("Viability", f"{ai_assess['viability_score']:.1f}/10"),
            ("Realism", f"{ai_assess['realism_score']:.1f}/10"),
            ("Innovation", f"{ai_assess['innovation_score']:.2f}")
        ]
        
        for name, value in ai_stats:
            ai_stat_frame = Frame(ai_frame, bg=self.colors['bg_light'])
            ai_stat_frame.pack(fill=X, padx=5, pady=2)
            
            Label(ai_stat_frame, text=f"{name}:", bg=self.colors['bg_light'],
                  fg=self.colors['text_normal'], font=('Arial', 9)).pack(side=LEFT)
            Label(ai_stat_frame, text=value, bg=self.colors['bg_light'],
                  fg=self.colors['accent_blue'], font=('Arial', 9, 'bold')).pack(side=RIGHT)
        
        # 成本信息
        cost_info = recommendation['practical_info']['estimated_cost']
        cost_label = Label(parent, text=f"💰 Cost: {cost_info}",
                         font=('Arial', 10, 'bold'),
                         fg=self.colors['accent_gold'], bg=self.colors['bg_light'])
        cost_label.pack(pady=10)
    
    def create_action_buttons(self, parent, recommendation):
        """创建操作按钮"""
        # 按钮容器
        btn_frame = Frame(parent, bg=self.colors['bg_light'])
        btn_frame.pack(fill=X)
        
        # 详细信息按钮
        details_btn = Button(btn_frame, text="📋 Details",
                           bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                           command=lambda: self.show_build_details(recommendation),
                           relief=RAISED, padx=10, pady=3, font=('Arial', 9))
        details_btn.pack(side=LEFT, padx=5)
        
        # 导出到PoB按钮
        export_btn = Button(btn_frame, text="📤 Export to PoB2",
                          bg=self.colors['accent_blue'], fg='white',
                          command=lambda: self.export_to_pob(recommendation),
                          relief=RAISED, padx=10, pady=3, font=('Arial', 9, 'bold'))
        export_btn.pack(side=LEFT, padx=5)
        
        # 查看物品链接按钮
        items_btn = Button(btn_frame, text="🔗 View Items",
                         bg=self.colors['accent_green'], fg='white',
                         command=lambda: self.show_item_links(recommendation),
                         relief=RAISED, padx=10, pady=3, font=('Arial', 9, 'bold'))
        items_btn.pack(side=LEFT, padx=5)
        
        # 收藏按钮
        fav_btn = Button(btn_frame, text="⭐ Favorite",
                       bg=self.colors['bg_medium'], fg=self.colors['text_normal'],
                       command=lambda: self.add_to_favorites(recommendation),
                       relief=RAISED, padx=10, pady=3, font=('Arial', 9))
        fav_btn.pack(side=RIGHT, padx=5)
    
    def show_skill_details(self, skill_name):
        """显示技能详情"""
        # 打开poe2db技能页面
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
        # 创建物品链接窗口
        items_window = Toplevel(self.root)
        items_window.title("Item Links - " + recommendation['name'])
        items_window.geometry("600x400")
        items_window.configure(bg=self.colors['bg_dark'])
        
        # 标题
        title_label = Label(items_window, text="🔗 Recommended Items",
                          font=('Arial', 14, 'bold'),
                          fg=self.colors['accent_gold'], bg=self.colors['bg_dark'])
        title_label.pack(pady=20)
        
        # 物品分类
        categories = [
            ("🗡️ Weapons", ["High DPS Weapon", "Spell Damage Staff", "Bow with Critical Multiplier"]),
            ("🛡️ Armor", ["Life + Resistances Chest", "ES Helmet", "Movement Speed Boots"]),
            ("💍 Jewelry", ["Life + Damage Ring", "Resistance Amulet", "Unique Belt"])
        ]
        
        for category, items in categories:
            cat_frame = LabelFrame(items_window, text=category,
                                 bg=self.colors['bg_medium'], fg=self.colors['accent_gold'],
                                 font=('Arial', 11, 'bold'))
            cat_frame.pack(fill=X, padx=20, pady=10)
            
            for item in items:
                item_btn = Button(cat_frame, text=f"🔍 {item}",
                                bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                command=lambda i=item: self.open_trade_search(i),
                                relief=RAISED, padx=10, pady=5)
                item_btn.pack(fill=X, padx=10, pady=2)
    
    def open_trade_search(self, item_name):
        """打开交易搜索"""
        # 这里可以集成实际的交易网站搜索
        trade_url = f"https://poe2scout.com/search?item={item_name.replace(' ', '+')}"
        webbrowser.open(trade_url)
        self.status_var.set(f"Opening trade search: {item_name}")
    
    def export_to_pob(self, recommendation):
        """导出到Path of Building"""
        # 生成PoB导入代码
        pob_code = self.generate_pob_code(recommendation)
        
        # 创建导出窗口
        export_window = Toplevel(self.root)
        export_window.title("Export to PoB2")
        export_window.geometry("500x300")
        export_window.configure(bg=self.colors['bg_dark'])
        
        Label(export_window, text="📤 Path of Building 2 Import Code",
              font=('Arial', 12, 'bold'),
              fg=self.colors['accent_gold'], bg=self.colors['bg_dark']).pack(pady=20)
        
        # 代码文本框
        import tkinter.scrolledtext as st
        code_text = st.ScrolledText(export_window, width=60, height=15,
                                   bg=self.colors['bg_light'], fg=self.colors['text_normal'])
        code_text.pack(padx=20, pady=10)
        code_text.insert(END, pob_code)
        
        # 复制按钮
        copy_btn = Button(export_window, text="📋 Copy to Clipboard",
                         bg=self.colors['accent_blue'], fg='white',
                         command=lambda: self.copy_to_clipboard(pob_code),
                         font=('Arial', 10, 'bold'), padx=20, pady=5)
        copy_btn.pack(pady=10)
    
    def generate_pob_code(self, recommendation):
        """生成Path of Building导入代码"""
        # 简化的PoB导入代码生成
        pob_data = {
            "build_name": recommendation['name'],
            "class": recommendation['character_class'],
            "ascendancy": recommendation['ascendancy'],
            "main_skill": recommendation['main_skill'],
            "support_gems": recommendation['support_gems'],
            "estimated_dps": recommendation['performance']['dps'],
            "estimated_life": recommendation['performance']['ehp']
        }
        
        return f"""PoB2 Build Import Code:
{json.dumps(pob_data, indent=2)}

Instructions:
1. Copy this code
2. Open Path of Building 2
3. Use Import/Export function
4. Paste the code

Note: This is a simplified export. 
For full integration, please use the official PoB2 export feature."""
    
    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("✅ Copied to clipboard")
    
    def show_build_details(self, recommendation):
        """显示构筑详情"""
        # 创建详情窗口
        details_window = Toplevel(self.root)
        details_window.title("Build Details - " + recommendation['name'])
        details_window.geometry("800x600")
        details_window.configure(bg=self.colors['bg_dark'])
        
        # 详情内容
        import tkinter.scrolledtext as st
        details_text = st.ScrolledText(details_window, width=80, height=35,
                                      bg=self.colors['bg_light'], fg=self.colors['text_normal'],
                                      font=('Consolas', 10))
        details_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 格式化详情文本
        details_content = self.format_build_details(recommendation)
        details_text.insert(END, details_content)
    
    def format_build_details(self, rec):
        """格式化构筑详情"""
        details = f"""
{'='*60}
🏆 {rec['name']}
{'='*60}

📋 Basic Information:
   Character: {rec['character_class']} - {rec['ascendancy']}
   Main Skill: {rec['main_skill']}
   Support Gems: {', '.join(rec['support_gems'])}

📊 Performance Statistics:
   DPS Output: {rec['performance']['dps']:,}
   Effective HP: {rec['performance']['ehp']:,}
   Mana Cost: {rec['performance']['mana_cost']}
   Stat Requirements: {rec['performance']['stat_requirements']}

🤖 AI Assessment:
   Viability Score: {rec['ai_assessment']['viability_score']:.1f}/10
   Realism Score: {rec['ai_assessment']['realism_score']:.1f}/10
   Innovation Score: {rec['ai_assessment']['innovation_score']:.2f}/1.0
   Composite Score: {rec['ai_assessment']['composite_score']:.1f}/10

💡 Why Recommended:
"""
        
        for reason in rec['recommendation_analysis']['why_recommended']:
            details += f"   • {reason}\n"
        
        details += f"""
⚠️ Risk Assessment:
   Risk Level: {rec['recommendation_analysis']['risk_level']}
"""
        
        if rec['recommendation_analysis']['risk_factors']:
            for risk in rec['recommendation_analysis']['risk_factors']:
                details += f"   • {risk}\n"
        
        details += f"""
💰 Cost Analysis:
   Estimated Cost: {rec['practical_info']['estimated_cost']}
   Difficulty Rating: {rec['practical_info']['difficulty_rating']}
   League Suitability: {rec['practical_info']['league_suitability']}

🔧 Technical Details:
   Generated By: {rec['metadata']['generated_by']}
   Data Sources: {', '.join(rec['metadata']['data_sources'])}
   Verification: {rec['metadata']['verification_status']}
   Confidence: {rec['metadata']['recommendation_confidence']:.2f}

{'='*60}
"""
        return details
    
    def add_to_favorites(self, recommendation):
        """添加到收藏"""
        # 简单的收藏功能
        self.status_var.set(f"⭐ Added to favorites: {recommendation['name']}")
        messagebox.showinfo("Favorite", f"Build '{recommendation['name']}' added to favorites!")
    
    def quick_high_value(self):
        """快速高价值构筑"""
        self.budget_var.set("10")
        self.complexity_var.set("Medium")
        self.innovation_var.set("balanced")
        self.generate_builds()
    
    def quick_ultra_rare(self):
        """快速超稀有构筑"""
        self.complexity_var.set("High")
        self.innovation_var.set("experimental")
        self.generate_builds()
    
    def quick_budget(self):
        """快速预算构筑"""
        self.budget_var.set("5")
        self.complexity_var.set("Low")
        self.innovation_var.set("conservative")
        self.generate_builds()

def main():
    """启动专业级GUI"""
    root = Tk()
    
    # 设置窗口图标（如果有）
    try:
        root.iconbitmap('poe2_icon.ico')
    except:
        pass
    
    app = PoE2ProfessionalGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()
    except Exception as e:
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()