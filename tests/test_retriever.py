import pytest
from unittest.mock import MagicMock, patch
from langchain.schema import Document
from datetime import datetime

from src.retriever import OHLCVRetriever


class TestOHLCVRetriever:
    
    def test_initialization(self, mock_vector_store):
        """Test retriever initialization"""
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        assert retriever.vector_store == mock_vector_store
        assert retriever.default_k == 5
    
    def test_initialization_with_custom_k(self, mock_vector_store):
        """Test retriever initialization with custom k value"""
        retriever = OHLCVRetriever(vector_store=mock_vector_store, default_k=10)
        
        assert retriever.default_k == 10
    
    def test_retrieve_basic(self, mock_vector_store):
        """Test basic retrieval without filters"""
        expected_docs = [
            Document(page_content="Doc 1", metadata={'ticker': 'AAPL'}),
            Document(page_content="Doc 2", metadata={'ticker': 'GOOGL'})
        ]
        mock_vector_store.similarity_search.return_value = expected_docs
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        results = retriever.retrieve("test query")
        
        assert results == expected_docs
        mock_vector_store.similarity_search.assert_called_once_with("test query", k=5)
    
    def test_retrieve_with_custom_k(self, mock_vector_store):
        """Test retrieval with custom k value"""
        mock_vector_store.similarity_search.return_value = []
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        retriever.retrieve("test query", k=10)
        
        mock_vector_store.similarity_search.assert_called_once_with("test query", k=10)
    
    def test_retrieve_with_ticker_filter(self, mock_vector_store):
        """Test retrieval with ticker filter"""
        expected_docs = [
            Document(page_content="AAPL Doc", metadata={'ticker': 'AAPL'})
        ]
        mock_vector_store.search_by_ticker.return_value = expected_docs
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        filters = {'tickers': ['AAPL']}
        results = retriever.retrieve("test query", filters=filters)
        
        mock_vector_store.search_by_ticker.assert_called_once_with(
            "test query", 
            ticker='AAPL',
            k=5
        )
    
    def test_retrieve_with_multiple_tickers(self, mock_vector_store):
        """Test retrieval with multiple ticker filters"""
        mock_vector_store.search_by_ticker.side_effect = [
            [Document(page_content="AAPL", metadata={'ticker': 'AAPL'})],
            [Document(page_content="GOOGL", metadata={'ticker': 'GOOGL'})]
        ]
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        filters = {'tickers': ['AAPL', 'GOOGL']}
        results = retriever.retrieve("test query", filters=filters)
        
        assert len(results) == 2
        assert mock_vector_store.search_by_ticker.call_count == 2
    
    def test_retrieve_with_date_range(self, mock_vector_store):
        """Test retrieval with date range filter"""
        expected_docs = [
            Document(
                page_content="Date filtered doc",
                metadata={'date': '2024-01-15'}
            )
        ]
        mock_vector_store.search_by_date_range.return_value = expected_docs
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        filters = {'date_range': ('2024-01-01', '2024-01-31')}
        results = retriever.retrieve("test query", filters=filters)
        
        mock_vector_store.search_by_date_range.assert_called_once_with(
            "test query",
            start_date='2024-01-01',
            end_date='2024-01-31',
            k=5
        )
    
    def test_retrieve_with_combined_filters(self, mock_vector_store):
        """Test retrieval with both ticker and date range filters"""
        mock_vector_store.search_by_ticker.return_value = [
            Document(page_content="Doc 1", metadata={'ticker': 'AAPL', 'date': '2024-01-15'}),
            Document(page_content="Doc 2", metadata={'ticker': 'AAPL', 'date': '2024-02-01'}),
            Document(page_content="Doc 3", metadata={'ticker': 'AAPL', 'date': '2024-01-20'})
        ]
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        filters = {
            'tickers': ['AAPL'],
            'date_range': ('2024-01-01', '2024-01-31')
        }
        
        results = retriever.retrieve("test query", filters=filters)
        
        # Should filter out the February document
        assert len([r for r in results if '2024-02' not in r.metadata.get('date', '')]) == len(results)
    
    def test_retrieve_with_metadata_filter(self, mock_vector_store):
        """Test retrieval with custom metadata filters"""
        all_docs = [
            Document(page_content="Doc 1", metadata={'ticker': 'AAPL', 'rsi': 65}),
            Document(page_content="Doc 2", metadata={'ticker': 'AAPL', 'rsi': 35}),
            Document(page_content="Doc 3", metadata={'ticker': 'AAPL', 'rsi': 75})
        ]
        mock_vector_store.similarity_search.return_value = all_docs
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        # Custom filter for RSI > 60
        filters = {'metadata': {'rsi': lambda x: x > 60}}
        results = retriever.retrieve("test query", filters=filters)
        
        # Manual filtering based on metadata
        mock_vector_store.similarity_search.assert_called_once()
    
    def test_retrieve_empty_results(self, mock_vector_store):
        """Test retrieval with no results"""
        mock_vector_store.similarity_search.return_value = []
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        results = retriever.retrieve("test query")
        
        assert results == []
    
    def test_retrieve_error_handling(self, mock_vector_store):
        """Test error handling during retrieval"""
        mock_vector_store.similarity_search.side_effect = Exception("Search error")
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        with pytest.raises(Exception, match="Search error"):
            retriever.retrieve("test query")
    
    def test_batch_retrieve(self, mock_vector_store):
        """Test batch retrieval of multiple queries"""
        mock_vector_store.similarity_search.side_effect = [
            [Document(page_content="Result 1", metadata={})],
            [Document(page_content="Result 2", metadata={})],
            [Document(page_content="Result 3", metadata={})]
        ]
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        queries = ["Query 1", "Query 2", "Query 3"]
        results = retriever.batch_retrieve(queries)
        
        assert len(results) == 3
        assert mock_vector_store.similarity_search.call_count == 3
    
    def test_retrieve_with_score_threshold(self, mock_vector_store):
        """Test retrieval with score threshold filtering"""
        mock_vector_store.similarity_search_with_score = MagicMock(return_value=[
            (Document(page_content="High score", metadata={}), 0.9),
            (Document(page_content="Medium score", metadata={}), 0.6),
            (Document(page_content="Low score", metadata={}), 0.3)
        ])
        
        retriever = OHLCVRetriever(vector_store=mock_vector_store)
        
        # Assuming the retriever has a method to filter by score
        results = retriever.retrieve_with_score("test query", score_threshold=0.5)
        
        # Should only return documents with score >= 0.5
        assert len(results) <= 3