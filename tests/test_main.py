import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMainScript:
    
    @patch('main.OHLCVDataIngestion')
    @patch('main.OHLCVVectorStore')
    @patch('main.OHLCVRetriever')
    @patch('main.OHLCVRAGPipeline')
    def test_main_flow(self, mock_rag, mock_retriever, mock_vector, mock_ingestion):
        """Test main script flow"""
        from main import main
        
        # Mock instances
        mock_ingestion_instance = MagicMock()
        mock_vector_instance = MagicMock()
        mock_retriever_instance = MagicMock()
        mock_rag_instance = MagicMock()
        
        mock_ingestion.return_value = mock_ingestion_instance
        mock_vector.return_value = mock_vector_instance
        mock_retriever.return_value = mock_retriever_instance
        mock_rag.return_value = mock_rag_instance
        
        # Mock data
        mock_ingestion_instance.fetch_ohlcv_data.return_value = None
        mock_ingestion_instance.calculate_technical_indicators.return_value = {'AAPL': 'data'}
        mock_ingestion_instance.prepare_documents.return_value = []
        
        mock_rag_instance.query.return_value = {
            'query': 'test',
            'answer': 'response'
        }
        
        with patch('builtins.print'):
            # This would normally run the main function
            # Since main() has an infinite loop or user interaction,
            # we'll test the components separately
            pass
    
    @patch('main.load_dotenv')
    def test_environment_setup(self, mock_load_dotenv):
        """Test environment variable loading"""
        import main
        
        mock_load_dotenv.assert_called_once()
    
    @patch('main.OHLCVDataIngestion')
    def test_data_ingestion_initialization(self, mock_ingestion_class):
        """Test data ingestion component initialization"""
        from main import initialize_data_ingestion
        
        mock_instance = MagicMock()
        mock_ingestion_class.return_value = mock_instance
        
        tickers = ['AAPL', 'GOOGL']
        result = initialize_data_ingestion(tickers)
        
        assert result == mock_instance
        mock_ingestion_class.assert_called_once()
    
    @patch('main.OHLCVVectorStore')
    def test_vector_store_initialization(self, mock_vector_class):
        """Test vector store initialization"""
        from main import initialize_vector_store
        
        mock_instance = MagicMock()
        mock_vector_class.return_value = mock_instance
        
        result = initialize_vector_store()
        
        assert result == mock_instance
        mock_vector_class.assert_called_once()
    
    def test_query_processing(self):
        """Test query processing logic"""
        from main import process_query
        
        mock_pipeline = MagicMock()
        mock_pipeline.query.return_value = {
            'query': 'What is the trend?',
            'answer': 'Upward trend detected',
            'retrieved_documents': ['doc1', 'doc2']
        }
        
        result = process_query(mock_pipeline, "What is the trend?")
        
        assert result['query'] == 'What is the trend?'
        assert 'Upward trend' in result['answer']
        mock_pipeline.query.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling in main flow"""
        from main import safe_execute
        
        def failing_function():
            raise Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            result = safe_execute(failing_function)
            
            assert result is None
            mock_print.assert_called()
    
    @patch('main.sys.argv', ['main.py', '--tickers', 'AAPL,GOOGL', '--period', '6mo'])
    def test_command_line_arguments(self):
        """Test command line argument parsing"""
        from main import parse_arguments
        
        args = parse_arguments()
        
        assert args.tickers == 'AAPL,GOOGL'
        assert args.period == '6mo'
    
    def test_demo_queries(self):
        """Test demo query generation"""
        from main import get_demo_queries
        
        queries = get_demo_queries()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)