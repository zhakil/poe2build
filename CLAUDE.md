# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Path of Exile 2 (PoE2) Build Generator** that uses real, verified PoE2-specific data sources to generate intelligent build recommendations. The project has been completely refactored from theoretical APIs to actual working data sources.

### Core Architecture

The system follows a **PoB2集成架构（PoB2-Integrated Architecture）** leveraging Path of Building Community for accurate calculations:

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
   - `PoB2LocalClient` - Local Path of Building Community interface
   - `PoB2BuildGenerator` - AI-generated build creation for PoB2
   - `PoB2Calculator` - Leverage PoB2's calculation engine
3. **AI Recommendation Engine** - Generate optimized build configurations
4. **Data Collection Layer**:
   - `PoE2ScoutAPI` (https://poe2scout.com) - Market pricing data
   - `PoE2NinjaScraper` (https://poe.ninja/poe2/builds) - Meta trends
5. **Resilience Layer**:
   - **PoB2 Installation Detection** - Auto-locate local PoB2 installation
   - **Fallback Mechanisms** - Web PoB2 or cached calculations when local unavailable
   - **Build Validation** - Verify AI-generated builds are valid in PoB2

#### 3. "生态公民" Philosophy
- Respectful API usage with intelligent rate limiting
- Graceful degradation when services are unavailable
- Future-ready for official API migration

## Common Commands

### Running the Application
```bash
# Main entry point - runs the PoB2-integrated AI recommendation system
python poe2_ai_orchestrator.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Alternative: Install dependencies manually
pip install requests beautifulsoup4 psutil

# Verify PoB2 installation detection
python -c "from poe2_ai_orchestrator import PoB2LocalClient; PoB2LocalClient().detect_pob2_installation()"

# Health check - verify all systems are accessible
python -c "from poe2_ai_orchestrator import PoE2AIOrchestrator; PoE2AIOrchestrator().health_check()"
```

### Testing Individual Components
```bash
# Test PoB2 integration
python -c "
from poe2_ai_orchestrator import PoB2LocalClient
pob2 = PoB2LocalClient()
if pob2.is_available():
    print('PoB2 successfully detected at:', pob2.installation_path)
else:
    print('PoB2 not found, will use web fallback')
"

# Test RAG-enhanced AI build generation + PoB2 calculation
python -c "
from poe2_ai_orchestrator import PoE2AIOrchestrator
orchestrator = PoE2AIOrchestrator()
build_request = {'preferences': {'class': 'Ranger', 'style': 'bow', 'goal': 'endgame'}}
recommendation = orchestrator.generate_build_recommendation(build_request)
print(f'RAG-generated builds: {len(recommendation[\"recommendations\"])}')
for rec in recommendation['recommendations'][:2]:
    print(f'- {rec[\"build_name\"]} (RAG confidence: {rec.get(\"rag_confidence\", 0):.3f})')
    if 'pob2_stats' in rec:
        print(f'  PoB2 DPS: {rec[\"pob2_stats\"][\"total_dps\"]:,}')
"
```

## Key Implementation Details

### PoB2 Integration Strategy
- **Local-First Approach**: Prioritize local PoB2 installation for maximum accuracy
- **Dynamic Discovery**: Auto-detect PoB2 installation paths across different systems
- **Build Generation**: AI creates optimized build configurations that PoB2 can calculate
- **Validation Pipeline**: Verify all AI-generated builds are valid in PoB2 before recommendations

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
    'poe.ninja': {'requests_per_minute': 10, 'backoff_factor': 3}
}
```

#### Error Handling Philosophy
Every external call has four resilience layers:
1. **Try real API/scraping** - Primary data source
2. **Apply circuit breaker logic** - Prevent cascade failures  
3. **Fall back to cached data** - Last known good data
4. **Use mock data as last resort** - Never fail completely

## File Structure

- `poe2_ai_orchestrator.py` - Main PoB2-integrated AI orchestrator with `main()` entry point
- `pob2_local_client.py` - Local Path of Building Community interface and integration
- `ai_build_generator.py` - AI-driven build recommendation and generation engine
- `requirements.txt` - Project dependencies (including psutil for process detection)
- `docs/` - Comprehensive documentation including architecture, API usage, deployment, and troubleshooting
  - `01_real_architecture.md` - Architecture overview
  - `02_poe2_data_sources.md` - Data sources documentation
  - `03_poe2_calculator.md` - Build calculator details
  - `04_api_usage.md` - API usage examples
  - `05_developer_guide.md` - Developer guidelines
  - `06_deployment.md` - Deployment instructions
  - `07_troubleshooting.md` - Troubleshooting guide
- Chinese documentation files:
  - `《流放之路2》生态系统程序化访问开发者指南：关键社区及官方工具API分析.docx`
  - `How to query POE2 API.docx`

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

## Testing & Quality Assurance

### Manual Testing
```bash
# Test the main application
python poe2_real_data_sources.py

# Test individual components (see "Testing Individual Components" section above)

# Validate data sources accessibility
python -c "from poe2_real_data_sources import PoE2RealDataOrchestrator; PoE2RealDataOrchestrator().health_check()"
```

### Code Quality
```bash
# Python style check (if flake8 installed)
flake8 poe2_real_data_sources.py

# Type checking (if mypy installed)
mypy poe2_real_data_sources.py
```

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

## Development Notes

- **Architecture Philosophy**: Modular, interface-based design for ecosystem adaptability
- **Language**: Mix of Chinese comments and English code (project originated in Chinese context)
- **No Tests**: No formal test suite exists yet - testing is done via manual execution
- **Dependencies**: Minimal - only requests and beautifulsoup4 required (see requirements.txt)
- **Network Dependent**: All functionality requires internet access to external PoE2 data sources
- **Graceful Degradation**: System continues to function even when external APIs are unavailable
- **生态公民意识**: Respectful API usage designed to maintain community service access

The codebase prioritizes working functionality over perfect code structure, with emphasis on resilience, respectful API usage, and adaptability to the evolving PoE2 ecosystem.