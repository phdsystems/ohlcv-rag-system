"""
Vector Store Adapter for OOP Integration
"""

from typing import List, Dict, Any, Optional

from src.core.base import BaseComponent
from src.core.interfaces import IVectorStore
from src.core.exceptions import VectorStoreError
from src.vector_stores import VectorStoreManager


class VectorStoreAdapter(BaseComponent, IVectorStore):
    """
    Adapter to integrate vector stores with OOP architecture
    """
    
    def __init__(self, name: str = "VectorStoreAdapter", config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector store adapter
        
        Args:
            name: Adapter name
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # Configuration
        self.store_type = config.get('store_type', 'chromadb')
        self.collection_name = config.get('collection_name', 'ohlcv_data')
        self.embedding_model = config.get('embedding_model', 'all-MiniLM-L6-v2')
        
        # Vector store manager
        self.manager = None
        
    def initialize(self) -> None:
        """Initialize the vector store adapter"""
        self.log_info(f"Initializing vector store adapter with {self.store_type}")
        
        if not self.validate_config():
            raise VectorStoreError("Invalid configuration")
        
        try:
            # Create vector store manager
            self.manager = VectorStoreManager(
                store_type=self.store_type,
                collection_name=self.collection_name,
                embedding_model=self.embedding_model,
                config=self.config.get('store_config', {})
            )
            
            self._initialized = True
            self.log_info(f"Initialized {self.store_type} vector store")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize vector store: {str(e)}", 
                                 store_type=self.store_type)
    
    def validate_config(self) -> bool:
        """Validate adapter configuration"""
        # Check if store type is valid
        available_stores = VectorStoreManager.get_available_stores()
        if self.store_type not in available_stores:
            self.log_error(f"Invalid store type: {self.store_type}. Available: {available_stores}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        status = {
            'name': self.name,
            'initialized': self._initialized,
            'store_type': self.store_type,
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model
        }
        
        if self._initialized and self.manager:
            status['store_info'] = self.manager.get_store_info()
        
        return status
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to vector store"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.manager.add_documents(documents, metadatas, ids)
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {str(e)}", 
                                 operation="add_documents", store_type=self.store_type)
    
    def search(self, query: str, n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self._initialized:
            self.initialize()
        
        try:
            results = self.manager.search(query, n_results, filter_dict)
            
            # Convert SearchResult objects to dictionaries
            return [
                {
                    'id': r.id,
                    'document': r.document,
                    'metadata': r.metadata,
                    'score': r.score,
                    'ticker': r.metadata.get('ticker', 'Unknown'),
                    'start_date': r.metadata.get('start_date'),
                    'end_date': r.metadata.get('end_date'),
                    'summary': r.document  # Use document as summary
                }
                for r in results
            ]
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}", 
                                 operation="search", store_type=self.store_type)
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.manager.delete_documents(ids)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete documents: {str(e)}", 
                                 operation="delete_documents", store_type=self.store_type)
    
    def update_documents(self, ids: List[str], documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update existing documents"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.manager.update_documents(ids, documents, metadatas)
        except Exception as e:
            raise VectorStoreError(f"Failed to update documents: {str(e)}", 
                                 operation="update_documents", store_type=self.store_type)
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.manager.get_document_count()
        except Exception as e:
            raise VectorStoreError(f"Failed to get document count: {str(e)}", 
                                 operation="get_document_count", store_type=self.store_type)
    
    def clear_collection(self) -> None:
        """Clear all documents"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.manager.clear_collection()
        except Exception as e:
            raise VectorStoreError(f"Failed to clear collection: {str(e)}", 
                                 operation="clear_collection", store_type=self.store_type)
    
    def batch_add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[str]:
        """Add documents in batches"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.manager.batch_add_documents(documents, metadatas, batch_size)
        except Exception as e:
            raise VectorStoreError(f"Failed to batch add documents: {str(e)}", 
                                 operation="batch_add_documents", store_type=self.store_type)
    
    def switch_store(self, store_type: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Switch to a different vector store at runtime"""
        self.log_info(f"Switching from {self.store_type} to {store_type}")
        
        self.store_type = store_type
        if config:
            self.config['store_config'] = config
        
        # Reinitialize with new store
        self._initialized = False
        self.initialize()