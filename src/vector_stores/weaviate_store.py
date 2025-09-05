import weaviate
from weaviate.embedded import EmbeddedOptions
import uuid
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from .vectordb_adapter import VectorDBAdapter, SearchResult


class WeaviateStore(VectorDBAdapter):
    """Weaviate vector store store"""
    
    def _validate_config(self) -> None:
        """Validate Weaviate configuration"""
        # Default configuration
        if 'mode' not in self.config:
            self.config['mode'] = 'embedded'  # embedded, local, or cloud
        
        if self.config['mode'] == 'cloud':
            if 'api_key' not in self.config or 'url' not in self.config:
                raise ValueError("Cloud mode requires 'api_key' and 'url' in config")
        elif self.config['mode'] == 'local':
            if 'url' not in self.config:
                self.config['url'] = 'http://localhost:8080'
    
    def _initialize_store(self) -> None:
        """Initialize Weaviate client and schema"""
        # Initialize client based on mode
        if self.config['mode'] == 'embedded':
            # Embedded Weaviate (no separate server needed)
            self.client = weaviate.Client(
                embedded_options=EmbeddedOptions()
            )
            print("✓ Initialized embedded Weaviate instance")
            
        elif self.config['mode'] == 'local':
            # Connect to local Weaviate server
            self.client = weaviate.Client(
                url=self.config['url']
            )
            print(f"✓ Connected to local Weaviate at {self.config['url']}")
            
        elif self.config['mode'] == 'cloud':
            # Connect to Weaviate Cloud
            self.client = weaviate.Client(
                url=self.config['url'],
                auth_client_secret=weaviate.AuthApiKey(api_key=self.config['api_key'])
            )
            print("✓ Connected to Weaviate Cloud")
        
        # Create schema for collection
        self._create_schema()
    
    def _create_schema(self) -> None:
        """Create or update Weaviate schema"""
        class_name = self._format_class_name(self.collection_name)
        
        # Check if class already exists
        try:
            self.client.schema.get(class_name)
            print(f"✓ Using existing Weaviate class: {class_name}")
        except:
            # Create new class
            class_obj = {
                "class": class_name,
                "description": "OHLCV financial data chunks",
                "vectorizer": "none",  # We provide our own embeddings
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "Document content"
                    },
                    {
                        "name": "ticker",
                        "dataType": ["string"],
                        "description": "Stock ticker symbol"
                    },
                    {
                        "name": "start_date",
                        "dataType": ["string"],
                        "description": "Start date of data chunk"
                    },
                    {
                        "name": "end_date",
                        "dataType": ["string"],
                        "description": "End date of data chunk"
                    },
                    {
                        "name": "trend",
                        "dataType": ["string"],
                        "description": "Market trend"
                    },
                    {
                        "name": "volatility",
                        "dataType": ["number"],
                        "description": "Price volatility"
                    },
                    {
                        "name": "avg_volume",
                        "dataType": ["number"],
                        "description": "Average trading volume"
                    },
                    {
                        "name": "rsi_avg",
                        "dataType": ["number"],
                        "description": "Average RSI"
                    }
                ]
            }
            
            self.client.schema.create_class(class_obj)
            print(f"✓ Created new Weaviate class: {class_name}")
    
    def _format_class_name(self, name: str) -> str:
        """Format collection name to Weaviate class name (PascalCase)"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to Weaviate"""
        class_name = self._format_class_name(self.collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # Create embeddings
        embeddings = self.create_embeddings(documents)
        
        # Add documents with embeddings
        with self.client.batch as batch:
            for i, (doc, meta, doc_id, embedding) in enumerate(zip(documents, metadatas, ids, embeddings)):
                properties = {
                    "content": doc,
                    "ticker": meta.get("ticker", ""),
                    "start_date": meta.get("start_date", ""),
                    "end_date": meta.get("end_date", ""),
                    "trend": meta.get("trend", ""),
                    "volatility": float(meta.get("volatility", 0)),
                    "avg_volume": float(meta.get("avg_volume", 0)),
                    "rsi_avg": float(meta.get("rsi_avg", 0))
                }
                
                batch.add_data_object(
                    data_object=properties,
                    class_name=class_name,
                    uuid=doc_id,
                    vector=embedding.tolist()
                )
        
        return ids
    
    def search(self,
              query: str,
              n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents in Weaviate"""
        class_name = self._format_class_name(self.collection_name)
        
        # Create query embedding
        query_embedding = self.create_embeddings([query])[0]
        
        # Build query
        query_builder = (
            self.client.query
            .get(class_name, ["content", "ticker", "start_date", "end_date", 
                             "trend", "volatility", "avg_volume", "rsi_avg"])
            .with_near_vector({"vector": query_embedding.tolist()})
            .with_limit(n_results)
            .with_additional(["distance", "id"])
        )
        
        # Add filters if provided
        if filter_dict:
            where_filter = self._build_where_filter(filter_dict)
            query_builder = query_builder.with_where(where_filter)
        
        # Execute query
        result = query_builder.do()
        
        # Convert to SearchResult objects
        search_results = []
        if class_name in result['data']['Get']:
            for item in result['data']['Get'][class_name]:
                metadata = {k: v for k, v in item.items() if k != 'content' and k != '_additional'}
                
                search_results.append(SearchResult(
                    id=item['_additional']['id'],
                    document=item['content'],
                    metadata=metadata,
                    score=1 - item['_additional']['distance']  # Convert distance to similarity
                ))
        
        return search_results
    
    def _build_where_filter(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build Weaviate where filter from filter dictionary"""
        operators = []
        
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle operators like $gt, $lt
                for op, val in value.items():
                    weaviate_op = {
                        "$gt": "GreaterThan",
                        "$gte": "GreaterThanEqual",
                        "$lt": "LessThan",
                        "$lte": "LessThanEqual",
                        "$eq": "Equal",
                        "$ne": "NotEqual"
                    }.get(op, "Equal")
                    
                    operators.append({
                        "path": [key],
                        "operator": weaviate_op,
                        "value": val
                    })
            else:
                # Simple equality
                operators.append({
                    "path": [key],
                    "operator": "Equal",
                    "value": value
                })
        
        if len(operators) == 1:
            return operators[0]
        else:
            return {"operator": "And", "operands": operators}
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from Weaviate"""
        for doc_id in ids:
            self.client.data_object.delete(doc_id)
    
    def update_documents(self,
                        ids: List[str],
                        documents: Optional[List[str]] = None,
                        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Update documents in Weaviate"""
        class_name = self._format_class_name(self.collection_name)
        
        for i, doc_id in enumerate(ids):
            update_obj = {}
            
            if documents and i < len(documents):
                update_obj["content"] = documents[i]
                # Update embedding
                embedding = self.create_embeddings([documents[i]])[0]
                self.client.data_object.update(
                    uuid=doc_id,
                    class_name=class_name,
                    data_object=update_obj,
                    vector=embedding.tolist()
                )
            elif metadatas and i < len(metadatas):
                # Update only metadata
                meta = metadatas[i]
                update_obj.update({
                    "ticker": meta.get("ticker", ""),
                    "start_date": meta.get("start_date", ""),
                    "end_date": meta.get("end_date", ""),
                    "trend": meta.get("trend", ""),
                    "volatility": float(meta.get("volatility", 0)),
                    "avg_volume": float(meta.get("avg_volume", 0)),
                    "rsi_avg": float(meta.get("rsi_avg", 0))
                })
                self.client.data_object.update(
                    uuid=doc_id,
                    class_name=class_name,
                    data_object=update_obj
                )
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        class_name = self._format_class_name(self.collection_name)
        result = self.client.query.aggregate(class_name).with_meta_count().do()
        return result['data']['Aggregate'][class_name][0]['meta']['count']
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        class_name = self._format_class_name(self.collection_name)
        # Delete all objects of this class
        self.client.batch.delete_objects(
            class_name=class_name,
            where={"path": ["id"], "operator": "Like", "valueString": "*"}
        )
        print(f"✓ Cleared Weaviate class: {class_name}")
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get Weaviate adapter information"""
        return {
            'name': 'Weaviate',
            'type': 'weaviate',
            'mode': self.config['mode'],
            'persistent': True,
            'requires_server': self.config['mode'] != 'embedded',
            'supports_filtering': True,
            'supports_updates': True,
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'collection_name': self.collection_name,
            'document_count': self.get_document_count(),
            'features': [
                'GraphQL API',
                'Hybrid search',
                'Metadata filtering',
                'Embedded mode available',
                'Cloud deployment',
                'HNSW index',
                'Multi-tenancy'
            ],
            'license': 'BSD-3-Clause',
            'github': 'https://github.com/weaviate/weaviate'
        }
    
    @property
    def requires_server(self) -> bool:
        """Whether this store requires a separate server process"""
        return self.config['mode'] != 'embedded'