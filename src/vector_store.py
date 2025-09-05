import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict, Any, Optional
import numpy as np
from tqdm import tqdm
import os

class OHLCVVectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_db", 
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="ohlcv_data",
            metadata={"hnsw:space": "cosine"}
        )
        
    def create_embeddings(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
    
    def index_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100):
        print(f"Indexing {len(chunks)} chunks into vector store...")
        
        for i in tqdm(range(0, len(chunks), batch_size), desc="Indexing batches"):
            batch = chunks[i:i + batch_size]
            
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for j, chunk in enumerate(batch):
                # Create document text from summary and key metrics
                doc_text = self._create_document_text(chunk)
                documents.append(doc_text)
                
                # Generate embedding
                embedding = self.create_embeddings(doc_text)
                embeddings.append(embedding)
                
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
                    'chunk_index': i + j
                }
                
                if chunk['metadata'].get('rsi_avg'):
                    metadata['rsi_avg'] = chunk['metadata']['rsi_avg']
                    
                metadatas.append(metadata)
                ids.append(f"chunk_{i + j}")
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
        print(f"✓ Successfully indexed {len(chunks)} chunks")
        
    def _create_document_text(self, chunk: Dict[str, Any]) -> str:
        ticker = chunk['ticker']
        start_date = chunk['start_date']
        end_date = chunk['end_date']
        summary = chunk['summary']
        metadata = chunk['metadata']
        
        # Create a comprehensive text representation
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
            
        # Add pattern descriptions
        if metadata['trend'] == 'Uptrend':
            doc_text += "\n\nPattern: Bullish uptrend with higher highs and higher lows"
        elif metadata['trend'] == 'Downtrend':
            doc_text += "\n\nPattern: Bearish downtrend with lower highs and lower lows"
        else:
            doc_text += "\n\nPattern: Sideways consolidation or ranging market"
            
        return doc_text.strip()
    
    def search(self, query: str, n_results: int = 5, 
               filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Create query embedding
        query_embedding = self.create_embeddings(query)
        
        # Build where clause for filtering
        where_clause = None
        if filter_dict:
            where_clause = filter_dict
            
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'relevance_score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
            
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results)
        }
    
    def search_by_pattern(self, pattern_type: str, ticker: Optional[str] = None, 
                         n_results: int = 5) -> Dict[str, Any]:
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
        
        filter_dict = None
        if ticker:
            filter_dict = {'ticker': ticker}
            
        return self.search(query, n_results, filter_dict)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        count = self.collection.count()
        
        # Get sample of metadata to show available fields
        sample = self.collection.peek(1)
        
        stats = {
            'total_chunks': count,
            'collection_name': 'ohlcv_data',
            'persist_directory': self.persist_directory,
            'embedding_model': 'all-MiniLM-L6-v2'
        }
        
        if sample['metadatas']:
            stats['available_metadata_fields'] = list(sample['metadatas'][0].keys())
            
        return stats
    
    def clear_collection(self):
        # Delete and recreate the collection
        self.client.delete_collection("ohlcv_data")
        self.collection = self.client.create_collection(
            name="ohlcv_data",
            metadata={"hnsw:space": "cosine"}
        )
        print("✓ Collection cleared")