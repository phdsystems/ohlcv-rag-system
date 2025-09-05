"""
Interface definitions for the OHLCV RAG System
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime


class IDataIngestion(ABC):
    """Interface for data ingestion components"""
    
    @abstractmethod
    def fetch_data(self, tickers: List[str], start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV data for given tickers"""
        pass
    
    @abstractmethod
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to data"""
        pass
    
    @abstractmethod
    def create_chunks(self, data: Dict[str, pd.DataFrame], window_size: int) -> List[Dict[str, Any]]:
        """Create data chunks for vector storage"""
        pass
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate OHLCV data"""
        pass
    
    @abstractmethod
    def save_data(self, data: Any, output_path: str) -> None:
        """Save processed data"""
        pass


class IVectorStore(ABC):
    """Interface for vector store components"""
    
    @abstractmethod
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], 
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to vector store"""
        pass
    
    @abstractmethod
    def search(self, query: str, n_results: int = 5, 
              filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        pass
    
    @abstractmethod
    def update_documents(self, ids: List[str], documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update existing documents"""
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """Get total number of documents"""
        pass
    
    @abstractmethod
    def clear_collection(self) -> None:
        """Clear all documents"""
        pass


class IRetriever(ABC):
    """Interface for retrieval components"""
    
    @abstractmethod
    def retrieve(self, query: str, n_results: int = 5, 
                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        pass
    
    @abstractmethod
    def retrieve_by_similarity(self, reference: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar documents"""
        pass
    
    @abstractmethod
    def retrieve_by_metadata(self, metadata_filters: Dict[str, Any], 
                            n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve by metadata filters"""
        pass
    
    @abstractmethod
    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank retrieval results"""
        pass


class IRAGPipeline(ABC):
    """Interface for RAG pipeline"""
    
    @abstractmethod
    def query(self, query: str, query_type: str = "general", 
             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query through the RAG pipeline"""
        pass
    
    @abstractmethod
    def analyze(self, analysis_type: str, data: Any, 
               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform specific analysis"""
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str, context: str) -> str:
        """Generate response using LLM"""
        pass
    
    @abstractmethod
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks as context"""
        pass
    
    @abstractmethod
    def evaluate_response(self, response: str, query: str, context: str) -> Dict[str, Any]:
        """Evaluate generated response quality"""
        pass


class IDataAdapter(ABC):
    """Interface for data source adapters"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    def fetch(self, symbol: str, **kwargs) -> pd.DataFrame:
        """Fetch data for a symbol"""
        pass
    
    @abstractmethod
    def fetch_batch(self, symbols: List[str], **kwargs) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols"""
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists"""
        pass
    
    @abstractmethod
    def get_available_intervals(self) -> List[str]:
        """Get available data intervals"""
        pass


class IAnalyzer(ABC):
    """Interface for analysis components"""
    
    @abstractmethod
    def analyze_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend in data"""
        pass
    
    @abstractmethod
    def analyze_patterns(self, data: pd.DataFrame, pattern_type: str) -> Dict[str, Any]:
        """Analyze specific patterns"""
        pass
    
    @abstractmethod
    def analyze_indicators(self, data: pd.DataFrame, indicators: List[str]) -> Dict[str, Any]:
        """Analyze technical indicators"""
        pass
    
    @abstractmethod
    def compare(self, data1: pd.DataFrame, data2: pd.DataFrame, 
               metrics: List[str]) -> Dict[str, Any]:
        """Compare two datasets"""
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, strategy: str) -> List[Dict[str, Any]]:
        """Generate trading signals"""
        pass