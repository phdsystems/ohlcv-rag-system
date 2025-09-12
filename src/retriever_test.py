"""
Unit tests for OHLCV Retriever functionality
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from .retriever import OHLCVRetriever


class TestOHLCVRetriever:
    """Test OHLCVRetriever initialization and basic functionality"""
    
    def test_init_default_parameters(self):
        """Test retriever initialization with default parameters"""
        retriever = OHLCVRetriever()
        
        # Should initialize without errors
        assert retriever is not None
    
    def test_init_with_vector_store(self):
        """Test initialization with custom vector store"""
        mock_vector_store = Mock()
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        assert retriever.vector_store == mock_vector_store
    
    @patch('src.retriever.ChromaVectorStore')
    def test_default_vector_store_creation(self, mock_chroma):
        """Test that default vector store is created when none provided"""
        mock_store_instance = Mock()
        mock_chroma.return_value = mock_store_instance
        
        retriever = OHLCVRetriever()
        
        # Should create a default vector store
        assert hasattr(retriever, 'vector_store')
    
    def test_query_parameter_validation(self):
        """Test query parameter validation"""
        retriever = OHLCVRetriever()
        
        # Test with empty query
        with pytest.raises((ValueError, TypeError)):
            retriever.retrieve("")
        
        # Test with None query
        with pytest.raises((ValueError, TypeError)):
            retriever.retrieve(None)
    
    @patch('src.retriever.ChromaVectorStore')
    def test_retrieve_with_mock_results(self, mock_chroma):
        """Test retrieve method with mocked vector store results"""
        # Setup mock vector store
        mock_results = [
            {"content": "AAPL stock data", "metadata": {"ticker": "AAPL"}},
            {"content": "MSFT stock data", "metadata": {"ticker": "MSFT"}}
        ]
        
        mock_store = Mock()
        mock_store.search.return_value = mock_results
        mock_chroma.return_value = mock_store
        
        retriever = OHLCVRetriever()
        results = retriever.retrieve("tech stocks")
        
        # Should return processed results
        assert isinstance(results, (list, dict))
        mock_store.search.assert_called_once()
    
    def test_retrieve_with_filters(self):
        """Test retrieve method with metadata filters"""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = []
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        # Test with ticker filter
        filters = {"ticker": "AAPL"}
        retriever.retrieve("price data", filters=filters)
        
        mock_vector_store.search.assert_called_once()
    
    def test_similarity_threshold(self):
        """Test similarity threshold parameter"""
        mock_vector_store = Mock()
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        # Test with custom threshold
        retriever.retrieve("query", similarity_threshold=0.8)
        
        # Should have passed threshold parameter
        mock_vector_store.search.assert_called_once()


class TestOHLCVRetrieverAdvanced:
    """Advanced retriever functionality tests"""
    
    @patch('src.retriever.ChromaVectorStore')
    def test_batch_retrieval(self, mock_chroma):
        """Test batch retrieval of multiple queries"""
        mock_store = Mock()
        mock_store.search.return_value = [{"content": "test", "metadata": {}}]
        mock_chroma.return_value = mock_store
        
        retriever = OHLCVRetriever()
        queries = ["AAPL data", "MSFT trends", "tech analysis"]
        
        # Test batch processing if method exists
        for query in queries:
            results = retriever.retrieve(query)
            assert results is not None
    
    def test_empty_results_handling(self):
        """Test handling of empty search results"""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = []
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        results = retriever.retrieve("no matches query")
        
        # Should handle empty results gracefully
        assert isinstance(results, (list, dict, type(None)))
    
    @pytest.mark.unit
    def test_query_preprocessing(self):
        """Test query preprocessing and normalization"""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = []
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        # Test different query formats
        queries = [
            "What are the trends?",
            "SHOW ME AAPL DATA",
            "   whitespace query   ",
            "special!@#$%characters"
        ]
        
        for query in queries:
            try:
                retriever.retrieve(query)
                # Should not raise exceptions for various query formats
            except Exception as e:
                # If it fails, should be a meaningful error
                assert isinstance(e, (ValueError, TypeError))


# Mark all tests as unit tests  
pytestmark = pytest.mark.unit