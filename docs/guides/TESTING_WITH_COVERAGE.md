# Testing with Real Code Coverage

## The Challenge

The `test_simple.py` file uses mocks and doesn't import actual source modules, resulting in 0% code coverage. To get real coverage, tests need to import and execute the actual source code.

## Dependencies Required for Source Imports

### Minimal Core Dependencies
To import and test the actual source modules, you need:

1. **Standard Library Only** (already available):
   - `abc`, `logging`, `datetime`, `typing`
   - Core modules like `src.core.base` can partially work

2. **Lightweight Dependencies** (~5MB):
   ```bash
   uv pip install python-dotenv
   ```

3. **Data Processing** (~30MB):
   ```bash
   uv pip install pandas numpy
   ```

4. **Full Dependencies** (500MB+ without CUDA):
   - langchain, sentence-transformers, vector stores
   - Required for complete module testing

## Levels of Testing Coverage

### Level 1: Mock Tests (Current)
- **Coverage**: 0% (uses mocks, no source imports)
- **Dependencies**: None
- **Speed**: ~0.03s
- **Use Case**: Quick smoke tests

### Level 2: Core Module Tests
- **Coverage**: ~10-20% (core modules only)
- **Dependencies**: python-dotenv
- **Speed**: ~0.5s
- **Example**: `test_core_with_imports.py`

### Level 3: Basic Integration
- **Coverage**: ~40-60%
- **Dependencies**: pandas, numpy, dotenv
- **Speed**: ~2s
- **Modules**: Core, models, exceptions

### Level 4: Full Unit Tests
- **Coverage**: 70-90%
- **Dependencies**: All Python packages (no Docker)
- **Speed**: ~10s
- **Modules**: All source code

### Level 5: Integration Tests
- **Coverage**: 95%+
- **Dependencies**: Full stack + Docker
- **Speed**: ~30s+
- **Includes**: E2E workflows

## Strategy for Incremental Coverage

### Step 1: Install Minimal Dependencies
```bash
# Just the essentials
uv pip install python-dotenv pandas numpy
```

### Step 2: Run Core Tests
```bash
# Test core modules with actual imports
.venv/bin/python -m pytest tests/test_core_with_imports.py \
    --cov=src/core \
    --cov-report=term-missing
```

### Step 3: Progressive Enhancement
```bash
# Add more dependencies as needed
uv pip install requests yfinance  # For data adapters
uv pip install scikit-learn       # For ML components
uv pip install langchain          # For RAG pipeline
```

## Creating Tests with Real Imports

### Example: Testing with Actual Imports
```python
# tests/test_with_coverage.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_real_import():
    """Test that imports and executes real code"""
    from src.core.base import BaseComponent
    
    class RealComponent(BaseComponent):
        def initialize(self):
            self._initialized = True
        
        def validate_config(self):
            return self.config.get('valid', True)
        
        def get_status(self):
            return {'initialized': self._initialized}
    
    # This executes real code, contributing to coverage
    component = RealComponent("test", {"valid": True})
    component.initialize()
    assert component.get_status()['initialized'] is True
```

## Coverage Report Analysis

When you run tests with real imports:

```bash
# Current result with minimal deps
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
src/core/__init__.py         5      3 40.00%   7-16
src/core/base.py            43     26 39.53%   22-26, 30-32
src/core/exceptions.py      74     74  0.00%   6-114
src/core/interfaces.py      10      7 30.00%   8-169
src/core/models.py         116    116  0.00%   5-201
------------------------------------------------------
TOTAL                      248    226  8.87%
```

This shows:
- `base.py`: 39% coverage (some methods executed)
- `__init__.py`: 40% coverage (partial imports)
- Others: 0% (need dependencies)

## Optimization Trade-offs

| Approach | Coverage | Dependencies | Install Time | Test Time |
|----------|----------|--------------|--------------|-----------|
| Mocks only | 0% | 0MB | 0s | 0.03s |
| Core imports | 10% | 5MB | 10s | 0.5s |
| Basic deps | 40% | 50MB | 1min | 2s |
| Full deps (CPU) | 80% | 500MB | 3min | 10s |
| Full + Docker | 95% | 3.5GB | 15min | 30s |

## Recommendations

1. **For Development**: Use mock tests for rapid iteration
2. **For PR Validation**: Use Level 3 (basic deps) for reasonable coverage
3. **For Release**: Use Level 4-5 for comprehensive testing
4. **For CI/CD**: Cache dependencies and use CPU-only PyTorch

## Quick Commands

```bash
# Install minimal deps for coverage
uv pip install python-dotenv pandas numpy

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Next Steps

1. Install pandas to enable more imports: `uv pip install pandas`
2. Create more tests that import actual modules
3. Gradually add dependencies for better coverage
4. Use coverage reports to identify untested code