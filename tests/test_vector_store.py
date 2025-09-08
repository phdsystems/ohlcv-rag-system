import pytest
from unittest.mock import MagicMock, patch, Mock
from langchain.schema import Document
import chromadb
import numpy as np

from src.vector_store import OHLCVVectorStore


class TestOHLCVVectorStore:
    
    def test_initialization_chromadb(self):
        """Test vector store initialization with ChromaDB"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            assert store.store_type == 'chromadb'
            assert store.collection == mock_collection
            mock_client.assert_called_once()
    
    def test_initialization_faiss(self):
        """Test vector store initialization with FAISS"""
        with patch('src.vector_store.FAISS') as mock_faiss:
            mock_faiss.from_texts.return_value = MagicMock()
            
            store = OHLCVVectorStore(store_type='faiss')
            
            assert store.store_type == 'faiss'
            assert store.vectorstore is not None
    
    def test_initialization_invalid_store(self):
        """Test initialization with invalid store type"""
        with pytest.raises(ValueError, match="Unsupported vector store"):
            OHLCVVectorStore(store_type='invalid_store')
    
    def test_add_documents_chromadb(self, sample_documents):
        """Test adding documents to ChromaDB"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            documents = [
                Document(
                    page_content=doc['content'],
                    metadata={'ticker': doc['ticker'], 'date': doc['date']}
                )
                for doc in sample_documents
            ]
            
            store.add_documents(documents)
            
            # Verify that documents were added
            assert mock_collection.add.called or mock_collection.upsert.called
    
    def test_add_documents_faiss(self, sample_documents):
        """Test adding documents to FAISS"""
        with patch('src.vector_store.FAISS') as mock_faiss:
            mock_vectorstore = MagicMock()
            mock_faiss.from_texts.return_value = mock_vectorstore
            
            store = OHLCVVectorStore(store_type='faiss')
            
            documents = [
                Document(
                    page_content=doc['content'],
                    metadata={'ticker': doc['ticker'], 'date': doc['date']}
                )
                for doc in sample_documents
            ]
            
            with patch.object(store, '_add_documents_faiss') as mock_add:
                store.add_documents(documents)
                mock_add.assert_called_once_with(documents)
    
    def test_similarity_search_chromadb(self):
        """Test similarity search with ChromaDB"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                'documents': [['Document 1', 'Document 2']],
                'metadatas': [[{'ticker': 'AAPL'}, {'ticker': 'GOOGL'}]],
                'distances': [[0.1, 0.2]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            results = store.similarity_search("test query", k=2)
            
            assert len(results) == 2
            assert all(isinstance(doc, Document) for doc in results)
            mock_collection.query.assert_called_once()
    
    def test_similarity_search_faiss(self):
        """Test similarity search with FAISS"""
        with patch('src.vector_store.FAISS') as mock_faiss:
            mock_vectorstore = MagicMock()
            mock_vectorstore.similarity_search.return_value = [
                Document(page_content="Doc 1", metadata={'ticker': 'AAPL'}),
                Document(page_content="Doc 2", metadata={'ticker': 'GOOGL'})
            ]
            mock_faiss.from_texts.return_value = mock_vectorstore
            
            store = OHLCVVectorStore(store_type='faiss')
            
            results = store.similarity_search("test query", k=2)
            
            assert len(results) == 2
            mock_vectorstore.similarity_search.assert_called_once_with("test query", k=2)
    
    def test_search_by_ticker(self):
        """Test searching by ticker filter"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                'documents': [['AAPL document']],
                'metadatas': [[{'ticker': 'AAPL', 'date': '2024-01-01'}]],
                'distances': [[0.1]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            results = store.search_by_ticker("query", ticker='AAPL')
            
            assert len(results) > 0
            assert all(doc.metadata.get('ticker') == 'AAPL' for doc in results)
    
    def test_search_by_date_range(self):
        """Test searching by date range"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                'documents': [['Doc in range']],
                'metadatas': [[{'ticker': 'AAPL', 'date': '2024-01-15'}]],
                'distances': [[0.1]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            results = store.search_by_date_range(
                "query",
                start_date='2024-01-01',
                end_date='2024-01-31'
            )
            
            assert len(results) >= 0
            mock_collection.query.assert_called()
    
    def test_delete_documents(self):
        """Test deleting documents"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            # Test delete by IDs
            store.delete_documents(ids=['id1', 'id2'])
            mock_collection.delete.assert_called_with(ids=['id1', 'id2'])
            
            # Test delete by filter
            store.delete_documents(filter={'ticker': 'AAPL'})
            mock_collection.delete.assert_called_with(where={'ticker': 'AAPL'})
    
    def test_update_documents(self):
        """Test updating documents"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            documents = [
                Document(
                    page_content="Updated content",
                    metadata={'ticker': 'AAPL', 'date': '2024-01-01', 'id': 'doc1'}
                )
            ]
            
            store.update_documents(documents)
            
            # Should call update or upsert
            assert mock_collection.update.called or mock_collection.upsert.called
    
    def test_get_collection_stats(self):
        """Test getting collection statistics"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 100
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            stats = store.get_collection_stats()
            
            assert 'count' in stats
            assert stats['count'] == 100
            mock_collection.count.assert_called_once()
    
    def test_clear_collection(self):
        """Test clearing the collection"""
        with patch('src.vector_store.chromadb.Client') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            mock_client.return_value.delete_collection = MagicMock()
            
            store = OHLCVVectorStore(store_type='chromadb')
            
            store.clear_collection()
            
            # Should delete and recreate collection
            assert mock_client.return_value.delete_collection.called or mock_collection.delete.called