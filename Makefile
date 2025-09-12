# Makefile for OHLCV RAG System Docker operations

# Variables
IMAGE_NAME ?= ohlcv-rag
BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
IMAGE_TAG ?= $(subst /,-,$(BRANCH))
DOCKER_BUILDKIT := 1
COMPOSE_DOCKER_CLI_BUILD := 1
BUILDKIT_PROGRESS := plain
PARALLEL_JOBS ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
DOCKERFILE := docker/Dockerfile.multi-stage

# Export for docker-compose
export IMAGE_TAG
export DOCKER_BUILDKIT
export COMPOSE_DOCKER_CLI_BUILD
export BUILDKIT_PROGRESS

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)OHLCV RAG System - Docker Operations$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make [target]"
	@echo ""
	@echo "$(YELLOW)Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Variables:$(NC)"
	@echo "  $(GREEN)IMAGE_NAME$(NC)    = $(IMAGE_NAME)"
	@echo "  $(GREEN)IMAGE_TAG$(NC)     = $(IMAGE_TAG)"
	@echo "  $(GREEN)BRANCH$(NC)        = $(BRANCH)"

.PHONY: build
build: ## Build Docker image (runtime target)
	@echo "$(BLUE)Building $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	@./docker/docker-build.sh build runtime

.PHONY: build-all
build-all: ## Build all Docker targets in parallel
	@echo "$(BLUE)Building all targets for $(IMAGE_NAME):$(IMAGE_TAG) with $(PARALLEL_JOBS) parallel jobs...$(NC)"
	@$(MAKE) -j$(PARALLEL_JOBS) build-runtime build-dev build-test build-production

.PHONY: up
up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose -f docker/docker-compose.prod.yml up -d --parallel

.PHONY: down
down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose -f docker/docker-compose.prod.yml down

.PHONY: logs
logs: ## Show logs from all services
	docker-compose -f docker/docker-compose.prod.yml logs -f

.PHONY: shell
shell: ## Open shell in running container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	docker-compose -f docker/docker-compose.prod.yml exec app /bin/bash

.PHONY: clean
clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose -f docker/docker-compose.prod.yml down -v
	docker system prune -f

.PHONY: test
test: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@uv run pytest tests/test_simple.py -v

.PHONY: test-all
test-all: ## Run all tests with coverage
	@echo "$(BLUE)Running all tests with coverage...$(NC)"
	@uv run pytest tests/ -v --cov=src --cov-report=term-missing || true

.PHONY: test-simple
test-simple: ## Run simple mock-based tests
	@echo "$(BLUE)Running simple tests...$(NC)"
	@uv run pytest tests/test_simple.py -v

.PHONY: test-quick
test-quick: ## Run quick tests with minimal dependencies
	@echo "$(BLUE)Running quick tests...$(NC)"
	@./scripts/test-quick.sh

.PHONY: test-mock
test-mock: ## Run comprehensive mock test suite
	@echo "$(BLUE)Running mock test suite...$(NC)"
	@./scripts/test-profiles.sh dev-mock

.PHONY: test-dev
test-dev: ## Run development tests (quick mock tests)
	@echo "$(BLUE)Running development tests...$(NC)"
	@./scripts/test-profiles.sh dev-quick

.PHONY: test-ci
test-ci: ## Run CI test suite
	@echo "$(BLUE)Running CI test suite...$(NC)"
	@./scripts/test-profiles.sh ci-full

.PHONY: test-profile
test-profile: ## Run specific test profile (use PROFILE=<name>)
	@echo "$(BLUE)Running test profile: $(PROFILE)...$(NC)"
	@./scripts/test-profiles.sh $(PROFILE)

.PHONY: install-cpu-only
install-cpu-only: ## Install with CPU-only PyTorch (faster, smaller)
	@echo "$(BLUE)Installing CPU-only dependencies (faster, smaller)...$(NC)"
	@./scripts/install-cpu-only.sh

.PHONY: test-install
test-install: ## Install test dependencies
	@echo "$(BLUE)Installing test dependencies...$(NC)"
	@pip install -r requirements-test.txt

.PHONY: test-integration
test-integration: ## Run integration tests with Testcontainers
	@echo "$(BLUE)Running integration tests with Testcontainers...$(NC)"
	@python -m pytest tests/integration/ -m integration -v

.PHONY: test-integration-install
test-integration-install: ## Install integration test dependencies
	@echo "$(BLUE)Installing integration test dependencies...$(NC)"
	@pip install -r requirements-integration.txt

.PHONY: test-chromadb
test-chromadb: ## Run ChromaDB integration tests
	@echo "$(BLUE)Running ChromaDB integration tests...$(NC)"
	@python -m pytest tests/integration/test_chromadb_integration.py -v

.PHONY: test-weaviate
test-weaviate: ## Run Weaviate integration tests
	@echo "$(BLUE)Running Weaviate integration tests...$(NC)"
	@python -m pytest tests/integration/test_weaviate_integration.py -v

.PHONY: test-qdrant
test-qdrant: ## Run Qdrant integration tests
	@echo "$(BLUE)Running Qdrant integration tests...$(NC)"
	@python -m pytest tests/integration/test_qdrant_integration.py -v

.PHONY: test-e2e
test-e2e: ## Run end-to-end integration tests
	@echo "$(BLUE)Running end-to-end integration tests...$(NC)"
	@python -m pytest tests/integration/test_end_to_end.py -v -s

# Parallel build targets
.PHONY: build-runtime
build-runtime: ## Build runtime Docker image
	@echo "$(BLUE)Building runtime image...$(NC)"
	@docker build \
		--target runtime \
		--tag $(IMAGE_NAME):runtime-$(IMAGE_TAG) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--build-arg UV_CONCURRENT_DOWNLOADS=10 \
		--build-arg UV_CONCURRENT_BUILDS=4 \
		--cache-from $(IMAGE_NAME):cache \
		-f $(DOCKERFILE) .

.PHONY: build-dev
build-dev: ## Build development Docker image
	@echo "$(BLUE)Building development image...$(NC)"
	@docker build \
		--target development \
		--tag $(IMAGE_NAME):dev-$(IMAGE_TAG) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--build-arg UV_CONCURRENT_DOWNLOADS=10 \
		--build-arg UV_CONCURRENT_BUILDS=4 \
		--cache-from $(IMAGE_NAME):runtime-$(IMAGE_TAG) \
		-f $(DOCKERFILE) .

.PHONY: build-test
build-test: ## Build test Docker image
	@echo "$(BLUE)Building test image...$(NC)"
	@docker build \
		--target test \
		--tag $(IMAGE_NAME):test-$(IMAGE_TAG) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--build-arg UV_CONCURRENT_DOWNLOADS=10 \
		--build-arg UV_CONCURRENT_BUILDS=4 \
		--cache-from $(IMAGE_NAME):runtime-$(IMAGE_TAG) \
		-f $(DOCKERFILE) .

.PHONY: build-production
build-production: ## Build production Docker image
	@echo "$(BLUE)Building production image...$(NC)"
	@docker build \
		--target production \
		--tag $(IMAGE_NAME):prod-$(IMAGE_TAG) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--build-arg UV_CONCURRENT_DOWNLOADS=10 \
		--build-arg UV_CONCURRENT_BUILDS=4 \
		--cache-from $(IMAGE_NAME):cache \
		-f $(DOCKERFILE) .

.PHONY: build-parallel
build-parallel: ## Build all images with maximum parallelism
	@echo "$(BLUE)Building all images in parallel with $(PARALLEL_JOBS) jobs...$(NC)"
	@$(MAKE) -j$(PARALLEL_JOBS) build-all

.PHONY: benchmark-builds
benchmark-builds: ## Benchmark sequential vs parallel builds
	@echo "$(YELLOW)Benchmarking build times...$(NC)"
	@echo "Sequential build:"
	@time $(MAKE) build-runtime build-dev build-test build-production
	@$(MAKE) clean
	@echo "\nParallel build ($(PARALLEL_JOBS) jobs):"
	@time $(MAKE) -j$(PARALLEL_JOBS) build-runtime build-dev build-test build-production

# Enable parallel execution for these targets
.PARALLEL: build-runtime build-dev build-test build-production

# Default target
.DEFAULT_GOAL := help