#!/bin/bash

# Docker build script with BuildKit and parallel builds
# Defaults image name to current git branch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export COMPOSE_DOCKER_CLI_BUILD=1

# Get current git branch name (fallback to 'main' if not in git repo)
get_branch_name() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        # Sanitize branch name for Docker tag (replace / with -)
        echo "${branch//\//-}"
    else
        echo "main"
    fi
}

# Get default image name from branch
DEFAULT_BRANCH=$(get_branch_name)
IMAGE_NAME=${IMAGE_NAME:-"ohlcv-rag"}
IMAGE_TAG=${IMAGE_TAG:-$DEFAULT_BRANCH}
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

print_color $BLUE "========================================="
print_color $BLUE "OHLCV RAG System - Docker Build Script"
print_color $BLUE "========================================="
echo ""
print_color $YELLOW "Build Configuration:"
print_color $GREEN "  Image Name: ${IMAGE_NAME}"
print_color $GREEN "  Image Tag: ${IMAGE_TAG}"
print_color $GREEN "  Full Name: ${FULL_IMAGE_NAME}"
print_color $GREEN "  BuildKit: Enabled"
echo ""

# Parse command line arguments
BUILD_TARGETS=("runtime")
PUSH=false
NO_CACHE=false
PARALLEL=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            BUILD_TARGETS=("runtime" "development" "production")
            shift
            ;;
        --dev)
            BUILD_TARGETS=("development")
            shift
            ;;
        --prod)
            BUILD_TARGETS=("production")
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all          Build all targets (runtime, development, production)"
            echo "  --dev          Build development target only"
            echo "  --prod         Build production target only"
            echo "  --push         Push images to registry after build"
            echo "  --no-cache     Build without using cache"
            echo "  --no-parallel  Disable parallel builds"
            echo "  --help         Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  IMAGE_NAME     Docker image name (default: ohlcv-rag)"
            echo "  IMAGE_TAG      Docker image tag (default: current git branch)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build cache arguments
CACHE_ARGS=""
if [ "$NO_CACHE" = false ]; then
    CACHE_ARGS="--cache-from ${IMAGE_NAME}:${IMAGE_TAG} --cache-from ${IMAGE_NAME}:latest"
fi

# Function to build a single target
build_target() {
    local target=$1
    local tag_suffix=""
    
    case $target in
        development)
            tag_suffix="-dev"
            ;;
        production)
            tag_suffix="-prod"
            ;;
    esac
    
    local target_image="${IMAGE_NAME}:${IMAGE_TAG}${tag_suffix}"
    
    print_color $YELLOW "Building target: ${target} -> ${target_image}"
    
    docker build \
        --target "$target" \
        --tag "$target_image" \
        --tag "${IMAGE_NAME}:latest${tag_suffix}" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        $CACHE_ARGS \
        --progress=auto \
        .
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✓ Successfully built: ${target_image}"
        
        # Show image size
        size=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "${target_image}" | awk '{print $2}')
        print_color $BLUE "  Image size: ${size}"
        
        # Push if requested
        if [ "$PUSH" = true ]; then
            print_color $YELLOW "Pushing ${target_image} to registry..."
            docker push "${target_image}"
            docker push "${IMAGE_NAME}:latest${tag_suffix}"
            print_color $GREEN "✓ Pushed: ${target_image}"
        fi
    else
        print_color $RED "✗ Failed to build: ${target}"
        return 1
    fi
}

# Export functions and variables for parallel execution
export -f build_target print_color
export IMAGE_NAME IMAGE_TAG CACHE_ARGS PUSH

# Main build process
print_color $BLUE "Starting builds..."
echo ""

if [ "$PARALLEL" = true ] && [ ${#BUILD_TARGETS[@]} -gt 1 ]; then
    print_color $YELLOW "Running parallel builds for ${#BUILD_TARGETS[@]} targets..."
    
    # Use GNU parallel if available, otherwise use background jobs
    if command -v parallel &> /dev/null; then
        printf '%s\n' "${BUILD_TARGETS[@]}" | parallel -j ${#BUILD_TARGETS[@]} build_target {}
    else
        # Fallback to background jobs
        pids=()
        for target in "${BUILD_TARGETS[@]}"; do
            build_target "$target" &
            pids+=($!)
        done
        
        # Wait for all background jobs
        failed=false
        for pid in "${pids[@]}"; do
            if ! wait $pid; then
                failed=true
            fi
        done
        
        if [ "$failed" = true ]; then
            print_color $RED "One or more builds failed"
            exit 1
        fi
    fi
else
    # Sequential build
    for target in "${BUILD_TARGETS[@]}"; do
        build_target "$target"
        if [ $? -ne 0 ]; then
            exit 1
        fi
    done
fi

echo ""
print_color $GREEN "========================================="
print_color $GREEN "Build Complete!"
print_color $GREEN "========================================="
echo ""

# Show all built images
print_color $BLUE "Built images:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -1
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep "${IMAGE_NAME}" | grep "${IMAGE_TAG}"

echo ""
print_color $YELLOW "To run the application:"
print_color $GREEN "  docker run -it --rm -v \$(pwd)/data:/data ${FULL_IMAGE_NAME} interactive"
print_color $YELLOW "Or with docker-compose:"
print_color $GREEN "  IMAGE_TAG=${IMAGE_TAG} docker-compose up ohlcv-rag"