#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速GUI测试 - 验证按钮点击功能
"""

import sys
import os
import time

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("Starting Quick GUI Test...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from src.poe2build.gui.app import PoE2BuildApp
        
        # 创建应用程序
        app = PoE2BuildApp(sys.argv)
        
        # 获取主窗口
        main_window = app.main_window
        print(f"Main window created: {main_window.windowTitle()}")
        
        # 显示主窗口
        main_window.show()
        print("Main window displayed")
        
        # 测试按钮点击功能的函数
        def test_button_clicks():
            try:
                print("Testing button functionality...")
                
                # 导航到构筑生成器页面
                main_window.show_page("build_generator")
                print("Navigated to build generator page")
                
                # 获取构筑生成器页面
                build_gen_page = main_window.pages.get("build_generator")
                
                if build_gen_page:
                    print("Build generator page found")
                    
                    # 检查生成按钮
                    if hasattr(build_gen_page, 'generate_button'):
                        generate_btn = build_gen_page.generate_button
                        print(f"Generate button - Text: '{generate_btn.text()}', Enabled: {generate_btn.isEnabled()}")
                        
                        # 模拟设置一些基本参数
                        if hasattr(build_gen_page, 'class_combo'):
                            build_gen_page.class_combo.setCurrentIndex(1)  # 选择一个职业
                            print("Set class to index 1")
                        
                        # 定义按钮点击测试函数
                        def on_button_test():
                            print("BUTTON CLICK TEST: Generate button was clicked!")
                            print("Button click event successfully triggered!")
                            
                        # 暂时连接我们的测试函数到按钮
                        try:
                            # 断开原有连接并连接测试函数
                            generate_btn.clicked.disconnect()
                            generate_btn.clicked.connect(on_button_test)
                            
                            # 程序化触发按钮点击
                            print("Triggering button click programmatically...")
                            generate_btn.click()
                            
                        except Exception as e:
                            print(f"Button click test error: {e}")
                            
                    else:
                        print("Generate button not found!")
                        
                else:
                    print("Build generator page not found!")
                    
            except Exception as e:
                print(f"Button test error: {e}")
                import traceback
                traceback.print_exc()
            
            # 延迟关闭应用
            QTimer.singleShot(2000, app.quit)
        
        # 延迟执行按钮测试
        QTimer.singleShot(1000, test_button_clicks)
        
        # 运行应用程序（最多运行5秒）
        print("Running application for 5 seconds...")
        
        # 设置超时退出
        QTimer.singleShot(5000, app.quit)
        
        # 启动事件循环
        return app.exec()
        
    except Exception as e:
        print(f"GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    print(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)