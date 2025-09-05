import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from tqdm import tqdm

from .vectordb_adapter import VectorDBAdapter, SearchResult


class ChromaDBStore(VectorDBAdapter):
    """ChromaDB vector store implementation"""
    
    def _validate_config(self) -> None:
        """Validate ChromaDB configuration"""
        # Set default persist directory if not provided
        if 'persist_directory' not in self.config:
            self.config['persist_directory'] = './data/chroma_db'
    
    def _initialize_store(self) -> None:
        """Initialize ChromaDB client and collection"""
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.config['persist_directory'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✓ Loaded existing ChromaDB collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✓ Created new ChromaDB collection: {self.collection_name}")
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to ChromaDB"""
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Create embeddings
        embeddings = self.create_embeddings(documents)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents in ChromaDB"""
        # Create query embedding
        query_embedding = self.create_embeddings([query])[0]
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=filter_dict,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Convert to SearchResult objects
        search_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                search_results.append(SearchResult(
                    id=results['ids'][0][i],
                    document=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    score=1 - results['distances'][0][i]  # Convert distance to similarity
                ))
        
        return search_results
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from ChromaDB"""
        self.collection.delete(ids=ids)
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update documents in ChromaDB"""
        update_args = {'ids': ids}
        
        if documents:
            embeddings = self.create_embeddings(documents)
            update_args['embeddings'] = embeddings.tolist()
            update_args['documents'] = documents
            
        if metadatas:
            update_args['metadatas'] = metadatas
        
        self.collection.update(**update_args)
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        return self.collection.count()
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✓ Cleared ChromaDB collection: {self.collection_name}")
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get ChromaDB store information"""
        return {
            'name': 'ChromaDB',
            'type': 'chromadb',
            'persistent': True,
            'requires_server': False,
            'supports_filtering': True,
            'supports_updates': True,
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'collection_name': self.collection_name,
            'persist_directory': self.config['persist_directory'],
            'document_count': self.get_document_count(),
            'features': [
                'Local persistence',
                'Metadata filtering',
                'Automatic persistence',
                'No server required',
                'Cosine similarity',
                'HNSW index'
            ],
            'license': 'Apache 2.0',
            'github': 'https://github.com/chroma-core/chroma'
        }
    
    def batch_add_documents(self,
                           documents: List[str],
                           metadatas: List[Dict[str, Any]],
                           batch_size: int = 100) -> List[str]:
        """Add documents in batches with progress bar"""
        all_ids = []
        
        for i in tqdm(range(0, len(documents), batch_size), 
                     desc="Indexing to ChromaDB"):
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            
            ids = self.add_documents(batch_docs, batch_meta)
            all_ids.extend(ids)
        
        return all_ids
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get detailed collection statistics"""
        count = self.collection.count()
        
        # Get sample to show metadata fields
        sample = self.collection.peek(1)
        
        stats = {
            'total_documents': count,
            'collection_name': self.collection_name,
            'persist_directory': self.config['persist_directory'],
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension
        }
        
        if sample['metadatas'] and len(sample['metadatas']) > 0:
            stats['metadata_fields'] = list(sample['metadatas'][0].keys())
        
        return stats