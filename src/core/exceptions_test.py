"""
Tests for custom exception classes
"""

import pytest
from .exceptions import (
    OHLCVRAGException,
    DataIngestionError,
    VectorStoreError,
    PipelineError,
    RetrieverError
)


class TestExceptions:
    """Test custom exception classes behavior"""
    
    def test_base_exception(self):
        """Test OHLCVRAGException base class"""
        exc = OHLCVRAGException("Test error message")
        assert str(exc) == "Test error message"
        assert isinstance(exc, Exception)
    
    def test_data_ingestion_error(self):
        """Test DataIngestionError includes proper prefix"""
        exc = DataIngestionError("Failed to fetch data")
        assert "DATA_INGESTION_ERROR" in str(exc)
        assert "Failed to fetch data" in str(exc)
        assert isinstance(exc, OHLCVRAGException)
    
    def test_vector_store_error(self):
        """Test VectorStoreError includes proper prefix"""
        exc = VectorStoreError("Collection not found")
        assert "VECTOR_STORE_ERROR" in str(exc)
        assert "Collection not found" in str(exc)
        assert isinstance(exc, OHLCVRAGException)
    
    def test_pipeline_error(self):
        """Test PipelineError includes proper prefix"""
        exc = PipelineError("OpenAI API key not provided")
        assert "PIPELINE_ERROR" in str(exc)
        assert "OpenAI API key not provided" in str(exc)
        assert isinstance(exc, OHLCVRAGException)
    
    def test_retriever_error(self):
        """Test RetrieverError includes proper prefix"""
        exc = RetrieverError("No documents found")
        assert "RETRIEVER_ERROR" in str(exc)
        assert "No documents found" in str(exc)
        assert isinstance(exc, OHLCVRAGException)
    
    def test_exception_inheritance(self):
        """Test exception inheritance chain"""
        exc = DataIngestionError("Test")
        
        # Should be catchable as any of these
        assert isinstance(exc, DataIngestionError)
        assert isinstance(exc, OHLCVRAGException)
        assert isinstance(exc, Exception)
    
    def test_raising_exceptions(self):
        """Test exceptions can be raised and caught properly"""
        
        def raise_data_error():
            raise DataIngestionError("No data available")
        
        with pytest.raises(DataIngestionError) as exc_info:
            raise_data_error()
        
        assert "No data available" in str(exc_info.value)
        
        # Can also catch as base exception
        with pytest.raises(OHLCVRAGException):
            raise_data_error()