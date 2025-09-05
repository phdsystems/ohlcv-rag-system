from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, DataType,
    utility, MilvusClient
)
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from tqdm import tqdm

from .vectordb_adapter import VectorDBAdapter, SearchResult


class MilvusStore(VectorDBAdapter):
    """Milvus vector store store"""
    
    def _validate_config(self) -> None:
        """Validate Milvus configuration"""
        # Default configuration
        if 'mode' not in self.config:
            self.config['mode'] = 'lite'  # lite, standalone, or cluster
        
        if self.config['mode'] == 'lite':
            # Milvus Lite - embedded version
            if 'uri' not in self.config:
                self.config['uri'] = './data/milvus_lite.db'
        elif self.config['mode'] in ['standalone', 'cluster']:
            # Milvus server
            if 'host' not in self.config:
                self.config['host'] = 'localhost'
            if 'port' not in self.config:
                self.config['port'] = 19530
            # Optional authentication
            self.config['user'] = self.config.get('user', '')
            self.config['password'] = self.config.get('password', '')
    
    def _initialize_store(self) -> None:
        """Initialize Milvus connection and collection"""
        if self.config['mode'] == 'lite':
            # Use Milvus Lite (embedded)
            self.client = MilvusClient(uri=self.config['uri'])
            print(f"✓ Initialized Milvus Lite at {self.config['uri']}")
            
        else:
            # Connect to Milvus server
            connections.connect(
                alias="default",
                host=self.config['host'],
                port=self.config['port'],
                user=self.config.get('user', ''),
                password=self.config.get('password', '')
            )
            print(f"✓ Connected to Milvus server at {self.config['host']}:{self.config['port']}")
        
        # Create or get collection
        self._setup_collection()
    
    def _setup_collection(self) -> None:
        """Create or verify Milvus collection"""
        if self.config['mode'] == 'lite':
            # Milvus Lite handles collections differently
            self._setup_lite_collection()
        else:
            self._setup_server_collection()
    
    def _setup_lite_collection(self) -> None:
        """Setup collection for Milvus Lite"""
        # Check if collection exists
        if self.client.has_collection(self.collection_name):
            print(f"✓ Using existing Milvus Lite collection: {self.collection_name}")
        else:
            # Create collection with schema
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embedding_dimension,
                metric_type="COSINE",
                consistency_level="Strong"
            )
            print(f"✓ Created new Milvus Lite collection: {self.collection_name}")
    
    def _setup_server_collection(self) -> None:
        """Setup collection for Milvus server"""
        # Check if collection exists
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            print(f"✓ Loaded existing Milvus collection: {self.collection_name}")
        else:
            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dimension),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="ticker", dtype=DataType.VARCHAR, max_length=10),
                FieldSchema(name="start_date", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="end_date", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="trend", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="volatility", dtype=DataType.FLOAT),
                FieldSchema(name="avg_volume", dtype=DataType.FLOAT),
                FieldSchema(name="rsi_avg", dtype=DataType.FLOAT)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="OHLCV financial data embeddings"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                consistency_level="Strong"
            )
            
            # Create index for vector field
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            self.collection.load()
            print(f"✓ Created new Milvus collection: {self.collection_name}")
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to Milvus"""
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Create embeddings
        embeddings = self.create_embeddings(documents)
        
        if self.config['mode'] == 'lite':
            # Milvus Lite insertion
            data = []
            for i, (doc_id, doc, meta, embedding) in enumerate(zip(ids, documents, metadatas, embeddings)):
                data.append({
                    "id": doc_id,
                    "vector": embedding.tolist(),
                    "content": doc,
                    **meta
                })
            
            self.client.insert(
                collection_name=self.collection_name,
                data=data
            )
        else:
            # Milvus server insertion
            entities = [
                ids,
                embeddings.tolist(),
                documents,
                [m.get("ticker", "") for m in metadatas],
                [m.get("start_date", "") for m in metadatas],
                [m.get("end_date", "") for m in metadatas],
                [m.get("trend", "") for m in metadatas],
                [float(m.get("volatility", 0)) for m in metadatas],
                [float(m.get("avg_volume", 0)) for m in metadatas],
                [float(m.get("rsi_avg", 0)) for m in metadatas]
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
        
        return ids
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents in Milvus"""
        # Create query embedding
        query_embedding = self.create_embeddings([query])
        
        if self.config['mode'] == 'lite':
            # Milvus Lite search
            search_params = {"metric_type": "COSINE", "params": {}}
            
            # Build filter expression
            filter_expr = self._build_filter_expression(filter_dict) if filter_dict else None
            
            results = self.client.search(
                collection_name=self.collection_name,
                data=query_embedding.tolist(),
                limit=n_results,
                filter=filter_expr,
                output_fields=["content", "ticker", "start_date", "end_date", 
                             "trend", "volatility", "avg_volume", "rsi_avg"]
            )
            
            # Convert to SearchResult objects
            search_results = []
            for hits in results:
                for hit in hits:
                    metadata = {k: v for k, v in hit['entity'].items() if k != 'content'}
                    
                    search_results.append(SearchResult(
                        id=hit['id'],
                        document=hit['entity']['content'],
                        metadata=metadata,
                        score=1 - hit['distance']  # Convert distance to similarity
                    ))
        else:
            # Milvus server search
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            # Build filter expression
            filter_expr = self._build_filter_expression(filter_dict) if filter_dict else None
            
            results = self.collection.search(
                data=query_embedding.tolist(),
                anns_field="embedding",
                param=search_params,
                limit=n_results,
                expr=filter_expr,
                output_fields=["content", "ticker", "start_date", "end_date",
                             "trend", "volatility", "avg_volume", "rsi_avg"]
            )
            
            # Convert to SearchResult objects
            search_results = []
            for hits in results:
                for hit in hits:
                    metadata = {
                        "ticker": hit.entity.get("ticker"),
                        "start_date": hit.entity.get("start_date"),
                        "end_date": hit.entity.get("end_date"),
                        "trend": hit.entity.get("trend"),
                        "volatility": hit.entity.get("volatility"),
                        "avg_volume": hit.entity.get("avg_volume"),
                        "rsi_avg": hit.entity.get("rsi_avg")
                    }
                    
                    search_results.append(SearchResult(
                        id=hit.id,
                        document=hit.entity.get("content"),
                        metadata=metadata,
                        score=1 - hit.distance  # Convert distance to similarity
                    ))
        
        return search_results
    
    def _build_filter_expression(self, filter_dict: Dict[str, Any]) -> str:
        """Build Milvus filter expression from filter dictionary"""
        expressions = []
        
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle operators
                for op, val in value.items():
                    if op == "$gt":
                        expressions.append(f"{key} > {val}")
                    elif op == "$gte":
                        expressions.append(f"{key} >= {val}")
                    elif op == "$lt":
                        expressions.append(f"{key} < {val}")
                    elif op == "$lte":
                        expressions.append(f"{key} <= {val}")
                    elif op == "$eq":
                        if isinstance(val, str):
                            expressions.append(f'{key} == "{val}"')
                        else:
                            expressions.append(f"{key} == {val}")
                    elif op == "$ne":
                        if isinstance(val, str):
                            expressions.append(f'{key} != "{val}"')
                        else:
                            expressions.append(f"{key} != {val}")
            else:
                # Simple equality
                if isinstance(value, str):
                    expressions.append(f'{key} == "{value}"')
                else:
                    expressions.append(f"{key} == {value}")
        
        return " and ".join(expressions) if expressions else ""
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from Milvus"""
        if self.config['mode'] == 'lite':
            self.client.delete(
                collection_name=self.collection_name,
                ids=ids
            )
        else:
            expr = f'id in {ids}'
            self.collection.delete(expr)
            self.collection.flush()
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update documents in Milvus (delete and re-insert)"""
        # Milvus doesn't support in-place updates, so delete and re-insert
        self.delete_documents(ids)
        
        if documents:
            self.add_documents(documents, metadatas or [{} for _ in documents], ids)
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        if self.config['mode'] == 'lite':
            # Query count for Milvus Lite
            return self.client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["count(*)"]
            )[0]["count(*)"]
        else:
            return self.collection.num_entities
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        if self.config['mode'] == 'lite':
            self.client.drop_collection(self.collection_name)
            self._setup_lite_collection()
        else:
            self.collection.drop()
            self._setup_server_collection()
        
        print(f"✓ Cleared Milvus collection: {self.collection_name}")
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get Milvus adapter information"""
        return {
            'name': 'Milvus',
            'type': 'milvus',
            'mode': self.config['mode'],
            'persistent': True,
            'requires_server': self.config['mode'] != 'lite',
            'supports_filtering': True,
            'supports_updates': False,  # Requires delete + re-insert
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'collection_name': self.collection_name,
            'document_count': self.get_document_count(),
            'features': [
                'Distributed architecture',
                'Milvus Lite embedded mode',
                'Multiple index types',
                'GPU acceleration',
                'Hybrid search',
                'Time Travel queries',
                'Partition support',
                'High availability'
            ],
            'license': 'Apache 2.0',
            'github': 'https://github.com/milvus-io/milvus'
        }
    
    @property
    def requires_server(self) -> bool:
        """Whether this store requires a separate server process"""
        return self.config['mode'] != 'lite'
    
    @property
    def supports_updates(self) -> bool:
        """Milvus requires delete + re-insert for updates"""
        return False