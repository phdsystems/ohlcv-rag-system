"""
Integration tests for Qdrant using Testcontainers
"""

import pytest
import numpy as np
from typing import List, Dict, Any
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range


class TestQdrantIntegration:
    
    @pytest.mark.integration
    def test_qdrant_connection(self, clean_qdrant):
        """Test basic connection to Qdrant container"""
        # Test that we can connect and get collections
        collections = clean_qdrant.get_collections()
        assert collections is not None
        assert hasattr(collections, 'collections')
    
    @pytest.mark.integration
    def test_qdrant_collection_creation(self, clean_qdrant):
        """Test creating collections in Qdrant"""
        # Create collection with specific vector configuration
        clean_qdrant.create_collection(
            collection_name="ohlcv_data",
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
        # Verify collection exists
        collections = clean_qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        assert "ohlcv_data" in collection_names
        
        # Get collection info
        info = clean_qdrant.get_collection("ohlcv_data")
        assert info.config.params.vectors.size == 768
        assert info.config.params.vectors.distance == Distance.COSINE
    
    @pytest.mark.integration
    def test_qdrant_point_operations(self, clean_qdrant):
        """Test CRUD operations with points in Qdrant"""
        # Create collection
        clean_qdrant.create_collection(
            collection_name="test_points",
            vectors_config=VectorParams(size=128, distance=Distance.DOT)
        )
        
        # Insert points
        points = [
            PointStruct(
                id=i,
                vector=np.random.rand(128).tolist(),
                payload={
                    "ticker": f"TICK{i}",
                    "price": 100.0 + i * 10,
                    "date": f"2024-01-{i+1:02d}"
                }
            )
            for i in range(10)
        ]
        
        clean_qdrant.upsert(
            collection_name="test_points",
            points=points
        )
        
        # Retrieve point
        result = clean_qdrant.retrieve(
            collection_name="test_points",
            ids=[0, 1, 2]
        )
        assert len(result) == 3
        assert result[0].payload["ticker"] == "TICK0"
        
        # Update point
        clean_qdrant.set_payload(
            collection_name="test_points",
            payload={"price": 200.0},
            points=[0]
        )
        
        updated = clean_qdrant.retrieve(
            collection_name="test_points",
            ids=[0]
        )[0]
        assert updated.payload["price"] == 200.0
        
        # Delete point
        clean_qdrant.delete(
            collection_name="test_points",
            points_selector=[5]
        )
        
        # Verify deletion
        remaining = clean_qdrant.count(collection_name="test_points")
        assert remaining.count == 9
    
    @pytest.mark.integration
    def test_qdrant_vector_search(self, clean_qdrant, sample_embeddings):
        """Test vector similarity search in Qdrant"""
        # Create collection
        clean_qdrant.create_collection(
            collection_name="search_test",
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
        # Insert points with embeddings
        points = [
            PointStruct(
                id=i,
                vector=sample_embeddings["embeddings"][i],
                payload=sample_embeddings["metadata"][i]
            )
            for i in range(len(sample_embeddings["embeddings"]))
        ]
        
        clean_qdrant.upsert(
            collection_name="search_test",
            points=points
        )
        
        # Search similar vectors
        query_vector = sample_embeddings["embeddings"][0]
        results = clean_qdrant.search(
            collection_name="search_test",
            query_vector=query_vector,
            limit=5
        )
        
        assert len(results) == 5
        # First result should be the same vector (highest similarity)
        assert results[0].id == 0
        assert results[0].score > 0.99  # Cosine similarity should be very high
    
    @pytest.mark.integration
    def test_qdrant_filtered_search(self, clean_qdrant):
        """Test filtered search in Qdrant"""
        # Create collection
        clean_qdrant.create_collection(
            collection_name="filtered_search",
            vectors_config=VectorParams(size=128, distance=Distance.EUCLID)
        )
        
        # Insert diverse data
        points = []
        for i in range(50):
            points.append(PointStruct(
                id=i,
                vector=np.random.rand(128).tolist(),
                payload={
                    "ticker": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"][i % 5],
                    "price": 100.0 + i * 5,
                    "volume": 1000000 + i * 10000,
                    "date": f"2024-01-{(i % 30) + 1:02d}"
                }
            ))
        
        clean_qdrant.upsert(
            collection_name="filtered_search",
            points=points
        )
        
        # Search with ticker filter
        query_vector = np.random.rand(128).tolist()
        results = clean_qdrant.search(
            collection_name="filtered_search",
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="ticker",
                        match={"value": "AAPL"}
                    )
                ]
            ),
            limit=5
        )
        
        # All results should be AAPL
        for result in results:
            assert result.payload["ticker"] == "AAPL"
        
        # Search with price range filter
        results = clean_qdrant.search(
            collection_name="filtered_search",
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="price",
                        range=Range(gte=200.0, lte=300.0)
                    )
                ]
            ),
            limit=10
        )
        
        # All results should have price in range
        for result in results:
            assert 200.0 <= result.payload["price"] <= 300.0
    
    @pytest.mark.integration
    def test_qdrant_batch_operations(self, clean_qdrant):
        """Test batch operations in Qdrant"""
        # Create collection
        clean_qdrant.create_collection(
            collection_name="batch_test",
            vectors_config=VectorParams(size=256, distance=Distance.DOT)
        )
        
        # Batch insert
        batch_size = 1000
        points = [
            PointStruct(
                id=i,
                vector=np.random.rand(256).tolist(),
                payload={
                    "batch_id": i // 100,
                    "item_id": i
                }
            )
            for i in range(batch_size)
        ]
        
        # Insert in chunks
        chunk_size = 100
        for i in range(0, batch_size, chunk_size):
            clean_qdrant.upsert(
                collection_name="batch_test",
                points=points[i:i+chunk_size]
            )
        
        # Verify all inserted
        count = clean_qdrant.count(collection_name="batch_test")
        assert count.count == batch_size
        
        # Batch search
        query_vectors = [np.random.rand(256).tolist() for _ in range(5)]
        
        for query_vector in query_vectors:
            results = clean_qdrant.search(
                collection_name="batch_test",
                query_vector=query_vector,
                limit=10
            )
            assert len(results) <= 10
    
    @pytest.mark.integration
    def test_qdrant_payload_indexing(self, clean_qdrant):
        """Test payload field indexing for faster filtering"""
        # Create collection
        clean_qdrant.create_collection(
            collection_name="indexed_collection",
            vectors_config=VectorParams(size=128, distance=Distance.COSINE)
        )
        
        # Create payload index for faster filtering
        clean_qdrant.create_payload_index(
            collection_name="indexed_collection",
            field_name="ticker",
            field_schema="keyword"
        )
        
        clean_qdrant.create_payload_index(
            collection_name="indexed_collection",
            field_name="price",
            field_schema="float"
        )
        
        # Insert data
        points = [
            PointStruct(
                id=i,
                vector=np.random.rand(128).tolist(),
                payload={
                    "ticker": f"TICK{i % 10}",
                    "price": 100.0 + i
                }
            )
            for i in range(100)
        ]
        
        clean_qdrant.upsert(
            collection_name="indexed_collection",
            points=points
        )
        
        # Search should be faster with indexes
        results = clean_qdrant.search(
            collection_name="indexed_collection",
            query_vector=np.random.rand(128).tolist(),
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="ticker",
                        match={"value": "TICK5"}
                    ),
                    FieldCondition(
                        key="price",
                        range=Range(gte=150.0)
                    )
                ]
            ),
            limit=10
        )
        
        # Verify filtered results
        for result in results:
            assert result.payload["ticker"] == "TICK5"
            assert result.payload["price"] >= 150.0
    
    @pytest.mark.integration
    def test_qdrant_snapshot_operations(self, clean_qdrant):
        """Test snapshot creation and restoration"""
        # Create collection with data
        clean_qdrant.create_collection(
            collection_name="snapshot_test",
            vectors_config=VectorParams(size=128, distance=Distance.COSINE)
        )
        
        # Add data
        points = [
            PointStruct(
                id=i,
                vector=np.random.rand(128).tolist(),
                payload={"value": i}
            )
            for i in range(10)
        ]
        clean_qdrant.upsert(
            collection_name="snapshot_test",
            points=points
        )
        
        # Create snapshot
        snapshot = clean_qdrant.create_snapshot(collection_name="snapshot_test")
        assert snapshot is not None
        
        # List snapshots
        snapshots = clean_qdrant.list_snapshots(collection_name="snapshot_test")
        assert len(snapshots) > 0