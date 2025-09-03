"""
Mock API响应数据
用于模拟各种数据源的API响应
"""

from typing import Dict, List, Any


# ===== PoE2 Scout API响应 =====
MOCK_POE2_SCOUT_RESPONSES = {
    # 物品价格查询响应
    'item_prices': {
        'Staff of Power': {
            'item_name': 'Staff of Power',
            'median_price': 15.5,
            'mean_price': 16.2,
            'min_price': 12.0,
            'max_price': 22.0,
            'currency': 'divine',
            'sample_size': 147,
            'confidence': 0.92,
            'last_updated': 1700000000,
            'market_trend': 'stable',
            'price_history': [14.8, 15.1, 15.5, 15.2, 15.5]
        },
        'Lightning Amulet': {
            'item_name': 'Lightning Amulet',
            'median_price': 3.2,
            'mean_price': 3.8,
            'min_price': 2.5,
            'max_price': 6.0,
            'currency': 'divine',
            'sample_size': 89,
            'confidence': 0.87,
            'last_updated': 1700000000,
            'market_trend': 'rising',
            'price_history': [2.8, 3.0, 3.1, 3.2, 3.2]
        },
        'Basic Staff': {
            'item_name': 'Basic Staff',
            'median_price': 0.3,
            'mean_price': 0.4,
            'min_price': 0.1,
            'max_price': 0.8,
            'currency': 'divine',
            'sample_size': 234,
            'confidence': 0.95,
            'last_updated': 1700000000,
            'market_trend': 'falling',
            'price_history': [0.5, 0.4, 0.3, 0.3, 0.3]
        }
    },
    
    # 市场趋势数据
    'market_trends': {
        'popular_items': [
            {
                'item_name': 'Lightning Staff',
                'demand_index': 95,
                'price_velocity': 1.15,
                'market_share': 12.3
            },
            {
                'item_name': 'Ice Bow',
                'demand_index': 88,
                'price_velocity': 0.98,
                'market_share': 8.7
            }
        ],
        'meta_shifts': [
            {
                'build_archetype': 'Lightning Caster',
                'popularity_change': 0.23,
                'timeframe_days': 7
            },
            {
                'build_archetype': 'Cold Archer',
                'popularity_change': -0.08,
                'timeframe_days': 7
            }
        ]
    },
    
    # 构筑数据
    'build_data': {
        'top_builds': [
            {
                'build_id': 'scout_build_001',
                'name': 'Lightning Stormweaver',
                'class': 'Sorceress',
                'ascendancy': 'Stormweaver',
                'main_skill': 'Lightning Bolt',
                'estimated_dps': 1200000,
                'estimated_cost': 25.5,
                'popularity_rank': 1,
                'win_rate': 0.87,
                'average_level': 93,
                'sample_size': 456
            },
            {
                'build_id': 'scout_build_002',
                'name': 'Ice Shot Deadeye',
                'class': 'Ranger',
                'ascendancy': 'Deadeye',
                'main_skill': 'Ice Shot',
                'estimated_dps': 850000,
                'estimated_cost': 18.2,
                'popularity_rank': 3,
                'win_rate': 0.82,
                'average_level': 91,
                'sample_size': 312
            }
        ]
    }
}


# ===== Ninja API响应 =====
MOCK_NINJA_RESPONSES = {
    # 构筑排行榜
    'build_rankings': [
        {
            'rank': 1,
            'name': 'Meta Lightning Build',
            'class': 'Sorceress',
            'ascendancy': 'Stormweaver',
            'main_skill': 'Lightning Bolt',
            'support_gems': ['Added Lightning Damage', 'Lightning Penetration', 'Elemental Focus'],
            'level': 95,
            'dps': 1350000,
            'life': 5800,
            'energy_shield': 3200,
            'popularity_percent': 15.7,
            'character_count': 2847,
            'gear_value_divine': 28.5,
            'last_updated': 1700000000
        },
        {
            'rank': 2,
            'name': 'Tanky Monk Build',
            'class': 'Monk',
            'ascendancy': 'Invoker',
            'main_skill': 'Spirit Wave',
            'support_gems': ['Melee Physical Damage', 'Multistrike', 'Increased AoE'],
            'level': 92,
            'dps': 680000,
            'life': 7200,
            'energy_shield': 1800,
            'popularity_percent': 12.3,
            'character_count': 2234,
            'gear_value_divine': 15.2,
            'last_updated': 1700000000
        },
        {
            'rank': 5,
            'name': 'Budget Ice Shot',
            'class': 'Ranger',
            'ascendancy': 'Deadeye',
            'main_skill': 'Ice Shot',
            'support_gems': ['Added Cold Damage', 'Pierce', 'Increased Critical Strikes'],
            'level': 87,
            'dps': 520000,
            'life': 5200,
            'energy_shield': 2100,
            'popularity_percent': 8.9,
            'character_count': 1612,
            'gear_value_divine': 6.8,
            'last_updated': 1700000000
        }
    ],
    
    # 职业分布
    'class_distribution': {
        'Sorceress': {'percentage': 22.5, 'count': 4089},
        'Ranger': {'percentage': 18.3, 'count': 3321},
        'Monk': {'percentage': 16.7, 'count': 3029},
        'Witch': {'percentage': 15.1, 'count': 2742},
        'Mercenary': {'percentage': 14.2, 'count': 2576},
        'Warrior': {'percentage': 13.2, 'count': 2394}
    },
    
    # 升华分布
    'ascendancy_distribution': {
        'Stormweaver': {'percentage': 12.8, 'count': 2324},
        'Deadeye': {'percentage': 11.2, 'count': 2032},
        'Invoker': {'percentage': 9.8, 'count': 1779},
        'Chronomancer': {'percentage': 9.7, 'count': 1765},
        'Pathfinder': {'percentage': 7.1, 'count': 1289},
        'Witchhunter': {'percentage': 8.4, 'count': 1523}
    },
    
    # 技能使用率
    'skill_usage': [
        {'skill_name': 'Lightning Bolt', 'usage_percent': 18.7, 'average_dps': 1200000},
        {'skill_name': 'Ice Shot', 'usage_percent': 15.2, 'average_dps': 850000},
        {'skill_name': 'Spirit Wave', 'usage_percent': 12.9, 'average_dps': 720000},
        {'skill_name': 'Fireball', 'usage_percent': 11.3, 'average_dps': 950000},
        {'skill_name': 'Crossbow Shot', 'usage_percent': 8.6, 'average_dps': 680000}
    ]
}


# ===== PoE2DB API响应 =====
MOCK_POE2DB_RESPONSES = {
    # 技能宝石数据
    'skill_gems': {
        'Lightning Bolt': {
            'name': 'Lightning Bolt',
            'gem_type': 'Active',
            'damage_type': ['Lightning'],
            'tags': ['Spell', 'Projectile', 'Lightning'],
            'base_damage': '28-85',
            'damage_effectiveness': 100,
            'critical_strike_chance': 6,
            'cast_time': 0.8,
            'mana_cost': 12,
            'requirements': {
                'level': 1,
                'intelligence': 14
            },
            'quality_bonus': '+1% increased Lightning Damage per 1% Quality',
            'description': 'Launches a bolt of lightning that pierces through enemies.'
        },
        'Ice Shot': {
            'name': 'Ice Shot',
            'gem_type': 'Active',
            'damage_type': ['Cold', 'Physical'],
            'tags': ['Attack', 'Projectile', 'Cold', 'Bow'],
            'base_damage': '100% of base damage',
            'damage_effectiveness': 110,
            'critical_strike_chance': 5,
            'attack_speed': 100,
            'requirements': {
                'level': 1,
                'dexterity': 14
            },
            'quality_bonus': '+1% increased Cold Damage per 1% Quality',
            'description': 'Fires an arrow that converts physical damage to cold damage.'
        }
    },
    
    # 辅助宝石数据
    'support_gems': {
        'Added Lightning Damage': {
            'name': 'Added Lightning Damage',
            'gem_type': 'Support',
            'tags': ['Lightning', 'Support'],
            'effect': 'Adds 1-13 Lightning Damage',
            'damage_multiplier': 130,
            'mana_multiplier': 120,
            'requirements': {
                'level': 8,
                'intelligence': 25
            },
            'quality_bonus': '+0.5% increased Lightning Damage per 1% Quality'
        },
        'Lightning Penetration': {
            'name': 'Lightning Penetration',
            'gem_type': 'Support',
            'tags': ['Lightning', 'Support'],
            'effect': 'Penetrates 30% Lightning Resistance',
            'damage_multiplier': 100,
            'mana_multiplier': 110,
            'requirements': {
                'level': 31,
                'intelligence': 78
            },
            'quality_bonus': '+0.5% Lightning Penetration per 1% Quality'
        }
    },
    
    # 物品数据库
    'item_database': {
        'Staff of Power': {
            'name': 'Staff of Power',
            'item_class': 'Two-Handed Staff',
            'rarity': 'Unique',
            'required_level': 68,
            'requirements': {
                'strength': 85,
                'intelligence': 128
            },
            'properties': {
                'physical_damage': '45-68',
                'critical_strike_chance': 6.5,
                'attacks_per_second': 1.2,
                'weapon_range': 13
            },
            'implicit_mods': ['+18% Chance to Block Attack Damage while wielding a Staff'],
            'explicit_mods': [
                '+50 to Intelligence',
                '80% increased Spell Damage',
                '+25% to Lightning Resistance',
                '50% increased Lightning Damage'
            ],
            'flavor_text': 'The storm bows to none.'
        }
    },
    
    # 天赋树数据
    'passive_tree': {
        'keystones': [
            {
                'name': 'Elemental Overload',
                'description': '40% more Elemental Damage if you have not Crit Recently',
                'position': {'x': 1250, 'y': 850},
                'connected_nodes': ['elem_damage_1', 'spell_crit_2']
            },
            {
                'name': 'Lightning Mastery',
                'description': '25% increased Lightning Damage, Lightning Skills have 10% chance to Shock',
                'position': {'x': 1450, 'y': 950},
                'connected_nodes': ['lightning_1', 'shock_1']
            }
        ],
        'notable_passives': [
            {
                'name': 'Crackling Speed',
                'description': '12% increased Cast Speed, 8% increased Lightning Damage',
                'position': {'x': 1100, 'y': 750},
                'allocation_cost': 1
            }
        ]
    }
}


# ===== PoB2集成响应 =====
MOCK_POB2_RESPONSES = {
    # 构筑计算结果
    'build_calculations': {
        'valid_build': {
            'build_valid': True,
            'calculations': {
                'total_dps': 1250000,
                'average_hit': 85000,
                'hit_rate': 14.7,
                'critical_strike_chance': 45.2,
                'critical_strike_multiplier': 320,
                'effective_health_pool': 8750,
                'life': 5800,
                'energy_shield': 2950,
                'mana': 1200,
                'resistances': {
                    'fire': 78,
                    'cold': 76,
                    'lightning': 79,
                    'chaos': -22
                },
                'defensive_stats': {
                    'block_chance': 15,
                    'dodge_chance': 8,
                    'damage_reduction': 12
                },
                'speed_stats': {
                    'cast_speed': 3.2,
                    'attack_speed': 0,
                    'movement_speed': 118
                }
            },
            'warnings': [
                'Chaos resistance is below -30%',
                'Consider increasing life pool'
            ],
            'calculation_time_ms': 234,
            'pob2_version': '2.35.1'
        },
        
        'invalid_build': {
            'build_valid': False,
            'error': 'Insufficient attribute requirements',
            'error_details': [
                'Required Intelligence: 350, Available: 280',
                'Required Strength: 120, Available: 95'
            ],
            'calculation_time_ms': 156,
            'pob2_version': '2.35.1'
        }
    },
    
    # PoB2导入代码
    'import_codes': {
        'lightning_build': 'eNrtXNtu2zYUfhXDuE2AJVuSJdm6qYG4bYdh2DC0BbYNuzcYkYrZyOKCkXyLlr77KNFF...',
        'ice_build': 'eNqNksFu2zAMhV+l0LU9OLJlS5Z1K4uhPQzYsGFAe9gJQGDQsRtLjWxAkruhSd692M...',
        'budget_build': 'eNrNXctu4zYUfRVDuI4BS5YetuqmAtq2wCyKAu1i0Y0lkha7AYsCaVEsavfd59yH5yV...'
    },
    
    # 路径检测结果
    'path_detection': {
        'found_paths': [
            {
                'path': 'F:\\steam\\steamapps\\common\\Path of Exile 2\\Path of Building Community (PoE2)',
                'version': '2.35.1',
                'platform': 'steam',
                'verified': True,
                'last_modified': 1700000000
            },
            {
                'path': 'C:\\Program Files\\Path of Building Community\\PathOfBuildingCommunity.exe',
                'version': '2.34.8',
                'platform': 'standalone',
                'verified': True,
                'last_modified': 1699500000
            }
        ],
        'recommended_path': 'F:\\steam\\steamapps\\common\\Path of Exile 2\\Path of Building Community (PoE2)',
        'detection_time_ms': 1250
    }
}


# ===== RAG系统响应 =====
MOCK_RAG_RESPONSES = {
    # 相似构筑检索
    'similar_builds': [
        {
            'build_id': 'rag_001',
            'name': 'Lightning Stormweaver v2',
            'similarity_score': 0.92,
            'source_build_id': 'ninja_build_123',
            'adaptations': [
                'Increased Lightning Penetration support gem level',
                'Added more defensive layers',
                'Optimized passive tree for better mana efficiency'
            ],
            'confidence': 0.87,
            'meta_relevance': 0.91
        },
        {
            'build_id': 'rag_002', 
            'name': 'Budget Lightning Caster',
            'similarity_score': 0.78,
            'source_build_id': 'ninja_build_087',
            'adaptations': [
                'Removed expensive unique items',
                'Alternative passive tree route',
                'Lower-tier support gems for budget version'
            ],
            'confidence': 0.82,
            'meta_relevance': 0.65
        }
    ],
    
    # 构筑推荐
    'recommendations': [
        {
            'name': 'RAG Enhanced Lightning Build',
            'confidence': 0.89,
            'reasoning': [
                'High similarity to top-performing meta builds',
                'Proven effectiveness in current league',
                'Good balance of offense and defense'
            ],
            'estimated_performance': {
                'dps': 1100000,
                'survivability': 8200,
                'build_cost': 18.5,
                'difficulty': 'medium'
            },
            'key_features': [
                'Lightning damage specialization',
                'Energy shield + Life hybrid defense',
                'Shock proliferation for clear speed'
            ]
        }
    ],
    
    # 向量检索结果
    'vector_search': {
        'query_vector_dim': 384,
        'search_results': [
            {
                'document_id': 'build_doc_001',
                'similarity_score': 0.94,
                'content_snippet': 'Lightning Bolt Stormweaver focused on high DPS with energy shield defense...',
                'metadata': {
                    'build_name': 'Meta Lightning Build',
                    'character_class': 'Sorceress',
                    'last_updated': 1700000000
                }
            },
            {
                'document_id': 'build_doc_045',
                'similarity_score': 0.86,
                'content_snippet': 'Budget-friendly lightning caster utilizing basic gear and efficient passive tree...',
                'metadata': {
                    'build_name': 'Budget Lightning Starter',
                    'character_class': 'Sorceress',
                    'last_updated': 1699800000
                }
            }
        ],
        'search_time_ms': 45,
        'total_documents_searched': 1247
    }
}


# ===== 错误响应样例 =====
MOCK_ERROR_RESPONSES = {
    'api_timeout': {
        'error': 'TimeoutError',
        'message': 'Request timed out after 30 seconds',
        'timestamp': 1700000000,
        'endpoint': '/api/market/prices',
        'retry_after': 60
    },
    
    'rate_limit': {
        'error': 'RateLimitError',
        'message': 'Rate limit exceeded: 60 requests per minute',
        'timestamp': 1700000000,
        'retry_after': 45,
        'limit': 60,
        'window': 60
    },
    
    'data_not_found': {
        'error': 'NotFoundError',
        'message': 'Requested data not found',
        'timestamp': 1700000000,
        'requested_resource': 'build_id_12345'
    },
    
    'validation_error': {
        'error': 'ValidationError',
        'message': 'Invalid request parameters',
        'timestamp': 1700000000,
        'validation_errors': [
            {'field': 'character_class', 'error': 'Invalid character class'},
            {'field': 'max_budget', 'error': 'Must be positive number'}
        ]
    }
}


def get_mock_response(service: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """
    获取Mock响应数据
    
    Args:
        service: 服务名 ('scout', 'ninja', 'poe2db', 'pob2', 'rag')
        endpoint: 端点名称
        **kwargs: 额外参数
        
    Returns:
        Mock响应数据
    """
    response_map = {
        'scout': MOCK_POE2_SCOUT_RESPONSES,
        'ninja': MOCK_NINJA_RESPONSES,
        'poe2db': MOCK_POE2DB_RESPONSES,
        'pob2': MOCK_POB2_RESPONSES,
        'rag': MOCK_RAG_RESPONSES
    }
    
    service_responses = response_map.get(service, {})
    return service_responses.get(endpoint, {})


def get_error_response(error_type: str) -> Dict[str, Any]:
    """
    获取错误响应数据
    
    Args:
        error_type: 错误类型
        
    Returns:
        错误响应数据
    """
    return MOCK_ERROR_RESPONSES.get(error_type, {})