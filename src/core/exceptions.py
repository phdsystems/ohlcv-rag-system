"""
Custom exceptions for the OHLCV RAG System
"""


class OHLCVRAGException(Exception):
    """Base exception for OHLCV RAG System"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DataIngestionError(OHLCVRAGException):
    """Exception for data ingestion errors"""
    
    def __init__(self, message: str, ticker: str = None, source: str = None):
        details = {}
        if ticker:
            details['ticker'] = ticker
        if source:
            details['source'] = source
        super().__init__(message, error_code="DATA_INGESTION_ERROR", details=details)


class VectorStoreError(OHLCVRAGException):
    """Exception for vector store operations"""
    
    def __init__(self, message: str, operation: str = None, store_type: str = None):
        details = {}
        if operation:
            details['operation'] = operation
        if store_type:
            details['store_type'] = store_type
        super().__init__(message, error_code="VECTOR_STORE_ERROR", details=details)


class RetrieverError(OHLCVRAGException):
    """Exception for retrieval operations"""
    
    def __init__(self, message: str, query: str = None, num_results: int = None):
        details = {}
        if query:
            details['query'] = query
        if num_results is not None:
            details['num_results'] = num_results
        super().__init__(message, error_code="RETRIEVER_ERROR", details=details)


class PipelineError(OHLCVRAGException):
    """Exception for RAG pipeline operations"""
    
    def __init__(self, message: str, stage: str = None, query_type: str = None):
        details = {}
        if stage:
            details['stage'] = stage
        if query_type:
            details['query_type'] = query_type
        super().__init__(message, error_code="PIPELINE_ERROR", details=details)


class ConfigurationError(OHLCVRAGException):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_key: str = None, expected_type: str = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if expected_type:
            details['expected_type'] = expected_type
        super().__init__(message, error_code="CONFIG_ERROR", details=details)


class DataValidationError(OHLCVRAGException):
    """Exception for data validation errors"""
    
    def __init__(self, message: str, field: str = None, validation_rule: str = None):
        details = {}
        if field:
            details['field'] = field
        if validation_rule:
            details['validation_rule'] = validation_rule
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class AdapterError(OHLCVRAGException):
    """Exception for adapter operations"""
    
    def __init__(self, message: str, adapter_type: str = None, operation: str = None):
        details = {}
        if adapter_type:
            details['adapter_type'] = adapter_type
        if operation:
            details['operation'] = operation
        super().__init__(message, error_code="ADAPTER_ERROR", details=details)


class LLMError(OHLCVRAGException):
    """Exception for LLM operations"""
    
    def __init__(self, message: str, model: str = None, prompt_length: int = None):
        details = {}
        if model:
            details['model'] = model
        if prompt_length:
            details['prompt_length'] = prompt_length
        super().__init__(message, error_code="LLM_ERROR", details=details)