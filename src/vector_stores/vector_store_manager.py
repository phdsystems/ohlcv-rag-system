from typing import Dict, Any, Optional, Type
from .base import VectorStoreAdapter
from .chromadb_adapter import ChromaDBAdapter
from .weaviate_adapter import WeaviateAdapter
from .qdrant_adapter import QdrantAdapter
from .faiss_adapter import FAISSAdapter
from .milvus_adapter import MilvusAdapter


class VectorStoreManager:
    """Manager for creating and managing vector store adapters"""
    
    # Registry of available adapters
    ADAPTERS: Dict[str, Type[VectorStoreAdapter]] = {
        'chromadb': ChromaDBAdapter,
        'chroma': ChromaDBAdapter,
        'weaviate': WeaviateAdapter,
        'qdrant': QdrantAdapter,
        'faiss': FAISSAdapter,
        'milvus': MilvusAdapter
    }
    
    @classmethod
    def create_adapter(cls,
                      store_type: str,
                      collection_name: str = "ohlcv_data",
                      embedding_model: str = "all-MiniLM-L6-v2",
                      config: Optional[Dict[str, Any]] = None) -> VectorStoreAdapter:
        """
        Create a vector store adapter
        
        Args:
            store_type: Type of vector store (chromadb, weaviate, qdrant, faiss, milvus)
            collection_name: Name of the collection/index
            embedding_model: Name of the sentence transformer model
            config: Store-specific configuration
            
        Returns:
            Instance of the specified vector store adapter
            
        Raises:
            ValueError: If store_type is not recognized
        """
        store_type_lower = store_type.lower()
        
        if store_type_lower not in cls.ADAPTERS:
            available = ', '.join(cls.get_available_stores())
            raise ValueError(f"Unknown vector store: {store_type}. Available: {available}")
        
        adapter_class = cls.ADAPTERS[store_type_lower]
        return adapter_class(
            collection_name=collection_name,
            embedding_model=embedding_model,
            config=config
        )
    
    @classmethod
    def get_available_stores(cls) -> list[str]:
        """Get list of available vector stores"""
        # Return unique store names
        stores = set()
        for key in cls.ADAPTERS.keys():
            if key in ['chromadb', 'weaviate', 'qdrant', 'faiss', 'milvus']:
                stores.add(key)
        return sorted(list(stores))
    
    @classmethod
    def get_store_info(cls, store_type: str) -> Dict[str, Any]:
        """
        Get information about a specific vector store
        
        Args:
            store_type: Type of vector store
            
        Returns:
            Dictionary with store information
        """
        # Create adapter with minimal config to get info
        minimal_config = cls._get_minimal_config(store_type)
        adapter = cls.create_adapter(store_type, config=minimal_config)
        return adapter.get_adapter_info()
    
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
    def get_all_stores_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all available vector stores"""
        info = {}
        for store_type in cls.get_available_stores():
            try:
                info[store_type] = cls.get_store_info(store_type)
            except Exception as e:
                info[store_type] = {
                    'name': store_type,
                    'error': f"Could not get info: {str(e)}"
                }
        return info
    
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