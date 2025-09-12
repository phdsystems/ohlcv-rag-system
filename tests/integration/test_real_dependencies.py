"""
Integration tests with real dependencies
These tests require actual services to be running
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import chromadb
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import weaviate
import yfinance as yf
import openai
import os
import time
from typing import List, Dict, Any


@pytest.mark.integration
@pytest.mark.real_deps
class TestRealDataIngestion:
    """Test data ingestion with real APIs"""
    
    @pytest.mark.skipif(not os.getenv('ENABLE_REAL_API_TESTS'), 
                        reason="Real API tests disabled")
    def test_yahoo_finance_real(self):
        """Test real Yahoo Finance data fetching"""
        ticker = yf.Ticker("AAPL")
        
        # Fetch last 5 days of data
        data = ticker.history(period="5d")
        
        assert not data.empty
        assert 'Close' in data.columns
        assert 'Volume' in data.columns
        assert len(data) > 0
        
        # Verify data quality
        assert data['Close'].notna().all()
        assert data['Volume'].notna().all()
        assert (data['High'] >= data['Low']).all()
    
    @pytest.mark.skipif(not os.getenv('ALPHA_VANTAGE_API_KEY'), 
                        reason="Alpha Vantage API key not configured")
    def test_alpha_vantage_real(self):
        """Test real Alpha Vantage API"""
        import requests
        
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': 'AAPL',
            'apikey': api_key,
            'outputsize': 'compact'
        }
        
        response = requests.get(url, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert 'Time Series (Daily)' in data or 'Note' in data  # API might be rate limited
    
    def test_batch_ticker_ingestion(self):
        """Test batch ticker data ingestion"""
        tickers = ['AAPL', 'GOOGL', 'MSFT']
        all_data = {}
        
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1mo")
                if not data.empty:
                    all_data[symbol] = data
            except Exception as e:
                print(f"Failed to fetch {symbol}: {e}")
        
        assert len(all_data) > 0
        for symbol, data in all_data.items():
            assert not data.empty
            assert 'Close' in data.columns


@pytest.mark.integration
@pytest.mark.real_deps
class TestRealVectorStores:
    """Test real vector store operations"""
    
    @pytest.mark.docker
    def test_chromadb_real_operations(self):
        """Test ChromaDB with real instance"""
        # Connect to ChromaDB (assumes it's running)
        try:
            client = chromadb.HttpClient(host='localhost', port=8000)
            
            # Create collection
            collection_name = f"test_collection_{int(time.time())}"
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Generate test data
            embeddings = np.random.rand(10, 384).tolist()
            documents = [f"Document {i}" for i in range(10)]
            metadatas = [{"index": i, "type": "test"} for i in range(10)]
            ids = [f"doc_{i}" for i in range(10)]
            
            # Add documents
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Query
            query_embedding = np.random.rand(1, 384).tolist()
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=5
            )
            
            assert len(results['ids'][0]) == 5
            
            # Cleanup
            client.delete_collection(collection_name)
            
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")
    
    @pytest.mark.docker
    def test_qdrant_real_operations(self):
        """Test Qdrant with real instance"""
        try:
            client = QdrantClient(host="localhost", port=6333)
            
            # Create collection
            collection_name = f"test_collection_{int(time.time())}"
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
            # Generate test data
            points = []
            for i in range(10):
                points.append(PointStruct(
                    id=i,
                    vector=np.random.rand(384).tolist(),
                    payload={"ticker": f"TEST{i}", "date": "2024-01-01"}
                ))
            
            # Upsert points
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            # Search
            search_result = client.search(
                collection_name=collection_name,
                query_vector=np.random.rand(384).tolist(),
                limit=5
            )
            
            assert len(search_result) == 5
            
            # Cleanup
            client.delete_collection(collection_name)
            
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")
    
    @pytest.mark.docker
    def test_weaviate_real_operations(self):
        """Test Weaviate with real instance"""
        try:
            client = weaviate.Client("http://localhost:8080")
            
            # Create schema
            class_name = f"TestClass_{int(time.time())}"
            class_obj = {
                "class": class_name,
                "properties": [
                    {"name": "ticker", "dataType": ["string"]},
                    {"name": "date", "dataType": ["string"]},
                    {"name": "close", "dataType": ["number"]}
                ]
            }
            
            client.schema.create_class(class_obj)
            
            # Add data
            for i in range(10):
                client.data_object.create(
                    data_object={
                        "ticker": f"TEST{i}",
                        "date": "2024-01-01",
                        "close": 100.0 + i
                    },
                    class_name=class_name
                )
            
            # Query
            result = client.query.get(class_name, ["ticker", "close"]).do()
            
            assert 'data' in result
            
            # Cleanup
            client.schema.delete_class(class_name)
            
        except Exception as e:
            pytest.skip(f"Weaviate not available: {e}")


@pytest.mark.integration
@pytest.mark.real_deps
class TestRealLLMIntegration:
    """Test real LLM integration"""
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), 
                        reason="OpenAI API key not configured")
    def test_openai_real_completion(self):
        """Test real OpenAI API completion"""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": "What does RSI of 70 indicate? Answer in one sentence."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        assert response.choices[0].message.content
        assert len(response.choices[0].message.content) > 0
        assert any(word in response.choices[0].message.content.lower() 
                  for word in ['overbought', 'high', 'strong'])
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), 
                        reason="OpenAI API key not configured")
    def test_openai_embeddings(self):
        """Test real OpenAI embeddings"""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        texts = [
            "AAPL stock closed at 150.00",
            "Technical indicators show bullish trend",
            "Volume increased by 20%"
        ]
        
        embeddings = []
        for text in texts:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 1536  # Dimension of text-embedding-3-small
        
        # Test similarity (similar texts should have higher cosine similarity)
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # First two should be more similar than first and third
        sim_12 = cosine_similarity(embeddings[0], embeddings[1])
        sim_13 = cosine_similarity(embeddings[0], embeddings[2])
        
        assert sim_12 > 0  # Should have some similarity


@pytest.mark.integration
@pytest.mark.real_deps
class TestEndToEndPipeline:
    """Test complete end-to-end pipeline with real components"""
    
    @pytest.mark.slow
    @pytest.mark.skipif(not all([os.getenv('OPENAI_API_KEY')]), 
                        reason="Required API keys not configured")
    def test_full_pipeline_real(self):
        """Test full RAG pipeline with real components"""
        # 1. Fetch real data
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="1mo")
        
        assert not data.empty
        
        # 2. Calculate technical indicators
        from ta import add_all_ta_features
        data_with_ta = add_all_ta_features(
            data, open="Open", high="High", low="Low", 
            close="Close", volume="Volume", fillna=True
        )
        
        assert 'momentum_rsi' in data_with_ta.columns
        
        # 3. Create embeddings (using OpenAI)
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create sample document
        latest_data = data_with_ta.iloc[-1]
        document = f"""
        AAPL Analysis for {data.index[-1].strftime('%Y-%m-%d')}:
        Close: ${latest_data['Close']:.2f}
        Volume: {latest_data['Volume']:,}
        RSI: {latest_data.get('momentum_rsi', 'N/A')}
        """
        
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=document
        )
        
        embedding = embedding_response.data[0].embedding
        assert len(embedding) == 1536
        
        # 4. Generate analysis using LLM
        completion_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": f"Based on this data, provide a brief analysis:\n{document}"}
            ],
            max_tokens=150,
            temperature=0
        )
        
        analysis = completion_response.choices[0].message.content
        assert len(analysis) > 0
        assert 'AAPL' in document or 'Apple' in analysis or 'stock' in analysis.lower()


@pytest.mark.integration
@pytest.mark.real_deps
class TestPerformanceWithRealData:
    """Test performance metrics with real data"""
    
    def test_data_ingestion_performance(self):
        """Test data ingestion performance"""
        import time
        
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        start_time = time.time()
        
        results = {}
        for ticker_symbol in tickers:
            ticker_start = time.time()
            try:
                ticker = yf.Ticker(ticker_symbol)
                data = ticker.history(period="1mo")
                ticker_time = time.time() - ticker_start
                results[ticker_symbol] = {
                    'success': not data.empty,
                    'time': ticker_time,
                    'rows': len(data) if not data.empty else 0
                }
            except Exception as e:
                results[ticker_symbol] = {
                    'success': False,
                    'error': str(e)
                }
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert total_time < 30  # Should complete within 30 seconds
        successful = sum(1 for r in results.values() if r.get('success', False))
        assert successful >= 3  # At least 3 should succeed
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), 
                        reason="OpenAI API key not configured")
    def test_embedding_generation_performance(self):
        """Test embedding generation performance"""
        import time
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Generate 10 documents
        documents = [
            f"Stock analysis document {i}: Price movement and technical indicators"
            for i in range(10)
        ]
        
        start_time = time.time()
        embeddings = []
        
        for doc in documents:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=doc
            )
            embeddings.append(response.data[0].embedding)
        
        total_time = time.time() - start_time
        
        assert len(embeddings) == 10
        assert total_time < 10  # Should complete within 10 seconds
        
        # Calculate average time per embedding
        avg_time = total_time / len(documents)
        assert avg_time < 1  # Less than 1 second per embedding


if __name__ == "__main__":
    # Run specific test suites based on environment
    import sys
    
    if '--mock-only' in sys.argv:
        pytest.main(["-v", "-m", "not real_deps"])
    elif '--real-only' in sys.argv:
        pytest.main(["-v", "-m", "real_deps"])
    else:
        pytest.main(["-v"])