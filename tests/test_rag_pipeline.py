import pytest
from unittest.mock import MagicMock, patch, Mock
from langchain.schema import Document
import os

from src.rag_pipeline import OHLCVRAGPipeline


class TestOHLCVRAGPipeline:
    
    def test_initialization_with_api_key(self, mock_vector_store, env_setup):
        """Test RAG pipeline initialization with API key"""
        mock_retriever = MagicMock()
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_llm:
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever,
                openai_api_key='test-key'
            )
            
            assert pipeline.vector_store == mock_vector_store
            assert pipeline.retriever == mock_retriever
            mock_llm.assert_called_once()
    
    def test_initialization_without_api_key(self, mock_vector_store):
        """Test RAG pipeline initialization without API key raises error"""
        mock_retriever = MagicMock()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                OHLCVRAGPipeline(
                    vector_store=mock_vector_store,
                    retriever=mock_retriever
                )
    
    def test_create_prompts(self, mock_vector_store, env_setup):
        """Test prompt creation"""
        mock_retriever = MagicMock()
        
        with patch('src.rag_pipeline.ChatOpenAI'):
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            prompts = pipeline.prompts
            assert 'general' in prompts
            assert 'pattern' in prompts
            assert 'comparison' in prompts
            assert 'prediction' in prompts
    
    def test_query_general(self, mock_vector_store, env_setup, sample_documents):
        """Test general query processing"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="AAPL data: Close=150.0, RSI=55",
                metadata={'ticker': 'AAPL', 'date': '2024-01-01'}
            )
        ]
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="Analysis result")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            result = pipeline.query("What is the trend for AAPL?")
            
            assert 'query' in result
            assert 'answer' in result
            assert 'retrieved_documents' in result
            assert result['query'] == "What is the trend for AAPL?"
            mock_retriever.retrieve.assert_called_once()
    
    def test_query_with_pattern_detection(self, mock_vector_store, env_setup):
        """Test query with pattern detection"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Pattern detected",
                metadata={'ticker': 'AAPL'}
            )
        ]
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="Pattern analysis")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            result = pipeline.query("Find patterns in AAPL", query_type='pattern')
            
            assert result['query_type'] == 'pattern'
            assert 'answer' in result
    
    def test_query_with_comparison(self, mock_vector_store, env_setup):
        """Test comparison query"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="AAPL vs GOOGL comparison",
                metadata={'ticker': 'AAPL'}
            )
        ]
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="Comparison result")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            result = pipeline.query("Compare AAPL and GOOGL", query_type='comparison')
            
            assert result['query_type'] == 'comparison'
    
    def test_query_with_filters(self, mock_vector_store, env_setup):
        """Test query with filters"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="Filtered result")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            filters = {
                'tickers': ['AAPL', 'GOOGL'],
                'date_range': ('2024-01-01', '2024-01-31')
            }
            
            result = pipeline.query("Analyze trends", filters=filters)
            
            mock_retriever.retrieve.assert_called_once_with(
                "Analyze trends",
                filters=filters,
                k=5
            )
    
    def test_query_empty_retrieval(self, mock_vector_store, env_setup):
        """Test query with no retrieved documents"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="No data available")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            result = pipeline.query("Show me data")
            
            assert len(result['retrieved_documents']) == 0
            assert 'answer' in result
    
    def test_batch_query(self, mock_vector_store, env_setup):
        """Test batch query processing"""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            Document(page_content="Sample data", metadata={})
        ]
        
        with patch('src.rag_pipeline.ChatOpenAI') as mock_chat:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(content="Batch result")
            mock_chat.return_value = mock_llm_instance
            
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            queries = [
                "Query 1",
                "Query 2",
                "Query 3"
            ]
            
            results = pipeline.batch_query(queries)
            
            assert len(results) == 3
            assert all('query' in r for r in results)
            assert all('answer' in r for r in results)
    
    def test_invalid_query_type(self, mock_vector_store, env_setup):
        """Test handling of invalid query type"""
        mock_retriever = MagicMock()
        
        with patch('src.rag_pipeline.ChatOpenAI'):
            pipeline = OHLCVRAGPipeline(
                vector_store=mock_vector_store,
                retriever=mock_retriever
            )
            
            # Should default to 'general' for invalid query type
            mock_retriever.retrieve.return_value = []
            result = pipeline.query("Test query", query_type='invalid')
            
            assert result['query_type'] == 'general'