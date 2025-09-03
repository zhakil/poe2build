# PoE2 AI Build Generator - Usage Guide

## Overview

PoE2 AI构筑生成器是一个智能的Path of Exile 2构筑推荐系统，集成了：
- RAG增强的AI构筑推荐
- PoB2本地/Web集成
- 实时市场数据
- 智能推荐引擎

## Quick Start

### 1. System Health Check
```bash
python poe2_ai_orchestrator.py --health
```

### 2. Interactive Mode
```bash
python poe2_ai_orchestrator.py --interactive
```

### 3. Quick Build Generation
```bash
# Generate Ranger builds for clear speed
python poe2_ai_orchestrator.py --class ranger --goal clear_speed --budget 15

# Generate Witch builds for boss killing
python poe2_ai_orchestrator.py --class witch --goal boss_killing --budget 30

# Generate budget-friendly builds
python poe2_ai_orchestrator.py --class warrior --goal budget_friendly --budget 5
```

### 4. Demo Mode
```bash
python poe2_ai_orchestrator.py --demo
```

## Command Line Options

| Option | Description | Examples |
|--------|-------------|----------|
| `--class/-c` | Character class | witch, ranger, warrior, monk, mercenary, sorceress |
| `--goal/-g` | Build goal | clear_speed, boss_killing, endgame_content, league_start, budget_friendly |
| `--budget/-b` | Maximum budget (divine orbs) | Default: 15 |
| `--count/-n` | Number of builds to generate | Default: 3 |
| `--interactive/-i` | Run in interactive mode | |
| `--health` | System health check | |
| `--demo` | Run demonstration | |
| `--verbose/-v` | Verbose output | |

## Interactive Mode Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `health` | Run system health check |
| `generate` | Generate builds (interactive) |
| `recommend` | Get build recommendations |
| `demo` | Run demonstrations |
| `stats` | Show system statistics |
| `quit` | Exit the program |

## System Architecture

### Core Components
1. **AI Orchestrator** - Main coordination system
2. **Build Generator** - Intelligent build creation
3. **Recommendation Engine** - Smart ranking and filtering
4. **RAG System** - Knowledge-enhanced recommendations
5. **PoB2 Integration** - Build validation and import codes
6. **Market Data** - Real-time pricing information

### Component Status
The system monitors 6 core components:
- Data Cache
- Market API
- Ninja Scraper (meta data)
- PoB2 Local Client
- PoB2 Web Client
- RAG Engine

## Example Output

### Build Summary
```
1. Speed Farmer Enhanced
   Class: Ranger
   Level: 86
   DPS: 448,421
   EHP: 4,849
   Resistances: [OK]
   Cost: 8.11 divine
   Main Skill: Lightning Arrow
```

### Health Check Report
```
============================================================
System Health Check Report
============================================================
Overall Status: [OK] HEALTHY

Component Status:
  [OK] data_cache: healthy (1.0ms)
  [OK] market_api: healthy (50.0ms)
  [OK] ninja_scraper: healthy (100.0ms)
  [OK] pob2_local: healthy (200.0ms)
  [OK] pob2_web: healthy (300.0ms)
  [OK] rag_engine: healthy (150.0ms)

Performance Metrics:
  Total Requests: 5
  Error Count: 0
  Average Response Time: 125.50ms
  Error Rate: 0.00%
============================================================
```

## Build Goals Explained

| Goal | Description | Focus |
|------|-------------|-------|
| `clear_speed` | Fast map clearing | Movement speed + AoE damage |
| `boss_killing` | Single target damage | High DPS + survivability |
| `endgame_content` | All-around performance | Balanced stats |
| `league_start` | Early league viability | Low gear requirements |
| `budget_friendly` | Cost-effective builds | Maximum value per divine |

## Character Classes

- **Witch** - Elemental caster, Energy Shield builds
- **Ranger** - Bow attacks, projectile builds  
- **Warrior** - Melee attacks, high survivability
- **Monk** - Martial arts, hybrid builds
- **Mercenary** - Crossbow attacks, tactical builds
- **Sorceress** - Elemental magic, glass cannon

## Technical Features

### RAG-Enhanced Recommendations
- Uses real player data from poe.ninja
- Similarity-based build matching
- Confidence scoring for recommendations

### PoB2 Integration
- Auto-detection of local PoB2 installation
- Build import code generation
- Stat calculation validation
- Web fallback when local unavailable

### Market Integration
- Real-time item pricing
- Budget optimization
- Cost-effectiveness analysis

### Resilience Features
- Circuit breaker patterns
- Graceful degradation
- Fallback mechanisms
- Comprehensive error handling

## Troubleshooting

### Common Issues

1. **System initialization failed**
   - Check internet connection
   - Verify all dependencies installed

2. **PoB2 not detected**
   - System will automatically fallback to web version
   - Manual PoB2 path configuration coming soon

3. **No builds generated**
   - Try relaxing budget constraints
   - Check if character class is supported
   - Use different build goals

4. **Component unhealthy**
   - Run health check to identify specific issues
   - Most components have fallback mechanisms

### Performance Tips

- Use `--verbose` for detailed logging
- Interactive mode provides better error feedback
- Demo mode showcases all system capabilities
- Health check should show all components as healthy

## Future Enhancements

- Official GGG API integration when available
- Enhanced PoB2 integration features
- More character class templates
- Advanced filtering options
- Build comparison tools
- Export to various formats

## Support

For issues or feature requests, check the project documentation in the `docs/` directory.

System logs are saved to `logs/poe2_orchestrator.log` for debugging.