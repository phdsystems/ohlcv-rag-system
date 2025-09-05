"""
Vector Store Module - Bridge to new adapter system

This module provides backward compatibility while using the new adapter pattern.
"""

from typing import List, Dict, Any, Optional
from src.vector_stores import VectorStoreManager, SearchResult


class OHLCVVectorStore:
    """
    Backward-compatible wrapper for vector store adapters
    Defaults to ChromaDB for compatibility with existing code
    """
    
    def __init__(self, 
                 persist_directory: str = "./data/chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 store_type: str = "chromadb"):
        """
        Initialize vector store with adapter pattern
        
        Args:
            persist_directory: Directory for persistent storage
            embedding_model: Name of the embedding model
            store_type: Type of vector store to use
        """
        # Get store type from environment or use default
        import os
        self.store_type = os.getenv("VECTOR_STORE_TYPE", store_type)
        
        # Build configuration based on store type
        config = self._build_config(persist_directory)
        
        # Create adapter using manager
        self.adapter = VectorStoreManager.create_adapter(
            store_type=self.store_type,
            collection_name="ohlcv_data",
            embedding_model=embedding_model,
            config=config
        )
        
        # Store references for compatibility
        self.collection = self.adapter
        self.embedding_model = self.adapter.embedding_model
        self.persist_directory = persist_directory
        
        print(f"Initialized vector store: {self.store_type}")
    
    def _build_config(self, persist_directory: str) -> Dict[str, Any]:
        """Build configuration for the selected store type"""
        import os
        
        configs = {
            'chromadb': {
                'persist_directory': persist_directory
            },
            'weaviate': {
                'mode': os.getenv('WEAVIATE_MODE', 'embedded'),
                'url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
                'api_key': os.getenv('WEAVIATE_API_KEY')
            },
            'qdrant': {
                'mode': os.getenv('QDRANT_MODE', 'memory'),
                'path': persist_directory.replace('chroma', 'qdrant'),
                'url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
                'api_key': os.getenv('QDRANT_API_KEY')
            },
            'faiss': {
                'persist_directory': persist_directory.replace('chroma', 'faiss'),
                'index_type': os.getenv('FAISS_INDEX_TYPE', 'flat')
            },
            'milvus': {
                'mode': os.getenv('MILVUS_MODE', 'lite'),
                'uri': persist_directory.replace('chroma_db', 'milvus_lite.db'),
                'host': os.getenv('MILVUS_HOST', 'localhost'),
                'port': int(os.getenv('MILVUS_PORT', '19530'))
            }
        }
        
        return configs.get(self.store_type, {'persist_directory': persist_directory})
    
    def create_embeddings(self, text: str) -> List[float]:
        """Create embeddings for text (backward compatibility)"""
        return self.adapter.create_embeddings([text])[0].tolist()
    
    def index_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100):
        """Index chunks into vector store (backward compatibility)"""
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Create document text
            doc_text = self._create_document_text(chunk)
            documents.append(doc_text)
            
            # Prepare metadata
            metadata = {
                'ticker': chunk['ticker'],
                'start_date': chunk['start_date'],
                'end_date': chunk['end_date'],
                'avg_volume': chunk['metadata']['avg_volume'],
                'trend': chunk['metadata']['trend'],
                'volatility': chunk['metadata']['volatility'],
                'price_high': chunk['metadata']['price_range']['high'],
                'price_low': chunk['metadata']['price_range']['low'],
                'price_open': chunk['metadata']['price_range']['open'],
                'price_close': chunk['metadata']['price_range']['close'],
                'chunk_index': chunks.index(chunk)
            }
            
            if chunk['metadata'].get('rsi_avg'):
                metadata['rsi_avg'] = chunk['metadata']['rsi_avg']
                
            metadatas.append(metadata)
        
        # Use adapter's batch add
        self.adapter.batch_add_documents(documents, metadatas, batch_size)
        print(f"✓ Successfully indexed {len(chunks)} chunks")
    
    def _create_document_text(self, chunk: Dict[str, Any]) -> str:
        """Create document text from chunk (backward compatibility)"""
        ticker = chunk['ticker']
        start_date = chunk['start_date']
        end_date = chunk['end_date']
        summary = chunk['summary']
        metadata = chunk['metadata']
        
        doc_text = f"""
        Stock: {ticker}
        Period: {start_date} to {end_date}
        
        {summary}
        
        Key Metrics:
        - Trend: {metadata['trend']}
        - Average Volume: {metadata['avg_volume']:,.0f}
        - Price Range: ${metadata['price_range']['low']:.2f} - ${metadata['price_range']['high']:.2f}
        - Opening Price: ${metadata['price_range']['open']:.2f}
        - Closing Price: ${metadata['price_range']['close']:.2f}
        - Volatility: {metadata['volatility']:.4f}
        """
        
        if metadata.get('rsi_avg'):
            doc_text += f"\n- Average RSI: {metadata['rsi_avg']:.2f}"
            
        return doc_text.strip()
    
    def search(self, query: str, n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for similar documents (backward compatibility)"""
        results = self.adapter.search(query, n_results, filter_dict)
        
        # Format for backward compatibility
        formatted_results = []
        for result in results:
            formatted_results.append({
                'document': result.document,
                'metadata': result.metadata,
                'relevance_score': result.score
            })
        
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results)
        }
    
    def search_by_pattern(self, pattern_type: str, ticker: Optional[str] = None,
                         n_results: int = 5) -> Dict[str, Any]:
        """Search by pattern (backward compatibility)"""
        pattern_queries = {
            'uptrend': "Strong uptrend bullish momentum higher highs ascending",
            'downtrend': "Downtrend bearish momentum lower lows descending",
            'breakout': "Breakout resistance breakthrough volume surge price spike",
            'reversal': "Trend reversal bottom top turning point change direction",
            'consolidation': "Sideways consolidation ranging flat trading range",
            'volatile': "High volatility large price swings unstable fluctuation",
            'overbought': "Overbought RSI above 70 extended rally due for pullback",
            'oversold': "Oversold RSI below 30 extended decline due for bounce"
        }
        
        query = pattern_queries.get(pattern_type.lower(), pattern_type)
        filter_dict = {'ticker': ticker} if ticker else None
        
        return self.search(query, n_results, filter_dict)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics (backward compatibility)"""
        info = self.adapter.get_adapter_info()
        
        return {
            'total_chunks': info.get('document_count', 0),
            'collection_name': info.get('collection_name', 'ohlcv_data'),
            'persist_directory': self.persist_directory,
            'embedding_model': info.get('embedding_model', 'all-MiniLM-L6-v2'),
            'vector_store_type': self.store_type,
            'adapter_info': info
        }
    
    def clear_collection(self):
        """Clear the collection (backward compatibility)"""
        self.adapter.clear_collection()