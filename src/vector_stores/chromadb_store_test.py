"""
Tests for ChromaDB vector database functionality
"""

import pytest
import chromadb
import numpy as np


class TestChromaDB:
    """Test ChromaDB vector storage operations"""
    
    def test_chromadb_client_creation(self):
        """Test creating ChromaDB client"""
        client = chromadb.Client()
        assert client is not None
    
    def test_chromadb_collection_operations(self):
        """Test ChromaDB collection creation and deletion"""
        client = chromadb.Client()
        
        # Create collection
        collection = client.create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )
        assert collection is not None
        assert collection.name == "test_collection"
        
        # Delete collection
        client.delete_collection("test_collection")
        
        # Verify deletion
        collections = client.list_collections()
        assert not any(c.name == "test_collection" for c in collections)
    
    def test_chromadb_document_storage(self):
        """Test storing and retrieving documents in ChromaDB"""
        client = chromadb.Client()
        collection = client.create_collection(name="test_docs")
        
        try:
            # Add documents
            documents = [
                "Apple stock rose 5% today",
                "AAPL shows bullish trend",
                "Technical indicators are positive"
            ]
            metadatas = [
                {"ticker": "AAPL", "date": "2024-01-01"},
                {"ticker": "AAPL", "date": "2024-01-02"},
                {"ticker": "AAPL", "date": "2024-01-03"}
            ]
            ids = ["doc1", "doc2", "doc3"]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Query documents
            results = collection.query(
                query_texts=["Apple stock performance"],
                n_results=2
            )
            
            assert len(results['documents'][0]) > 0
            assert results['ids'][0] is not None
            
        finally:
            client.delete_collection("test_docs")
    
    def test_chromadb_metadata_filtering(self):
        """Test ChromaDB metadata filtering"""
        client = chromadb.Client()
        collection = client.create_collection(name="test_filter")
        
        try:
            # Add documents with metadata
            collection.add(
                documents=["Doc about AAPL", "Doc about MSFT", "Another AAPL doc"],
                metadatas=[
                    {"ticker": "AAPL", "year": 2024},
                    {"ticker": "MSFT", "year": 2024},
                    {"ticker": "AAPL", "year": 2023}
                ],
                ids=["1", "2", "3"]
            )
            
            # Query with metadata filter
            results = collection.query(
                query_texts=["stock"],
                where={"ticker": "AAPL"},
                n_results=10
            )
            
            # Should only get AAPL documents
            assert len(results['ids'][0]) == 2
            
        finally:
            client.delete_collection("test_filter")