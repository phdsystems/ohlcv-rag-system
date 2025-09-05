from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class SearchResult:
    """Standardized search result from vector store"""
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float  # Similarity score (0-1, higher is better)
    
    def __repr__(self) -> str:
        return f"SearchResult(id={self.id}, score={self.score:.3f})"


class VectorStoreAdapter(ABC):
    """Abstract base class for vector store adapters"""
    
    def __init__(self, 
                 collection_name: str = "ohlcv_data",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector store adapter
        
        Args:
            collection_name: Name of the collection/index
            embedding_model: Name of the sentence transformer model
            config: Adapter-specific configuration
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.config = config or {}
        
        # Initialize embedding model (shared across all adapters)
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Validate configuration
        self._validate_config()
        
        # Initialize the vector store
        self._initialize_store()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate adapter-specific configuration"""
        pass
    
    @abstractmethod
    def _initialize_store(self) -> None:
        """Initialize the vector store connection/client"""
        pass
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for text using sentence transformers
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings
        """
        return self.embedding_model.encode(texts, show_progress_bar=False)
    
    @abstractmethod
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        pass
    
    @abstractmethod
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by ID
        
        Args:
            ids: List of document IDs to delete
        """
        pass
    
    @abstractmethod
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Update existing documents
        
        Args:
            ids: List of document IDs to update
            documents: Optional new document texts
            metadatas: Optional new metadata dictionaries
        """
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """Get total number of documents in the store"""
        pass
    
    @abstractmethod
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        pass
    
    @abstractmethod
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the adapter"""
        pass
    
    def batch_add_documents(self,
                           documents: List[str],
                           metadatas: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[str]:
        """
        Add documents in batches (default implementation)
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            batch_size: Size of each batch
            
        Returns:
            List of all document IDs
        """
        all_ids = []
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            
            ids = self.add_documents(batch_docs, batch_meta)
            all_ids.extend(ids)
            
        return all_ids
    
    def similarity_search_with_score(self,
                                    query: str,
                                    n_results: int = 5,
                                    filter_dict: Optional[Dict[str, Any]] = None,
                                    score_threshold: float = 0.0) -> List[SearchResult]:
        """
        Search with minimum score threshold
        
        Args:
            query: Query text
            n_results: Maximum number of results
            filter_dict: Optional metadata filters
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of SearchResult objects above threshold
        """
        results = self.search(query, n_results, filter_dict)
        return [r for r in results if r.score >= score_threshold]
    
    def get_documents_by_ids(self, ids: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Retrieve documents by their IDs
        
        Args:
            ids: List of document IDs
            
        Returns:
            List of (document, metadata) tuples
        """
        # Default implementation using search
        # Adapters can override with more efficient implementations
        results = []
        for doc_id in ids:
            # This is a workaround - adapters should implement direct retrieval
            pass
        return results
    
    def persist(self) -> None:
        """
        Persist the vector store to disk (if applicable)
        Some stores like ChromaDB auto-persist, others may need explicit save
        """
        pass
    
    def create_collection_if_not_exists(self) -> None:
        """
        Create collection if it doesn't exist
        Default implementation - adapters can override
        """
        pass
    
    @property
    def is_persistent(self) -> bool:
        """Whether this store persists data between sessions"""
        return True
    
    @property
    def supports_filtering(self) -> bool:
        """Whether this store supports metadata filtering"""
        return True
    
    @property
    def supports_updates(self) -> bool:
        """Whether this store supports document updates"""
        return True
    
    @property
    def requires_server(self) -> bool:
        """Whether this store requires a separate server process"""
        return False