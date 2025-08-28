# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Path of Exile 2 (PoE2) Build Generator** that uses real, verified PoE2-specific data sources to generate intelligent build recommendations. The project has been completely refactored from theoretical APIs to actual working data sources.

### Core Architecture

The system follows a **PoB2集成架构（PoB2-Integrated Architecture）** leveraging Path of Building Community for Path of Exile 2 (https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2) for accurate calculations:

**Path of Building Community PoE2 Features:**
- Offline build planner specifically for Path of Exile 2
- Comprehensive damage and defense calculations
- Passive skill tree planner with full PoE2 support
- Character importing and build sharing capabilities
- Version: v0.9.0+ (active development)

#### 1. PoB2-Driven Architecture
```
ICalculationEngine (interface)
├── PoB2LocalEngine (primary - local PoB2 installation)
├── PoB2WebEngine (fallback - web-based PoB2)
└── MockCalculationEngine (testing/offline)

IDataProvider (interface)
├── PoE2ScoutAPI (market data)
├── PoE2NinjaScraper (meta analysis)
├── PoB2DataExtractor (build calculations)
└── PoB2BuildImporter (build import/export)
```

#### 2. Core Components
1. **PoE2AIOrchestrator** - AI-driven build recommendation coordinator
2. **PoB2 Integration Layer**:
   - `PoB2LocalClient` - Local Path of Building Community PoE2 interface
   - `PoB2BuildGenerator` - AI-generated build creation for PoB2
   - `PoB2Calculator` - Leverage Path of Building Community PoE2's calculation engine
3. **AI Recommendation Engine** - Generate optimized build configurations
4. **Data Collection Layer**:
   - `PoE2ScoutAPI` (https://poe2scout.com) - Market pricing data
   - `PoE2NinjaScraper` (https://poe.ninja/poe2/builds) - Meta trends
5. **Resilience Layer**:
   - **PoB2 Installation Detection** - Auto-locate local Path of Building Community PoE2 installation
   - **Fallback Mechanisms** - Backup calculations when Path of Building unavailable
   - **Build Validation** - Verify AI-generated builds are valid using Path of Building Community PoE2

#### 3. "生态公民" Philosophy
- Respectful API usage with intelligent rate limiting
- Graceful degradation when services are unavailable
- Future-ready for official API migration

## Common Commands

### Project Structure
This project follows a modular architecture with the main source code in `src/poe2build/` and tests in `tests/`. 

### Development Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/poe2build --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only

# Run single test file
pytest tests/unit/test_models.py
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/poe2build

# Linting with flake8
flake8 src/ tests/
```

### Running the Application
```bash
# Demo models and validate architecture
python examples/demo_models.py

# Main entry point (when implemented)
python -m poe2build.cli

# Run development setup script
python scripts/setup_dev.py
```

## Key Implementation Details

### PoB2 Integration Strategy
- **Local-First Approach**: Prioritize local Path of Building Community PoE2 installation for maximum accuracy
- **Dynamic Discovery**: Auto-detect Path of Building installation paths across different systems
- **Build Generation**: AI creates optimized build configurations that Path of Building Community PoE2 can calculate
- **Validation Pipeline**: Verify all AI-generated builds are valid using Path of Building Community PoE2 before recommendations

### RAG-Enhanced AI Build Generation
- **ninja.poe2 RAG Training**: Use real player build data from poe.ninja/poe2 as training knowledge base
- **Similarity-Based Recommendations**: Find and adapt successful builds similar to user preferences
- **Meta-Pattern Recognition**: AI identifies successful build patterns and applies them intelligently
- **PoB2 Calculation Integration**: Generate builds as PoB2 import codes with RAG-validated configurations
- **Continuous Learning**: RAG knowledge base updates daily with latest meta trends and successful builds

### Resilience Implementation Strategy

#### Circuit Breaker Pattern
```python
# Example implementation approach
class CircuitBreaker:
    states = ['CLOSED', 'OPEN', 'HALF_OPEN']
    # Auto-recovery after consecutive failures
    failure_threshold = 5
    recovery_timeout = 60  # seconds
```

#### Rate Limiting with Exponential Backoff
```python
# Respectful API usage
rate_limits = {
    'poe2scout.com': {'requests_per_minute': 30, 'backoff_factor': 2},
    'poe2db.tw': {'requests_per_minute': 20, 'backoff_factor': 1.5}, 
    'poe.ninja/poe2': {'requests_per_minute': 10, 'backoff_factor': 3}
}
```

#### Error Handling Philosophy
Every external call has four resilience layers:
1. **Try real API/scraping** - Primary data source
2. **Apply circuit breaker logic** - Prevent cascade failures  
3. **Fall back to cached data** - Last known good data
4. **Use mock data as last resort** - Never fail completely

## Project Architecture

### Source Code Structure
```
src/poe2build/
├── core/           # Main orchestration and coordination
├── data_sources/   # External API integrations
├── models/         # Data models and structures
├── pob2/          # Path of Building integration
├── rag/           # RAG AI training system
├── utils/         # Utility functions
└── config/        # Configuration management

tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
├── performance/   # Performance tests
├── e2e/          # End-to-end tests
└── fixtures/     # Test fixtures and mock data

examples/          # Demo and example scripts
docs/             # Documentation
scripts/          # Development and deployment scripts
```

### Key Files
- `src/poe2build/models/build.py` - Core build data models with PoE2-specific mechanics
- `src/poe2build/models/characters.py` - Character classes and ascendancies
- `src/poe2build/models/items.py` - Item and equipment models
- `examples/demo_models.py` - Demonstrates all data model features
- `pyproject.toml` - Modern Python project configuration
- `requirements.txt` - Production dependencies

## Important Constants

### PoE2 Game Mechanics
- Max resistance: 80% (defined in `poe2_constants['max_resistance']`)
- Energy shield multiplier: 0.3 base
- Chaos resistance penalty: -30% base penalty
- Level scaling factor: 0.03 for damage calculations

### Cache TTL Values
- Market data: 600s (10 minutes)
- Build data: 1800s (30 minutes) 
- Game data: 3600s (1 hour)

## API Request Format

The AI orchestrator expects this structure:
```python
user_request = {
    'game': 'poe2',
    'mode': 'standard',  # or 'hardcore'
    'preferences': {
        'class': 'Ranger',              # PoE2 character class
        'ascendancy': 'Deadeye',        # Optional ascendancy
        'style': 'bow',                 # Build style/weapon type
        'goal': 'endgame_content',      # clear_speed, boss_killing, etc.
        'budget': {
            'amount': 15, 
            'currency': 'divine'
        },
        'pob2_integration': {
            'generate_import_code': True,  # Generate PoB2 import code
            'calculate_stats': True,       # Use PoB2 for calculations
            'validate_build': True         # Validate build in PoB2
        }
    }
}

# Response includes PoB2 integration data:
response = {
    'recommendations': [...],
    'pob2_data': {
        'import_codes': ['<PoB2 import code>'],
        'calculated_stats': {
            'total_dps': 1250000,
            'effective_health_pool': 8500,
            'calculated_by': 'PoB2_Local_v2.35.1'
        },
        'validation_status': 'valid'
    }
}
```

## Development Status and Architecture

### Current Implementation Status
The project is in active development with the following components implemented:

**Phase 1 Complete: Foundation and Data Models**
- ✅ Complete data model system with PoE2-specific mechanics
- ✅ Character classes, ascendancies, and PoE2 unique features
- ✅ Build stats with 80% max resistance validation
- ✅ Skill system with Spirit cost mechanics
- ✅ Item and weapon modeling
- ✅ Market data structures

**In Progress: Multi-Phase Architecture**
- 🔄 Data source integrations (PoE2Scout, ninja.poe2)
- 🔄 PoB2 local installation detection and integration
- 🔄 RAG AI training system with ninja.poe2 data
- 🔄 Core AI orchestrator
- 🔄 Resilience and circuit breaker patterns

### Implementation Order
Follow `IMPLEMENTATION_ORDER.md` for the complete 6-phase development plan. Current focus should be on Phase 2 (Data Sources) and Phase 3 (PoB2 Integration).

## Future Architecture Evolution

### Planned Modular Enhancements
1. **Interface Migration**: Refactor current implementations to interface-based pattern
2. **Official API Ready**: Prepare `OfficialTradeProvider` stub for GGG's future OAuth API
3. **PoeB Integration**: Add `PoebParserModule` for Path of Building import/export
4. **Enhanced Resilience**: Implement full circuit breaker and rate limiting systems

### Migration Strategy
```python
# Current: Direct class instantiation
scout_api = PoE2ScoutAPI()

# Future: Interface-based dependency injection
trade_provider = TradeProviderFactory.create('scout')  # or 'official' when available
```

## Development Guidelines

### Architecture Philosophy
- **Modular Design**: Interface-based components for ecosystem adaptability
- **PoE2-Specific**: All mechanics and calculations tailored for Path of Exile 2
- **Type Safety**: Comprehensive type annotations with dataclasses
- **Validation**: Built-in data validation with PoE2-specific rules
- **Resilience**: Circuit breaker patterns and graceful degradation

### Code Standards
- **Python 3.8+**: Modern Python with type hints
- **Data Models**: Use dataclasses with validation in `__post_init__`
- **Error Handling**: Validate ranges (e.g., resistances -100% to +80%)
- **Testing**: Comprehensive test coverage with pytest
- **Documentation**: Clear docstrings and examples

### PoE2-Specific Mechanics
- **Max Resistance**: 80% cap (not 75% like PoE1)
- **Spirit System**: Unique PoE2 resource for auras and skills
- **Currency**: Divine Orbs as primary high-value currency
- **Character Classes**: 6 classes with 2 ascendancies each
- **Chaos Resistance**: Can be negative (penalty system)

The project follows a "working architecture first" approach with emphasis on PoE2 accuracy, respectful API usage, and community ecosystem compatibility.