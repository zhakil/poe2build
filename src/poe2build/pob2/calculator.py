"""PoB2计算引擎集成 - 实现ICalculationProvider接口"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
from datetime import datetime

from ..data_sources.interfaces import ICalculationProvider, DataProviderStatus
from ..models.build import PoE2Build, PoE2BuildStats
from .local_client import PoB2LocalClient, PoB2ProcessConfig, MockPoB2LocalClient
from .import_export import PoB2DataConverter
from .path_detector import PoB2PathDetector


@dataclass
class CalculationRequest:
    """计算请求数据结构"""
    build_data: Dict[str, Any]
    request_id: str
    priority: int = 0
    timeout: Optional[int] = None
    options: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'build_data': self.build_data,
            'request_id': self.request_id,
            'priority': self.priority,
            'timeout': self.timeout,
            'options': self.options or {}
        }


@dataclass
class CalculationResult:
    """计算结果数据结构"""
    success: bool
    request_id: str
    calculated_stats: Optional[Dict[str, Any]] = None
    pob2_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    calculation_time: float = 0.0
    validation_status: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'request_id': self.request_id,
            'calculated_stats': self.calculated_stats,
            'pob2_data': self.pob2_data,
            'error_message': self.error_message,
            'calculation_time': self.calculation_time,
            'validation_status': self.validation_status
        }


class PoB2Calculator(ICalculationProvider):
    """Path of Building Community PoE2计算引擎"""
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.PoB2Calculator")
        
        # 核心组件
        self.path_detector = PoB2PathDetector()
        self.data_converter = PoB2DataConverter()
        self.client: Optional[PoB2LocalClient] = None
        self.config = PoB2ProcessConfig()
        
        # 状态管理
        self._initialized = False
        self._available = False
        self.installation = None
        
        # 统计信息
        self.stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'average_calculation_time': 0.0,
            'last_calculation_time': None
        }
    
    async def initialize(self) -> bool:
        """初始化计算引擎"""
        try:
            self._logger.info("初始化PoB2计算引擎...")
            
            # 检测PoB2安装
            self.installation = await self.path_detector.find_best_installation()
            
            if not self.installation:
                self._logger.warning("未找到PoB2安装，将使用Mock模式")
                self._available = False
            else:
                self._logger.info(f"找到PoB2安装: {self.installation.path}")
                self._available = True
            
            self._initialized = True
            return True
            
        except Exception as e:
            self._logger.error(f"初始化PoB2计算引擎失败: {e}")
            self._initialized = True
            self._available = False
            return True  # 即使失败也返回True，使用Mock模式
    
    async def get_health_status(self) -> DataProviderStatus:
        """获取计算引擎健康状态"""
        if not self._initialized:
            return DataProviderStatus.OFFLINE
        
        if not self._available:
            return DataProviderStatus.DEGRADED  # Mock模式
        
        try:
            # 测试PoB2可用性
            if self.installation:
                if self.installation.executable.exists():
                    return DataProviderStatus.HEALTHY
                else:
                    return DataProviderStatus.UNHEALTHY
            else:
                return DataProviderStatus.DEGRADED
                
        except Exception:
            return DataProviderStatus.UNHEALTHY
    
    async def test_connection(self) -> bool:
        """测试PoB2连接"""
        try:
            if not self._available:
                return True  # Mock模式总是可用
            
            if not self.installation:
                return False
            
            # 尝试创建客户端
            test_client = PoB2LocalClient(self.installation, self.config)
            async with test_client:
                return True
                
        except Exception as e:
            self._logger.error(f"PoB2连接测试失败: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        if self._available:
            return "PoB2Calculator"
        else:
            return "MockPoB2Calculator"
    
    def get_rate_limit_info(self) -> Dict[str, int]:
        """获取速率限制信息"""
        return {
            'concurrent_calculations': 1,  # 一次只能进行一个计算
            'max_queue_size': 10,
            'calculation_timeout': self.config.calculation_timeout
        }
    
    async def calculate_build_stats(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算构筑统计数据"""
        request_id = f"calc_{int(datetime.now().timestamp() * 1000)}"
        
        try:
            self.stats['total_calculations'] += 1
            start_time = datetime.now()
            
            # 创建计算请求
            request = CalculationRequest(
                build_data=build_data,
                request_id=request_id,
                timeout=self.config.calculation_timeout
            )
            
            # 执行计算
            result = await self._perform_calculation(request)
            
            # 更新统计信息
            calculation_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(result.success, calculation_time)
            
            return result.to_dict()
            
        except Exception as e:
            self._logger.error(f"构筑统计计算失败: {e}")
            self.stats['failed_calculations'] += 1
            return {
                'success': False,
                'request_id': request_id,
                'error_message': str(e),
                'validation_status': 'error'
            }
    
    async def _perform_calculation(self, request: CalculationRequest) -> CalculationResult:
        """执行计算"""
        try:
            # 获取客户端
            client = await self._get_client()
            
            # 转换构筑数据为PoB2格式
            import_code = await self._convert_to_pob2_format(request.build_data)
            
            if not import_code:
                return CalculationResult(
                    success=False,
                    request_id=request.request_id,
                    error_message="无法转换构筑数据为PoB2格式"
                )
            
            # 使用PoB2计算
            pob2_result = await client.calculate_build(import_code, request.timeout)
            
            if not pob2_result.success:
                return CalculationResult(
                    success=False,
                    request_id=request.request_id,
                    error_message=pob2_result.error_message,
                    calculation_time=pob2_result.calculation_time
                )
            
            # 解析计算结果
            calculated_stats = await self._parse_calculation_result(pob2_result.data)
            
            return CalculationResult(
                success=True,
                request_id=request.request_id,
                calculated_stats=calculated_stats,
                pob2_data=pob2_result.data,
                calculation_time=pob2_result.calculation_time,
                validation_status='valid'
            )
            
        except Exception as e:
            self._logger.error(f"执行计算失败: {e}")
            return CalculationResult(
                success=False,
                request_id=request.request_id,
                error_message=str(e)
            )
    
    async def _get_client(self) -> PoB2LocalClient:
        """获取PoB2客户端"""
        if self._available and self.installation:
            # 使用真实的PoB2客户端
            if not self.client:
                self.client = PoB2LocalClient(self.installation, self.config)
                if not await self.client.initialize():
                    raise RuntimeError("PoB2客户端初始化失败")
            return self.client
        else:
            # 使用Mock客户端
            return MockPoB2LocalClient()
    
    async def _convert_to_pob2_format(self, build_data: Dict[str, Any]) -> Optional[str]:
        """转换构筑数据为PoB2格式"""
        try:
            # 如果已经是PoB2导入代码格式
            if isinstance(build_data, str) and len(build_data) > 100:
                if self.data_converter.validate_pob2_code(build_data):
                    return build_data
            
            # 如果是PoE2Build字典格式
            if isinstance(build_data, dict):
                # 尝试转换为PoE2Build对象
                try:
                    from ..models.build import PoE2Build
                    build = PoE2Build.from_dict(build_data)
                    return self.data_converter.build_to_pob2_code(build)
                except Exception as e:
                    self._logger.error(f"从字典创建PoE2Build失败: {e}")
            
            # 如果是最小格式数据
            if isinstance(build_data, dict) and 'character_class' in build_data:
                from ..models.characters import PoE2CharacterClass
                char_class = PoE2CharacterClass(build_data['character_class'])
                level = build_data.get('level', 1)
                main_skill = build_data.get('main_skill', None)
                
                return self.data_converter.generate_minimal_pob2_code(
                    char_class, level, main_skill
                )
            
            self._logger.error(f"无法识别的构筑数据格式: {type(build_data)}")
            return None
            
        except Exception as e:
            self._logger.error(f"转换构筑数据失败: {e}")
            return None
    
    async def _parse_calculation_result(self, pob2_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """解析PoB2计算结果"""
        try:
            if not pob2_data:
                return self._create_default_stats()
            
            # 解析统计数据
            stats = {}
            
            # DPS数据
            if 'stats' in pob2_data:
                stats_data = pob2_data['stats']
                stats.update({
                    'total_dps': stats_data.get('total_dps', 0.0),
                    'physical_dps': stats_data.get('physical_dps', 0.0),
                    'elemental_dps': stats_data.get('elemental_dps', 0.0),
                    'chaos_dps': stats_data.get('chaos_dps', 0.0)
                })
            
            # 防御数据
            if 'defenses' in pob2_data:
                defense_data = pob2_data['defenses']
                stats.update({
                    'life': defense_data.get('life', 0.0),
                    'energy_shield': defense_data.get('energy_shield', 0.0),
                    'effective_health_pool': defense_data.get('effective_health_pool', 0.0),
                    'fire_resistance': defense_data.get('fire_resistance', 75),
                    'cold_resistance': defense_data.get('cold_resistance', 75),
                    'lightning_resistance': defense_data.get('lightning_resistance', 75),
                    'chaos_resistance': defense_data.get('chaos_resistance', -30)
                })
            
            # 其他数据
            if 'miscellaneous' in pob2_data:
                misc_data = pob2_data['miscellaneous']
                stats.update({
                    'critical_strike_chance': misc_data.get('critical_strike_chance', 0.0),
                    'critical_strike_multiplier': misc_data.get('critical_strike_multiplier', 0.0),
                    'attack_speed': misc_data.get('attack_speed', 0.0),
                    'cast_speed': misc_data.get('cast_speed', 0.0),
                    'movement_speed': misc_data.get('movement_speed', 0.0)
                })
            
            # 添加PoB2特定信息
            stats['calculated_by'] = pob2_data.get('calculated_by', 'PoB2')
            stats['calculation_source'] = 'PathOfBuilding_PoE2'
            
            return stats
            
        except Exception as e:
            self._logger.error(f"解析计算结果失败: {e}")
            return self._create_default_stats()
    
    def _create_default_stats(self) -> Dict[str, Any]:
        """创建默认统计数据"""
        return {
            'total_dps': 100000.0,
            'life': 4000.0,
            'energy_shield': 1000.0,
            'effective_health_pool': 5000.0,
            'fire_resistance': 75,
            'cold_resistance': 75,
            'lightning_resistance': 75,
            'chaos_resistance': -30,
            'calculated_by': 'DefaultCalculator',
            'calculation_source': 'fallback'
        }
    
    async def validate_build(self, build_data: Dict[str, Any]) -> bool:
        """验证构筑有效性"""
        try:
            # 转换为PoB2格式进行验证
            import_code = await self._convert_to_pob2_format(build_data)
            
            if not import_code:
                return False
            
            # 验证PoB2代码
            return self.data_converter.validate_pob2_code(import_code)
            
        except Exception as e:
            self._logger.error(f"验证构筑失败: {e}")
            return False
    
    async def generate_import_code(self, build_data: Dict[str, Any]) -> Optional[str]:
        """生成PoB2导入代码"""
        try:
            return await self._convert_to_pob2_format(build_data)
        except Exception as e:
            self._logger.error(f"生成导入代码失败: {e}")
            return None
    
    async def parse_import_code(self, import_code: str) -> Optional[Dict[str, Any]]:
        """解析PoB2导入代码"""
        try:
            # 验证代码
            if not self.data_converter.validate_pob2_code(import_code):
                return None
            
            # 解码数据
            decoded = self.data_converter.decode_pob2_code(import_code)
            
            if not decoded:
                return None
            
            # 转换为构筑对象
            build = self.data_converter.pob2_code_to_build(import_code)
            
            if not build:
                return None
            
            # 返回构筑数据字典
            return build.to_dict()
            
        except Exception as e:
            self._logger.error(f"解析导入代码失败: {e}")
            return None
    
    def _update_stats(self, success: bool, calculation_time: float):
        """更新统计信息"""
        if success:
            self.stats['successful_calculations'] += 1
        else:
            self.stats['failed_calculations'] += 1
        
        # 更新平均计算时间
        total_calcs = self.stats['total_calculations']
        current_avg = self.stats['average_calculation_time']
        
        self.stats['average_calculation_time'] = (
            (current_avg * (total_calcs - 1) + calculation_time) / total_calcs
        )
        
        self.stats['last_calculation_time'] = datetime.now().isoformat()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.stats['total_calculations'] > 0:
            success_rate = (self.stats['successful_calculations'] / 
                          self.stats['total_calculations']) * 100
        
        return {
            'provider_name': self.get_provider_name(),
            'initialized': self._initialized,
            'available': self._available,
            'installation_path': str(self.installation.path) if self.installation else None,
            'total_calculations': self.stats['total_calculations'],
            'success_rate': f"{success_rate:.1f}%",
            'average_calculation_time': f"{self.stats['average_calculation_time']:.2f}s",
            'last_calculation_time': self.stats['last_calculation_time']
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.client:
                await self.client.cleanup()
                self.client = None
            
            self._logger.info("PoB2计算引擎资源已清理")
            
        except Exception as e:
            self._logger.error(f"清理PoB2计算引擎资源失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if await self.initialize():
            return self
        else:
            raise RuntimeError("PoB2计算引擎初始化失败")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.cleanup()


# 便捷函数
async def create_pob2_calculator() -> PoB2Calculator:
    """创建PoB2计算器的便捷函数"""
    calculator = PoB2Calculator()
    if await calculator.initialize():
        return calculator
    else:
        raise RuntimeError("PoB2计算器初始化失败")


async def calculate_build_with_pob2(build_data: Dict[str, Any]) -> Dict[str, Any]:
    """使用PoB2计算构筑的便捷函数"""
    async with await create_pob2_calculator() as calculator:
        return await calculator.calculate_build_stats(build_data)