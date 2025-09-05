# OHLCV RAG System Makefile

.PHONY: help install install-dev run clean test format lint setup

help: ## Show this help message
	@echo "OHLCV RAG System - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies with uv
	@echo "Installing dependencies..."
	@uv sync --no-dev

install-dev: ## Install all dependencies including dev tools
	@echo "Installing dependencies with dev tools..."
	@uv sync

run: ## Run the OHLCV RAG system
	@uv run python main.py

setup: ## Complete setup (install uv if needed, sync deps, create .env)
	@./setup.sh

clean: ## Clean up cache and temporary files
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true
	@echo "✓ Cleaned up cache and temporary files"

test: ## Run tests
	@uv run pytest

format: ## Format code with black
	@uv run black src/ main.py

lint: ## Lint code with ruff
	@uv run ruff check src/ main.py

shell: ## Start interactive Python shell with project context
	@uv run ipython

fetch-data: ## Fetch fresh OHLCV data
	@uv run python -c "from src.data_ingestion import OHLCVDataIngestion; import os; from dotenv import load_dotenv; load_dotenv(); tickers = os.getenv('TICKER_SYMBOLS', 'AAPL,MSFT').split(','); ingestion = OHLCVDataIngestion(tickers); ingestion.fetch_ohlcv_data(); ingestion.save_data()"

query: ## Interactive query mode
	@uv run python -c "import main; main.main()"

# Development commands
dev-repl: ## Start IPython with all modules loaded
	@uv run ipython -i -c "from src.data_ingestion import *; from src.vector_store import *; from src.retriever import *; from src.rag_pipeline import *; print('OHLCV RAG modules loaded')"

check: format lint ## Format and lint code