"""
PoE2 Build Generator主应用程序入口

PyQt6应用程序主类，负责初始化和管理整个GUI应用。
"""

import sys
import os
import asyncio
from typing import Optional
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QDir, Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor

from .main_window import MainWindow
from .styles.poe2_theme import PoE2Theme
# 尝试导入后端编排器，如果失败则使用模拟类
try:
    from ..core.ai_orchestrator import PoE2AIOrchestrator
except ImportError:
    # 如果无法导入，创建一个模拟类用于开发测试
    class PoE2AIOrchestrator:
        def health_check(self):
            return {"mock": {"status": "healthy"}}
        
        def generate_build_recommendation(self, request_data):
            return {"recommendations": [], "status": "mock_mode"}


class PoE2BuildApp(QApplication):
    """PoE2构筑生成器主应用程序类"""
    
    # 信号定义
    backend_status_changed = pyqtSignal(bool)  # 后端状态变化信号
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # 应用程序基本信息
        self.setApplicationName("PoE2 Build Generator")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("PoE2BuildTools")
        self.setOrganizationDomain("poe2buildtools.com")
        
        # 设置应用图标
        self._setup_app_icon()
        
        # 初始化主题
        self.theme = PoE2Theme()
        self._apply_theme()
        
        # 初始化后端连接
        self.orchestrator: Optional[PoE2AIOrchestrator] = None
        self._initialize_backend()
        
        # 创建主窗口
        self.main_window = MainWindow(orchestrator=self.orchestrator)
        
        # 连接信号
        self._connect_signals()
        
    def _setup_app_icon(self):
        """设置应用程序图标"""
        # 优先查找应用图标文件
        icon_paths = [
            "resources/icons/app_icon.png",
            "assets/icons/app_icon.png",
            "gui/styles/icons/poe2_icon.png"
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                return
                
        # 如果没有找到图标文件，使用默认图标
        self.setWindowIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
    
    def _apply_theme(self):
        """应用PoE2暗色主题"""
        # 设置样式表
        self.setStyleSheet(self.theme.get_stylesheet())
        
        # 设置调色板
        palette = self.theme.get_palette()
        self.setPalette(palette)
        
        # PyQt6中高DPI支持默认启用，无需设置
        
    def _initialize_backend(self):
        """初始化后端AI编排器"""
        try:
            # 创建后端编排器（使用默认配置）
            from ..core.ai_orchestrator import PoE2AIOrchestrator
            self.orchestrator = PoE2AIOrchestrator()
            
            # 使用QTimer延迟执行异步初始化，避免阻塞GUI
            QTimer.singleShot(100, self._async_initialize_backend)
            
        except ImportError as e:
            print(f"无法导入后端模块: {e}")
            print("将使用模拟后端运行")
            # 使用模拟编排器
            self.orchestrator = PoE2AIOrchestrator()
            self.backend_status_changed.emit(True)  # 模拟编排器始终可用
        except Exception as e:
            print(f"后端初始化过程中发生严重错误: {e}")
            self.orchestrator = None
            self.backend_status_changed.emit(False)
    
    def _async_initialize_backend(self):
        """异步初始化后端编排器（在独立线程中）"""
        import threading
        
        def init_backend():
            import asyncio
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def init_and_check():
                    if self.orchestrator:
                        init_success = await self.orchestrator.initialize()
                        if not init_success:
                            return False
                        
                        health_status = await self.orchestrator.health_check()
                        is_healthy = health_status.get('overall_status') == 'healthy'
                        return is_healthy
                    return False
                
                # 执行异步初始化
                is_healthy = loop.run_until_complete(init_and_check())
                
                # 使用QTimer.singleShot确保在主线程中发射信号
                QTimer.singleShot(0, lambda: self.backend_status_changed.emit(is_healthy))
                
                if is_healthy:
                    print("后端初始化并健康检查成功。")
                else:
                    print("后端初始化成功，但健康检查失败。")
                    
            except Exception as e:
                print(f"异步后端初始化失败: {e}")
                # 在主线程中发射错误信号
                QTimer.singleShot(0, lambda: self.backend_status_changed.emit(False))
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        # 在独立线程中运行异步初始化
        thread = threading.Thread(target=init_backend)
        thread.daemon = True
        thread.start()
    
    def _connect_signals(self):
        """连接应用程序信号"""
        # 当最后一个窗口关闭时退出应用程序
        self.lastWindowClosed.connect(self.quit)
        
        # 连接后端状态信号到主窗口
        self.backend_status_changed.connect(self.main_window.update_backend_status)
    
    def run(self):
        """运行应用程序"""
        # 显示主窗口
        self.main_window.show()
        
        # 如果后端初始化失败，显示警告
        if not self.orchestrator:
            self._show_backend_warning()
        
        # 进入事件循环
        return self.exec()
    
    def _show_backend_warning(self):
        """显示后端连接警告"""
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle("后端连接警告")
        msg.setText("后端AI编排器初始化失败")
        msg.setInformativeText("应用程序将以离线模式运行，部分功能可能不可用。")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def get_orchestrator(self) -> Optional[PoE2AIOrchestrator]:
        """获取后端编排器实例"""
        return self.orchestrator
    
    def refresh_backend_connection(self):
        """刷新后端连接"""
        self._initialize_backend()


def main():
    """主函数入口点"""
    # PyQt6中高DPI支持默认启用
    
    # 创建并运行应用程序
    app = PoE2BuildApp(sys.argv)
    return app.run()


if __name__ == '__main__':
    sys.exit(main())