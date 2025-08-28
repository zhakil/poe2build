"""Path of Building Community PoE2本地客户端接口"""

import asyncio
import subprocess
import tempfile
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import os
import signal

try:
    import psutil
except ImportError:
    psutil = None

from .path_detector import PoB2Installation, PoB2PathDetector


class PoB2ProcessState(Enum):
    """PoB2进程状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"  
    RUNNING = "running"
    CALCULATING = "calculating"
    EXPORTING = "exporting"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class PoB2ProcessConfig:
    """PoB2进程配置"""
    timeout: int = 120  # 超时时间(秒)
    memory_limit: int = 2048  # 内存限制(MB)
    startup_wait: int = 10  # 启动等待时间(秒)
    calculation_timeout: int = 60  # 计算超时(秒)
    export_timeout: int = 30  # 导出超时(秒)
    headless_mode: bool = True  # 无界面模式
    log_level: str = "INFO"  # 日志级别


@dataclass
class PoB2Result:
    """PoB2计算结果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    calculation_time: float = 0.0
    export_file: Optional[Path] = None
    process_stats: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'error_message': self.error_message,
            'calculation_time': self.calculation_time,
            'export_file': str(self.export_file) if self.export_file else None,
            'process_stats': self.process_stats
        }


class PoB2LocalClient:
    """Path of Building Community PoE2本地客户端"""
    
    def __init__(self, 
                 installation: Optional[PoB2Installation] = None,
                 config: Optional[PoB2ProcessConfig] = None):
        
        self._logger = logging.getLogger(f"{__name__}.PoB2LocalClient")
        
        self.installation = installation
        self.config = config or PoB2ProcessConfig()
        
        # 进程管理
        self.process: Optional[subprocess.Popen] = None
        self.process_state = PoB2ProcessState.STOPPED
        self.process_pid: Optional[int] = None
        
        # 临时文件管理
        self.temp_dir = Path(tempfile.mkdtemp(prefix='pob2_'))
        self.input_file: Optional[Path] = None
        self.output_file: Optional[Path] = None
        
        # 状态回调
        self.state_callbacks: List[Callable[[PoB2ProcessState], None]] = []
        
        # 如果没有提供安装信息，尝试自动检测
        if not self.installation:
            self._auto_detect_installation()
    
    def _auto_detect_installation(self):
        """自动检测PoB2安装"""
        try:
            detector = PoB2PathDetector()
            # 注意：这里使用同步调用，在实际使用中应该异步调用
            # self.installation = asyncio.run(detector.find_best_installation())
            pass
        except Exception as e:
            self._logger.error(f"自动检测PoB2安装失败: {e}")
    
    async def initialize(self) -> bool:
        """初始化客户端"""
        try:
            # 如果没有安装信息，尝试检测
            if not self.installation:
                detector = PoB2PathDetector()
                self.installation = await detector.find_best_installation()
                
                if not self.installation:
                    self._logger.error("未找到有效的PoB2安装")
                    return False
            
            # 验证安装
            if not await self._validate_installation():
                return False
            
            # 准备临时目录
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            self._logger.info(f"PoB2客户端初始化成功: {self.installation.executable}")
            return True
            
        except Exception as e:
            self._logger.error(f"初始化PoB2客户端失败: {e}")
            return False
    
    async def _validate_installation(self) -> bool:
        """验证PoB2安装"""
        if not self.installation:
            return False
        
        if not self.installation.executable.exists():
            self._logger.error(f"PoB2可执行文件不存在: {self.installation.executable}")
            return False
        
        if not os.access(self.installation.executable, os.X_OK):
            self._logger.error(f"PoB2可执行文件无执行权限: {self.installation.executable}")
            return False
        
        return True
    
    async def start_process(self, import_code: Optional[str] = None) -> bool:
        """启动PoB2进程"""
        try:
            if self.process_state != PoB2ProcessState.STOPPED:
                self._logger.warning("PoB2进程已在运行")
                return True
            
            self._set_state(PoB2ProcessState.STARTING)
            
            # 准备启动参数
            cmd = await self._build_command(import_code)
            
            self._logger.info(f"启动PoB2进程: {' '.join(map(str, cmd))}")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=self.installation.path,
                env=self._get_environment()
            )
            
            self.process_pid = self.process.pid
            self._logger.info(f"PoB2进程已启动，PID: {self.process_pid}")
            
            # 等待启动
            await self._wait_for_startup()
            
            self._set_state(PoB2ProcessState.RUNNING)
            return True
            
        except Exception as e:
            self._logger.error(f"启动PoB2进程失败: {e}")
            self._set_state(PoB2ProcessState.ERROR)
            return False
    
    async def _build_command(self, import_code: Optional[str] = None) -> List[str]:
        """构建启动命令"""
        cmd = [str(self.installation.executable)]
        
        # 无界面模式
        if self.config.headless_mode:
            cmd.extend(['--headless', '--no-gui'])
        
        # 导入代码文件
        if import_code:
            self.input_file = self.temp_dir / 'input.xml'
            await self._write_import_file(import_code)
            cmd.extend(['--import', str(self.input_file)])
        
        # 输出文件
        self.output_file = self.temp_dir / 'output.json'
        cmd.extend(['--export', str(self.output_file), '--format', 'json'])
        
        # 其他参数
        cmd.extend([
            '--timeout', str(self.config.calculation_timeout),
            '--log-level', self.config.log_level
        ])
        
        return cmd
    
    async def _write_import_file(self, import_code: str):
        """写入导入代码文件"""
        try:
            with open(self.input_file, 'w', encoding='utf-8') as f:
                f.write(import_code)
            self._logger.debug(f"导入文件已写入: {self.input_file}")
        except Exception as e:
            self._logger.error(f"写入导入文件失败: {e}")
            raise
    
    def _get_environment(self) -> Dict[str, str]:
        """获取环境变量"""
        env = os.environ.copy()
        
        # 设置内存限制
        if self.config.memory_limit:
            env['POB_MEMORY_LIMIT'] = str(self.config.memory_limit)
        
        # 设置临时目录
        env['POB_TEMP_DIR'] = str(self.temp_dir)
        
        return env
    
    async def _wait_for_startup(self):
        """等待进程启动"""
        start_time = time.time()
        
        while time.time() - start_time < self.config.startup_wait:
            if not self._is_process_running():
                raise RuntimeError("PoB2进程意外退出")
            
            # 检查是否有输出
            if self.process.poll() is None:  # 进程仍在运行
                await asyncio.sleep(0.5)
            else:
                # 进程已退出，检查退出代码
                returncode = self.process.returncode
                if returncode != 0:
                    stdout, stderr = self.process.communicate()
                    error_msg = f"PoB2进程启动失败，退出代码: {returncode}"
                    if stderr:
                        error_msg += f", 错误: {stderr.decode()}"
                    raise RuntimeError(error_msg)
                break
        
        self._logger.info("PoB2进程启动完成")
    
    async def calculate_build(self, import_code: str, timeout: Optional[int] = None) -> PoB2Result:
        """计算构筑数据"""
        calculation_start = time.time()
        
        try:
            self._set_state(PoB2ProcessState.CALCULATING)
            
            # 确保进程正在运行
            if not await self._ensure_process_running(import_code):
                return PoB2Result(
                    success=False,
                    error_message="无法启动PoB2进程"
                )
            
            # 等待计算完成
            result = await self._wait_for_calculation(timeout or self.config.calculation_timeout)
            
            calculation_time = time.time() - calculation_start
            result.calculation_time = calculation_time
            
            self._logger.info(f"构筑计算完成，耗时: {calculation_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self._logger.error(f"构筑计算失败: {e}")
            return PoB2Result(
                success=False,
                error_message=str(e),
                calculation_time=time.time() - calculation_start
            )
        finally:
            self._set_state(PoB2ProcessState.RUNNING)
    
    async def _ensure_process_running(self, import_code: str) -> bool:
        """确保进程正在运行"""
        if self.process_state == PoB2ProcessState.STOPPED:
            return await self.start_process(import_code)
        elif not self._is_process_running():
            await self.stop_process()
            return await self.start_process(import_code)
        
        return True
    
    async def _wait_for_calculation(self, timeout: int) -> PoB2Result:
        """等待计算完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查进程状态
            if not self._is_process_running():
                # 进程已退出，检查输出文件
                if self.output_file and self.output_file.exists():
                    return await self._parse_output_file()
                else:
                    return PoB2Result(
                        success=False,
                        error_message="PoB2进程意外退出，无输出文件"
                    )
            
            # 检查输出文件
            if self.output_file and self.output_file.exists():
                # 等待文件稳定（确保写入完成）
                await asyncio.sleep(1)
                if self.output_file.exists():
                    return await self._parse_output_file()
            
            await asyncio.sleep(0.5)
        
        # 超时
        self._set_state(PoB2ProcessState.TIMEOUT)
        return PoB2Result(
            success=False,
            error_message=f"计算超时 ({timeout}秒)"
        )
    
    async def _parse_output_file(self) -> PoB2Result:
        """解析输出文件"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
            
            # 获取进程统计信息
            process_stats = await self._get_process_stats()
            
            return PoB2Result(
                success=True,
                data=output_data,
                export_file=self.output_file,
                process_stats=process_stats
            )
            
        except Exception as e:
            self._logger.error(f"解析输出文件失败: {e}")
            return PoB2Result(
                success=False,
                error_message=f"解析输出失败: {str(e)}"
            )
    
    async def _get_process_stats(self) -> Dict[str, Any]:
        """获取进程统计信息"""
        stats = {}
        
        if psutil and self.process_pid:
            try:
                process = psutil.Process(self.process_pid)
                stats = {
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'create_time': process.create_time(),
                    'status': process.status()
                }
            except Exception as e:
                self._logger.debug(f"获取进程统计失败: {e}")
        
        return stats
    
    def _is_process_running(self) -> bool:
        """检查进程是否运行"""
        if not self.process:
            return False
        
        # 检查进程是否仍在运行
        if self.process.poll() is not None:
            return False
        
        # 使用psutil进行额外检查
        if psutil and self.process_pid:
            try:
                process = psutil.Process(self.process_pid)
                return process.is_running()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        
        return True
    
    async def stop_process(self, force: bool = False) -> bool:
        """停止PoB2进程"""
        try:
            if self.process_state == PoB2ProcessState.STOPPED:
                return True
            
            self._logger.info("正在停止PoB2进程...")
            
            if self.process:
                if force:
                    # 强制终止
                    self.process.kill()
                else:
                    # 优雅停止
                    self.process.terminate()
                
                # 等待进程退出
                try:
                    await asyncio.wait_for(
                        self._wait_for_process_exit(),
                        timeout=10
                    )
                except asyncio.TimeoutError:
                    self._logger.warning("进程未在预期时间内退出，强制终止")
                    self.process.kill()
                    await self._wait_for_process_exit()
            
            # 清理资源
            self.process = None
            self.process_pid = None
            self._set_state(PoB2ProcessState.STOPPED)
            
            self._logger.info("PoB2进程已停止")
            return True
            
        except Exception as e:
            self._logger.error(f"停止PoB2进程失败: {e}")
            return False
    
    async def _wait_for_process_exit(self):
        """等待进程退出"""
        while self._is_process_running():
            await asyncio.sleep(0.1)
    
    def _set_state(self, state: PoB2ProcessState):
        """设置进程状态"""
        if self.process_state != state:
            old_state = self.process_state
            self.process_state = state
            self._logger.debug(f"进程状态变化: {old_state.value} -> {state.value}")
            
            # 调用状态回调
            for callback in self.state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    self._logger.error(f"状态回调执行失败: {e}")
    
    def add_state_callback(self, callback: Callable[[PoB2ProcessState], None]):
        """添加状态回调"""
        self.state_callbacks.append(callback)
    
    def remove_state_callback(self, callback: Callable[[PoB2ProcessState], None]):
        """移除状态回调"""
        if callback in self.state_callbacks:
            self.state_callbacks.remove(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            'process_state': self.process_state.value,
            'process_pid': self.process_pid,
            'installation_path': str(self.installation.path) if self.installation else None,
            'executable_path': str(self.installation.executable) if self.installation else None,
            'temp_directory': str(self.temp_dir),
            'input_file': str(self.input_file) if self.input_file else None,
            'output_file': str(self.output_file) if self.output_file else None,
            'is_running': self._is_process_running()
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 停止进程
            await self.stop_process(force=True)
            
            # 清理临时文件
            if self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self._logger.debug(f"临时目录已清理: {self.temp_dir}")
            
        except Exception as e:
            self._logger.error(f"清理资源失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if await self.initialize():
            return self
        else:
            raise RuntimeError("PoB2客户端初始化失败")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.cleanup()


# Mock客户端（用于测试和降级）
class MockPoB2LocalClient:
    """Mock PoB2本地客户端"""
    
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(f"{__name__}.MockPoB2LocalClient")
        self.process_state = PoB2ProcessState.STOPPED
    
    async def initialize(self) -> bool:
        """初始化Mock客户端"""
        self._logger.warning("使用Mock PoB2客户端")
        return True
    
    async def start_process(self, import_code: Optional[str] = None) -> bool:
        """启动Mock进程"""
        self.process_state = PoB2ProcessState.RUNNING
        return True
    
    async def calculate_build(self, import_code: str, timeout: Optional[int] = None) -> PoB2Result:
        """Mock计算构筑"""
        self._logger.warning("使用Mock构筑计算")
        
        # 模拟计算时间
        await asyncio.sleep(2)
        
        # 返回Mock数据
        mock_data = {
            'character': {
                'level': 90,
                'class': 'Witch',
                'ascendancy': 'Infernalist'
            },
            'stats': {
                'total_dps': 750000.0,
                'life': 6500,
                'energy_shield': 2000,
                'effective_health_pool': 8500,
                'fire_resistance': 76,
                'cold_resistance': 77,
                'lightning_resistance': 75,
                'chaos_resistance': -25
            },
            'skills': {
                'main_skill': 'Fireball',
                'support_gems': ['Fire Penetration', 'Elemental Focus', 'Controlled Destruction']
            },
            'calculated_by': 'MockPoB2LocalClient',
            'mock': True
        }
        
        return PoB2Result(
            success=True,
            data=mock_data,
            calculation_time=2.0,
            process_stats={'memory_mb': 100, 'cpu_percent': 5.0}
        )
    
    async def stop_process(self, force: bool = False) -> bool:
        """停止Mock进程"""
        self.process_state = PoB2ProcessState.STOPPED
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取Mock状态"""
        return {
            'process_state': self.process_state.value,
            'mock': True,
            'installation_path': 'mock://pob2',
            'is_running': self.process_state != PoB2ProcessState.STOPPED
        }
    
    async def cleanup(self):
        """清理Mock资源"""
        pass
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()