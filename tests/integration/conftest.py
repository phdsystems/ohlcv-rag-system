"""
Testcontainers fixtures for integration testing
"""

import pytest
import os
import time
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
    """Spin up a ChromaDB container for testing"""
    container = DockerContainer("chromadb/chroma:latest")
    container.with_exposed_ports(8000)
    container.with_env("IS_PERSISTENT", "TRUE")
    container.with_env("PERSIST_DIRECTORY", "/chroma/chroma")
    
    with container as chroma:
        chroma.start()
        wait_for_logs(chroma, "Application startup complete", timeout=30)
        
        yield {
            "host": chroma.get_container_host_ip(),
            "port": chroma.get_exposed_port(8000),
            "url": f"http://{chroma.get_container_host_ip()}:{chroma.get_exposed_port(8000)}"
        }


@pytest.fixture(scope="session")
def weaviate_container() -> Generator:
    """Spin up a Weaviate container for testing"""
    container = DockerContainer("semitechnologies/weaviate:latest")
    container.with_exposed_ports(8080)
    container.with_env("AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED", "true")
    container.with_env("PERSISTENCE_DATA_PATH", "/var/lib/weaviate")
    container.with_env("DEFAULT_VECTORIZER_MODULE", "none")
    
    with container as weaviate:
        weaviate.start()
        wait_for_logs(weaviate, "Weaviate is ready", timeout=30)
        
        yield {
            "host": weaviate.get_container_host_ip(),
            "port": weaviate.get_exposed_port(8080),
            "url": f"http://{weaviate.get_container_host_ip()}:{weaviate.get_exposed_port(8080)}"
        }


@pytest.fixture(scope="session")
def qdrant_container() -> Generator:
    """Spin up a Qdrant container for testing"""
    container = DockerContainer("qdrant/qdrant:latest")
    container.with_exposed_ports(6333)
    container.with_env("QDRANT__SERVICE__HTTP_PORT", "6333")
    
    with container as qdrant:
        qdrant.start()
        wait_for_logs(qdrant, "Qdrant is ready", timeout=30)
        
        yield {
            "host": qdrant.get_container_host_ip(),
            "port": qdrant.get_exposed_port(6333),
            "url": f"http://{qdrant.get_container_host_ip()}:{qdrant.get_exposed_port(6333)}"
        }


@pytest.fixture(scope="session")
def milvus_container() -> Generator:
    """Spin up a Milvus container for testing"""
    # Milvus requires etcd and MinIO, so we use docker-compose
    compose_file = """
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd-test
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    container_name: milvus-minio-test
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: minio server /minio_data

  milvus:
    container_name: milvus-standalone-test
    image: milvusdb/milvus:v2.3.3
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
    depends_on:
      - etcd
      - minio
"""
    
    # Create temporary docker-compose file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(compose_file)
        compose_path = f.name
    
    try:
        with DockerCompose(filepath=os.path.dirname(compose_path), 
                          compose_file_name=os.path.basename(compose_path)) as compose:
            compose.start()
            time.sleep(10)  # Wait for Milvus to be ready
            
            yield {
                "host": "localhost",
                "port": 19530,
                "url": "localhost:19530"
            }
    finally:
        os.unlink(compose_path)


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