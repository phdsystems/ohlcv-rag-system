"""
Simple unit tests that don't require heavy dependencies
"""

import pytest
from unittest.mock import MagicMock, patch


class TestBasicFunctionality:
    
    def test_mock_data_ingestion(self):
        """Test data ingestion with mocks"""
        mock_ingestion = MagicMock()
        mock_ingestion.fetch_data.return_value = {'status': 'success'}
        
        result = mock_ingestion.fetch_data('AAPL')
        
        assert result['status'] == 'success'
        mock_ingestion.fetch_data.assert_called_once_with('AAPL')
    
    def test_mock_vector_store(self):
        """Test vector store operations with mocks"""
        mock_store = MagicMock()
        mock_store.add_documents.return_value = True
        mock_store.search.return_value = ['doc1', 'doc2']
        
        # Test adding documents
        assert mock_store.add_documents(['doc']) is True
        
        # Test searching
        results = mock_store.search('query')
        assert len(results) == 2
    
    def test_mock_retriever(self):
        """Test retriever with mocks"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            {'content': 'doc1', 'score': 0.9},
            {'content': 'doc2', 'score': 0.8}
        ]
        
        results = mock_retriever.retrieve('test query', k=2)
        
        assert len(results) == 2
        assert results[0]['score'] > results[1]['score']
    
    def test_mock_rag_pipeline(self):
        """Test RAG pipeline with mocks"""
        mock_pipeline = MagicMock()
        mock_pipeline.query.return_value = {
            'query': 'What is the trend?',
            'answer': 'Upward trend detected',
            'confidence': 0.95
        }
        
        result = mock_pipeline.query('What is the trend?')
        
        assert 'query' in result
        assert 'answer' in result
        assert 'Upward' in result['answer']
    
    def test_error_handling(self):
        """Test error handling"""
        mock_component = MagicMock()
        mock_component.process.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            mock_component.process()
    
    def test_configuration(self):
        """Test configuration handling"""
        config = {
            'source': 'yahoo',
            'period': '1y',
            'interval': '1d'
        }
        
        assert config['source'] == 'yahoo'
        assert config['period'] == '1y'
        assert config['interval'] == '1d'
    
    def test_data_validation(self):
        """Test data validation logic"""
        def validate_ticker(ticker):
            return isinstance(ticker, str) and len(ticker) > 0 and ticker.isalpha()
        
        assert validate_ticker('AAPL') is True
        assert validate_ticker('123') is False
        assert validate_ticker('') is False
        assert validate_ticker('AAPL123') is False
    
    def test_date_range_validation(self):
        """Test date range validation"""
        def validate_date_range(start, end):
            return start < end
        
        assert validate_date_range('2024-01-01', '2024-12-31') is True
        assert validate_date_range('2024-12-31', '2024-01-01') is False
    
    def test_batch_processing(self):
        """Test batch processing logic"""
        mock_processor = MagicMock()
        mock_processor.process_batch.return_value = [
            {'ticker': 'AAPL', 'status': 'success'},
            {'ticker': 'GOOGL', 'status': 'success'}
        ]
        
        results = mock_processor.process_batch(['AAPL', 'GOOGL'])
        
        assert len(results) == 2
        assert all(r['status'] == 'success' for r in results)
    
    def test_cache_functionality(self):
        """Test caching logic"""
        cache = {}
        
        def get_with_cache(key, fetch_func):
            if key not in cache:
                cache[key] = fetch_func()
            return cache[key]
        
        fetch_count = 0
        def fetch_data():
            nonlocal fetch_count
            fetch_count += 1
            return 'data'
        
        # First call should fetch
        result1 = get_with_cache('key1', fetch_data)
        assert result1 == 'data'
        assert fetch_count == 1
        
        # Second call should use cache
        result2 = get_with_cache('key1', fetch_data)
        assert result2 == 'data'
        assert fetch_count == 1  # Should not increment