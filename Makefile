# Makefile for OHLCV RAG System Docker operations

# Variables
IMAGE_NAME ?= ohlcv-rag
BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
IMAGE_TAG ?= $(subst /,-,$(BRANCH))
DOCKER_BUILDKIT := 1
COMPOSE_DOCKER_CLI_BUILD := 1

# Export for docker-compose
export IMAGE_TAG
export DOCKER_BUILDKIT
export COMPOSE_DOCKER_CLI_BUILD

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
	@bash scripts/docker-build.sh

.PHONY: build-all
build-all: ## Build all Docker targets in parallel
	@echo "$(BLUE)Building all targets for $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	@bash scripts/docker-build.sh --all

.PHONY: up
up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d

.PHONY: down
down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down

.PHONY: logs
logs: ## Show logs from all services
	docker-compose logs -f

.PHONY: shell
shell: ## Open shell in running container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	docker-compose exec ohlcv-rag /bin/bash

.PHONY: clean
clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose down
	docker system prune -f

# Default target
.DEFAULT_GOAL := help