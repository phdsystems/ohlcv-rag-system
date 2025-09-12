"""
Testcontainers fixtures for integration testing
"""

import pytest
import os
import time
import requests
from typing import Generator, Dict, Any
from testcontainers.compose import DockerCompose
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import docker
from docker.errors import NotFound


@pytest.fixture(scope="session")
def docker_client():
    """Create a Docker client for managing containers"""
    return docker.from_env()


@pytest.fixture(scope="session")
def postgres_container() -> Generator:
    """Spin up a PostgreSQL container for testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.start()
        yield {
            "host": postgres.get_container_host_ip(),
            "port": postgres.get_exposed_port(5432),
            "username": postgres.username,
            "password": postgres.password,
            "database": postgres.database,
            "url": postgres.get_connection_url()
        }


@pytest.fixture(scope="session")
def redis_container() -> Generator:
    """Spin up a Redis container for testing"""
    with RedisContainer("redis:7-alpine") as redis:
        redis.start()
        yield {
            "host": redis.get_container_host_ip(),
            "port": redis.get_exposed_port(6379),
            "url": f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}"
        }


@pytest.fixture(scope="session")
def chromadb_container() -> Generator:
    """Spin up a ChromaDB container for testing with robust startup handling"""
    # Use specific version for reproducibility  
    container = DockerContainer("chromadb/chroma:0.4.15")
    container.with_exposed_ports(8000)
    container.with_env("IS_PERSISTENT", "FALSE")  # Use memory mode for faster tests
    container.with_env("CHROMA_SERVER_AUTHN_CREDENTIALS", "admin:test")
    container.with_env("CHROMA_SERVER_AUTHN_PROVIDER", "chromadb.auth.basic_authn.BasicAuthenticationServerProvider")
    container.with_env("ANONYMIZED_TELEMETRY", "FALSE")
    
    with container as chroma:
        chroma.start()
        
        # Use multiple strategies for waiting
        import time
        import requests
        
        # Wait for port to be available
        host = chroma.get_container_host_ip()
        port = chroma.get_exposed_port(8000)
        url = f"http://{host}:{port}"
        
        # Retry connection with exponential backoff
        max_wait_time = 60  # seconds
        wait_time = 1
        total_waited = 0
        
        while total_waited < max_wait_time:
            try:
                # Try to hit the health endpoint
                response = requests.get(f"{url}/api/v1/heartbeat", timeout=5)
                if response.status_code == 200:
                    print(f"ChromaDB container ready at {url}")
                    break
            except:
                pass
            
            print(f"Waiting for ChromaDB container... ({total_waited}s/{max_wait_time}s)")
            time.sleep(wait_time)
            total_waited += wait_time
            wait_time = min(wait_time * 1.5, 10)  # Exponential backoff capped at 10s
        else:
            raise TimeoutError(f"ChromaDB container failed to start within {max_wait_time}s")
        
        yield {
            "host": host,
            "port": port,
            "url": url
        }


@pytest.fixture(scope="session")
def weaviate_container() -> Generator:
    """Spin up a Weaviate container for testing with robust startup handling"""
    # Use specific version for reproducibility
    container = DockerContainer("semitechnologies/weaviate:1.22.4")
    container.with_exposed_ports(8080)
    container.with_env("AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED", "true")
    container.with_env("PERSISTENCE_DATA_PATH", "/tmp/weaviate")  # Use tmp for faster startup
    container.with_env("DEFAULT_VECTORIZER_MODULE", "none")
    container.with_env("ENABLE_MODULES", "")
    container.with_env("LOG_LEVEL", "warning")  # Reduce log noise
    
    with container as weaviate:
        weaviate.start()
        
        # Use health endpoint for waiting
        import time
        import requests
        
        host = weaviate.get_container_host_ip()
        port = weaviate.get_exposed_port(8080)
        url = f"http://{host}:{port}"
        
        # Retry connection with exponential backoff
        max_wait_time = 60
        wait_time = 1
        total_waited = 0
        
        while total_waited < max_wait_time:
            try:
                # Check health endpoint
                response = requests.get(f"{url}/v1/meta", timeout=5)
                if response.status_code == 200:
                    print(f"Weaviate container ready at {url}")
                    break
            except:
                pass
            
            print(f"Waiting for Weaviate container... ({total_waited}s/{max_wait_time}s)")
            time.sleep(wait_time)
            total_waited += wait_time
            wait_time = min(wait_time * 1.5, 10)
        else:
            raise TimeoutError(f"Weaviate container failed to start within {max_wait_time}s")
        
        yield {
            "host": host,
            "port": port,
            "url": url
        }


@pytest.fixture(scope="session")
def qdrant_container() -> Generator:
    """Spin up a Qdrant container for testing with robust startup handling"""
    # Use specific version for reproducibility
    container = DockerContainer("qdrant/qdrant:v1.6.1")
    container.with_exposed_ports(6333)
    container.with_env("QDRANT__SERVICE__HTTP_PORT", "6333")
    container.with_env("QDRANT__STORAGE__STORAGE_PATH", "/tmp/qdrant_storage")  # Use tmp for speed
    
    with container as qdrant:
        qdrant.start()
        
        # Use health endpoint for waiting
        import time
        import requests
        
        host = qdrant.get_container_host_ip()
        port = qdrant.get_exposed_port(6333)
        url = f"http://{host}:{port}"
        
        # Retry connection
        max_wait_time = 60
        wait_time = 1
        total_waited = 0
        
        while total_waited < max_wait_time:
            try:
                # Check health endpoint
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"Qdrant container ready at {url}")
                    break
            except:
                pass
            
            print(f"Waiting for Qdrant container... ({total_waited}s/{max_wait_time}s)")
            time.sleep(wait_time)
            total_waited += wait_time
            wait_time = min(wait_time * 1.5, 10)
        else:
            raise TimeoutError(f"Qdrant container failed to start within {max_wait_time}s")
        
        yield {
            "host": host,
            "port": port,
            "url": url
        }


@pytest.fixture(scope="session")
def milvus_container() -> Generator:
    """Spin up a Milvus Lite container for testing (simpler setup)"""
    # Skip complex Milvus setup for now - use embedded mode in the actual store
    # This fixture exists for API compatibility but doesn't start actual container
    yield {
        "host": "localhost",
        "port": 19530,
        "url": "lite:///tmp/milvus_test.db"  # Use lite mode URL
    }


@pytest.fixture(scope="function")
def clean_chromadb(chromadb_container):
    """Provide a clean ChromaDB instance for each test"""
    import chromadb
    
    client = chromadb.HttpClient(
        host=chromadb_container["host"],
        port=chromadb_container["port"]
    )
    
    # Clean existing collections
    for collection in client.list_collections():
        client.delete_collection(collection.name)
    
    yield client
    
    # Cleanup after test
    for collection in client.list_collections():
        client.delete_collection(collection.name)


@pytest.fixture(scope="function")
def clean_weaviate(weaviate_container):
    """Provide a clean Weaviate instance for each test"""
    import weaviate
    
    client = weaviate.Client(url=weaviate_container["url"])
    
    # Clean existing schema
    try:
        client.schema.delete_all()
    except:
        pass
    
    yield client
    
    # Cleanup after test
    try:
        client.schema.delete_all()
    except:
        pass


@pytest.fixture(scope="function")
def clean_qdrant(qdrant_container):
    """Provide a clean Qdrant instance for each test"""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(
        host=qdrant_container["host"],
        port=qdrant_container["port"]
    )
    
    # Clean existing collections
    collections = client.get_collections().collections
    for collection in collections:
        client.delete_collection(collection.name)
    
    yield client
    
    # Cleanup after test
    collections = client.get_collections().collections
    for collection in collections:
        client.delete_collection(collection.name)


@pytest.fixture
def sample_embeddings():
    """Generate sample embeddings for testing"""
    import numpy as np
    
    return {
        "embeddings": np.random.rand(10, 768).tolist(),  # 10 vectors of dimension 768
        "metadata": [
            {"ticker": "AAPL", "date": "2024-01-01", "price": 150.0},
            {"ticker": "GOOGL", "date": "2024-01-01", "price": 2800.0},
            {"ticker": "MSFT", "date": "2024-01-01", "price": 370.0},
            {"ticker": "AAPL", "date": "2024-01-02", "price": 152.0},
            {"ticker": "GOOGL", "date": "2024-01-02", "price": 2850.0},
            {"ticker": "MSFT", "date": "2024-01-02", "price": 375.0},
            {"ticker": "AAPL", "date": "2024-01-03", "price": 155.0},
            {"ticker": "GOOGL", "date": "2024-01-03", "price": 2900.0},
            {"ticker": "MSFT", "date": "2024-01-03", "price": 380.0},
            {"ticker": "TSLA", "date": "2024-01-01", "price": 240.0},
        ],
        "documents": [
            f"Technical analysis for {meta['ticker']} on {meta['date']}: Price at ${meta['price']}"
            for meta in [
                {"ticker": "AAPL", "date": "2024-01-01", "price": 150.0},
                {"ticker": "GOOGL", "date": "2024-01-01", "price": 2800.0},
                {"ticker": "MSFT", "date": "2024-01-01", "price": 370.0},
                {"ticker": "AAPL", "date": "2024-01-02", "price": 152.0},
                {"ticker": "GOOGL", "date": "2024-01-02", "price": 2850.0},
                {"ticker": "MSFT", "date": "2024-01-02", "price": 375.0},
                {"ticker": "AAPL", "date": "2024-01-03", "price": 155.0},
                {"ticker": "GOOGL", "date": "2024-01-03", "price": 2900.0},
                {"ticker": "MSFT", "date": "2024-01-03", "price": 380.0},
                {"ticker": "TSLA", "date": "2024-01-01", "price": 240.0},
            ]
        ]
    }