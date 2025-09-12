#!/bin/bash

# Test profile runner for OHLCV RAG System
# Provides different test configurations for various environments

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
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to run tests with specific profile
run_test_profile() {
    profile=$1
    shift
    extra_args=$@
    
    print_color "$BLUE" "Running test profile: $profile"
    
    case $profile in
        "dev-mock")
            # Development tests - mock only, no external dependencies
            print_color "$YELLOW" "Running mock tests for development..."
            pytest src/ -m unit \
                   -m "mock or unit" \
                   --tb=short \
                   -v \
                   $extra_args
            ;;
            
        "dev-quick")
            # Quick development tests - subset of unit tests
            print_color "$YELLOW" "Running quick unit tests..."
            pytest src/ \
                   src/::TestDataIngestionMocked \
                   src/::TestRAGPipelineMocked \
                   -m "not slow" \
                   --tb=line \
                   -q \
                   $extra_args
            ;;
            
        "integration-local")
            # Integration tests with local Docker containers
            print_color "$YELLOW" "Running integration tests with local containers..."
            
            # Check if Docker is running
            if ! docker info > /dev/null 2>&1; then
                print_color "$RED" "Error: Docker is not running"
                exit 1
            fi
            
            pytest tests/integration/ \
                   -m "integration and docker" \
                   -v \
                   --tb=short \
                   $extra_args
            ;;
            
        "integration-real")
            # Integration tests with real external services
            print_color "$YELLOW" "Running integration tests with real dependencies..."
            
            # Check for required API keys
            if [ -z "$OPENAI_API_KEY" ]; then
                print_color "$YELLOW" "Warning: OPENAI_API_KEY not set, some tests will be skipped"
            fi
            
            pytest tests/integration/test_real_dependencies.py \
                   -m "real_deps" \
                   -v \
                   --tb=short \
                   $extra_args
            ;;
            
        "ci-unit")
            # CI/CD unit tests - comprehensive but no external deps
            print_color "$YELLOW" "Running CI unit tests..."
            pytest tests/ \
                   -m "unit or mock" \
                   -m "not integration and not real_deps" \
                   --cov=src \
                   --cov-report=term-missing \
                   --cov-report=xml \
                   --junit-xml=test-results/junit.xml \
                   -v \
                   $extra_args
            ;;
            
        "ci-integration")
            # CI/CD integration tests - with containers
            print_color "$YELLOW" "Running CI integration tests..."
            pytest tests/integration/ \
                   -m "integration" \
                   --cov=src \
                   --cov-report=term-missing \
                   --cov-report=xml \
                   --junit-xml=test-results/junit-integration.xml \
                   -v \
                   $extra_args
            ;;
            
        "ci-full")
            # CI/CD full test suite
            print_color "$YELLOW" "Running full CI test suite..."
            
            # Run unit tests first
            pytest tests/ \
                   -m "unit or mock" \
                   -m "not integration and not real_deps" \
                   --cov=src \
                   --cov-report=term-missing \
                   --cov-report=xml:coverage-unit.xml \
                   --junit-xml=test-results/junit-unit.xml \
                   -v || true
            
            # Then run integration tests
            pytest tests/integration/ \
                   -m "integration" \
                   --cov=src \
                   --cov-append \
                   --cov-report=term-missing \
                   --cov-report=xml:coverage-integration.xml \
                   --junit-xml=test-results/junit-integration.xml \
                   -v || true
            
            # Generate combined coverage report
            coverage combine || true
            coverage report || true
            coverage xml -o coverage.xml || true
            ;;
            
        "performance")
            # Performance and benchmark tests
            print_color "$YELLOW" "Running performance tests..."
            pytest tests/ \
                   -m "benchmark or stress" \
                   --tb=short \
                   -v \
                   --durations=10 \
                   $extra_args
            ;;
            
        "smoke")
            # Smoke tests - minimal set to verify basic functionality
            print_color "$YELLOW" "Running smoke tests..."
            pytest src/ -k TestBasicFunctionality::test_mock_data_ingestion \
                   src/ -k TestBasicFunctionality::test_mock_vector_store \
                   src/ -k TestBasicFunctionality::test_mock_rag_pipeline \
                   --tb=line \
                   -v \
                   $extra_args
            ;;
            
        "pre-commit")
            # Pre-commit tests - fast tests to run before committing
            print_color "$YELLOW" "Running pre-commit tests..."
            pytest tests/test_simple.py src/ \
                   -m "not slow and not integration and not real_deps" \
                   --tb=line \
                   -x \
                   --ff \
                   $extra_args
            ;;
            
        "specific-service")
            # Test specific vector store service
            service=$2
            if [ -z "$service" ]; then
                print_color "$RED" "Error: Please specify a service (chromadb, weaviate, qdrant, milvus)"
                exit 1
            fi
            
            print_color "$YELLOW" "Running tests for $service..."
            pytest tests/ \
                   -m "$service" \
                   -v \
                   --tb=short \
                   $extra_args
            ;;
            
        *)
            print_color "$RED" "Unknown profile: $profile"
            echo ""
            echo "Available profiles:"
            echo "  dev-mock         - Mock tests for development (no dependencies)"
            echo "  dev-quick        - Quick subset of unit tests"
            echo "  integration-local - Integration tests with local Docker"
            echo "  integration-real  - Integration tests with real services"
            echo "  ci-unit          - CI unit tests with coverage"
            echo "  ci-integration   - CI integration tests with coverage"
            echo "  ci-full          - Full CI test suite"
            echo "  performance      - Performance and benchmark tests"
            echo "  smoke           - Minimal smoke tests"
            echo "  pre-commit      - Fast tests for pre-commit hooks"
            echo "  specific-service - Test specific service (chromadb, weaviate, etc.)"
            echo ""
            echo "Usage: $0 <profile> [additional pytest args]"
            echo "Example: $0 dev-mock --pdb"
            exit 1
            ;;
    esac
    
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_color "$GREEN" "✓ Tests passed!"
    else
        print_color "$RED" "✗ Tests failed!"
    fi
    
    return $exit_code
}

# Main execution
if [ $# -eq 0 ]; then
    # Default to dev-mock profile
    run_test_profile "dev-mock"
else
    run_test_profile "$@"
fi