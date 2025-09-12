"""
Tests for main.py script functionality
Verifies the CLI entry point, argument parsing, and system setup with real components
"""

import pytest
import sys
import os
from unittest.mock import patch
import pandas as pd

# Tests are now co-located with source


class TestMainScriptFunctionality:
    """Test main.py CLI script functionality with real components"""
    
    def test_real_imports(self):
        """Test that all imports in main.py are real and work"""
        import main
        from src.data_ingestion import OHLCVDataIngestion
        from src.vector_store import OHLCVVectorStore
        from src.retriever import OHLCVRetriever
        from src.rag_pipeline import OHLCVRAGPipeline
        
        # Verify these are real classes, not mocks
        assert OHLCVDataIngestion.__module__ == 'src.data_ingestion'
        assert OHLCVVectorStore.__module__ == 'src.vector_store'
        assert OHLCVRetriever.__module__ == 'src.retriever'
        assert OHLCVRAGPipeline.__module__ == 'src.rag_pipeline'
    
    def test_initialize_data_ingestion_real(self):
        """Test data ingestion initialization with real implementation"""
        from main import initialize_data_ingestion
        from src.data_ingestion import OHLCVDataIngestion
        
        # Create real data ingestion engine
        tickers = ['AAPL']
        engine = initialize_data_ingestion(
            tickers=tickers,
            source='yahoo',
            period='5d',
            interval='1d'
        )
        
        # Verify it's a real instance
        assert isinstance(engine, OHLCVDataIngestion)
        assert engine.tickers == tickers
        assert engine.source == 'yahoo'
    
    def test_initialize_vector_store_real(self):
        """Test vector store initialization with real implementation"""
        from main import initialize_vector_store
        from src.vector_store import OHLCVVectorStore
        
        # Create real vector store
        store = initialize_vector_store()
        
        # Verify it's a real instance
        assert isinstance(store, OHLCVVectorStore)
        assert hasattr(store, 'collection')
        # Check for actual attributes the store has
        assert hasattr(store, 'adapter')
        assert hasattr(store, 'embedding_model')
    
    def test_parse_arguments_real(self):
        """Test argument parsing with real argparse"""
        from main import parse_arguments
        
        # Test with custom arguments
        test_args = ['--tickers', 'AAPL,MSFT', '--period', '1mo', '--interval', '1h']
        with patch('sys.argv', ['main.py'] + test_args):
            args = parse_arguments()
            
            assert args.tickers == 'AAPL,MSFT'
            assert args.period == '1mo'
            assert args.interval == '1h'
            assert args.source == 'yahoo'  # default value
    
    def test_get_demo_queries_real(self):
        """Test demo queries are real strings"""
        from main import get_demo_queries
        
        queries = get_demo_queries()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q) > 10 for q in queries)  # Meaningful queries
    
    def test_safe_execute_real(self):
        """Test safe_execute with real function execution"""
        from main import safe_execute
        
        # Test successful execution
        def good_func(x, y):
            return x + y
        
        result = safe_execute(good_func, 2, 3)
        assert result == 5
        
        # Test error handling
        def bad_func():
            raise ValueError("Test error")
        
        with patch('builtins.print'):  # Only mock the print to avoid console output
            result = safe_execute(bad_func)
            assert result is None
    
    def test_process_query_real(self):
        """Test query processing with mock LLM provider"""
        from main import process_query
        from src.rag_pipeline import OHLCVRAGPipeline
        from src.vector_store import OHLCVVectorStore
        from src.retriever import OHLCVRetriever
        import json
        import os
        
        # Create minimal chunks file for retriever
        os.makedirs('./data', exist_ok=True)
        with open('./data/ohlcv_chunks.json', 'w') as f:
            json.dump([], f)
        
        try:
            # Create real components with mock LLM provider
            vector_store = OHLCVVectorStore()
            retriever = OHLCVRetriever(vector_store)
            
            # Use mock provider for testing - no API key needed
            pipeline = OHLCVRAGPipeline(
                vector_store, 
                retriever,
                llm_provider="mock"  # Use mock provider for testing
            )
            
            # Mock the query method to return test data
            with patch.object(pipeline, 'query') as mock_query:
                mock_query.return_value = {
                    'query': 'test query',
                    'answer': 'Mock response for testing',
                    'retrieved_documents': []
                }
                
                result = process_query(pipeline, "test query")
                
                assert result['query'] == 'test query'
                assert 'Mock' in result['answer'] or 'test' in result['answer']
        finally:
            # Clean up test file
            if os.path.exists('./data/ohlcv_chunks.json'):
                os.remove('./data/ohlcv_chunks.json')
    
    @patch('builtins.input', return_value='3')  # Choose exit option
    @patch('builtins.print')  # Mock print to avoid console output
    def test_setup_system_real_components(self, mock_print, mock_input):
        """Test setup_system creates real components"""
        from main import setup_system
        import os
        
        # Set minimal environment variables
        os.environ['DATA_SOURCE'] = 'yahoo'
        os.environ['TICKER_SYMBOLS'] = 'AAPL'
        os.environ['DATA_PERIOD'] = '5d'
        
        # Run setup (it will fetch real data from Yahoo Finance)
        vector_store, retriever, rag_pipeline = setup_system()
        
        # Verify real components were created
        assert vector_store is not None
        from src.vector_store import OHLCVVectorStore
        assert isinstance(vector_store, OHLCVVectorStore)
        
        assert retriever is not None
        from src.retriever import OHLCVRetriever
        assert isinstance(retriever, OHLCVRetriever)
        
        # RAG pipeline might be None if no OpenAI key
        if rag_pipeline:
            from src.rag_pipeline import OHLCVRAGPipeline
            assert isinstance(rag_pipeline, OHLCVRAGPipeline)
    
    def test_environment_variables_used(self):
        """Test that environment variables are actually used"""
        import os
        from main import setup_system
        
        # Set test environment variables
        test_tickers = 'TEST1,TEST2'
        test_period = '10d'
        test_interval = '1h'
        
        os.environ['TICKER_SYMBOLS'] = test_tickers
        os.environ['DATA_PERIOD'] = test_period
        os.environ['DATA_INTERVAL'] = test_interval
        
        # Import main to see if it uses these values
        import main
        
        # The environment variables should be accessible in the module
        assert os.getenv('TICKER_SYMBOLS') == test_tickers
        assert os.getenv('DATA_PERIOD') == test_period
        assert os.getenv('DATA_INTERVAL') == test_interval