#!/bin/bash

# Docker Build and Management Script for OHLCV RAG System
# Usage: ./docker-build.sh [command] [options]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ohlcv-rag"
DOCKERFILE="Dockerfile.multi-stage"
COMPOSE_FILE="docker-compose.prod.yml"
DEFAULT_TAG="latest"

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

show_help() {
    echo "Docker Build and Management Script for OHLCV RAG System"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build [target]     Build Docker image (targets: runtime, dev, test, production)"
    echo "  up [profile]       Start services (profiles: default, dev, test, full)"
    echo "  down              Stop and remove containers"
    echo "  clean             Clean up Docker resources"
    echo "  test              Run tests in container"
    echo "  shell [service]   Open shell in container"
    echo "  logs [service]    Show logs for service"
    echo "  status            Show container status"
    echo "  push [tag]        Push image to registry"
    echo "  pull [tag]        Pull image from registry"
    echo ""
    echo "Options:"
    echo "  --tag TAG         Specify image tag (default: latest)"
    echo "  --no-cache        Build without cache"
    echo "  --parallel        Build with parallel execution"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build runtime --tag v1.0.0"
    echo "  $0 up dev"
    echo "  $0 test"
    echo "  $0 shell app"
}

# Enable BuildKit and parallel builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain
export DOCKER_BUILD_PARALLEL=1

# Parse command line arguments
COMMAND=${1:-help}
shift || true

TAG=$DEFAULT_TAG
NO_CACHE=""
PARALLEL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --parallel)
            PARALLEL="--parallel"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            ARGS="$1"
            shift
            ;;
    esac
done

# Main commands
case $COMMAND in
    build)
        TARGET=${ARGS:-runtime}
        print_info "Building Docker image for target: $TARGET with tag: $TAG"
        
        # Create necessary directories
        mkdir -p data/{chromadb,qdrant,weaviate} test-results
        
        # Build with BuildKit optimizations
        BUILDX_ARGS=""
        if [ "$PARALLEL" = "--parallel" ]; then
            BUILDX_ARGS="--build-arg UV_CONCURRENT_DOWNLOADS=10 --build-arg UV_CONCURRENT_BUILDS=4"
            print_info "Building with parallelism enabled"
        fi
        
        docker build \
            --target $TARGET \
            --tag ${PROJECT_NAME}:${TAG} \
            --tag ${PROJECT_NAME}:${TARGET}-${TAG} \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --cache-from ${PROJECT_NAME}:cache \
            --cache-from python:3.11-slim \
            ${BUILDX_ARGS} \
            ${NO_CACHE} \
            -f $DOCKERFILE \
            .
        
        # Tag as cache for future builds
        docker tag ${PROJECT_NAME}:${TAG} ${PROJECT_NAME}:cache
        
        print_success "Build completed successfully!"
        ;;
        
    up)
        PROFILE=${ARGS:-default}
        print_info "Starting services with profile: $PROFILE"
        
        # Set environment variables
        export IMAGE_TAG=$TAG
        
        # Start services based on profile
        case $PROFILE in
            dev)
                docker-compose -f $COMPOSE_FILE --profile dev up -d --parallel
                print_success "Development environment started!"
                print_info "Jupyter available at: http://localhost:8888"
                ;;
            test)
                docker-compose -f $COMPOSE_FILE --profile test up --abort-on-container-exit
                ;;
            full)
                docker-compose -f $COMPOSE_FILE --profile full up -d --parallel
                print_success "Full stack started with all services!"
                ;;
            *)
                docker-compose -f $COMPOSE_FILE up -d --parallel
                print_success "Default services started!"
                ;;
        esac
        
        # Show status
        docker-compose -f $COMPOSE_FILE ps
        ;;
        
    down)
        print_info "Stopping and removing containers..."
        docker-compose -f $COMPOSE_FILE down
        print_success "Containers stopped and removed!"
        ;;
        
    clean)
        print_warning "Cleaning up Docker resources..."
        
        # Stop containers
        docker-compose -f $COMPOSE_FILE down -v
        
        # Remove images
        docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f
        
        # Prune system
        docker system prune -f
        
        print_success "Cleanup completed!"
        ;;
        
    test)
        print_info "Running tests in container..."
        
        # Build test image if needed
        docker build --target test --tag ${PROJECT_NAME}:test -f $DOCKERFILE .
        
        # Run tests
        docker run --rm \
            -v $(pwd)/test-results:/app/test-results \
            -e PYTEST_ADDOPTS="-v --tb=short --color=yes" \
            ${PROJECT_NAME}:test
        
        print_success "Tests completed! Results in ./test-results/"
        ;;
        
    shell)
        SERVICE=${ARGS:-app}
        print_info "Opening shell in $SERVICE container..."
        
        # Check if container is running
        if docker-compose -f $COMPOSE_FILE ps | grep -q $SERVICE; then
            docker-compose -f $COMPOSE_FILE exec $SERVICE /bin/bash
        else
            print_warning "Container $SERVICE is not running. Starting it first..."
            docker-compose -f $COMPOSE_FILE run --rm $SERVICE /bin/bash
        fi
        ;;
        
    logs)
        SERVICE=${ARGS:-}
        if [ -z "$SERVICE" ]; then
            docker-compose -f $COMPOSE_FILE logs -f --tail=100
        else
            docker-compose -f $COMPOSE_FILE logs -f --tail=100 $SERVICE
        fi
        ;;
        
    status)
        print_info "Container status:"
        docker-compose -f $COMPOSE_FILE ps
        echo ""
        print_info "Resource usage:"
        docker stats --no-stream $(docker-compose -f $COMPOSE_FILE ps -q)
        ;;
        
    push)
        PUSH_TAG=${ARGS:-$TAG}
        print_info "Pushing image with tag: $PUSH_TAG"
        
        # Assume registry URL is set in environment
        REGISTRY=${DOCKER_REGISTRY:-""}
        
        if [ -z "$REGISTRY" ]; then
            print_error "DOCKER_REGISTRY environment variable not set!"
            exit 1
        fi
        
        docker tag ${PROJECT_NAME}:${PUSH_TAG} ${REGISTRY}/${PROJECT_NAME}:${PUSH_TAG}
        docker push ${REGISTRY}/${PROJECT_NAME}:${PUSH_TAG}
        
        print_success "Image pushed successfully!"
        ;;
        
    pull)
        PULL_TAG=${ARGS:-$TAG}
        print_info "Pulling image with tag: $PULL_TAG"
        
        REGISTRY=${DOCKER_REGISTRY:-""}
        
        if [ -z "$REGISTRY" ]; then
            print_error "DOCKER_REGISTRY environment variable not set!"
            exit 1
        fi
        
        docker pull ${REGISTRY}/${PROJECT_NAME}:${PULL_TAG}
        docker tag ${REGISTRY}/${PROJECT_NAME}:${PULL_TAG} ${PROJECT_NAME}:${PULL_TAG}
        
        print_success "Image pulled successfully!"
        ;;
        
    help|--help)
        show_help
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac