"""
降级服务提供者 - 实现优雅降级
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class FallbackProvider(ABC):
    """降级服务提供者抽象基类"""
    
    @abstractmethod
    def provide_fallback(self, service_name: str, operation: str, *args, **kwargs) -> Any:
        """提供降级服务"""
        pass

class PoE2FallbackProvider(FallbackProvider):
    """PoE2专用降级服务提供者"""
    
    def __init__(self):
        # 预置的降级数据
        self.fallback_data = {
            "market_data": self._load_fallback_market_data(),
            "build_templates": self._load_fallback_build_templates(),
            "game_data": self._load_fallback_game_data()
        }
        
    def provide_fallback(self, service_name: str, operation: str, *args, **kwargs) -> Any:
        """提供降级服务"""
        
        if service_name == "poe2_scout":
            return self._provide_scout_fallback(operation, *args, **kwargs)
        elif service_name == "poe2db":
            return self._provide_db_fallback(operation, *args, **kwargs)
        elif service_name == "poe_ninja":
            return self._provide_ninja_fallback(operation, *args, **kwargs)
        else:
            logger.warning(f"No fallback available for service: {service_name}")
            return self._provide_generic_fallback(operation, *args, **kwargs)
            
    def _provide_scout_fallback(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """PoE2 Scout降级服务"""
        
        if operation == "get_market_data":
            return {
                "status": "fallback",
                "data": self.fallback_data["market_data"],
                "message": "使用缓存的市场数据 - PoE2 Scout服务不可用"
            }
        elif operation == "get_build_trends":
            return {
                "status": "fallback",
                "trends": self._get_fallback_trends(),
                "message": "使用预设趋势数据 - PoE2 Scout服务不可用"
            }
        else:
            return self._provide_generic_fallback(operation, *args, **kwargs)
            
    def _provide_db_fallback(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """PoE2DB降级服务"""
        
        if operation == "get_skill_data":
            return {
                "status": "fallback", 
                "skills": self.fallback_data["game_data"]["skills"],
                "message": "使用离线技能数据 - PoE2DB服务不可用"
            }
        elif operation == "get_item_data":
            return {
                "status": "fallback",
                "items": self.fallback_data["game_data"]["items"], 
                "message": "使用离线物品数据 - PoE2DB服务不可用"
            }
        else:
            return self._provide_generic_fallback(operation, *args, **kwargs)
            
    def _provide_ninja_fallback(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """poe.ninja降级服务"""
        
        if operation == "get_popular_builds":
            return {
                "status": "fallback",
                "builds": self.fallback_data["build_templates"],
                "message": "使用预设构筑模板 - poe.ninja服务不可用"
            }
        else:
            return self._provide_generic_fallback(operation, *args, **kwargs)
            
    def _provide_generic_fallback(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """通用降级服务"""
        
        return {
            "status": "error",
            "message": f"服务暂时不可用，请稍后重试。操作: {operation}",
            "fallback": True
        }
        
    def _load_fallback_market_data(self) -> Dict[str, Any]:
        """加载降级市场数据"""
        
        return {
            "currency": {
                "divine": {"chaos_value": 180, "trend": "stable"},
                "exalted": {"chaos_value": 45, "trend": "rising"}
            },
            "popular_items": [
                {"name": "Midnight Fang", "type": "Claw", "avg_price": 12},
                {"name": "Shaper of Storms", "type": "Unique Jewel", "avg_price": 8}
            ]
        }
        
    def _load_fallback_build_templates(self) -> List[Dict[str, Any]]:
        """加载降级构筑模板"""
        
        return [
            {
                "name": "Lightning Arrow Ranger",
                "class": "Ranger", 
                "ascendancy": "Deadeye",
                "main_skill": "Lightning Arrow",
                "estimated_dps": 850000,
                "difficulty": "medium",
                "budget_tier": "medium"
            },
            {
                "name": "Ice Nova Witch",
                "class": "Witch",
                "ascendancy": "Chronomancer", 
                "main_skill": "Ice Nova",
                "estimated_dps": 1200000,
                "difficulty": "high",
                "budget_tier": "high"
            },
            {
                "name": "Ground Slam Warrior",
                "class": "Warrior",
                "ascendancy": "Titan",
                "main_skill": "Ground Slam",
                "estimated_dps": 750000,
                "difficulty": "low",
                "budget_tier": "low"
            }
        ]
        
    def _load_fallback_game_data(self) -> Dict[str, Any]:
        """加载降级游戏数据"""
        
        return {
            "skills": [
                {"name": "Lightning Arrow", "type": "Bow", "damage_type": "Lightning"},
                {"name": "Ice Nova", "type": "Spell", "damage_type": "Cold"},
                {"name": "Ground Slam", "type": "Melee", "damage_type": "Physical"}
            ],
            "items": [
                {"name": "Midnight Fang", "type": "Claw", "tier": "Unique"},
                {"name": "The Last Resort", "type": "Sword", "tier": "Unique"},
                {"name": "Marohi Erqi", "type": "Two Hand Mace", "tier": "Unique"}
            ]
        }
        
    def _get_fallback_trends(self) -> Dict[str, Any]:
        """获取降级趋势数据"""
        
        return {
            "popular_classes": ["Ranger", "Witch", "Warrior"],
            "trending_skills": ["Lightning Arrow", "Ice Nova", "Ground Slam"],
            "meta_shifts": {
                "bow_builds": "rising",
                "spell_builds": "stable", 
                "melee_builds": "declining"
            }
        }
        
    def update_fallback_data(self, service_name: str, data: Dict[str, Any]):
        """更新降级数据（从缓存中获取最新数据时使用）"""
        
        if service_name == "poe2_scout" and "market_data" in data:
            self.fallback_data["market_data"] = data["market_data"]
            logger.info("Updated fallback market data from cache")
            
        elif service_name == "poe_ninja" and "builds" in data:
            self.fallback_data["build_templates"] = data["builds"]
            logger.info("Updated fallback build templates from cache")
            
        elif service_name == "poe2db" and "game_data" in data:
            self.fallback_data["game_data"].update(data["game_data"])
            logger.info("Updated fallback game data from cache")