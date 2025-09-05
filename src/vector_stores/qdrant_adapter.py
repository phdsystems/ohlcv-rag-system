from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, Range
)
import uuid
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from .base import VectorStoreAdapter, SearchResult


class QdrantAdapter(VectorStoreAdapter):
    """Qdrant vector store adapter"""
    
    def _validate_config(self) -> None:
        """Validate Qdrant configuration"""
        # Default configuration
        if 'mode' not in self.config:
            self.config['mode'] = 'memory'  # memory, local, or remote
        
        if self.config['mode'] == 'local':
            if 'path' not in self.config:
                self.config['path'] = './data/qdrant_db'
        elif self.config['mode'] == 'remote':
            if 'url' not in self.config:
                self.config['url'] = 'http://localhost:6333'
            # Optional API key for cloud deployment
            self.config['api_key'] = self.config.get('api_key', None)
    
    def _initialize_store(self) -> None:
        """Initialize Qdrant client and collection"""
        # Initialize client based on mode
        if self.config['mode'] == 'memory':
            # In-memory Qdrant (for testing/development)
            self.client = QdrantClient(":memory:")
            print("✓ Initialized in-memory Qdrant instance")
            
        elif self.config['mode'] == 'local':
            # Local persistent Qdrant
            self.client = QdrantClient(path=self.config['path'])
            print(f"✓ Initialized local Qdrant at {self.config['path']}")
            
        elif self.config['mode'] == 'remote':
            # Remote Qdrant server
            self.client = QdrantClient(
                url=self.config['url'],
                api_key=self.config.get('api_key')
            )
            print(f"✓ Connected to Qdrant server at {self.config['url']}")
        
        # Create collection if it doesn't exist
        self._create_collection()
    
    def _create_collection(self) -> None:
        """Create or verify Qdrant collection"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Created new Qdrant collection: {self.collection_name}")
        else:
            print(f"✓ Using existing Qdrant collection: {self.collection_name}")
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to Qdrant"""
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Create embeddings
        embeddings = self.create_embeddings(documents)
        
        # Create points for Qdrant
        points = []
        for i, (doc_id, doc, meta, embedding) in enumerate(zip(ids, documents, metadatas, embeddings)):
            # Prepare payload
            payload = {
                "content": doc,
                **meta  # Include all metadata
            }
            
            points.append(PointStruct(
                id=doc_id,
                vector=embedding.tolist(),
                payload=payload
            ))
        
        # Upload points to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return ids
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents in Qdrant"""
        # Create query embedding
        query_embedding = self.create_embeddings([query])[0]
        
        # Build filter if provided
        search_filter = None
        if filter_dict:
            search_filter = self._build_filter(filter_dict)
        
        # Perform search
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=n_results,
            query_filter=search_filter,
            with_payload=True
        )
        
        # Convert to SearchResult objects
        search_results = []
        for hit in search_result:
            metadata = {k: v for k, v in hit.payload.items() if k != 'content'}
            
            search_results.append(SearchResult(
                id=str(hit.id),
                document=hit.payload.get('content', ''),
                metadata=metadata,
                score=hit.score
            ))
        
        return search_results
    
    def _build_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from filter dictionary"""
        must_conditions = []
        
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle range operators
                for op, val in value.items():
                    if op == "$gt":
                        must_conditions.append(
                            FieldCondition(key=key, range=Range(gt=val))
                        )
                    elif op == "$gte":
                        must_conditions.append(
                            FieldCondition(key=key, range=Range(gte=val))
                        )
                    elif op == "$lt":
                        must_conditions.append(
                            FieldCondition(key=key, range=Range(lt=val))
                        )
                    elif op == "$lte":
                        must_conditions.append(
                            FieldCondition(key=key, range=Range(lte=val))
                        )
            else:
                # Simple equality
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        return Filter(must=must_conditions)
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from Qdrant"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update documents in Qdrant"""
        points = []
        
        for i, doc_id in enumerate(ids):
            if documents and i < len(documents):
                # Update both document and embedding
                embedding = self.create_embeddings([documents[i]])[0]
                
                payload = {"content": documents[i]}
                if metadatas and i < len(metadatas):
                    payload.update(metadatas[i])
                
                points.append(PointStruct(
                    id=doc_id,
                    vector=embedding.tolist(),
                    payload=payload
                ))
            elif metadatas and i < len(metadatas):
                # Update only metadata (keep existing vector)
                # First get the existing point
                existing = self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[doc_id],
                    with_vectors=True
                )[0]
                
                payload = existing.payload.copy()
                payload.update(metadatas[i])
                
                points.append(PointStruct(
                    id=doc_id,
                    vector=existing.vector,
                    payload=payload
                ))
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        collection_info = self.client.get_collection(self.collection_name)
        return collection_info.points_count
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self._create_collection()
        print(f"✓ Cleared Qdrant collection: {self.collection_name}")
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get Qdrant adapter information"""
        return {
            'name': 'Qdrant',
            'type': 'qdrant',
            'mode': self.config['mode'],
            'persistent': self.config['mode'] != 'memory',
            'requires_server': self.config['mode'] == 'remote',
            'supports_filtering': True,
            'supports_updates': True,
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'collection_name': self.collection_name,
            'document_count': self.get_document_count(),
            'features': [
                'Written in Rust (fast)',
                'REST and gRPC APIs',
                'Advanced filtering',
                'In-memory mode',
                'Distributed deployment',
                'Snapshot support',
                'Full-text search',
                'Payload indexing'
            ],
            'license': 'Apache 2.0',
            'github': 'https://github.com/qdrant/qdrant'
        }
    
    def batch_add_documents(self,
                           documents: List[str],
                           metadatas: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[str]:
        """Add documents in batches with progress bar"""
        all_ids = []
        
        for i in tqdm(range(0, len(documents), batch_size), 
                     desc="Indexing to Qdrant"):
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            
            ids = self.add_documents(batch_docs, batch_meta)
            all_ids.extend(ids)
        
        return all_ids
    
    @property
    def is_persistent(self) -> bool:
        """Whether this store persists data between sessions"""
        return self.config['mode'] != 'memory'
    
    @property
    def requires_server(self) -> bool:
        """Whether this store requires a separate server process"""
        return self.config['mode'] == 'remote'