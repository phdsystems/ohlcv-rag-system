"""
Core module containing base classes and interfaces for the OHLCV RAG System
"""

from .base import BaseComponent, Configurable, DataProcessor
from .interfaces import IDataIngestion, IVectorStore, IRetriever, IRAGPipeline
from .models import OHLCVDataModel, ChunkModel, QueryResult, AnalysisResult
from .exceptions import (
    OHLCVRAGException,
    DataIngestionError,
    VectorStoreError,
    RetrieverError,
    PipelineError
)

__all__ = [
    # Base classes
    'BaseComponent',
    'Configurable',
    'DataProcessor',
    
    # Interfaces
    'IDataIngestion',
    'IVectorStore',
    'IRetriever',
    'IRAGPipeline',
    
    # Models
    'OHLCVDataModel',
    'ChunkModel',
    'QueryResult',
    'AnalysisResult',
    
    # Exceptions
    'OHLCVRAGException',
    'DataIngestionError',
    'VectorStoreError',
    'RetrieverError',
    'PipelineError'
]