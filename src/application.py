"""
Main Application Class for OHLCV RAG System
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

from src.core.base import BaseComponent
from src.core.exceptions import OHLCVRAGException
from src.data_ingestion import OHLCVDataIngestion as DataIngestionEngine
from src.rag_pipeline import OHLCVRAGPipeline as RAGPipeline
from src.retriever import OHLCVRetriever as EnhancedRetriever
from src.vector_store import OHLCVVectorStore as VectorStoreAdapter

load_dotenv()


class OHLCVRAGApplication(BaseComponent):
    """
    Main application class orchestrating all components
    """
    
    def __init__(self, name: str = "OHLCVRAGApplication", config: Optional[Dict[str, Any]] = None):
        """
        Initialize OHLCV RAG Application
        
        Args:
            name: Application name
            config: Configuration dictionary
        """
        super().__init__(name, config or self._load_default_config())
        
        # Components
        self.data_ingestion: Optional[DataIngestionEngine] = None
        self.vector_store: Optional[VectorStoreAdapter] = None
        self.retriever: Optional[EnhancedRetriever] = None
        self.rag_pipeline: Optional[RAGPipeline] = None
        
        # Application state
        self.state = ApplicationState()
        
        # Setup logging
        self._setup_logging()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from environment"""
        return {
            # Data ingestion config
            'ingestion': {
                'source': os.getenv('DATA_SOURCE', 'yahoo'),
                'interval': os.getenv('DATA_INTERVAL', '1d'),
                'period': os.getenv('DATA_PERIOD', '1y'),
                'window_size': int(os.getenv('CHUNK_WINDOW_SIZE', 30))
            },
            
            # Vector store config
            'vector_store': {
                'store_type': os.getenv('VECTOR_STORE_TYPE', 'chromadb'),
                'collection_name': os.getenv('COLLECTION_NAME', 'ohlcv_data'),
                'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            },
            
            # RAG pipeline config
            'pipeline': {
                'model': os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', 0.1)),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', 2000))
            },
            
            # Retriever config
            'retriever': {
                'default_n_results': int(os.getenv('DEFAULT_N_RESULTS', 5)),
                'similarity_threshold': float(os.getenv('SIMILARITY_THRESHOLD', 0.7)),
                'rerank_enabled': os.getenv('RERANK_ENABLED', 'true').lower() == 'true'
            }
        }
    
    def _setup_logging(self) -> None:
        """Setup application logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def initialize_components(self) -> None:
        """Initialize all application components (alias for initialize)"""
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize all application components"""
        self.log_info("Initializing OHLCV RAG Application")
        
        try:
            # Initialize data ingestion - uses tickers from config or empty list
            ingestion_config = self.config['ingestion']
            self.data_ingestion = DataIngestionEngine(
                tickers=[],  # Will be populated during ingest_data calls
                source=ingestion_config.get('source', 'yahoo'),
                period=ingestion_config.get('period', '1y'),
                interval=ingestion_config.get('interval', '1d')
            )
            self.state.components_status['ingestion'] = 'initialized'
            
            # Initialize vector store
            vector_config = self.config['vector_store']
            self.vector_store = VectorStoreAdapter(
                persist_directory=vector_config.get('persist_directory', './data/chroma_db'),
                embedding_model=vector_config.get('embedding_model', 'all-MiniLM-L6-v2'),
                store_type=vector_config.get('store_type', 'chromadb')
            )
            self.state.components_status['vector_store'] = 'initialized'
            
            # Initialize retriever - requires vector store and chunks file
            self.retriever = EnhancedRetriever(
                vector_store=self.vector_store,
                chunks_file=self.config['retriever'].get('chunks_file', './data/ohlcv_chunks.json')
            )
            self.state.components_status['retriever'] = 'initialized'
            
            # Initialize RAG pipeline
            pipeline_config = self.config['pipeline']
            self.rag_pipeline = RAGPipeline(
                vector_store=self.vector_store,
                retriever=self.retriever,
                llm_provider=pipeline_config.get('provider', 'mock'),  # Default to mock for testing
                api_key=pipeline_config.get('api_key'),
                model=pipeline_config.get('model', 'gpt-3.5-turbo')
            )
            self.state.components_status['pipeline'] = 'initialized'
            
            self._initialized = True
            self.state.application_status = 'ready'
            self.log_info("Application initialized successfully")
            
        except Exception as e:
            self.state.application_status = 'error'
            self.state.last_error = str(e)
            raise OHLCVRAGException(f"Application initialization failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate application configuration"""
        required_sections = ['ingestion', 'vector_store', 'pipeline', 'retriever']
        
        for section in required_sections:
            if section not in self.config:
                self.log_error(f"Missing configuration section: {section}")
                return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            'name': self.name,
            'initialized': self._initialized,
            'state': self.state.to_dict(),
            'components': {
                'ingestion': self.data_ingestion.get_status() if self.data_ingestion else None,
                'vector_store': self.vector_store.get_status() if self.vector_store else None,
                'retriever': self.retriever.get_status() if self.retriever else None,
                'pipeline': self.rag_pipeline.get_status() if self.rag_pipeline else None
            }
        }
    
    def ingest_data(self, tickers: List[str], start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest OHLCV data for specified tickers
        
        Args:
            tickers: List of ticker symbols
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Ingestion result dictionary
        """
        if not self.data_ingestion:
            raise OHLCVRAGException("Components not initialized. Call initialize_components() first.")
        
        if not self._initialized:
            self.initialize()
        
        self.log_info(f"Ingesting data for {len(tickers)} tickers")
        self.state.current_operation = 'data_ingestion'
        
        try:
            # Update data ingestion tickers
            self.data_ingestion.tickers = tickers
            
            # Fetch OHLCV data
            data = self.data_ingestion.fetch_ohlcv_data(start_date, end_date)
            
            # Create contextual chunks
            chunks = self.data_ingestion.create_contextual_chunks(
                self.config['ingestion'].get('window_size', 30)
            )
            
            # Index chunks in vector store
            if chunks:
                self.vector_store.index_chunks(chunks)
                self.log_info(f"Indexed {len(chunks)} chunks in vector store")
            
            result = {
                'success': True,
                'tickers': tickers,
                'chunks_created': len(chunks),
                'documents_indexed': len(chunks)
            }
            
            self.state.last_ingestion = datetime.now()
            self.state.ingested_tickers.extend(tickers)
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            self.state.last_error = str(e)
            self.log_error(f"Data ingestion failed: {str(e)}")
        
        self.state.current_operation = None
        return result
    
    def query(self, query: str, query_type: str = "general",
             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline
        
        Args:
            query: User query
            query_type: Type of query
            context: Additional context
            
        Returns:
            Query result dictionary
        """
        if not self.rag_pipeline:
            raise OHLCVRAGException("RAG pipeline not initialized. Call initialize_components() first.")
        
        if not self._initialized:
            self.initialize()
        
        self.log_info(f"Processing query: {query[:50]}...")
        self.state.current_operation = 'query_processing'
        self.state.total_queries += 1
        
        try:
            result = self.rag_pipeline.query(query, query_type, context)
            self.state.successful_queries += 1
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            self.state.last_error = str(e)
            self.log_error(f"Query processing failed: {str(e)}")
        
        self.state.current_operation = None
        self.state.last_query = datetime.now()
        return result
    
    def analyze(self, analysis_type: str, tickers: Optional[List[str]] = None,
               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform specific analysis
        
        Args:
            analysis_type: Type of analysis
            tickers: Optional list of tickers to analyze
            parameters: Analysis parameters
            
        Returns:
            Analysis result dictionary
        """
        if not self._initialized:
            self.initialize()
        
        self.log_info(f"Performing {analysis_type} analysis")
        self.state.current_operation = 'analysis'
        
        try:
            # Prepare data for analysis
            data = {}
            if tickers:
                for ticker in tickers:
                    if ticker in self.state.ingested_tickers:
                        # Retrieve data for ticker
                        results = self.retriever.retrieve_by_metadata(
                            {'ticker': ticker}, 
                            n_results=10
                        )
                        data[ticker] = results
            
            # Perform analysis
            result = self.rag_pipeline.analyze(analysis_type, data, parameters)
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            self.state.last_error = str(e)
            self.log_error(f"Analysis failed: {str(e)}")
        
        self.state.current_operation = None
        return result
    
    def update_data(self, tickers: List[str]) -> Dict[str, Any]:
        """Update data for specified tickers"""
        self.log_info(f"Updating data for {tickers}")
        return self.ingest_data(tickers)
    
    def batch_ingest(self, ticker_batches: List[List[str]]) -> Dict[str, Any]:
        """Ingest data in batches"""
        results = []
        for batch in ticker_batches:
            result = self.ingest_data(batch)
            results.append(result)
        return {
            'batches': len(ticker_batches),
            'results': results
        }
    
    def export_data(self, path: str) -> bool:
        """Export data to file"""
        try:
            # Implementation would export vector store data
            self.log_info(f"Exporting data to {path}")
            return True
        except Exception as e:
            self.log_error(f"Export failed: {str(e)}")
            return False
    
    def import_data(self, path: str) -> bool:
        """Import data from file"""
        try:
            # Implementation would import data to vector store
            self.log_info(f"Importing data from {path}")
            return True
        except Exception as e:
            self.log_error(f"Import failed: {str(e)}")
            return False
    
    def clear_data(self) -> bool:
        """Clear all data from vector store"""
        self.log_info("Clearing all data")
        
        try:
            if self.vector_store:
                self.vector_store.clear_collection()
            self.state.ingested_tickers.clear()
            self.state.last_ingestion = None
            self.log_info("Data cleared successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to clear data: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully"""
        self.log_info("Shutting down application")
        
        # Save state if needed
        self.state.application_status = 'shutdown'
        
        # Cleanup resources
        # Components will be garbage collected
        
        self.log_info("Application shutdown complete")


class ApplicationState:
    """Track application state"""
    
    def __init__(self):
        self.application_status = 'initializing'
        self.components_status = {}
        self.current_operation = None
        self.last_error = None
        self.last_ingestion = None
        self.last_query = None
        self.ingested_tickers = []
        self.total_queries = 0
        self.successful_queries = 0
        self.start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            'status': self.application_status,
            'components': self.components_status,
            'current_operation': self.current_operation,
            'last_error': self.last_error,
            'last_ingestion': str(self.last_ingestion) if self.last_ingestion else None,
            'last_query': str(self.last_query) if self.last_query else None,
            'ingested_tickers': self.ingested_tickers,
            'statistics': {
                'total_queries': self.total_queries,
                'successful_queries': self.successful_queries,
                'success_rate': (self.successful_queries / self.total_queries * 100) 
                               if self.total_queries > 0 else 0,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
        }