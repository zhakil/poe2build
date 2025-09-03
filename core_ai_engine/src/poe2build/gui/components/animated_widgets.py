"""
PoE2风格的动画组件
"""

from PyQt6.QtWidgets import QLabel, QPushButton, QFrame, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPen, QLinearGradient
from PyQt6.QtCore import Qt
from typing import Optional


class PoE2GlowLabel(QLabel):
    """带光效的标签"""
    
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._glow_intensity = 0.0
        self._glow_color = QColor(212, 175, 55)  # PoE2金色
        self._pulse_animation = None
        self.setup_glow_animation()
    
    @pyqtProperty(float)
    def glow_intensity(self) -> float:
        return self._glow_intensity
    
    @glow_intensity.setter
    def glow_intensity(self, value: float):
        self._glow_intensity = value
        self.update()
    
    def setup_glow_animation(self):
        """设置光效动画"""
        self._pulse_animation = QPropertyAnimation(self, b"glow_intensity")
        self._pulse_animation.setDuration(2000)
        self._pulse_animation.setStartValue(0.0)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # 设置循环
        self._pulse_animation.setLoopCount(-1)  # 无限循环
        
        # 反向动画
        self._pulse_animation.finished.connect(self._reverse_animation)
    
    def _reverse_animation(self):
        """反向动画"""
        start_value = self._pulse_animation.startValue()
        end_value = self._pulse_animation.endValue()
        self._pulse_animation.setStartValue(end_value)
        self._pulse_animation.setEndValue(start_value)
    
    def start_glow(self):
        """开始光效"""
        if self._pulse_animation and not self._pulse_animation.state() == QPropertyAnimation.State.Running:
            self._pulse_animation.start()
    
    def stop_glow(self):
        """停止光效"""
        if self._pulse_animation:
            self._pulse_animation.stop()
            self._glow_intensity = 0.0
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制光效
        if self._glow_intensity > 0:
            rect = self.rect()
            center_x = rect.width() // 2
            center_y = rect.height() // 2
            radius = max(rect.width(), rect.height()) // 2
            
            # 创建光效渐变
            gradient = QRadialGradient(center_x, center_y, radius * self._glow_intensity)
            glow_color = QColor(self._glow_color)
            glow_color.setAlphaF(self._glow_intensity * 0.3)
            gradient.setColorAt(0, glow_color)
            glow_color.setAlphaF(0)
            gradient.setColorAt(1, glow_color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawEllipse(center_x - radius, center_y - radius, 
                              radius * 2, radius * 2)
        
        painter.end()
        
        # 调用父类绘制方法
        super().paintEvent(event)


class PoE2AnimatedButton(QPushButton):
    """带动画效果的按钮"""
    
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._scale_factor = 1.0
        self._opacity = 1.0
        self._hover_animation = None
        self._press_animation = None
        self._opacity_effect = None
        
        self.setup_animations()
    
    @pyqtProperty(float)
    def scale_factor(self) -> float:
        return self._scale_factor
    
    @scale_factor.setter
    def scale_factor(self, value: float):
        self._scale_factor = value
        self.update()
    
    @pyqtProperty(float)
    def opacity(self) -> float:
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: float):
        self._opacity = value
        if self._opacity_effect:
            self._opacity_effect.setOpacity(value)
    
    def setup_animations(self):
        """设置动画"""
        # 悬停动画
        self._hover_animation = QPropertyAnimation(self, b"scale_factor")
        self._hover_animation.setDuration(200)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 按下动画
        self._press_animation = QPropertyAnimation(self, b"scale_factor")
        self._press_animation.setDuration(100)
        self._press_animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        
        # 透明度效果
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if self._hover_animation:
            self._hover_animation.stop()
            self._hover_animation.setStartValue(self._scale_factor)
            self._hover_animation.setEndValue(1.05)
            self._hover_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self._hover_animation:
            self._hover_animation.stop()
            self._hover_animation.setStartValue(self._scale_factor)
            self._hover_animation.setEndValue(1.0)
            self._hover_animation.start()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self._press_animation:
            self._press_animation.stop()
            self._press_animation.setStartValue(self._scale_factor)
            self._press_animation.setEndValue(0.95)
            self._press_animation.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if self._press_animation:
            self._press_animation.stop()
            self._press_animation.setStartValue(self._scale_factor)
            self._press_animation.setEndValue(1.05)  # 回到悬停状态
            self._press_animation.start()
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """绘制事件"""
        if self._scale_factor != 1.0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 计算缩放后的矩形
            rect = self.rect()
            scaled_width = rect.width() * self._scale_factor
            scaled_height = rect.height() * self._scale_factor
            x_offset = (rect.width() - scaled_width) / 2
            y_offset = (rect.height() - scaled_height) / 2
            
            # 应用变换
            painter.translate(x_offset, y_offset)
            painter.scale(self._scale_factor, self._scale_factor)
            
            painter.end()
        
        super().paintEvent(event)


class PoE2LoadingSpinner(QWidget):
    """PoE2风格的加载旋转器"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_rotation)
        self._timer.setInterval(50)  # 20 FPS
        
        self.setFixedSize(64, 64)
        self._spinning = False
    
    def start_spinning(self):
        """开始旋转"""
        if not self._spinning:
            self._spinning = True
            self._timer.start()
    
    def stop_spinning(self):
        """停止旋转"""
        if self._spinning:
            self._spinning = False
            self._timer.stop()
            self._angle = 0
            self.update()
    
    def _update_rotation(self):
        """更新旋转角度"""
        self._angle = (self._angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 移动到中心
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self._angle)
        
        # 绘制旋转圆环
        radius = min(self.width(), self.height()) // 2 - 8
        
        # 外圈光环
        outer_gradient = QRadialGradient(0, 0, radius + 4)
        outer_gradient.setColorAt(0, QColor(212, 175, 55, 100))  # PoE2金色
        outer_gradient.setColorAt(1, QColor(212, 175, 55, 0))
        
        painter.setBrush(QBrush(outer_gradient))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(-radius-4, -radius-4, (radius+4)*2, (radius+4)*2)
        
        # 主旋转环
        pen = QPen(QColor(212, 175, 55), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        # 绘制不完整的圆（创建旋转效果）
        painter.drawArc(-radius, -radius, radius*2, radius*2, 0, 270 * 16)
        
        painter.end()


class PoE2PulseFrame(QFrame):
    """脉动边框框架"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._pulse_intensity = 0.0
        self._pulse_animation = None
        self._base_color = QColor(212, 175, 55)  # PoE2金色
        
        self.setup_pulse_animation()
    
    @pyqtProperty(float)
    def pulse_intensity(self) -> float:
        return self._pulse_intensity
    
    @pulse_intensity.setter
    def pulse_intensity(self, value: float):
        self._pulse_intensity = value
        self.update()
    
    def setup_pulse_animation(self):
        """设置脉动动画"""
        self._pulse_animation = QPropertyAnimation(self, b"pulse_intensity")
        self._pulse_animation.setDuration(1500)
        self._pulse_animation.setStartValue(0.3)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)
        
        # 创建往复动画
        def reverse_animation():
            start = self._pulse_animation.startValue()
            end = self._pulse_animation.endValue()
            self._pulse_animation.setStartValue(end)
            self._pulse_animation.setEndValue(start)
        
        self._pulse_animation.finished.connect(reverse_animation)
    
    def start_pulse(self):
        """开始脉动"""
        if self._pulse_animation and not self._pulse_animation.state() == QPropertyAnimation.State.Running:
            self._pulse_animation.start()
    
    def stop_pulse(self):
        """停止脉动"""
        if self._pulse_animation:
            self._pulse_animation.stop()
            self._pulse_intensity = 0.3
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        if self._pulse_intensity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 计算脉动颜色
            color = QColor(self._base_color)
            color.setAlphaF(self._pulse_intensity)
            
            # 绘制脉动边框
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            
            rect = self.rect()
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
            
            painter.end()


class PoE2FadeWidget(QWidget):
    """淡入淡出组件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_animation = None
        
        self.setup_fade_animation()
    
    def setup_fade_animation(self):
        """设置淡入淡出动画"""
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(500)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def fade_in(self, duration: int = 500):
        """淡入"""
        if self._fade_animation:
            self._fade_animation.stop()
            self._fade_animation.setDuration(duration)
            self._fade_animation.setStartValue(0.0)
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.start()
    
    def fade_out(self, duration: int = 500):
        """淡出"""
        if self._fade_animation:
            self._fade_animation.stop()
            self._fade_animation.setDuration(duration)
            self._fade_animation.setStartValue(1.0)
            self._fade_animation.setEndValue(0.0)
            self._fade_animation.start()
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        if self._opacity_effect:
            self._opacity_effect.setOpacity(opacity)