"""
Integration tests for ChromaDB using Testcontainers
"""

import pytest
import numpy as np
from typing import List, Dict, Any


class TestChromaDBIntegration:
    
    @pytest.mark.integration
    def test_chromadb_connection(self, clean_chromadb):
        """Test basic connection to ChromaDB container"""
        # Test that we can connect and create a collection
        collection = clean_chromadb.create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )
        
        assert collection.name == "test_collection"
        assert collection.count() == 0
    
    @pytest.mark.integration
    def test_chromadb_crud_operations(self, clean_chromadb, sample_embeddings):
        """Test CRUD operations with ChromaDB"""
        # Create collection
        collection = clean_chromadb.create_collection(
            name="ohlcv_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents
        collection.add(
            embeddings=sample_embeddings["embeddings"][:5],
            metadatas=sample_embeddings["metadata"][:5],
            documents=sample_embeddings["documents"][:5],
            ids=[f"doc_{i}" for i in range(5)]
        )
        
        assert collection.count() == 5
        
        # Query documents
        results = collection.query(
            query_embeddings=[sample_embeddings["embeddings"][0]],
            n_results=3
        )
        
        assert len(results["ids"][0]) == 3
        assert results["ids"][0][0] == "doc_0"  # Should match itself first
        
        # Update document
        collection.update(
            ids=["doc_0"],
            metadatas=[{"ticker": "AAPL", "date": "2024-01-01", "price": 160.0}]
        )
        
        # Get updated document
        result = collection.get(ids=["doc_0"])
        assert result["metadatas"][0]["price"] == 160.0
        
        # Delete document
        collection.delete(ids=["doc_0"])
        assert collection.count() == 4
    
    @pytest.mark.integration
    def test_chromadb_filtering(self, clean_chromadb, sample_embeddings):
        """Test filtering capabilities in ChromaDB"""
        collection = clean_chromadb.create_collection(
            name="filtered_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add all documents
        collection.add(
            embeddings=sample_embeddings["embeddings"],
            metadatas=sample_embeddings["metadata"],
            documents=sample_embeddings["documents"],
            ids=[f"doc_{i}" for i in range(len(sample_embeddings["embeddings"]))]
        )
        
        # Filter by ticker
        results = collection.query(
            query_embeddings=[sample_embeddings["embeddings"][0]],
            n_results=10,
            where={"ticker": "AAPL"}
        )
        
        # Should only return AAPL documents
        for metadata in results["metadatas"][0]:
            assert metadata["ticker"] == "AAPL"
        
        # Filter by date range (ChromaDB doesn't support range queries directly)
        # We'll test exact match instead
        results = collection.query(
            query_embeddings=[sample_embeddings["embeddings"][0]],
            n_results=10,
            where={"date": "2024-01-01"}
        )
        
        for metadata in results["metadatas"][0]:
            assert metadata["date"] == "2024-01-01"
    
    @pytest.mark.integration
    def test_chromadb_batch_operations(self, clean_chromadb):
        """Test batch operations with ChromaDB"""
        collection = clean_chromadb.create_collection(name="batch_test")
        
        # Generate large batch of data
        batch_size = 100
        embeddings = np.random.rand(batch_size, 768).tolist()
        metadatas = [
            {"ticker": f"TICK{i%5}", "batch": i//10}
            for i in range(batch_size)
        ]
        documents = [f"Document {i}" for i in range(batch_size)]
        ids = [f"doc_{i}" for i in range(batch_size)]
        
        # Batch insert
        collection.add(
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
            ids=ids
        )
        
        assert collection.count() == batch_size
        
        # Batch query
        query_embeddings = embeddings[:5]
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=3
        )
        
        assert len(results["ids"]) == 5  # 5 queries
        assert all(len(ids) == 3 for ids in results["ids"])  # 3 results each
    
    @pytest.mark.integration
    def test_chromadb_persistence(self, chromadb_container):
        """Test data persistence across connections"""
        import chromadb
        
        # First connection - add data
        client1 = chromadb.HttpClient(
            host=chromadb_container["host"],
            port=chromadb_container["port"]
        )
        
        collection1 = client1.create_collection(name="persistent_test")
        collection1.add(
            embeddings=[[1.0] * 768],
            metadatas=[{"test": "data"}],
            documents=["Test document"],
            ids=["test_id"]
        )
        
        # Second connection - verify data exists
        client2 = chromadb.HttpClient(
            host=chromadb_container["host"],
            port=chromadb_container["port"]
        )
        
        collection2 = client2.get_collection(name="persistent_test")
        assert collection2.count() == 1
        
        result = collection2.get(ids=["test_id"])
        assert result["metadatas"][0]["test"] == "data"
        
        # Cleanup
        client2.delete_collection("persistent_test")
    
    @pytest.mark.integration
    def test_chromadb_similarity_search(self, clean_chromadb, sample_embeddings):
        """Test similarity search functionality"""
        collection = clean_chromadb.create_collection(
            name="similarity_test",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents
        collection.add(
            embeddings=sample_embeddings["embeddings"],
            metadatas=sample_embeddings["metadata"],
            documents=sample_embeddings["documents"],
            ids=[f"doc_{i}" for i in range(len(sample_embeddings["embeddings"]))]
        )
        
        # Create a query embedding similar to first document
        query_embedding = sample_embeddings["embeddings"][0].copy()
        # Add small noise to make it slightly different
        query_embedding = [val + np.random.normal(0, 0.01) for val in query_embedding]
        
        # Search for similar documents
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["metadatas", "distances", "documents"]
        )
        
        # Check results are ordered by similarity (distance)
        distances = results["distances"][0]
        assert distances == sorted(distances)  # Should be in ascending order
        
        # First result should be most similar (lowest distance)
        assert results["ids"][0][0] == "doc_0"  # Should be closest to original
    
    @pytest.mark.integration
    def test_chromadb_error_handling(self, clean_chromadb):
        """Test error handling in ChromaDB operations"""
        collection = clean_chromadb.create_collection(name="error_test")
        
        # Try to add document with mismatched dimensions
        with pytest.raises(Exception):
            collection.add(
                embeddings=[[1.0] * 100],  # Wrong dimension
                documents=["Test"],
                ids=["test1"]
            )
        
        # Try to get non-existent document
        result = collection.get(ids=["non_existent"])
        assert len(result["ids"]) == 0
        
        # Try to create collection with same name
        with pytest.raises(Exception):
            clean_chromadb.create_collection(name="error_test")