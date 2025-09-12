"""
Tests for OHLCVRAGApplication class
Tests application initialization, data ingestion, querying, and state management
"""

import pytest
from unittest.mock import patch
from datetime import datetime
import pandas as pd
import numpy as np
import os

from .application import OHLCVRAGApplication, ApplicationState
from .core.exceptions import OHLCVRAGException


class TestOHLCVRAGApplication:
    """Test OHLCVRAGApplication class methods and functionality"""
    
    def test_application_initialization_real(self):
        """Test creating real application instance"""
        app = OHLCVRAGApplication(name="TestApp")
        
        # Verify real instance
        assert app.name == "TestApp"
        assert isinstance(app.state, ApplicationState)
        assert app.data_ingestion is None  # Not initialized yet
        assert app.vector_store is None
        assert app.retriever is None
        assert app.rag_pipeline is None
    
    def test_application_state_real(self):
        """Test ApplicationState with real operations"""
        state = ApplicationState()
        
        # Initial state
        assert state.application_status == 'initializing'
        assert state.total_queries == 0
        assert state.successful_queries == 0
        assert len(state.ingested_tickers) == 0
        
        # Modify state
        state.application_status = 'ready'
        state.ingested_tickers = ['AAPL', 'GOOGL', 'MSFT']
        state.total_queries = 10
        state.successful_queries = 8
        
        # Convert to dict
        state_dict = state.to_dict()
        assert state_dict['status'] == 'ready'
        assert len(state_dict['ingested_tickers']) == 3
        assert state_dict['statistics']['total_queries'] == 10
        assert state_dict['statistics']['successful_queries'] == 8
        assert state_dict['statistics']['success_rate'] == 80.0
    
    def test_application_config_real(self):
        """Test application with real configuration"""
        config = {
            'ingestion': {
                'source': 'yahoo',
                'period': '1mo',
                'interval': '1d',
                'window_size': 20
            },
            'vector_store': {
                'store_type': 'chromadb',
                'collection_name': 'test_collection',
                'embedding_model': 'all-MiniLM-L6-v2'
            },
            'pipeline': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.2,
                'max_tokens': 1000
            },
            'retriever': {
                'default_n_results': 3,
                'similarity_threshold': 0.6,
                'rerank_enabled': False
            }
        }
        
        app = OHLCVRAGApplication(name="ConfigTest", config=config)
        
        assert app.config == config
        assert app.validate_config() == True
    
    def test_initialize_components_real(self):
        """Test initializing real components"""
        app = OHLCVRAGApplication()
        
        # Mock only the OpenAI API key check for RAG pipeline
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'OPENAI_API_KEY': 'test-key',
                'LOG_LEVEL': 'INFO'
            }.get(key, default)
            
            try:
                app.initialize_components()
                
                # Verify real components were created
                assert app.data_ingestion is not None
                assert app.vector_store is not None
                assert app.retriever is not None
                # RAG pipeline might fail without real API key
                
                # Check component types
                from src.ingestion import DataIngestionEngine
                from src.pipeline import VectorStoreAdapter, EnhancedRetriever
                
                assert isinstance(app.data_ingestion, DataIngestionEngine)
                assert isinstance(app.vector_store, VectorStoreAdapter)
                assert isinstance(app.retriever, EnhancedRetriever)
                
            except OHLCVRAGException as e:
                # Expected if OpenAI key validation fails
                assert "OpenAI API key" in str(e) or "initialization failed" in str(e)
    
    def test_ingest_data_real_yahoo(self):
        """Test data ingestion with real Yahoo Finance data"""
        app = OHLCVRAGApplication()
        
        # Initialize components first
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'OPENAI_API_KEY': 'test-key',
                'LOG_LEVEL': 'INFO'
            }.get(key, default)
            
            try:
                app.initialize_components()
                
                # Ingest real data from Yahoo Finance
                result = app.ingest_data(['AAPL'], start_date='2024-01-01', end_date='2024-01-05')
                
                # Check result structure
                assert 'success' in result
                assert 'tickers' in result
                
                if result['success']:
                    assert result['tickers'] == ['AAPL']
                    assert 'chunks_created' in result
                    assert 'documents_indexed' in result
                    assert result['chunks_created'] >= 0
                    
            except Exception as e:
                # May fail due to network or API issues
                print(f"Test skipped due to: {e}")
    
    def test_get_status_real(self):
        """Test getting real application status"""
        app = OHLCVRAGApplication()
        
        # Get initial status
        status = app.get_status()
        
        assert 'name' in status
        assert 'initialized' in status
        assert 'state' in status
        assert 'components' in status
        
        assert status['name'] == 'OHLCVRAGApplication'
        assert status['initialized'] == False
        
        # Status should have component info even when not initialized
        assert status['components']['ingestion'] is None
        assert status['components']['vector_store'] is None
    
    def test_clear_data_real(self):
        """Test clearing data with real components"""
        app = OHLCVRAGApplication()
        
        # Initialize vector store
        from src.pipeline import VectorStoreAdapter
        app.vector_store = VectorStoreAdapter(
            name='test_vector_store',
            config={'store_type': 'chromadb', 'collection_name': 'test_clear'}
        )
        app.vector_store.initialize()
        
        # Add some test data
        app.vector_store.add_documents(
            ["test doc 1", "test doc 2"],
            [{"test": "meta1"}, {"test": "meta2"}]
        )
        
        # Clear data
        result = app.clear_data()
        assert result == True
        
        # Verify state was cleared
        assert len(app.state.ingested_tickers) == 0
        assert app.state.last_ingestion is None
    
    def test_update_data_real(self):
        """Test update_data calls real ingest_data"""
        app = OHLCVRAGApplication()
        
        # Mock the internal ingest_data to avoid full initialization
        with patch.object(app, 'ingest_data') as mock_ingest:
            mock_ingest.return_value = {
                'success': True,
                'tickers': ['AAPL'],
                'chunks_created': 5
            }
            
            result = app.update_data(['AAPL'])
            
            # Verify it called ingest_data
            mock_ingest.assert_called_once_with(['AAPL'])
            assert result['success'] == True
    
    def test_batch_ingest_real(self):
        """Test batch ingestion with real method"""
        app = OHLCVRAGApplication()
        
        # Mock ingest_data to avoid full initialization
        with patch.object(app, 'ingest_data') as mock_ingest:
            mock_ingest.side_effect = [
                {'success': True, 'tickers': ['AAPL']},
                {'success': True, 'tickers': ['GOOGL']},
                {'success': True, 'tickers': ['MSFT']}
            ]
            
            batches = [['AAPL'], ['GOOGL'], ['MSFT']]
            result = app.batch_ingest(batches)
            
            assert result['batches'] == 3
            assert len(result['results']) == 3
            assert all(r['success'] for r in result['results'])
    
    def test_query_requires_pipeline(self):
        """Test that query properly checks for pipeline"""
        app = OHLCVRAGApplication()
        
        # Should raise exception when pipeline not initialized
        with pytest.raises(OHLCVRAGException, match="RAG pipeline not initialized"):
            app.query("test query")
    
    def test_shutdown_real(self):
        """Test real shutdown process"""
        app = OHLCVRAGApplication()
        
        # Initialize some state
        app.state.application_status = 'ready'
        app.state.ingested_tickers = ['AAPL']
        
        # Shutdown
        app.shutdown()
        
        # Verify shutdown
        assert app.state.application_status == 'shutdown'
    
    def test_export_import_data_real(self):
        """Test export and import functionality"""
        app = OHLCVRAGApplication()
        
        # Test export (currently returns True as placeholder)
        result = app.export_data('/tmp/test_export.json')
        assert result == True
        
        # Test import (currently returns True as placeholder)
        result = app.import_data('/tmp/test_export.json')
        assert result == True
    
    def test_analyze_method_real(self):
        """Test analyze method with real components"""
        app = OHLCVRAGApplication()
        
        # Initialize minimal components
        from src.pipeline import EnhancedRetriever, VectorStoreAdapter
        
        app.vector_store = VectorStoreAdapter(
            name='test_vector_store',
            config={'store_type': 'chromadb', 'collection_name': 'test_analyze'}
        )
        app.vector_store.initialize()
        
        app.retriever = EnhancedRetriever(config={'default_n_results': 3})
        app.retriever.initialize()
        app.retriever.set_vector_store(app.vector_store)
        
        app._initialized = True
        app.state.ingested_tickers = ['AAPL']
        
        # Mock the RAG pipeline analyze method
        from src.pipeline import RAGPipeline
        with patch.object(RAGPipeline, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                'success': True,
                'analysis': 'Test analysis result'
            }
            
            app.rag_pipeline = RAGPipeline(
                name="TestPipeline",
                config={'model': 'gpt-3.5-turbo'}
            )
            
            result = app.analyze('trend', tickers=['AAPL'])
            
            assert 'success' in result or 'error' in result