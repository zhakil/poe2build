"""
GUI后端通信客户端

负责GUI与后端AI协调器的异步通信，提供：
1. 异步的AI协调器调用接口
2. 线程安全的数据传输
3. 完整的错误处理和重试机制
4. 进度反馈和状态更新
5. PoB2服务集成检测
"""

import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QApplication

# 尝试导入后端模块，如果失败则使用模拟实现
try:
    from ...core.ai_orchestrator import PoE2AIOrchestrator, UserRequest, RecommendationResult
    from ...models.build import PoE2BuildGoal, PoE2Build, PoE2BuildStats
    from ...models.characters import PoE2CharacterClass, PoE2Ascendancy
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    # 延迟logger定义到这里，避免循环导入
    
    # 模拟实现
    class PoE2BuildGoal:
        ENDGAME_CONTENT = "endgame_content"
        BOSS_KILLING = "boss_killing"
        CLEAR_SPEED = "clear_speed"
        LEAGUE_START = "league_start"
    
    class PoE2CharacterClass:
        WITCH = "witch"
        SORCERESS = "sorceress"
        RANGER = "ranger"
        MONK = "monk"
        WARRIOR = "warrior"
        MERCENARY = "mercenary"
    
    class PoE2Ascendancy:
        pass
    
    class PoE2BuildStats:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def is_resistance_capped(self):
            return True
    
    class PoE2Build:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class UserRequest:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class RecommendationResult:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class PoE2AIOrchestrator:
        def __init__(self, config=None):
            self._initialized = True
        
        async def initialize(self):
            return True
        
        async def health_check(self):
            return {"overall_status": "healthy", "components": {}}
        
        async def generate_build_recommendations(self, user_request):
            from dataclasses import dataclass
            @dataclass
            class RecommendationResult:
                builds: list
                metadata: dict
                rag_confidence: float
                pob2_validated: bool
                generation_time_ms: int
                used_components: list
            
            return RecommendationResult(
                builds=[],
                metadata={"fallback": True},
                rag_confidence=0.5,
                pob2_validated=False,
                generation_time_ms=100,
                used_components=[]
            )


# 配置日志
logger = logging.getLogger(__name__)

# 如果后端不可用，在这里输出警告信息
if not BACKEND_AVAILABLE:
    logger.warning("后端模块不可用，将使用模拟实现")


class RequestStatus(Enum):
    """请求状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """进度更新数据"""
    progress: int  # 0-100
    stage: str
    message: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class BackendWorkerThread(QThread):
    """后端处理工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(dict)  # 进度更新
    result_ready = pyqtSignal(dict)  # 结果就绪
    error_occurred = pyqtSignal(dict)  # 发生错误
    status_changed = pyqtSignal(str)  # 状态变化
    
    def __init__(self, backend_client, request_data: Dict[str, Any]):
        super().__init__()
        self.backend_client = backend_client
        self.request_data = request_data
        self.is_cancelled = False
        self._current_orchestrator = None
        
    def run(self):
        """执行后端请求"""
        try:
            # 在工作线程中创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 执行异步操作
                result = loop.run_until_complete(self._process_request())
                
                if not self.is_cancelled:
                    self.result_ready.emit(result)
                    
            finally:
                loop.close()
                
        except Exception as e:
            if not self.is_cancelled:
                error_data = {
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': time.time()
                }
                self.error_occurred.emit(error_data)
    
    async def _process_request(self) -> Dict[str, Any]:
        """处理后端请求"""
        if self.is_cancelled:
            return {}
            
        # Stage 1: 初始化
        self._emit_progress(5, "initialization", "初始化后端协调器...")
        
        orchestrator = await self.backend_client._get_orchestrator()
        self._current_orchestrator = orchestrator
        
        if self.is_cancelled:
            return {}
            
        # Stage 2: 验证系统健康
        self._emit_progress(15, "health_check", "检查系统组件状态...")
        
        health_status = await orchestrator.health_check()
        logger.info(f"系统健康状态: {health_status.get('overall_status', 'unknown')}")
        
        if self.is_cancelled:
            return {}
            
        # Stage 3: 数据转换
        self._emit_progress(25, "data_conversion", "转换请求数据...")
        
        user_request = self.backend_client._convert_gui_request(self.request_data)
        
        if self.is_cancelled:
            return {}
            
        # Stage 4: 生成推荐
        self._emit_progress(40, "generation", "生成AI构筑推荐...")
        
        try:
            result = await orchestrator.generate_build_recommendations(user_request)
        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            # 尝试降级处理
            self._emit_progress(60, "fallback", "使用备用方案生成推荐...")
            result = await self._generate_fallback_result(user_request)
        
        if self.is_cancelled:
            return {}
            
        # Stage 5: 处理结果
        self._emit_progress(80, "processing", "处理生成结果...")
        
        processed_result = self.backend_client._process_backend_result(result)
        
        if self.is_cancelled:
            return {}
            
        # Stage 6: 完成
        self._emit_progress(100, "completed", "构筑推荐生成完成!")
        
        return processed_result
    
    def _emit_progress(self, progress: int, stage: str, message: str):
        """发射进度更新信号"""
        if not self.is_cancelled:
            progress_data = asdict(ProgressUpdate(progress, stage, message))
            self.progress_updated.emit(progress_data)
    
    async def _generate_fallback_result(self, user_request: UserRequest) -> RecommendationResult:
        """生成备用结果"""
        from poe2build.models.build import PoE2Build, PoE2BuildStats
        
        # 创建基本的备用构筑
        fallback_build = PoE2Build(
            name=f"备用 {user_request.character_class.value if user_request.character_class else 'Generic'} 构筑",
            character_class=user_request.character_class or PoE2CharacterClass.WITCH,
            level=85,
            ascendancy=user_request.ascendancy,
            stats=PoE2BuildStats(
                total_dps=300000,
                effective_health_pool=5000,
                fire_resistance=75,
                cold_resistance=75,
                lightning_resistance=75,
                chaos_resistance=-30
            ),
            estimated_cost=user_request.max_budget * 0.5 if user_request.max_budget else 5.0,
            goal=user_request.build_goal or PoE2BuildGoal.ENDGAME_CONTENT,
            main_skill_gem="推荐技能",
            notes="此为系统不可用时的备用推荐，建议稍后重试获取更准确的推荐。"
        )
        
        return RecommendationResult(
            builds=[fallback_build],
            metadata={
                'fallback_mode': True,
                'generation_timestamp': time.time(),
                'warning': '主系统暂时不可用，这是备用推荐'
            },
            rag_confidence=0.3,
            pob2_validated=False,
            generation_time_ms=100,
            used_components=[]
        )
    
    def cancel(self):
        """取消操作"""
        self.is_cancelled = True
        if self._current_orchestrator:
            logger.info("取消当前构筑生成请求")


class BackendClient(QObject):
    """
    GUI后端通信客户端
    
    提供GUI与后端AI协调器之间的异步通信桥梁
    """
    
    # 信号定义
    progress_updated = pyqtSignal(dict)  # 进度更新
    build_generated = pyqtSignal(dict)  # 构筑生成完成
    error_occurred = pyqtSignal(dict)  # 发生错误
    status_changed = pyqtSignal(str)  # 状态变化
    pob2_status_changed = pyqtSignal(dict)  # PoB2状态变化
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or {}
        self._orchestrator: Optional[PoE2AIOrchestrator] = None
        self._initialization_task = None
        self._current_status = RequestStatus.IDLE
        self._worker_thread: Optional[BackendWorkerThread] = None
        
        # 重试配置
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1000)  # ms
        
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._check_backend_status)
        self.status_timer.start(30000)  # 每30秒检查一次
        
        logger.info("BackendClient 已创建")
    
    async def initialize(self) -> bool:
        """
        异步初始化后端连接
        
        Returns:
            初始化是否成功
        """
        if self._orchestrator and self._orchestrator._initialized:
            return True
        
        logger.info("开始初始化后端协调器...")
        self._set_status(RequestStatus.INITIALIZING)
        
        try:
            # 加载配置
            orchestrator_config = self._load_orchestrator_config()
            
            # 创建协调器实例
            self._orchestrator = PoE2AIOrchestrator(orchestrator_config)
            
            # 异步初始化
            success = await self._orchestrator.initialize()
            
            if success:
                logger.info("后端协调器初始化成功")
                self._set_status(RequestStatus.IDLE)
                
                # 检查PoB2状态
                await self._check_pob2_status()
                
                return True
            else:
                logger.error("后端协调器初始化失败")
                self._set_status(RequestStatus.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"后端协调器初始化异常: {e}")
            self._set_status(RequestStatus.ERROR)
            return False
    
    def generate_build_async(self, request_data: Dict[str, Any]) -> bool:
        """
        异步生成构筑推荐
        
        Args:
            request_data: GUI表单数据
            
        Returns:
            是否成功启动生成过程
        """
        if self._current_status not in [RequestStatus.IDLE, RequestStatus.COMPLETED, RequestStatus.ERROR]:
            logger.warning(f"当前状态 {self._current_status.value} 不允许新的请求")
            return False
        
        if not self._orchestrator:
            logger.error("后端协调器未初始化")
            self._emit_error("后端协调器未初始化，请先初始化系统")
            return False
        
        # 验证请求数据
        validation_result = self._validate_request_data(request_data)
        if not validation_result['valid']:
            self._emit_error(f"请求数据验证失败: {validation_result['error']}")
            return False
        
        # 设置状态并启动工作线程
        self._set_status(RequestStatus.PROCESSING)
        
        try:
            # 创建工作线程
            self._worker_thread = BackendWorkerThread(self, request_data)
            
            # 连接信号
            self._worker_thread.progress_updated.connect(self._on_progress_updated)
            self._worker_thread.result_ready.connect(self._on_result_ready)
            self._worker_thread.error_occurred.connect(self._on_error_occurred)
            self._worker_thread.finished.connect(self._on_thread_finished)
            
            # 启动线程
            self._worker_thread.start()
            
            logger.info("构筑生成请求已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动构筑生成失败: {e}")
            self._set_status(RequestStatus.ERROR)
            self._emit_error(f"启动构筑生成失败: {str(e)}")
            return False
    
    def cancel_current_request(self) -> bool:
        """
        取消当前请求
        
        Returns:
            是否成功取消
        """
        if self._worker_thread and self._worker_thread.isRunning():
            logger.info("取消当前构筑生成请求")
            self._worker_thread.cancel()
            self._worker_thread.quit()
            self._worker_thread.wait(5000)  # 等待5秒
            
            self._set_status(RequestStatus.CANCELLED)
            return True
        
        return False
    
    async def check_backend_health(self) -> Dict[str, Any]:
        """
        检查后端健康状态
        
        Returns:
            健康检查结果
        """
        if not self._orchestrator:
            return {
                'overall_status': 'error',
                'error': '后端协调器未初始化'
            }
        
        try:
            health_result = await self._orchestrator.health_check()
            logger.debug(f"后端健康检查: {health_result.get('overall_status', 'unknown')}")
            return health_result
            
        except Exception as e:
            logger.error(f"后端健康检查失败: {e}")
            return {
                'overall_status': 'error',
                'error': str(e)
            }
    
    async def get_pob2_status(self) -> Dict[str, Any]:
        """
        获取PoB2服务状态
        
        Returns:
            PoB2状态信息
        """
        if not self._orchestrator:
            return {
                'available': False,
                'local_client': False,
                'web_client': False,
                'error': '后端协调器未初始化'
            }
        
        try:
            health_result = await self._orchestrator.health_check()
            components = health_result.get('components', {})
            
            local_status = components.get('pob2_local', {})
            web_status = components.get('pob2_web', {})
            
            return {
                'available': (
                    local_status.get('status') == 'healthy' or 
                    web_status.get('status') == 'healthy'
                ),
                'local_client': local_status.get('status') == 'healthy',
                'web_client': web_status.get('status') == 'healthy',
                'local_response_time': local_status.get('response_time_ms'),
                'web_response_time': web_status.get('response_time_ms'),
                'local_error': local_status.get('error_message'),
                'web_error': web_status.get('error_message')
            }
            
        except Exception as e:
            logger.error(f"获取PoB2状态失败: {e}")
            return {
                'available': False,
                'local_client': False,
                'web_client': False,
                'error': str(e)
            }
    
    def get_current_status(self) -> str:
        """获取当前状态"""
        return self._current_status.value
    
    def is_busy(self) -> bool:
        """检查是否忙碌"""
        return self._current_status in [
            RequestStatus.INITIALIZING,
            RequestStatus.PROCESSING
        ]
    
    def _load_orchestrator_config(self) -> Dict[str, Any]:
        """加载协调器配置"""
        default_config = {
            "max_recommendations": 10,
            "default_budget": 15.0,
            "cache_ttl": 3600,
            "pob2": {
                "enable_local": True,
                "enable_web": True,
                "timeout": 30
            },
            "rag": {
                "confidence_threshold": 0.7,
                "max_results": 20
            },
            "market": {
                "update_interval": 600,
                "cache_size": 1000
            },
            "retry": {
                "max_attempts": 3,
                "backoff_factor": 2.0
            }
        }
        
        # 合并用户配置
        config = default_config.copy()
        if 'orchestrator' in self.config:
            self._deep_update(config, self.config['orchestrator'])
        
        return config
    
    def _deep_update(self, target: Dict, source: Dict):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _validate_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证请求数据"""
        try:
            # 检查必需字段
            if 'preferences' not in request_data:
                return {'valid': False, 'error': '缺少preferences字段'}
            
            preferences = request_data['preferences']
            
            # 检查职业选择
            if 'class' not in preferences or not preferences['class']:
                return {'valid': False, 'error': '必须选择职业'}
            
            # 验证数值范围
            if 'level' in preferences:
                level = preferences['level']
                if not isinstance(level, int) or level < 1 or level > 100:
                    return {'valid': False, 'error': '等级必须在1-100之间'}
            
            # 验证预算
            if 'budget' in preferences and preferences['budget']:
                budget = preferences['budget']
                if 'amount' in budget and budget['amount'] is not None:
                    if not isinstance(budget['amount'], (int, float)) or budget['amount'] < 0:
                        return {'valid': False, 'error': '预算金额必须为非负数'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'数据验证异常: {str(e)}'}
    
    def _convert_gui_request(self, gui_data: Dict[str, Any]) -> UserRequest:
        """将GUI请求转换为后端格式"""
        preferences = gui_data.get('preferences', {})
        
        # 解析职业
        character_class = None
        class_name = preferences.get('class', '').lower()
        class_mapping = {
            '女巫': PoE2CharacterClass.WITCH,
            'witch': PoE2CharacterClass.WITCH,
            '法师': PoE2CharacterClass.SORCERESS,
            'sorceress': PoE2CharacterClass.SORCERESS,
            '游侠': PoE2CharacterClass.RANGER,
            'ranger': PoE2CharacterClass.RANGER,
            '僧侣': PoE2CharacterClass.MONK,
            'monk': PoE2CharacterClass.MONK,
            '战士': PoE2CharacterClass.WARRIOR,
            'warrior': PoE2CharacterClass.WARRIOR,
            '女猎手': PoE2CharacterClass.MERCENARY,
            'huntress': PoE2CharacterClass.MERCENARY,
            'mercenary': PoE2CharacterClass.MERCENARY
        }
        
        if class_name in class_mapping:
            character_class = class_mapping[class_name]
        
        # 解析构筑目标
        build_goal = None
        goal = preferences.get('goal', '').lower()
        goal_mapping = {
            'balanced': PoE2BuildGoal.ENDGAME_CONTENT,
            'high_dps': PoE2BuildGoal.BOSS_KILLING,
            'tanky': PoE2BuildGoal.ENDGAME_CONTENT,
            'clear_speed': PoE2BuildGoal.CLEAR_SPEED,
            'boss_killing': PoE2BuildGoal.BOSS_KILLING,
            'beginner_friendly': PoE2BuildGoal.LEAGUE_START
        }
        
        if goal in goal_mapping:
            build_goal = goal_mapping[goal]
        
        # 解析预算
        budget_info = preferences.get('budget', {})
        max_budget = budget_info.get('amount') if budget_info.get('amount', 0) > 0 else None
        
        # 创建UserRequest
        user_request = UserRequest(
            character_class=character_class,
            build_goal=build_goal,
            max_budget=max_budget,
            currency_type=budget_info.get('currency', 'divine_orb'),
            preferred_skills=preferences.get('preferred_skills'),
            playstyle=preferences.get('playstyle', 'balanced'),
            min_dps=preferences.get('min_dps'),
            min_ehp=preferences.get('min_ehp'),
            require_resistance_cap=True,
            include_meta_builds=preferences.get('include_meta_builds', True),
            include_budget_builds=preferences.get('include_budget_builds', True),
            max_build_complexity=preferences.get('max_build_complexity', 'medium'),
            generate_pob2_code=preferences.get('pob2_integration', {}).get('generate_import_code', True),
            validate_with_pob2=preferences.get('pob2_integration', {}).get('calculate_stats', True)
        )
        
        return user_request
    
    def _process_backend_result(self, result: RecommendationResult) -> Dict[str, Any]:
        """处理后端结果"""
        try:
            # 转换构筑列表
            builds_data = []
            for build in result.builds:
                build_data = {
                    'name': build.name,
                    'character_class': build.character_class.value,
                    'ascendancy': build.ascendancy.value if build.ascendancy else None,
                    'level': build.level,
                    'estimated_cost': build.estimated_cost,
                    'currency_type': getattr(build, 'currency_type', 'divine'),
                    'main_skill_gem': build.main_skill_gem,
                    'support_gems': build.support_gems or [],
                    'key_items': build.key_items or [],
                    'passive_keystones': build.passive_keystones or [],
                    'pob2_code': build.pob2_code,
                    'notes': build.notes,
                    'goal': build.goal.value if build.goal else None
                }
                
                # 添加统计数据
                if build.stats:
                    build_data['stats'] = {
                        'total_dps': build.stats.total_dps,
                        'effective_health_pool': build.stats.effective_health_pool,
                        'life': getattr(build.stats, 'life', 0),
                        'energy_shield': getattr(build.stats, 'energy_shield', 0),
                        'fire_resistance': build.stats.fire_resistance,
                        'cold_resistance': build.stats.cold_resistance,
                        'lightning_resistance': build.stats.lightning_resistance,
                        'chaos_resistance': build.stats.chaos_resistance,
                        'is_resistance_capped': build.stats.is_resistance_capped()
                    }
                
                builds_data.append(build_data)
            
            # 构建最终结果
            processed_result = {
                'success': True,
                'builds': builds_data,
                'metadata': result.metadata,
                'rag_confidence': result.rag_confidence,
                'pob2_validated': result.pob2_validated,
                'generation_time_ms': result.generation_time_ms,
                'used_components': [comp.value for comp in result.used_components],
                'timestamp': time.time()
            }
            
            return processed_result
            
        except Exception as e:
            logger.error(f"处理后端结果失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def _get_orchestrator(self) -> PoE2AIOrchestrator:
        """获取协调器实例（确保已初始化）"""
        if not self._orchestrator:
            await self.initialize()
        
        if not self._orchestrator._initialized:
            await self._orchestrator.initialize()
        
        return self._orchestrator
    
    async def _check_pob2_status(self):
        """检查PoB2状态"""
        try:
            status = await self.get_pob2_status()
            self.pob2_status_changed.emit(status)
        except Exception as e:
            logger.error(f"检查PoB2状态失败: {e}")
    
    def _check_backend_status(self):
        """定期检查后端状态"""
        if self._orchestrator and not self.is_busy():
            # 在主线程中异步运行
            QTimer.singleShot(0, self._async_status_check)
    
    def _async_status_check(self):
        """异步状态检查"""
        async def check():
            try:
                health = await self.check_backend_health()
                pob2_status = await self.get_pob2_status()
                
                # 发射状态更新信号
                if health.get('overall_status') != 'healthy':
                    logger.warning(f"后端状态异常: {health.get('overall_status')}")
                
                self.pob2_status_changed.emit(pob2_status)
                
            except Exception as e:
                logger.error(f"状态检查失败: {e}")
        
        # 创建新的事件循环来运行异步函数
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(check())
            loop.close()
        except Exception as e:
            logger.error(f"异步状态检查失败: {e}")
    
    def _set_status(self, status: RequestStatus):
        """设置当前状态"""
        if self._current_status != status:
            self._current_status = status
            self.status_changed.emit(status.value)
            logger.debug(f"状态变更: {status.value}")
    
    def _emit_error(self, message: str, error_type: str = "GeneralError"):
        """发射错误信号"""
        error_data = {
            'error': message,
            'error_type': error_type,
            'timestamp': time.time()
        }
        self.error_occurred.emit(error_data)
    
    def _on_progress_updated(self, progress_data: Dict[str, Any]):
        """处理进度更新"""
        self.progress_updated.emit(progress_data)
    
    def _on_result_ready(self, result_data: Dict[str, Any]):
        """处理结果就绪"""
        self._set_status(RequestStatus.COMPLETED)
        self.build_generated.emit(result_data)
    
    def _on_error_occurred(self, error_data: Dict[str, Any]):
        """处理错误发生"""
        self._set_status(RequestStatus.ERROR)
        self.error_occurred.emit(error_data)
    
    def _on_thread_finished(self):
        """处理线程完成"""
        if self._worker_thread:
            self._worker_thread.deleteLater()
            self._worker_thread = None
        
        logger.debug("工作线程已完成")
    
    def cleanup(self):
        """清理资源"""
        # 停止状态检查定时器
        if self.status_timer:
            self.status_timer.stop()
        
        # 取消当前请求
        self.cancel_current_request()
        
        # 清理协调器
        self._orchestrator = None
        
        logger.info("BackendClient 资源已清理")