"""
PoE2资源管理器 - 处理图片、动画和图标
"""

import os
import sys
from typing import Dict, Optional
from PyQt6.QtGui import QPixmap, QIcon, QMovie, QPainter, QBrush, QRadialGradient, QLinearGradient, QPen
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication

class PoE2ResourceManager:
    """PoE2资源管理器"""
    
    def __init__(self):
        self.base_path = self._get_resource_base_path()
        self.images: Dict[str, QPixmap] = {}
        self.icons: Dict[str, QIcon] = {}
        self.animations: Dict[str, QMovie] = {}
        
        # 创建默认资源
        self._create_default_resources()
    
    def _get_resource_base_path(self) -> str:
        """获取资源基础路径"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的执行文件
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            current_dir = os.path.dirname(__file__)
            base_path = os.path.join(current_dir, '..', '..', '..', '..', 'resources')
        
        return os.path.abspath(base_path)
    
    def _create_default_resources(self):
        """创建默认资源（程序化生成）"""
        
        # PoE2金色光效图标
        self._create_golden_orb_icon()
        
        # 职业图标
        self._create_class_icons()
        
        # 状态指示器
        self._create_status_indicators()
        
        # 背景纹理
        self._create_background_textures()
    
    def _create_golden_orb_icon(self):
        """创建金色法球图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 外层光环
        outer_gradient = QRadialGradient(32, 32, 30)
        outer_gradient.setColorAt(0, Qt.GlobalColor.transparent)
        outer_gradient.setColorAt(0.7, Qt.GlobalColor.transparent)
        outer_gradient.setColorAt(1, Qt.GlobalColor.yellow)
        painter.setBrush(QBrush(outer_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        
        # 主体球
        main_gradient = QRadialGradient(32, 32, 25)
        main_gradient.setColorAt(0, Qt.GlobalColor.yellow)
        main_gradient.setColorAt(0.6, Qt.GlobalColor.darkYellow)
        main_gradient.setColorAt(1, Qt.GlobalColor.darkGray)
        painter.setBrush(QBrush(main_gradient))
        painter.drawEllipse(7, 7, 50, 50)
        
        # 高光
        highlight_gradient = QRadialGradient(25, 25, 15)
        highlight_gradient.setColorAt(0, Qt.GlobalColor.white)
        highlight_gradient.setColorAt(1, Qt.GlobalColor.transparent)
        painter.setBrush(QBrush(highlight_gradient))
        painter.drawEllipse(15, 15, 25, 25)
        
        painter.end()
        
        self.images['golden_orb'] = pixmap
        self.icons['golden_orb'] = QIcon(pixmap)
    
    def _create_class_icons(self):
        """创建职业图标"""
        classes = {
            'Witch': Qt.GlobalColor.magenta,
            'Ranger': Qt.GlobalColor.green,
            'Warrior': Qt.GlobalColor.red,
            'Monk': Qt.GlobalColor.yellow,
            'Sorceress': Qt.GlobalColor.blue,
            'Mercenary': Qt.GlobalColor.gray
        }
        
        for class_name, color in classes.items():
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 背景圆
            gradient = QRadialGradient(16, 16, 14)
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, Qt.GlobalColor.black)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawEllipse(2, 2, 28, 28)
            
            # 简单的职业符号
            painter.setPen(QPen(Qt.GlobalColor.white, 3))
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            
            if 'Witch' in class_name or 'Sorceress' in class_name:
                # 法杖符号
                painter.drawLine(16, 8, 16, 24)
                painter.drawEllipse(13, 6, 6, 6)
            elif 'Ranger' in class_name:
                # 弓箭符号
                painter.drawLine(8, 12, 24, 20)
                painter.drawLine(8, 20, 24, 12)
            elif 'Warrior' in class_name:
                # 剑盾符号
                painter.drawLine(12, 8, 12, 24)
                painter.drawLine(8, 12, 16, 12)
            elif 'Monk' in class_name:
                # 拳头符号
                painter.drawEllipse(12, 12, 8, 8)
            else:
                # 默认符号
                painter.drawEllipse(12, 12, 8, 8)
            
            painter.end()
            
            self.images[f'class_{class_name.lower()}'] = pixmap
            self.icons[f'class_{class_name.lower()}'] = QIcon(pixmap)
    
    def _create_status_indicators(self):
        """创建状态指示器"""
        statuses = {
            'healthy': Qt.GlobalColor.green,
            'warning': Qt.GlobalColor.yellow,
            'error': Qt.GlobalColor.red,
            'offline': Qt.GlobalColor.gray
        }
        
        for status, color in statuses.items():
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 状态圆点
            gradient = QRadialGradient(8, 8, 6)
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, Qt.GlobalColor.black)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.drawEllipse(2, 2, 12, 12)
            
            painter.end()
            
            self.images[f'status_{status}'] = pixmap
            self.icons[f'status_{status}'] = QIcon(pixmap)
    
    def _create_background_textures(self):
        """创建背景纹理"""
        # 创建金属纹理
        metal_pixmap = QPixmap(100, 100)
        metal_pixmap.fill(Qt.GlobalColor.black)
        
        painter = QPainter(metal_pixmap)
        
        # 添加金属光泽效果
        gradient = QLinearGradient(0, 0, 100, 100)
        gradient.setColorAt(0, Qt.GlobalColor.darkGray)
        gradient.setColorAt(0.5, Qt.GlobalColor.gray)
        gradient.setColorAt(1, Qt.GlobalColor.darkGray)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, 100, 100)
        
        painter.end()
        
        self.images['metal_texture'] = metal_pixmap
    
    def get_image(self, name: str, size: Optional[QSize] = None) -> Optional[QPixmap]:
        """获取图片"""
        if name in self.images:
            pixmap = self.images[name]
            if size:
                return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
            return pixmap
        
        # 尝试从文件加载
        return self._load_image_from_file(name, size)
    
    def get_icon(self, name: str, size: Optional[QSize] = None) -> Optional[QIcon]:
        """获取图标"""
        if name in self.icons:
            return self.icons[name]
        
        # 尝试从图片创建图标
        pixmap = self.get_image(name, size)
        if pixmap:
            icon = QIcon(pixmap)
            self.icons[name] = icon
            return icon
        
        return None
    
    def get_animation(self, name: str) -> Optional[QMovie]:
        """获取动画"""
        if name in self.animations:
            return self.animations[name]
        
        # 尝试从文件加载动画
        return self._load_animation_from_file(name)
    
    def _load_image_from_file(self, name: str, size: Optional[QSize] = None) -> Optional[QPixmap]:
        """从文件加载图片"""
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']
        
        for ext in image_extensions:
            file_path = os.path.join(self.base_path, 'images', f'{name}{ext}')
            if os.path.exists(file_path):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    if size:
                        pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
                    self.images[name] = pixmap
                    return pixmap
        
        return None
    
    def _load_animation_from_file(self, name: str) -> Optional[QMovie]:
        """从文件加载动画"""
        animation_extensions = ['.gif', '.webp']
        
        for ext in animation_extensions:
            file_path = os.path.join(self.base_path, 'animations', f'{name}{ext}')
            if os.path.exists(file_path):
                movie = QMovie(file_path)
                if movie.isValid():
                    self.animations[name] = movie
                    return movie
        
        return None
    
    def create_loading_animation(self) -> QMovie:
        """创建加载动画"""
        # 这里可以创建程序化的加载动画
        # 或者使用现有的GIF文件
        loading_anim = self.get_animation('loading_spinner')
        if loading_anim:
            return loading_anim
        
        # 创建简单的加载动画（实际应用中可以使用GIF）
        return None
    
    def apply_glow_effect(self, pixmap: QPixmap, glow_color: Qt.GlobalColor = Qt.GlobalColor.yellow) -> QPixmap:
        """为图片添加光效"""
        if pixmap.isNull():
            return pixmap
        
        # 创建光效版本
        glowed = QPixmap(pixmap.size() + QSize(20, 20))
        glowed.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(glowed)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制光晕
        from PyQt6.QtGui import QRadialGradient
        glow_gradient = QRadialGradient(glowed.width()//2, glowed.height()//2, 
                                       max(glowed.width(), glowed.height())//2)
        glow_gradient.setColorAt(0, glow_color)
        glow_gradient.setColorAt(1, Qt.GlobalColor.transparent)
        
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, glowed.width(), glowed.height())
        
        # 绘制原图
        painter.drawPixmap(10, 10, pixmap)
        painter.end()
        
        return glowed


# 全局资源管理器实例
_resource_manager = None

def get_resource_manager() -> PoE2ResourceManager:
    """获取全局资源管理器实例"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = PoE2ResourceManager()
    return _resource_manager