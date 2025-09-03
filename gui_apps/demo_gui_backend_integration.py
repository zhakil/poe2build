#!/usr/bin/env python3
"""
GUI后端集成演示脚本

演示GUI与AI协调器后端的完整集成功能，包括：
1. 异步构筑生成
2. 实时进度反馈
3. 错误处理和恢复
4. PoB2状态监控
5. 数据转换和验证

运行要求：
- Python 3.8+
- PyQt6
- 所有后端依赖项
"""

import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import QTimer

from poe2build.gui.pages.build_generator_page import BuildGeneratorPage
from poe2build.gui.services.backend_client import BackendClient
from poe2build.gui.widgets.error_handler import ErrorHandler, NotificationType
from poe2build.gui.widgets.pob2_status_widget import PoB2StatusWidget


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/gui_demo.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PoE2 GUI后端集成演示")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 后端配置
        backend_config = {
            'orchestrator': {
                'max_recommendations': 10,
                'cache_ttl': 3600,
                'pob2': {
                    'enable_local': True,
                    'enable_web': True,
                    'timeout': 30
                },
                'rag': {
                    'confidence_threshold': 0.7
                },
                'retry': {
                    'max_attempts': 3,
                    'backoff_factor': 2.0
                }
            },
            'max_retries': 3,
            'retry_delay': 1000
        }
        
        # 构筑生成器页面
        self.build_generator = BuildGeneratorPage(backend_config, self)
        self.build_generator.build_generated.connect(self._on_build_generated)
        tab_widget.addTab(self.build_generator, "AI构筑生成器")
        
        # 后端状态监控页面
        self.backend_client = BackendClient(backend_config, self)
        self.status_widget = PoB2StatusWidget(self.backend_client, self)
        tab_widget.addTab(self.status_widget, "PoB2状态监控")
        
        # 错误处理演示页面
        self.error_handler = ErrorHandler(self)
        tab_widget.addTab(self.error_handler, "错误处理演示")
        
        # 启动演示
        self._start_demo()
        
        logger.info("演示主窗口已启动")
    
    def _start_demo(self):
        """启动演示"""
        # 显示欢迎消息
        QTimer.singleShot(1000, self._show_welcome_message)
        
        # 演示错误处理
        QTimer.singleShot(3000, self._demo_error_handling)
        
        # 演示通知系统
        QTimer.singleShot(5000, self._demo_notifications)
    
    def _show_welcome_message(self):
        """显示欢迎消息"""
        self.error_handler.show_notification(
            NotificationType.INFO,
            "欢迎使用PoE2构筑生成器",
            "这是GUI后端集成系统的演示，展示完整的AI构筑推荐功能",
            auto_close=True,
            duration=6000
        )
    
    def _demo_error_handling(self):
        """演示错误处理"""
        # 模拟一个恢复错误
        self.error_handler.handle_error(
            ConnectionError("模拟网络连接超时"),
            context="演示错误处理",
            title="演示错误",
            show_dialog=False,
            recoverable=True
        )
    
    def _demo_notifications(self):
        """演示通知系统"""
        # 成功通知
        self.error_handler.show_notification(
            NotificationType.SUCCESS,
            "系统就绪",
            "所有组件已初始化完成，可以开始生成构筑推荐",
            actions=["开始生成"],
            auto_close=True,
            duration=4000
        )
        
        # 延迟显示警告通知
        QTimer.singleShot(2000, self._show_warning_notification)
    
    def _show_warning_notification(self):
        """显示警告通知"""
        self.error_handler.show_notification(
            NotificationType.WARNING,
            "PoB2状态提醒",
            "建议安装本地PoB2客户端以获得最佳体验",
            actions=["查看状态", "了解更多"],
            auto_close=False
        )
    
    def _on_build_generated(self, build_data):
        """处理构筑生成完成"""
        builds = build_data.get('builds', [])
        logger.info(f"构筑生成完成，共 {len(builds)} 个推荐")
        
        # 显示生成结果摘要
        if builds:
            self.error_handler.show_notification(
                NotificationType.SUCCESS,
                "构筑生成成功",
                f"成功生成 {len(builds)} 个AI构筑推荐，点击查看详情",
                actions=["查看构筑"],
                auto_close=False
            )
        
        # 在这里可以打开构筑结果页面或处理结果数据
        self._display_build_summary(builds)
    
    def _display_build_summary(self, builds):
        """显示构筑摘要"""
        if not builds:
            return
        
        summary_lines = ["=== 构筑推荐摘要 ==="]
        
        for i, build in enumerate(builds[:3], 1):  # 只显示前3个
            name = build.get('name', f'构筑 {i}')
            character_class = build.get('character_class', {}).get('display_name', '未知职业')
            cost = build.get('estimated_cost', 0)
            
            stats = build.get('stats', {})
            dps = stats.get('offensive', {}).get('total_dps', {}).get('formatted', '未知')
            ehp = stats.get('defensive', {}).get('effective_health_pool', {}).get('formatted', '未知')
            
            summary_lines.extend([
                f"\n{i}. {name}",
                f"   职业: {character_class}",
                f"   预算: {cost:.1f} divine",
                f"   DPS: {dps}",
                f"   EHP: {ehp}"
            ])
        
        logger.info("\n".join(summary_lines))
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 清理资源
        try:
            self.build_generator.cleanup()
            self.backend_client.cleanup()
            self.status_widget.cleanup()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
        
        event.accept()


def main():
    """主函数"""
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("PoE2 GUI后端集成演示")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #3c3c3c;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 16px;
            margin: 2px;
            border-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #4d4d4d;
            color: #d4af37;
        }
        
        QTabBar::tab:hover {
            background-color: #505050;
        }
    """)
    
    try:
        # 创建并显示主窗口
        window = DemoMainWindow()
        window.show()
        
        logger.info("PoE2 GUI后端集成演示已启动")
        logger.info("="*50)
        logger.info("演示功能:")
        logger.info("1. AI构筑生成 - 填写表单并点击生成")
        logger.info("2. PoB2状态监控 - 查看服务状态")
        logger.info("3. 错误处理 - 自动错误处理和用户反馈")
        logger.info("4. 实时通知 - 系统状态和操作反馈")
        logger.info("="*50)
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"演示程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()