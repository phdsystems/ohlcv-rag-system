#!/usr/bin/env python3
"""
Quick test to verify Testcontainers setup with uv
"""

import docker
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer

def test_docker_available():
    """Check if Docker is available"""
    try:
        client = docker.from_env()
        print("✓ Docker is available")
        info = client.info()
        print(f"  Docker version: {info.get('ServerVersion', 'unknown')}")
        return True
    except Exception as e:
        print(f"✗ Docker not available: {e}")
        return False

def test_simple_container():
    """Test running a simple container"""
    try:
        with DockerContainer("alpine:latest") as container:
            container.with_command("echo 'Hello from Testcontainers!'")
            container.start()
            print("✓ Simple container test passed")
            return True
    except Exception as e:
        print(f"✗ Simple container failed: {e}")
        return False

def test_postgres_container():
    """Test PostgreSQL container"""
    try:
        print("Starting PostgreSQL container (this may take a moment)...")
        with PostgresContainer("postgres:15-alpine") as postgres:
            postgres.start()
            conn_url = postgres.get_connection_url()
            print(f"✓ PostgreSQL container started")
            print(f"  Connection URL: {conn_url}")
            return True
    except Exception as e:
        print(f"✗ PostgreSQL container failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Testcontainers with uv setup ===\n")
    
    results = []
    
    # Test Docker availability
    results.append(test_docker_available())
    
    if results[0]:  # Only test containers if Docker is available
        print()
        results.append(test_simple_container())
        print()
        results.append(test_postgres_container())
    
    print("\n=== Summary ===")
    if all(results):
        print("✅ All Testcontainers tests passed!")
        print("\nYou can now run integration tests with:")
        print("  uv run pytest tests/integration/ -v")
    else:
        print("❌ Some tests failed. Check Docker installation.")