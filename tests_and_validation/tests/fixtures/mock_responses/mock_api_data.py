"""
Mock API数据 - 测试用的模拟API响应数据

提供各种测试场景下的模拟API响应，包括：
- 成功响应
- 错误响应
- 边界情况
- 性能测试数据
"""

from datetime import datetime, timedelta
import json


# =============================================================================
# PoE2Scout API Mock 数据
# =============================================================================

MOCK_SCOUT_API_RESPONSES = {
    # 成功响应
    'success': {
        'staff_of_power': {
            'status_code': 200,
            'json_data': {
                'item_name': 'Staff of Power',
                'median_price': 15.5,
                'mean_price': 16.2,
                'min_price': 12.0,
                'max_price': 22.0,
                'currency': 'divine',
                'listings_count': 47,
                'confidence': 0.92,
                'last_updated': '2024-01-15T14:30:22Z',
                'price_history': [
                    {'date': '2024-01-14', 'price': 14.8},
                    {'date': '2024-01-13', 'price': 15.2},
                    {'date': '2024-01-12', 'price': 16.0}
                ],
                'market_trend': 'stable'
            }
        },
        'lightning_amulet': {
            'status_code': 200,
            'json_data': {
                'item_name': 'Lightning Amulet',
                'median_price': 3.2,
                'currency': 'divine',
                'listings_count': 28,
                'confidence': 0.87,
                'last_updated': '2024-01-15T14:25:18Z'
            }
        },
        'budget_item': {
            'status_code': 200,
            'json_data': {
                'item_name': 'Basic Wand',
                'median_price': 0.8,
                'currency': 'divine',
                'listings_count': 156,
                'confidence': 0.95,
                'last_updated': '2024-01-15T14:35:45Z'
            }
        }
    },
    
    # 错误响应
    'errors': {
        'item_not_found': {
            'status_code': 404,
            'json_data': {
                'error': 'Item not found',
                'message': 'No listings found for this item',
                'suggestions': ['Staff of Power', 'Lightning Wand']
            }
        },
        'rate_limited': {
            'status_code': 429,
            'json_data': {
                'error': 'Rate limit exceeded',
                'message': 'Too many requests, please slow down',
                'retry_after': 60
            },
            'headers': {'Retry-After': '60'}
        },
        'server_error': {
            'status_code': 500,
            'json_data': {
                'error': 'Internal server error',
                'message': 'Temporary server issue, please try again later'
            }
        },
        'timeout': {
            'side_effect': 'timeout',
            'exception_type': 'requests.exceptions.Timeout'
        }
    }
}


# =============================================================================
# Ninja Scraper Mock 数据
# =============================================================================

MOCK_NINJA_RESPONSES = {
    'meta_builds': {
        'success': [
            {
                'name': 'Lightning Sorceress Meta',
                'character_class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'main_skill': 'Lightning Bolt',
                'support_gems': ['Added Lightning', 'Lightning Penetration', 'Elemental Focus'],
                'estimated_dps': 1250000,
                'level': 94,
                'popularity_percent': 18.5,
                'popularity_rank': 1,
                'league': 'Standard',
                'sample_size': 245,
                'last_updated': '2024-01-15T12:00:00Z'
            },
            {
                'name': 'Ice Shot Ranger',
                'character_class': 'Ranger',
                'ascendancy': 'Deadeye',
                'main_skill': 'Ice Shot',
                'support_gems': ['Added Cold Damage', 'Pierce', 'Elemental Damage'],
                'estimated_dps': 850000,
                'level': 88,
                'popularity_percent': 12.8,
                'popularity_rank': 3,
                'league': 'Standard',
                'sample_size': 186
            },
            {
                'name': 'Budget Monk Invoker',
                'character_class': 'Monk',
                'ascendancy': 'Invoker',
                'main_skill': 'Spirit Wave',
                'support_gems': ['Melee Physical Damage', 'Increased Area'],
                'estimated_dps': 450000,
                'level': 82,
                'popularity_percent': 8.2,
                'popularity_rank': 8,
                'league': 'Standard',
                'sample_size': 95,
                'tags': ['budget', 'league_start']
            }
        ],
        'filtered_sorceress': [
            {
                'name': 'Lightning Sorceress Meta',
                'character_class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'estimated_dps': 1250000,
                'popularity_percent': 18.5
            },
            {
                'name': 'Ice Sorceress Build',
                'character_class': 'Sorceress',
                'ascendancy': 'Chronomancer',
                'estimated_dps': 920000,
                'popularity_percent': 7.3
            }
        ]
    },
    
    'errors': {
        'parsing_failed': {
            'exception_type': 'ParseError',
            'message': 'Failed to parse HTML content'
        },
        'connection_error': {
            'exception_type': 'ConnectionError',
            'message': 'Failed to connect to poe.ninja'
        }
    }
}


# =============================================================================
# PoB2 Integration Mock 数据
# =============================================================================

MOCK_POB2_RESPONSES = {
    'local_client': {
        'available': {
            'is_available': True,
            'version': '2.35.1',
            'installation_path': 'C:\\Path of Building Community\\PathOfBuilding.exe'
        },
        'unavailable': {
            'is_available': False,
            'error': 'PoB2 installation not found'
        },
        'calculate_stats': {
            'lightning_build': {
                'total_dps': 875000,
                'ehp': 8200,
                'fire_res': 78,
                'cold_res': 76,
                'lightning_res': 79,
                'chaos_res': -25,
                'life': 5800,
                'energy_shield': 2400,
                'critical_strike_chance': 52.0,
                'critical_strike_multiplier': 340.0,
                'attack_speed': 2.2,
                'cast_speed': 3.8,
                'movement_speed': 118.0,
                'validation_status': 'valid',
                'calculated_by': 'pob2_local_v2.35.1',
                'calculation_time_ms': 1250
            },
            'budget_build': {
                'total_dps': 420000,
                'ehp': 6500,
                'fire_res': 75,
                'cold_res': 75,
                'lightning_res': 75,
                'chaos_res': -30,
                'life': 4800,
                'energy_shield': 1700,
                'validation_status': 'valid',
                'calculated_by': 'pob2_local_v2.35.1'
            }
        },
        'generate_build_code': {
            'lightning_build': 'eNrtXVuP2zYS_jUFn9uEFN2epwRo0KTYom2CJkWLfTBoaMqMLSKSVIlyvMji3y8lXRz7kth1XLsnOQ-2ZpCEo5lvvpkZ6n-77_95-_E6ePD99ej9v379-dvvr4p2_vAP_vfvw',
            'budget_build': 'eNqdlluPmzYYhu_7K1YrndM_X8BarSJ1pE7UHak7Uh-4Qwdms0mRjcOYJJ5f37Ezh9meVpMrJMFr3_e-7_U'
        }
    },
    
    'web_client': {
        'calculate_stats': {
            'fallback_result': {
                'total_dps': 720000,
                'ehp': 7800,
                'fire_res': 75,
                'cold_res': 75,
                'lightning_res': 75,
                'chaos_res': -30,
                'validation_status': 'valid',
                'calculated_by': 'pob2_web_fallback',
                'calculation_time_ms': 3500
            }
        },
        'generate_build_code': {
            'web_code': 'eNrFWFuP2jgYfd-_wpm3kT9fkqdVVdVWq7aq2m1V7QP3gQnuBIiJQ0Knv37tJJCEzHR2ND3sE_Ix53z-fCE5N98_'
        }
    },
    
    'errors': {
        'calculation_failed': {
            'exception_type': 'CalculationError',
            'message': 'Failed to calculate build statistics',
            'details': 'Invalid skill tree configuration'
        },
        'timeout': {
            'exception_type': 'TimeoutError', 
            'message': 'PoB2 calculation timed out after 10 seconds'
        }
    }
}


# =============================================================================
# RAG System Mock 数据
# =============================================================================

MOCK_RAG_RESPONSES = {
    'recommendations': {
        'lightning_focused': [
            {
                'name': 'RAG Lightning Sorceress Pro',
                'character_class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'level': 92,
                'main_skill': 'Lightning Bolt',
                'support_gems': ['Added Lightning', 'Lightning Penetration', 'Elemental Focus', 'Spell Echo'],
                'estimated_dps': 820000,
                'estimated_ehp': 8200,
                'estimated_cost': 18.5,
                'confidence': 0.91,
                'source_similarity': 0.89,
                'reasoning': 'Based on analysis of 15 similar high-performance lightning builds',
                'key_items': ['Staff of Lightning', 'Thunder Amulet', 'Storm Ring'],
                'passive_keystones': ['Elemental Overload', 'Lightning Mastery', 'Spell Damage'],
                'pros': ['Excellent single-target DPS', 'Good AoE clear', 'Endgame viable'],
                'cons': ['Requires specific unique items', 'Mana management needed']
            },
            {
                'name': 'RAG Lightning Hybrid',
                'character_class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'level': 88,
                'main_skill': 'Chain Lightning',
                'support_gems': ['Added Lightning', 'Chain', 'Elemental Focus'],
                'estimated_dps': 650000,
                'estimated_ehp': 7500,
                'estimated_cost': 12.0,
                'confidence': 0.84,
                'source_similarity': 0.76,
                'reasoning': 'Hybrid approach balancing DPS and survivability'
            }
        ],
        'budget_focused': [
            {
                'name': 'RAG Budget Starter',
                'character_class': 'Monk',
                'ascendancy': 'Invoker',
                'level': 80,
                'main_skill': 'Spirit Wave',
                'support_gems': ['Melee Physical Damage', 'Increased Area'],
                'estimated_dps': 350000,
                'estimated_ehp': 6800,
                'estimated_cost': 3.5,
                'confidence': 0.82,
                'source_similarity': 0.71,
                'reasoning': 'Optimized for league start and low budget scenarios',
                'tags': ['league_start', 'budget', 'beginner_friendly']
            }
        ]
    },
    
    'vectorization': {
        'sample_vectors': {
            'lightning_build': [0.15, -0.23, 0.41, 0.67, -0.12],  # 简化的向量示例
            'budget_build': [0.31, 0.18, -0.45, 0.22, 0.56],
            'endgame_build': [-0.67, 0.89, 0.14, -0.33, 0.75]
        },
        'similarity_scores': {
            'high_similarity': 0.92,
            'medium_similarity': 0.76,
            'low_similarity': 0.54
        }
    },
    
    'errors': {
        'model_unavailable': {
            'exception_type': 'ModelError',
            'message': 'RAG model temporarily unavailable'
        },
        'insufficient_context': {
            'exception_type': 'ContextError',
            'message': 'Insufficient training data for this build type'
        }
    }
}


# =============================================================================
# 缓存系统 Mock 数据
# =============================================================================

MOCK_CACHE_DATA = {
    'popular_builds': {
        'cache_key': 'builds:popular:standard',
        'cached_data': [
            {
                'name': 'Cached Lightning Build',
                'character_class': 'Sorceress',
                'estimated_dps': 750000,
                'estimated_cost': 14.0,
                'confidence': 0.86,
                'source': 'cached_popular_builds',
                'cached_at': '2024-01-15T13:00:00Z',
                'cache_ttl': 1800
            }
        ]
    },
    
    'market_prices': {
        'cache_key': 'market:staff_of_power:standard',
        'cached_data': {
            'item_name': 'Staff of Power',
            'median_price': 15.2,
            'confidence': 0.90,
            'cached_at': '2024-01-15T13:45:00Z',
            'cache_ttl': 600
        }
    },
    
    'user_sessions': {
        'cache_key': 'session:user_123:preferences',
        'cached_data': {
            'character_class': 'Sorceress',
            'preferred_skills': ['Lightning Bolt', 'Chain Lightning'],
            'budget_range': [10.0, 25.0],
            'build_goals': ['endgame_content', 'boss_killing'],
            'session_start': '2024-01-15T12:30:00Z'
        }
    }
}


# =============================================================================
# 错误场景数据
# =============================================================================

MOCK_ERROR_SCENARIOS = {
    'network_errors': {
        'connection_timeout': {
            'exception_type': 'requests.exceptions.ConnectTimeout',
            'message': 'Connection timeout after 30 seconds'
        },
        'read_timeout': {
            'exception_type': 'requests.exceptions.ReadTimeout',
            'message': 'Read timeout after 60 seconds'
        },
        'connection_error': {
            'exception_type': 'requests.exceptions.ConnectionError',
            'message': 'Failed to establish connection'
        }
    },
    
    'api_errors': {
        'authentication_failed': {
            'status_code': 401,
            'message': 'Invalid API credentials'
        },
        'forbidden': {
            'status_code': 403,
            'message': 'Access forbidden - insufficient permissions'
        },
        'service_unavailable': {
            'status_code': 503,
            'message': 'Service temporarily unavailable'
        }
    },
    
    'validation_errors': {
        'invalid_build_data': {
            'exception_type': 'ValidationError',
            'message': 'Build data validation failed',
            'details': {
                'level': 'Level must be between 1 and 100',
                'dps': 'DPS cannot be negative'
            }
        },
        'missing_required_fields': {
            'exception_type': 'ValidationError',
            'message': 'Required fields missing',
            'missing_fields': ['character_class', 'build_goal']
        }
    }
}


# =============================================================================
# 性能测试数据
# =============================================================================

MOCK_PERFORMANCE_DATA = {
    'response_times': {
        'fast_responses': {
            'rag_generation': 150,  # ms
            'pob2_calculation': 800,
            'market_api_call': 200,
            'cache_lookup': 5,
            'total_request': 950
        },
        'slow_responses': {
            'rag_generation': 2500,
            'pob2_calculation': 8000,
            'market_api_call': 5000,
            'cache_lookup': 50,
            'total_request': 15000
        }
    },
    
    'throughput_data': {
        'baseline': {
            'requests_per_second': 10,
            'concurrent_users': 20,
            'success_rate': 0.98
        },
        'stress_test': {
            'requests_per_second': 50,
            'concurrent_users': 100,
            'success_rate': 0.92
        }
    },
    
    'memory_usage': {
        'baseline_mb': 256,
        'under_load_mb': 512,
        'peak_mb': 768,
        'after_gc_mb': 280
    }
}


# =============================================================================
# 辅助函数
# =============================================================================

def get_mock_response(api_type: str, scenario: str, specific_item: str = None):
    """
    获取模拟API响应数据
    
    Args:
        api_type: API类型 ('scout', 'ninja', 'pob2', 'rag')
        scenario: 场景类型 ('success', 'errors', etc.)
        specific_item: 具体项目名称
    
    Returns:
        模拟API响应数据
    """
    mock_data_map = {
        'scout': MOCK_SCOUT_API_RESPONSES,
        'ninja': MOCK_NINJA_RESPONSES,
        'pob2': MOCK_POB2_RESPONSES,
        'rag': MOCK_RAG_RESPONSES,
        'cache': MOCK_CACHE_DATA,
        'errors': MOCK_ERROR_SCENARIOS,
        'performance': MOCK_PERFORMANCE_DATA
    }
    
    if api_type not in mock_data_map:
        raise ValueError(f"Unknown API type: {api_type}")
    
    data = mock_data_map[api_type]
    
    if scenario in data:
        scenario_data = data[scenario]
        if specific_item and specific_item in scenario_data:
            return scenario_data[specific_item]
        return scenario_data
    
    return None


def generate_realistic_timestamps(count: int, start_date: datetime = None):
    """
    生成逐渐递增的现实时间戳
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    
    timestamps = []
    current_time = start_date
    
    for i in range(count):
        timestamps.append(current_time.isoformat() + 'Z')
        # 每次增加一些随机时间
        current_time += timedelta(minutes=30 + (i % 60), seconds=i % 60)
    
    return timestamps


def create_mock_build_dataset(size: int = 100):
    """
    创建测试用的构筑数据集
    """
    character_classes = ['Sorceress', 'Ranger', 'Witch', 'Monk', 'Mercenary', 'Warrior']
    ascendancies = {
        'Sorceress': ['Stormweaver', 'Chronomancer'],
        'Ranger': ['Deadeye', 'Pathfinder'],
        'Witch': ['Infernalist', 'Blood Mage'],
        'Monk': ['Invoker', 'Acolyte'],
        'Mercenary': ['Witchhunter', 'Alchemist'],
        'Warrior': ['Titan', 'Gladiator']
    }
    
    main_skills = {
        'Sorceress': ['Lightning Bolt', 'Chain Lightning', 'Ice Shard'],
        'Ranger': ['Ice Shot', 'Lightning Arrow', 'Explosive Shot'],
        'Witch': ['Fireball', 'Raise Zombie', 'Dark Ritual'],
        'Monk': ['Spirit Wave', 'Falling Thunder', 'Palm Strike'],
        'Mercenary': ['Crossbow Shot', 'Gas Arrow', 'Explosive Grenade'],
        'Warrior': ['Slam', 'Shield Charge', 'Ancestral Totem']
    }
    
    builds = []
    timestamps = generate_realistic_timestamps(size)
    
    for i in range(size):
        char_class = character_classes[i % len(character_classes)]
        ascendancy = ascendancies[char_class][i % len(ascendancies[char_class])]
        main_skill = main_skills[char_class][i % len(main_skills[char_class])]
        
        build = {
            'id': f'mock_build_{i:04d}',
            'name': f'{main_skill} {char_class} Build {i+1}',
            'character_class': char_class,
            'ascendancy': ascendancy,
            'level': 80 + (i % 20),
            'main_skill': main_skill,
            'estimated_dps': 400000 + (i * 5000) + ((i % 10) * 50000),
            'estimated_ehp': 6000 + (i * 100) + ((i % 8) * 500),
            'estimated_cost': 5.0 + (i * 0.5) + ((i % 15) * 2.0),
            'confidence': 0.65 + (i % 35) * 0.01,
            'popularity_percent': max(0.1, 20.0 - (i * 0.2)),
            'created_at': timestamps[i],
            'league': 'Standard' if i % 3 == 0 else 'Hardcore',
            'tags': ['endgame' if i % 4 == 0 else 'leveling', 'budget' if i % 5 == 0 else 'expensive']
        }
        
        builds.append(build)
    
    return builds
