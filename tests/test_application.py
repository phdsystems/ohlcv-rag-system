import pytest
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from datetime import datetime
import os

from src.application import OHLCVRAGApplication, ApplicationState


class TestOHLCVRAGApplication:
    
    def test_initialization(self):
        """Test application initialization"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            assert app.name == "OHLCVRAGApplication"
            assert app.data_ingestion is None
            assert app.vector_store is None
            assert app.retriever is None
            assert app.rag_pipeline is None
            assert isinstance(app.state, ApplicationState)
    
    def test_initialization_with_config(self):
        """Test application initialization with custom config"""
        config = {
            'ingestion': {'source': 'yahoo', 'period': '6mo'},
            'vector_store': {'type': 'faiss'},
            'llm': {'model': 'gpt-4'}
        }
        
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication(name="TestApp", config=config)
            
            assert app.name == "TestApp"
            assert app.config == config
    
    @patch('src.application.DataIngestionEngine')
    @patch('src.application.VectorStoreAdapter')
    @patch('src.application.EnhancedRetriever')
    @patch('src.application.RAGPipeline')
    def test_initialize_components(self, mock_rag, mock_retriever, mock_vector, mock_ingestion):
        """Test initializing application components"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            # Mock the component creation
            mock_ingestion_instance = MagicMock()
            mock_vector_instance = MagicMock()
            mock_retriever_instance = MagicMock()
            mock_rag_instance = MagicMock()
            
            mock_ingestion.return_value = mock_ingestion_instance
            mock_vector.return_value = mock_vector_instance
            mock_retriever.return_value = mock_retriever_instance
            mock_rag.return_value = mock_rag_instance
            
            app.initialize_components()
            
            assert app.data_ingestion == mock_ingestion_instance
            assert app.vector_store == mock_vector_instance
            assert app.retriever == mock_retriever_instance
            assert app.rag_pipeline == mock_rag_instance
    
    @patch('src.application.DataIngestionEngine')
    def test_ingest_data(self, mock_ingestion_class):
        """Test data ingestion"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_ingestion = MagicMock()
            mock_ingestion.ingest.return_value = {
                'status': 'success',
                'tickers': ['AAPL', 'GOOGL'],
                'documents': 100
            }
            app.data_ingestion = mock_ingestion
            
            tickers = ['AAPL', 'GOOGL']
            result = app.ingest_data(tickers)
            
            assert result['status'] == 'success'
            assert result['tickers'] == tickers
            mock_ingestion.ingest.assert_called_once_with(tickers)
    
    def test_ingest_data_without_initialization(self):
        """Test data ingestion without initialized components"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            with pytest.raises(OHLCVRAGException, match="Components not initialized"):
                app.ingest_data(['AAPL'])
    
    @patch('src.application.RAGPipeline')
    def test_query(self, mock_rag_class):
        """Test querying the RAG system"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_rag = MagicMock()
            mock_rag.query.return_value = {
                'query': 'test query',
                'answer': 'test answer',
                'retrieved_documents': []
            }
            app.rag_pipeline = mock_rag
            
            result = app.query("test query")
            
            assert result['query'] == 'test query'
            assert result['answer'] == 'test answer'
            mock_rag.query.assert_called_once_with("test query", filters=None)
    
    def test_query_without_pipeline(self):
        """Test querying without initialized pipeline"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            with pytest.raises(OHLCVRAGException, match="RAG pipeline not initialized"):
                app.query("test query")
    
    @patch('src.application.DataIngestionEngine')
    @patch('src.application.VectorStoreAdapter')
    def test_update_data(self, mock_vector_class, mock_ingestion_class):
        """Test updating data for specific tickers"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_ingestion = MagicMock()
            mock_vector = MagicMock()
            
            app.data_ingestion = mock_ingestion
            app.vector_store = mock_vector
            
            mock_ingestion.fetch_latest.return_value = {'AAPL': 'data'}
            mock_vector.update_documents.return_value = True
            
            result = app.update_data(['AAPL'])
            
            assert result['status'] == 'success'
            mock_ingestion.fetch_latest.assert_called_once()
            mock_vector.update_documents.assert_called_once()
    
    def test_get_status(self):
        """Test getting application status"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            # Set up some mock components
            app.data_ingestion = MagicMock()
            app.vector_store = MagicMock()
            app.vector_store.get_stats.return_value = {'documents': 1000}
            
            status = app.get_status()
            
            assert 'components' in status
            assert 'state' in status
            assert status['components']['data_ingestion'] is True
            assert status['components']['vector_store'] is True
    
    def test_clear_data(self):
        """Test clearing all data"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_vector = MagicMock()
            app.vector_store = mock_vector
            
            app.clear_data()
            
            mock_vector.clear.assert_called_once()
            assert app.state.tickers == []
    
    def test_shutdown(self):
        """Test application shutdown"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            # Set up mock components with cleanup methods
            mock_ingestion = MagicMock()
            mock_vector = MagicMock()
            mock_rag = MagicMock()
            
            app.data_ingestion = mock_ingestion
            app.vector_store = mock_vector
            app.rag_pipeline = mock_rag
            
            app.shutdown()
            
            # Verify cleanup methods were called
            mock_ingestion.cleanup.assert_called_once()
            mock_vector.cleanup.assert_called_once()
            mock_rag.cleanup.assert_called_once()
    
    @patch('src.application.DataIngestionEngine')
    def test_batch_ingest(self, mock_ingestion_class):
        """Test batch data ingestion"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_ingestion = MagicMock()
            app.data_ingestion = mock_ingestion
            
            ticker_batches = [
                ['AAPL', 'GOOGL'],
                ['MSFT', 'AMZN'],
                ['TSLA', 'META']
            ]
            
            mock_ingestion.ingest.side_effect = [
                {'status': 'success', 'documents': 50},
                {'status': 'success', 'documents': 60},
                {'status': 'success', 'documents': 45}
            ]
            
            results = app.batch_ingest(ticker_batches)
            
            assert len(results) == 3
            assert all(r['status'] == 'success' for r in results)
            assert mock_ingestion.ingest.call_count == 3
    
    def test_export_data(self):
        """Test exporting data"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_vector = MagicMock()
            mock_vector.export.return_value = {'data': 'exported'}
            app.vector_store = mock_vector
            
            result = app.export_data(format='json')
            
            assert result == {'data': 'exported'}
            mock_vector.export.assert_called_once_with(format='json')
    
    def test_import_data(self):
        """Test importing data"""
        with patch('src.application.load_dotenv'):
            app = OHLCVRAGApplication()
            
            mock_vector = MagicMock()
            app.vector_store = mock_vector
            
            data = {'data': 'to_import'}
            app.import_data(data)
            
            mock_vector.import_data.assert_called_once_with(data)


class TestApplicationState:
    
    def test_state_initialization(self):
        """Test ApplicationState initialization"""
        state = ApplicationState()
        
        assert state.tickers == []
        assert state.last_update is None
        assert state.total_documents == 0
        assert state.is_ready is False
    
    def test_state_update(self):
        """Test updating application state"""
        state = ApplicationState()
        
        state.tickers = ['AAPL', 'GOOGL']
        state.last_update = datetime.now()
        state.total_documents = 100
        state.is_ready = True
        
        assert len(state.tickers) == 2
        assert state.last_update is not None
        assert state.total_documents == 100
        assert state.is_ready is True
    
    def test_state_to_dict(self):
        """Test converting state to dictionary"""
        state = ApplicationState()
        state.tickers = ['AAPL']
        state.total_documents = 50
        
        state_dict = state.to_dict()
        
        assert 'tickers' in state_dict
        assert 'last_update' in state_dict
        assert 'total_documents' in state_dict
        assert 'is_ready' in state_dict
        assert state_dict['tickers'] == ['AAPL']
        assert state_dict['total_documents'] == 50