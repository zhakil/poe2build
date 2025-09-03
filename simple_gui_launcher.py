#!/usr/bin/env python3
"""
简化的PoE2构筑推荐GUI启动器
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class PoE2BuildGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PoE2 AI构筑推荐系统")
        self.root.geometry("900x700")
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        self.create_widgets()
        self.load_ai_system()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="PoE2 AI智能构筑推荐系统", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 参数设置框架
        params_frame = ttk.LabelFrame(main_frame, text="推荐参数", padding="10")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 职业选择
        ttk.Label(params_frame, text="偏好职业:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.class_var = tk.StringVar(value="任意")
        class_combo = ttk.Combobox(params_frame, textvariable=self.class_var, 
                                  values=["任意", "Sorceress", "Witch", "Ranger", "Monk", "Warrior", "Mercenary"])
        class_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # 预算限制
        ttk.Label(params_frame, text="预算限制 (Divine):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.budget_var = tk.StringVar(value="10")
        budget_entry = ttk.Entry(params_frame, textvariable=self.budget_var, width=10)
        budget_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 创新程度
        ttk.Label(params_frame, text="创新程度:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.innovation_var = tk.StringVar(value="balanced")
        innovation_combo = ttk.Combobox(params_frame, textvariable=self.innovation_var,
                                       values=["conservative", "balanced", "experimental"])
        innovation_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # 最低DPS
        ttk.Label(params_frame, text="最低DPS:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.dps_var = tk.StringVar(value="100000")
        dps_entry = ttk.Entry(params_frame, textvariable=self.dps_var, width=10)
        dps_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 生成按钮
        generate_btn = ttk.Button(main_frame, text="🎯 生成AI推荐", 
                                 command=self.generate_recommendations, style="Accent.TButton")
        generate_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 结果显示区域
        results_frame = ttk.LabelFrame(main_frame, text="推荐结果", padding="10")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 结果文本区域
        self.results_text = scrolledtext.ScrolledText(results_frame, width=80, height=25, 
                                                     font=("Consolas", 10))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        params_frame.columnconfigure(1, weight=1)
        
        # 添加欢迎信息
        welcome_text = """
=== PoE2 AI智能构筑推荐系统 ===

🎯 系统特色:
• 基于真实PoE2数据训练的AI推荐
• 智能过滤不靠谱构筑，确保可行性
• 专注冷门高性价比构筑挖掘
• 多维度评估：可行性、现实度、创新度

📋 使用说明:
1. 设置你的偏好参数（职业、预算等）
2. 点击"生成AI推荐"按钮
3. 等待AI分析并生成个性化推荐
4. 查看详细的构筑分析报告

💡 提示: 留空"任意"选项将获得更多样化的推荐

准备好开始了吗？设置参数并点击生成按钮！
        """
        
        self.results_text.insert(tk.END, welcome_text)
        self.results_text.config(state=tk.DISABLED)
    
    def load_ai_system(self):
        """加载AI系统"""
        try:
            from ninja_trained_ai_recommender import NinjaTrainedAIRecommender
            self.ai_recommender = NinjaTrainedAIRecommender()
            self.status_var.set("AI系统加载完成")
        except Exception as e:
            self.status_var.set(f"AI系统加载失败: {e}")
            messagebox.showerror("错误", f"无法加载AI系统：{e}")
    
    def generate_recommendations(self):
        """生成推荐的线程函数"""
        def run_generation():
            try:
                self.status_var.set("正在生成AI推荐...")
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "正在运行AI分析，请稍候...\n\n")
                self.results_text.config(state=tk.DISABLED)
                self.root.update()
                
                # 构建用户偏好
                preferences = {}
                
                if self.class_var.get() != "任意":
                    preferences['preferred_class'] = self.class_var.get()
                
                try:
                    budget = float(self.budget_var.get())
                    preferences['budget_limit'] = budget
                except:
                    pass
                
                preferences['innovation_level'] = self.innovation_var.get()
                
                try:
                    min_dps = int(self.dps_var.get())
                    preferences['min_dps'] = min_dps
                except:
                    pass
                
                # 获取推荐
                recommendations = self.ai_recommender.get_ninja_trained_recommendations(preferences)
                
                # 显示结果
                self.display_recommendations(recommendations)
                self.status_var.set(f"完成！生成了 {len(recommendations)} 个推荐")
                
            except Exception as e:
                self.status_var.set(f"生成失败: {e}")
                messagebox.showerror("错误", f"生成推荐时出错：{e}")
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
    
    def display_recommendations(self, recommendations):
        """显示推荐结果"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        result_text = f"=== AI生成了 {len(recommendations)} 个冷门高性价比构筑 ===\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            result_text += f"🎯 推荐 #{i}: {rec['name']}\n"
            result_text += f"{'='*50}\n"
            result_text += f"职业配置: {rec['character_class']} - {rec['ascendancy']}\n"
            result_text += f"主技能: {rec['main_skill']}\n"
            result_text += f"辅助宝石: {', '.join(rec['support_gems'][:4])}\n"
            result_text += f"\n"
            
            # 性能数据
            perf = rec['performance']
            result_text += f"📊 性能表现:\n"
            result_text += f"  DPS输出: {perf['dps']:,}\n"
            result_text += f"  生存能力: {perf['ehp']:,} EHP\n"
            result_text += f"  法力消耗: {perf['mana_cost']}\n"
            result_text += f"\n"
            
            # AI评估
            ai_assess = rec['ai_assessment']
            result_text += f"🤖 AI评估:\n"
            result_text += f"  可行性: {ai_assess['viability_score']:.1f}/10\n"
            result_text += f"  现实度: {ai_assess['realism_score']:.1f}/10\n"
            result_text += f"  创新度: {ai_assess['innovation_score']:.2f}/1.0\n"
            result_text += f"  综合评分: {ai_assess['composite_score']:.1f}/10\n"
            result_text += f"\n"
            
            # 推荐理由
            analysis = rec['recommendation_analysis']
            if analysis['why_recommended']:
                result_text += f"💡 推荐理由:\n"
                for reason in analysis['why_recommended'][:2]:
                    result_text += f"  • {reason}\n"
                result_text += f"\n"
            
            # 实用信息
            practical = rec['practical_info']
            result_text += f"💰 实用信息:\n"
            result_text += f"  预估成本: {practical['estimated_cost']}\n"
            result_text += f"  操作难度: {practical['difficulty_rating']}\n"
            result_text += f"  适用联赛: {practical['league_suitability']}\n"
            
            # 风险评估
            if analysis.get('risk_factors'):
                result_text += f"\n⚠️  注意事项:\n"
                for risk in analysis['risk_factors'][:2]:
                    result_text += f"  • {risk}\n"
            
            result_text += f"\n{'='*60}\n\n"
        
        # 添加说明
        result_text += f"📋 说明:\n"
        result_text += f"• 以上推荐基于AI训练和真实PoE2数据生成\n"
        result_text += f"• 所有构筑都经过可行性验证，确保实际可用\n"
        result_text += f"• DPS和EHP基于游戏机制真实计算\n"
        result_text += f"• 推荐优先考虑冷门但高性价比的组合\n"
        
        self.results_text.insert(tk.END, result_text)
        self.results_text.config(state=tk.DISABLED)

def main():
    """启动GUI"""
    try:
        root = tk.Tk()
        app = PoE2BuildGUI(root)
        
        # 设置图标（如果有的话）
        try:
            root.iconbitmap('icon.ico')
        except:
            pass
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"GUI启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()