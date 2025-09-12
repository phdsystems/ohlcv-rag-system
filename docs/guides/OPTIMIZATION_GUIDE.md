# Dependency Optimization Guide

## Problem
The default installation downloads ~3GB+ of dependencies including PyTorch with CUDA support (846MB+), NVIDIA libraries (2GB+), and other heavy ML packages, making development and testing slow.

## Solutions Implemented

### 1. CPU-Only PyTorch Configuration
Modified `pyproject.toml` to use CPU-only PyTorch, reducing download from 3GB+ to ~200MB:

```toml
[tool.uv.sources]
torch = { index = "pytorch-cpu" }
torchvision = { index = "pytorch-cpu" }

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
```

### 2. Dependency Groups
Created separate dependency groups for different use cases:

- **test-minimal**: Just pytest and coverage (~10MB)
- **test**: Full test suite with testcontainers
- **dev**: Development tools (black, ruff, mypy)
- **docs**: Documentation generation

### 3. UV Optimizations
Created `.env.uv` with performance settings:
- Parallel downloads (8 concurrent)
- Bytecode compilation
- Prefer binary wheels
- Use hardlinks for faster installs

### 4. Helper Scripts

#### Quick Test (`scripts/test-quick.sh`)
Runs only simple unit tests with minimal dependencies:
```bash
./scripts/test-quick.sh
```

#### Smart Install (`scripts/smart-install.sh`)
Intelligent installation that detects GPU and installs optimal PyTorch:
```bash
./scripts/smart-install.sh
```

## Usage

### For Quick Testing
```bash
# Install minimal dependencies and run simple tests
make test-quick
```

### For Full Development
```bash
# Smart install - detects GPU and installs optimal PyTorch
make smart-install

# Then run all tests
make test-all
```

### For CI/CD
```bash
# Use dependency groups
uv sync --group test-minimal  # For unit tests
uv sync --group test          # For integration tests
```

## Performance Improvements

| Setup | Download Size | Install Time |
|-------|--------------|--------------|
| Original (with CUDA) | ~3.5GB | 10-15 min |
| CPU-only PyTorch | ~500MB | 2-3 min |
| Test-minimal | ~20MB | <30 sec |

## Tips

1. **First-time setup**: Use `make smart-install` for optimal dependencies (auto-detects GPU)
2. **Quick iterations**: Use `make test-quick` for rapid testing
3. **CI/CD**: Use minimal groups to speed up pipelines
4. **Production**: Use full dependencies with GPU support if needed

## Environment Variables

Set these for faster uv operations:
```bash
export UV_CONCURRENT_DOWNLOADS=8
export UV_COMPILE_BYTECODE=1
export UV_PREFER_BINARY=1
```

Or source the env file:
```bash
source .env.uv
```