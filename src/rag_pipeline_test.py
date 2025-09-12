"""
Tests for OHLCVRAGPipeline with multi-provider LLM support
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from src.rag_pipeline import OHLCVRAGPipeline
from src.vector_store import OHLCVVectorStore
from src.retriever import OHLCVRetriever


class TestRAGPipelineProviders:
    """Test RAG Pipeline with different LLM providers"""
    
    @pytest.fixture
    def setup_components(self):
        """Setup vector store and retriever for testing"""
        import json
        
        # Create minimal chunks file
        os.makedirs('./data', exist_ok=True)
        with open('./data/ohlcv_chunks.json', 'w') as f:
            json.dump([], f)
        
        vector_store = OHLCVVectorStore()
        retriever = OHLCVRetriever(vector_store)
        
        yield vector_store, retriever
        
        # Cleanup
        if os.path.exists('./data/ohlcv_chunks.json'):
            os.remove('./data/ohlcv_chunks.json')
    
    def test_mock_provider_initialization(self, setup_components):
        """Test pipeline initialization with mock provider"""
        vector_store, retriever = setup_components
        
        # Should work without any API keys
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="mock"
        )
        
        assert pipeline is not None
        assert pipeline.llm is not None
        assert pipeline.vector_store == vector_store
        assert pipeline.retriever == retriever
    
    def test_mock_provider_functionality(self, setup_components):
        """Test mock provider returns expected response"""
        vector_store, retriever = setup_components
        
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="mock"
        )
        
        # Mock LLM should return mock response
        response = pipeline.llm.invoke.return_value
        assert response == "Mock response for testing"
    
    def test_openai_provider_requires_api_key(self, setup_components):
        """Test OpenAI provider requires API key"""
        vector_store, retriever = setup_components
        
        # Remove any existing API key
        original_key = os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                OHLCVRAGPipeline(
                    vector_store=vector_store,
                    retriever=retriever,
                    llm_provider="openai"
                )
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
    
    def test_openai_provider_with_api_key(self, setup_components):
        """Test OpenAI provider with API key provided"""
        vector_store, retriever = setup_components
        
        # Mock the ChatOpenAI import and class
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            mock_llm = MagicMock()
            mock_openai.return_value = mock_llm
            
            pipeline = OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="openai",
                api_key="test-api-key"
            )
            
            assert pipeline.llm == mock_llm
            mock_openai.assert_called_once_with(
                api_key="test-api-key",
                model="gpt-3.5-turbo",
                temperature=0.1
            )
    
    def test_openai_provider_custom_model(self, setup_components):
        """Test OpenAI provider with custom model"""
        vector_store, retriever = setup_components
        
        # Mock the ChatOpenAI import and class
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            mock_llm = MagicMock()
            mock_openai.return_value = mock_llm
            
            pipeline = OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="openai",
                api_key="test-api-key",
                model="gpt-4"
            )
            
            mock_openai.assert_called_once_with(
                api_key="test-api-key",
                model="gpt-4",
                temperature=0.1
            )
    
    def test_unsupported_provider_error(self, setup_components):
        """Test error for unsupported provider"""
        vector_store, retriever = setup_components
        
        with pytest.raises(ValueError, match="Unsupported LLM provider: invalid"):
            OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="invalid"
            )
    
    def test_provider_case_insensitive(self, setup_components):
        """Test provider name is case insensitive"""
        vector_store, retriever = setup_components
        
        # Should work with uppercase
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="MOCK"
        )
        assert pipeline.llm is not None
        
        # Should work with mixed case
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="MoCk"
        )
        assert pipeline.llm is not None
    
    def test_ollama_provider_no_api_key_needed(self, setup_components):
        """Test Ollama provider doesn't require API key"""
        vector_store, retriever = setup_components
        
        # Mock the Ollama import and class
        with patch('langchain_community.llms.Ollama') as mock_ollama:
            mock_llm = MagicMock()
            mock_ollama.return_value = mock_llm
            
            # Should work without API key
            pipeline = OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="ollama"
            )
            
            assert pipeline.llm == mock_llm
            mock_ollama.assert_called_once_with(
                model="llama2",
                temperature=0.1
            )
    
    def test_ollama_provider_custom_model(self, setup_components):
        """Test Ollama provider with custom model"""
        vector_store, retriever = setup_components
        
        # Mock the Ollama import and class
        with patch('langchain_community.llms.Ollama') as mock_ollama:
            mock_llm = MagicMock()
            mock_ollama.return_value = mock_llm
            
            pipeline = OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="ollama",
                model="codellama"
            )
            
            mock_ollama.assert_called_once_with(
                model="codellama",
                temperature=0.1
            )
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'env-test-key'})
    def test_openai_provider_env_api_key(self, setup_components):
        """Test OpenAI provider uses environment variable API key"""
        vector_store, retriever = setup_components
        
        # Mock the ChatOpenAI import and class
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            mock_llm = MagicMock()
            mock_openai.return_value = mock_llm
            
            # Should use env var when no api_key provided
            pipeline = OHLCVRAGPipeline(
                vector_store=vector_store,
                retriever=retriever,
                llm_provider="openai"
            )
            
            mock_openai.assert_called_once_with(
                api_key="env-test-key",
                model="gpt-3.5-turbo",
                temperature=0.1
            )
    
    def test_pipeline_prompts_created(self, setup_components):
        """Test pipeline creates prompts correctly"""
        vector_store, retriever = setup_components
        
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="mock"
        )
        
        # Check prompts are created
        assert hasattr(pipeline, 'prompts')
        assert isinstance(pipeline.prompts, dict)
        assert 'general' in pipeline.prompts
        assert 'technical' in pipeline.prompts
        assert 'comparison' in pipeline.prompts
    
    def test_mock_provider_with_query(self, setup_components):
        """Test mock provider can be used in query"""
        vector_store, retriever = setup_components
        
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="mock"
        )
        
        # Mock the query method
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = {
                'query': 'What is the trend?',
                'answer': 'Mock response for testing',
                'retrieved_documents': []
            }
            
            result = pipeline.query("What is the trend?")
            
            assert result['query'] == 'What is the trend?'
            assert result['answer'] == 'Mock response for testing'
            assert result['retrieved_documents'] == []


class TestRAGPipelineFunctionality:
    """Test core RAG Pipeline functionality"""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create pipeline with mock provider"""
        import json
        
        # Create minimal chunks file
        os.makedirs('./data', exist_ok=True)
        with open('./data/ohlcv_chunks.json', 'w') as f:
            json.dump([], f)
        
        vector_store = OHLCVVectorStore()
        retriever = OHLCVRetriever(vector_store)
        
        pipeline = OHLCVRAGPipeline(
            vector_store=vector_store,
            retriever=retriever,
            llm_provider="mock"
        )
        
        yield pipeline
        
        # Cleanup
        if os.path.exists('./data/ohlcv_chunks.json'):
            os.remove('./data/ohlcv_chunks.json')
    
    def test_classify_query_technical(self, mock_pipeline):
        """Test query classification for technical queries"""
        technical_queries = [
            "What is the RSI?",
            "Show me the MACD",
            "Calculate moving average",
            "What's the Bollinger Band?",
            "RSI above 70"
        ]
        
        for query in technical_queries:
            query_type = mock_pipeline._classify_query(query)
            assert query_type == 'technical'
    
    def test_classify_query_comparison(self, mock_pipeline):
        """Test query classification for comparison queries"""
        comparison_queries = [
            "Compare AAPL and MSFT",
            "AAPL vs GOOGL performance",
            "Difference between Tesla and Ford",
            "Which is better: AMD or NVDA?"
        ]
        
        for query in comparison_queries:
            query_type = mock_pipeline._classify_query(query)
            assert query_type == 'comparison'
    
    def test_classify_query_general(self, mock_pipeline):
        """Test query classification for general queries"""
        general_queries = [
            "What is the market trend?",
            "How is the stock performing?",
            "Tell me about recent activity",
            "Market analysis please"
        ]
        
        for query in general_queries:
            query_type = mock_pipeline._classify_query(query)
            assert query_type == 'general'
    
    def test_format_context_with_documents(self, mock_pipeline):
        """Test context formatting with documents"""
        from langchain.schema import Document
        
        docs = [
            Document(
                page_content="AAPL data: Open=150, Close=155",
                metadata={"ticker": "AAPL", "date": "2024-01-01"}
            ),
            Document(
                page_content="MSFT data: Open=300, Close=305",
                metadata={"ticker": "MSFT", "date": "2024-01-01"}
            )
        ]
        
        context = mock_pipeline._format_context(docs)
        
        assert "AAPL" in context
        assert "MSFT" in context
        assert "150" in context
        assert "305" in context
        assert "---" in context  # Document separator
    
    def test_format_context_empty_documents(self, mock_pipeline):
        """Test context formatting with empty documents"""
        context = mock_pipeline._format_context([])
        assert context == "No relevant data found."
    
    def test_format_context_with_none(self, mock_pipeline):
        """Test context formatting with None"""
        context = mock_pipeline._format_context(None)
        assert context == "No relevant data found."