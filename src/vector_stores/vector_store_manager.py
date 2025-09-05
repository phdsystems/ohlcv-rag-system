from typing import Dict, Any, Optional, Type, List
from .vectordb_adapter import VectorDBAdapter, SearchResult
from .chromadb_store import ChromaDBStore
from .weaviate_store import WeaviateStore
from .qdrant_store import QdrantStore
from .faiss_store import FAISSStore
from .milvus_store import MilvusStore


class VectorStoreManager:
    """
    Manager that acts as the main adapter for vector stores.
    This is the single entry point for all vector database operations.
    
    Architecture:
    OHLCV Data → VectorStoreManager → ChromaDBStore/WeaviateStore/etc → Actual DB
    """
    
    # Registry of available vector stores
    STORES: Dict[str, Type[VectorDBAdapter]] = {
        'chromadb': ChromaDBStore,
        'chroma': ChromaDBStore,
        'weaviate': WeaviateStore,
        'qdrant': QdrantStore,
        'faiss': FAISSStore,
        'milvus': MilvusStore
    }
    
    def __init__(self,
                 store_type: str = "chromadb",
                 collection_name: str = "ohlcv_data",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the VectorStoreManager with a specific store
        
        Args:
            store_type: Type of vector store (chromadb, weaviate, qdrant, faiss, milvus)
            collection_name: Name of the collection/index
            embedding_model: Name of the sentence transformer model
            config: Store-specific configuration
        """
        self.store_type = store_type
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.config = config or {}
        
        # Create the actual store implementation
        self.store = self._create_store(store_type)
    
    def _create_store(self, store_type: str) -> VectorDBAdapter:
        """Create the specific vector store implementation"""
        store_type_lower = store_type.lower()
        
        if store_type_lower not in self.STORES:
            available = ', '.join(self.get_available_stores())
            raise ValueError(f"Unknown vector store: {store_type}. Available: {available}")
        
        store_class = self.STORES[store_type_lower]
        return store_class(
            collection_name=self.collection_name,
            embedding_model=self.embedding_model,
            config=self.config
        )
    
    # Delegate all operations to the underlying store
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to the vector store"""
        return self.store.add_documents(documents, metadatas, ids)
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents"""
        return self.store.search(query, n_results, filter_dict)
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        return self.store.delete_documents(ids)
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update existing documents"""
        return self.store.update_documents(ids, documents, metadatas)
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        return self.store.get_document_count()
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        return self.store.clear_collection()
    
    def batch_add_documents(self,
                           documents: List[str],
                           metadatas: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[str]:
        """Add documents in batches"""
        return self.store.batch_add_documents(documents, metadatas, batch_size)
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get information about the current vector store"""
        info = self.store.get_store_info()
        info['manager'] = {
            'current_store': self.store_type,
            'available_stores': self.get_available_stores()
        }
        return info
    
    def switch_store(self, store_type: str, config: Optional[Dict[str, Any]] = None):
        """
        Switch to a different vector store at runtime
        
        Args:
            store_type: New store type
            config: New configuration for the store
        """
        self.store_type = store_type
        self.config = config or self.config
        self.store = self._create_store(store_type)
        print(f"Switched to {store_type} vector store")
    
    @classmethod
    def get_available_stores(cls) -> List[str]:
        """Get list of available vector stores"""
        # Return unique store names
        stores = set()
        for key in cls.STORES.keys():
            if key in ['chromadb', 'weaviate', 'qdrant', 'faiss', 'milvus']:
                stores.add(key)
        return sorted(list(stores))
    
    @classmethod
    def create_adapter(cls,
                      store_type: str,
                      collection_name: str = "ohlcv_data",
                      embedding_model: str = "all-MiniLM-L6-v2",
                      config: Optional[Dict[str, Any]] = None) -> 'VectorStoreManager':
        """
        Factory method to create a VectorStoreManager (for backward compatibility)
        
        Args:
            store_type: Type of vector store
            collection_name: Name of the collection
            embedding_model: Embedding model to use
            config: Store-specific configuration
            
        Returns:
            VectorStoreManager instance configured with the specified store
        """
        return cls(store_type, collection_name, embedding_model, config)
    
    @classmethod
    def get_store_info_static(cls, store_type: str) -> Dict[str, Any]:
        """
        Get information about a specific vector store without instantiating it
        
        Args:
            store_type: Type of vector store
            
        Returns:
            Dictionary with store information
        """
        minimal_config = cls._get_minimal_config(store_type)
        manager = cls(store_type, config=minimal_config)
        return manager.get_store_info()
    
    @classmethod
    def _get_minimal_config(cls, store_type: str) -> Dict[str, Any]:
        """Get minimal configuration for a store type"""
        configs = {
            'chromadb': {'persist_directory': './data/chroma_db'},
            'weaviate': {'mode': 'embedded'},
            'qdrant': {'mode': 'memory'},
            'faiss': {'persist_directory': './data/faiss_db'},
            'milvus': {'mode': 'lite', 'uri': './data/milvus_lite.db'}
        }
        return configs.get(store_type.lower(), {})
    
    @classmethod
    def get_recommended_store(cls, requirements: Dict[str, Any]) -> str:
        """
        Get recommended vector store based on requirements
        
        Args:
            requirements: Dictionary with requirements like:
                - need_server: bool (whether a server is acceptable)
                - need_filtering: bool (whether metadata filtering is needed)
                - need_persistence: bool (whether data should persist)
                - scale: str (small/medium/large)
                - priority: str (speed/accuracy/features)
                
        Returns:
            Recommended store type
        """
        need_server = requirements.get('need_server', False)
        need_filtering = requirements.get('need_filtering', True)
        need_persistence = requirements.get('need_persistence', True)
        scale = requirements.get('scale', 'medium')
        priority = requirements.get('priority', 'balance')
        
        # Decision logic
        if not need_server:
            # No server required
            if priority == 'speed' and scale == 'large':
                return 'faiss'
            elif need_filtering and need_persistence:
                return 'chromadb'  # Best all-around no-server option
            else:
                return 'faiss'
        else:
            # Server is acceptable
            if scale == 'large':
                return 'milvus'  # Best for large scale
            elif priority == 'features':
                return 'weaviate'  # Most features
            elif priority == 'speed':
                return 'qdrant'  # Fast (Rust-based)
            else:
                return 'weaviate'  # Good balance
    
    @classmethod
    def compare_stores(cls) -> Dict[str, Any]:
        """Get comparison table of all vector stores"""
        comparison = {
            'chromadb': {
                'license': 'Apache 2.0',
                'language': 'Python',
                'requires_server': False,
                'embedded_mode': True,
                'cloud_option': False,
                'gpu_support': False,
                'best_for': 'Local development, small to medium datasets',
                'pros': ['Simple', 'No server', 'Auto-persist'],
                'cons': ['Python only', 'Limited scale']
            },
            'weaviate': {
                'license': 'BSD-3',
                'language': 'Go',
                'requires_server': 'Optional',
                'embedded_mode': True,
                'cloud_option': True,
                'gpu_support': False,
                'best_for': 'Production systems, GraphQL users',
                'pros': ['GraphQL API', 'Many features', 'Embedded mode'],
                'cons': ['Complex setup', 'Resource heavy']
            },
            'qdrant': {
                'license': 'Apache 2.0',
                'language': 'Rust',
                'requires_server': 'Optional',
                'embedded_mode': False,
                'cloud_option': True,
                'gpu_support': False,
                'best_for': 'High performance, production systems',
                'pros': ['Very fast', 'Good filtering', 'Memory mode'],
                'cons': ['No embedded mode', 'Newer project']
            },
            'faiss': {
                'license': 'MIT',
                'language': 'C++',
                'requires_server': False,
                'embedded_mode': True,
                'cloud_option': False,
                'gpu_support': True,
                'best_for': 'Large scale similarity search, research',
                'pros': ['Fastest search', 'GPU support', 'Facebook maintained'],
                'cons': ['Limited filtering', 'No built-in persistence']
            },
            'milvus': {
                'license': 'Apache 2.0',
                'language': 'Go/C++',
                'requires_server': 'Optional',
                'embedded_mode': True,
                'cloud_option': True,
                'gpu_support': True,
                'best_for': 'Large scale production, distributed systems',
                'pros': ['Scalable', 'GPU support', 'Lite mode'],
                'cons': ['Complex', 'Resource intensive']
            }
        }
        return comparison