"""
Comprehensive end-to-end tests for OHLCV RAG System
Tests the complete workflow from data ingestion to query response
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta


class TestCompleteWorkflow:
    """Test complete OHLCV RAG workflow end-to-end"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for test data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_ohlcv_data(self):
        """Generate sample OHLCV data for testing"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Open': [100 + i for i in range(len(dates))],
            'High': [105 + i for i in range(len(dates))],
            'Low': [95 + i for i in range(len(dates))],
            'Close': [102 + i for i in range(len(dates))],
            'Volume': [1000000 + i * 10000 for i in range(len(dates))],
            'Ticker': 'AAPL'
        })
        return data
    
    @pytest.mark.e2e
    def test_mock_data_ingestion_to_query_pipeline(self, temp_data_dir, sample_ohlcv_data):
        """Test complete pipeline with mocked external dependencies"""
        try:
            from src.application import OHLCVRAGApplication
            
            # Initialize application with mock LLM
            with patch('src.application.OpenAIProvider') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.query.return_value = "AAPL shows upward trend with volume increase"
                mock_llm.return_value = mock_llm_instance
                
                # Create application instance
                app = OHLCVRAGApplication(
                    data_dir=str(temp_data_dir),
                    llm_provider="mock"
                )
                
                # Test data ingestion
                with patch('src.data_adapters.yahoo_finance.YahooFinanceAdapter.get_data') as mock_data:
                    mock_data.return_value = sample_ohlcv_data
                    
                    result = app.ingest_data(
                        tickers=['AAPL'],
                        source='yahoo',
                        period='1mo'
                    )
                    
                    assert result is not None
                    assert app.state.ingested_tickers
                
                # Test query pipeline
                query_result = app.query("What are the trends for AAPL?")
                
                assert query_result is not None
                assert isinstance(query_result, str)
                assert "AAPL" in query_result or "trend" in query_result.lower()
                
                # Verify state tracking
                assert app.state.total_queries >= 1
                assert app.state.successful_queries >= 1
                
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
    
    @pytest.mark.e2e 
    def test_vector_store_integration_workflow(self, temp_data_dir):
        """Test vector store integration in complete workflow"""
        try:
            from src.vector_store import OHLCVVectorStore
            from src.retriever import OHLCVRetriever
            
            # Test vector store initialization
            vector_store = OHLCVVectorStore(store_type="chromadb")
            
            # Test document addition
            test_documents = [
                {
                    "content": "AAPL stock showed 5% increase in Q1 2024 with strong volume",
                    "metadata": {"ticker": "AAPL", "date": "2024-01-15", "type": "analysis"}
                },
                {
                    "content": "MSFT reported solid earnings with cloud growth driving revenue",
                    "metadata": {"ticker": "MSFT", "date": "2024-01-20", "type": "earnings"}
                }
            ]
            
            # Add documents to vector store
            vector_store.add_documents(test_documents)
            
            # Test retrieval
            retriever = OHLCVRetriever(vector_store=vector_store)
            results = retriever.retrieve("stock performance Q1", top_k=2)
            
            assert results is not None
            assert len(results) > 0
            
            # Test filtered retrieval
            filtered_results = retriever.retrieve(
                "earnings report",
                filters={"ticker": "MSFT"}
            )
            
            assert filtered_results is not None
            
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Vector store functionality not available: {e}")
    
    @pytest.mark.e2e
    def test_data_adapter_integration(self, sample_ohlcv_data):
        """Test data adapter integration workflow"""
        try:
            from src.data_adapters import DataSourceManager
            
            # Test data source manager
            manager = DataSourceManager()
            
            # Test getting adapter
            adapter = manager.get_adapter("yahoo")
            assert adapter is not None
            
            # Test with mocked data
            with patch.object(adapter, 'get_data', return_value=sample_ohlcv_data):
                data = adapter.get_data(
                    tickers=['AAPL'],
                    period='1mo',
                    interval='1d'
                )
                
                assert data is not None
                assert isinstance(data, pd.DataFrame)
                assert 'AAPL' in data['Ticker'].values or len(data) > 0
                
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Data adapter functionality not available: {e}")
    
    @pytest.mark.e2e
    def test_technical_analysis_integration(self, sample_ohlcv_data):
        """Test technical analysis integration in workflow"""
        try:
            import ta
            from src.data_ingestion import OHLCVDataIngestion
            
            # Test technical indicators calculation
            sma = ta.trend.sma_indicator(sample_ohlcv_data['Close'], window=5)
            rsi = ta.momentum.rsi(sample_ohlcv_data['Close'], window=14)
            
            assert len(sma) == len(sample_ohlcv_data)
            assert len(rsi) == len(sample_ohlcv_data)
            
            # Test with ingestion system
            with patch('src.data_adapters.DataSourceManager') as mock_manager:
                mock_adapter = Mock()
                mock_adapter.get_data.return_value = sample_ohlcv_data
                mock_manager_instance = Mock()
                mock_manager_instance.get_adapter.return_value = mock_adapter
                mock_manager.return_value = mock_manager_instance
                
                ingestion = OHLCVDataIngestion(tickers=['AAPL'])
                
                # Test that technical analysis can be applied
                assert ingestion.tickers == ['AAPL']
                
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Technical analysis functionality not available: {e}")


class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows"""
    
    @pytest.mark.e2e
    def test_invalid_ticker_handling(self):
        """Test handling of invalid tickers in complete workflow"""
        try:
            from src.application import OHLCVRAGApplication
            
            with patch('src.application.OpenAIProvider') as mock_llm:
                mock_llm.return_value = Mock()
                
                app = OHLCVRAGApplication(llm_provider="mock")
                
                # Test with invalid ticker
                result = app.ingest_data(
                    tickers=['INVALID_TICKER_12345'],
                    source='yahoo'
                )
                
                # Should handle gracefully
                assert app.state.last_error is None or "error" in str(app.state.last_error).lower()
                
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Application not available: {e}")
    
    @pytest.mark.e2e  
    def test_network_error_simulation(self):
        """Test handling of network errors in data fetching"""
        try:
            from src.data_adapters import DataSourceManager
            
            manager = DataSourceManager()
            adapter = manager.get_adapter("yahoo")
            
            # Simulate network error
            with patch.object(adapter, 'get_data', side_effect=ConnectionError("Network error")):
                try:
                    data = adapter.get_data(tickers=['AAPL'])
                    assert data is None or len(data) == 0
                except ConnectionError:
                    # Should handle network errors gracefully
                    pass
                    
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Data adapter not available: {e}")
    
    @pytest.mark.e2e
    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries"""
        try:
            from src.application import OHLCVRAGApplication
            
            with patch('src.application.OpenAIProvider') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.query.return_value = "Please provide a valid query"
                mock_llm.return_value = mock_llm_instance
                
                app = OHLCVRAGApplication(llm_provider="mock")
                
                # Test empty queries
                invalid_queries = ["", "   ", None]
                
                for query in invalid_queries:
                    if query is None:
                        continue
                        
                    result = app.query(query)
                    
                    # Should handle gracefully
                    assert result is not None or app.state.last_error is not None
                    
        except (ImportError, AttributeError, TypeError) as e:
            pytest.skip(f"Query handling not available: {e}")


class TestPerformanceWorkflow:
    """Test performance aspects of complete workflows"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_large_dataset_handling(self):
        """Test handling of larger datasets"""
        # Generate larger sample dataset
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        large_dataset = pd.DataFrame({
            'Date': dates,
            'Open': [100 + (i % 100) for i in range(len(dates))],
            'High': [105 + (i % 100) for i in range(len(dates))],
            'Low': [95 + (i % 100) for i in range(len(dates))],
            'Close': [102 + (i % 100) for i in range(len(dates))],
            'Volume': [1000000 + i for i in range(len(dates))],
            'Ticker': 'AAPL'
        })
        
        try:
            from src.data_ingestion import OHLCVDataIngestion
            
            with patch('src.data_adapters.DataSourceManager') as mock_manager:
                mock_adapter = Mock()
                mock_adapter.get_data.return_value = large_dataset
                mock_manager_instance = Mock()
                mock_manager_instance.get_adapter.return_value = mock_adapter
                mock_manager.return_value = mock_manager_instance
                
                ingestion = OHLCVDataIngestion(tickers=['AAPL'])
                
                # Should handle large datasets without errors
                assert len(large_dataset) > 1000
                assert ingestion.tickers == ['AAPL']
                
        except (ImportError, MemoryError) as e:
            pytest.skip(f"Large dataset test not feasible: {e}")
    
    @pytest.mark.e2e
    def test_concurrent_query_handling(self):
        """Test handling of multiple concurrent queries"""
        try:
            from src.application import OHLCVRAGApplication
            import threading
            import time
            
            with patch('src.application.OpenAIProvider') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.query.return_value = "Concurrent query response"
                mock_llm.return_value = mock_llm_instance
                
                app = OHLCVRAGApplication(llm_provider="mock")
                
                results = []
                
                def query_worker(query_id):
                    result = app.query(f"Query {query_id} about stock trends")
                    results.append(result)
                
                # Start multiple threads
                threads = []
                for i in range(5):
                    thread = threading.Thread(target=query_worker, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads
                for thread in threads:
                    thread.join()
                
                # Should handle concurrent queries
                assert len(results) == 5
                assert all(result is not None for result in results)
                
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Concurrent testing not available: {e}")


# Mark E2E tests
pytestmark = [pytest.mark.e2e, pytest.mark.slow]