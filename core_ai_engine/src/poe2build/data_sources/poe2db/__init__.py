"""
PoE2DB数据源模块 - 完整游戏数据库集成
https://poe2db.tw/cn/

提供装备属性、技能详情、升华信息等完整游戏数据
"""

from .api_client import (
    PoE2DBClient,
    ItemDetail,
    SkillDetail, 
    AscendancyInfo,
    get_poe2db_client
)

__all__ = [
    'PoE2DBClient',
    'ItemDetail', 
    'SkillDetail',
    'AscendancyInfo',
    'get_poe2db_client'
]