import faiss
import numpy as np
import pickle
import os
import json
from typing import List, Dict, Any, Optional
import uuid
from tqdm import tqdm

from .vectordb_adapter import VectorDBAdapter, SearchResult


class FAISSStore(VectorDBAdapter):
    """FAISS (Facebook AI Similarity Search) vector store store"""
    
    def _validate_config(self) -> None:
        """Validate FAISS configuration"""
        # Set default persist directory
        if 'persist_directory' not in self.config:
            self.config['persist_directory'] = './data/faiss_db'
        
        # Index type (flat, ivf, hnsw)
        if 'index_type' not in self.config:
            self.config['index_type'] = 'flat'  # Most accurate but slower for large datasets
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.config['persist_directory'], exist_ok=True)
    
    def _initialize_store(self) -> None:
        """Initialize FAISS index"""
        self.index_file = os.path.join(self.config['persist_directory'], f"{self.collection_name}.index")
        self.metadata_file = os.path.join(self.config['persist_directory'], f"{self.collection_name}_metadata.json")
        self.id_map_file = os.path.join(self.config['persist_directory'], f"{self.collection_name}_ids.pkl")
        
        # Try to load existing index
        if os.path.exists(self.index_file):
            self._load_index()
            print(f"✓ Loaded existing FAISS index: {self.collection_name}")
        else:
            self._create_index()
            print(f"✓ Created new FAISS index: {self.collection_name}")
    
    def _create_index(self) -> None:
        """Create a new FAISS index"""
        if self.config['index_type'] == 'flat':
            # Exact search with L2 distance
            self.index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
            
        elif self.config['index_type'] == 'ivf':
            # Inverted file index for faster search
            quantizer = faiss.IndexFlatIP(self.embedding_dimension)
            n_list = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dimension, n_list)
            
        elif self.config['index_type'] == 'hnsw':
            # Hierarchical Navigable Small World graph
            self.index = faiss.IndexHNSWFlat(self.embedding_dimension, 32)
        
        # Initialize metadata storage
        self.documents = {}
        self.metadatas = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0
    
    def _load_index(self) -> None:
        """Load existing FAISS index from disk"""
        self.index = faiss.read_index(self.index_file)
        
        # Load metadata
        with open(self.metadata_file, 'r') as f:
            data = json.load(f)
            self.documents = data['documents']
            self.metadatas = data['metadatas']
            self.next_index = data.get('next_index', len(self.documents))
        
        # Load ID mappings
        with open(self.id_map_file, 'rb') as f:
            id_data = pickle.load(f)
            self.id_to_index = id_data['id_to_index']
            self.index_to_id = id_data['index_to_id']
    
    def _save_index(self) -> None:
        """Save FAISS index to disk"""
        # Save FAISS index
        faiss.write_index(self.index, self.index_file)
        
        # Save metadata
        with open(self.metadata_file, 'w') as f:
            json.dump({
                'documents': self.documents,
                'metadatas': self.metadatas,
                'next_index': self.next_index
            }, f)
        
        # Save ID mappings
        with open(self.id_map_file, 'wb') as f:
            pickle.dump({
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id
            }, f)
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to FAISS index"""
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Create embeddings
        embeddings = self.create_embeddings(documents)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Train index if needed (for IVF)
        if self.config['index_type'] == 'ivf' and not self.index.is_trained:
            self.index.train(embeddings)
        
        # Add to index
        indices = []
        for i, (doc_id, doc, meta) in enumerate(zip(ids, documents, metadatas)):
            idx = self.next_index
            self.index.add(embeddings[i:i+1])
            
            # Store metadata
            self.documents[str(idx)] = doc
            self.metadatas[str(idx)] = meta
            self.id_to_index[doc_id] = idx
            self.index_to_id[idx] = doc_id
            
            indices.append(idx)
            self.next_index += 1
        
        # Save to disk
        self._save_index()
        
        return ids
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents in FAISS"""
        # Create query embedding
        query_embedding = self.create_embeddings([query])
        faiss.normalize_L2(query_embedding)
        
        # Search in index
        scores, indices = self.index.search(query_embedding, n_results * 2)  # Get more results for filtering
        
        # Convert to SearchResult objects with filtering
        search_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty results
                continue
                
            str_idx = str(idx)
            if str_idx not in self.documents:
                continue
                
            metadata = self.metadatas.get(str_idx, {})
            
            # Apply filters
            if filter_dict and not self._matches_filter(metadata, filter_dict):
                continue
            
            doc_id = self.index_to_id.get(idx, str(idx))
            
            search_results.append(SearchResult(
                id=doc_id,
                document=self.documents[str_idx],
                metadata=metadata,
                score=float(score)  # Already normalized
            ))
            
            if len(search_results) >= n_results:
                break
        
        return search_results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter conditions"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
                
            if isinstance(value, dict):
                # Handle operators
                meta_value = metadata[key]
                for op, val in value.items():
                    if op == "$gt" and not (meta_value > val):
                        return False
                    elif op == "$gte" and not (meta_value >= val):
                        return False
                    elif op == "$lt" and not (meta_value < val):
                        return False
                    elif op == "$lte" and not (meta_value <= val):
                        return False
                    elif op == "$eq" and not (meta_value == val):
                        return False
                    elif op == "$ne" and not (meta_value != val):
                        return False
            else:
                # Simple equality
                if metadata[key] != value:
                    return False
        
        return True
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from FAISS (rebuild index without them)"""
        # FAISS doesn't support deletion, so we need to rebuild
        # Collect documents to keep
        keep_indices = []
        keep_embeddings = []
        new_documents = {}
        new_metadatas = {}
        new_id_to_index = {}
        new_index_to_id = {}
        
        new_idx = 0
        for old_idx in range(self.next_index):
            doc_id = self.index_to_id.get(old_idx)
            if doc_id and doc_id not in ids:
                # Keep this document
                str_idx = str(old_idx)
                if str_idx in self.documents:
                    # Get the embedding
                    embedding = self.index.reconstruct(old_idx).reshape(1, -1)
                    keep_embeddings.append(embedding)
                    
                    # Update mappings
                    new_documents[str(new_idx)] = self.documents[str_idx]
                    new_metadatas[str(new_idx)] = self.metadatas[str_idx]
                    new_id_to_index[doc_id] = new_idx
                    new_index_to_id[new_idx] = doc_id
                    
                    new_idx += 1
        
        # Rebuild index
        self._create_index()
        if keep_embeddings:
            embeddings = np.vstack(keep_embeddings)
            if self.config['index_type'] == 'ivf':
                self.index.train(embeddings)
            self.index.add(embeddings)
        
        self.documents = new_documents
        self.metadatas = new_metadatas
        self.id_to_index = new_id_to_index
        self.index_to_id = new_index_to_id
        self.next_index = new_idx
        
        self._save_index()
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update documents in FAISS"""
        for i, doc_id in enumerate(ids):
            if doc_id in self.id_to_index:
                idx = self.id_to_index[doc_id]
                str_idx = str(idx)
                
                if documents and i < len(documents):
                    # Update document and embedding
                    self.documents[str_idx] = documents[i]
                    
                    # Update embedding in index
                    embedding = self.create_embeddings([documents[i]])
                    faiss.normalize_L2(embedding)
                    # FAISS doesn't support in-place updates, would need to rebuild
                    # For now, just update metadata
                    
                if metadatas and i < len(metadatas):
                    self.metadatas[str_idx] = metadatas[i]
        
        self._save_index()
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        return self.index.ntotal
    
    def clear_collection(self) -> None:
        """Clear all documents from index"""
        self._create_index()
        self._save_index()
        print(f"✓ Cleared FAISS index: {self.collection_name}")
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get FAISS adapter information"""
        return {
            'name': 'FAISS',
            'type': 'faiss',
            'index_type': self.config['index_type'],
            'persistent': True,
            'requires_server': False,
            'supports_filtering': True,  # Through post-filtering
            'supports_updates': False,  # Limited update support
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'collection_name': self.collection_name,
            'persist_directory': self.config['persist_directory'],
            'document_count': self.get_document_count(),
            'features': [
                'Very fast similarity search',
                'Multiple index types',
                'GPU acceleration support',
                'Minimal dependencies',
                'Memory efficient',
                'Batch operations',
                'Facebook/Meta maintained'
            ],
            'license': 'MIT',
            'github': 'https://github.com/facebookresearch/faiss'
        }
    
    def persist(self) -> None:
        """Persist the index to disk"""
        self._save_index()
    
    @property
    def supports_updates(self) -> bool:
        """FAISS has limited update support"""
        return False