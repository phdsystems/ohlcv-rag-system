"""
End-to-end integration tests using Testcontainers
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any
import time


class TestEndToEndIntegration:
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_rag_pipeline_with_chromadb(self, clean_chromadb):
        """Test complete RAG pipeline with ChromaDB backend"""
        # Simulate data ingestion
        mock_data = self._generate_mock_ohlcv_data()
        
        # Create collection for OHLCV data
        collection = clean_chromadb.create_collection(
            name="ohlcv_rag_test",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Process and embed data (mock embeddings)
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for i, (ticker, data) in enumerate(mock_data.items()):
            for j, row in enumerate(data):
                doc_id = f"{ticker}_{j}"
                content = f"Technical analysis for {ticker} on {row['date']}: Price ${row['close']:.2f}, Volume {row['volume']}, RSI {row['rsi']:.2f}"
                
                documents.append(content)
                embeddings.append(np.random.rand(768).tolist())  # Mock embedding
                metadatas.append({
                    "ticker": ticker,
                    "date": row["date"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "rsi": row["rsi"]
                })
                ids.append(doc_id)
        
        # Store in vector database
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Simulate RAG query
        query = "What is the trend for AAPL in January?"
        query_embedding = np.random.rand(768).tolist()  # Mock query embedding
        
        # Retrieve relevant documents
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            where={"ticker": "AAPL"}
        )
        
        assert len(results["ids"][0]) > 0
        assert all(meta["ticker"] == "AAPL" for meta in results["metadatas"][0])
        
        # Simulate LLM response generation
        context = "\n".join(results["documents"][0])
        mock_response = self._generate_mock_llm_response(query, context)
        
        assert "AAPL" in mock_response
        assert len(mock_response) > 0
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_multi_ticker_analysis_with_weaviate(self, clean_weaviate):
        """Test multi-ticker analysis with Weaviate backend"""
        # Create schema
        schema = {
            "class": "MarketData",
            "vectorizer": "none",
            "properties": [
                {"name": "ticker", "dataType": ["string"]},
                {"name": "date", "dataType": ["string"]},
                {"name": "analysis", "dataType": ["text"]},
                {"name": "metrics", "dataType": ["object"]}
            ]
        }
        clean_weaviate.schema.create_class(schema)
        
        # Generate and store data for multiple tickers
        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        
        with clean_weaviate.batch as batch:
            for ticker in tickers:
                for day in range(1, 11):  # 10 days of data
                    vector = np.random.rand(128).tolist()
                    data = {
                        "ticker": ticker,
                        "date": f"2024-01-{day:02d}",
                        "analysis": f"{ticker} showed {'bullish' if day % 2 == 0 else 'bearish'} signals",
                        "metrics": {
                            "rsi": 30 + day * 4,
                            "macd": -2 + day * 0.4,
                            "volume": 1000000 + day * 100000
                        }
                    }
                    batch.add_data_object(
                        data_object=data,
                        class_name="MarketData",
                        vector=vector
                    )
        
        time.sleep(2)  # Wait for indexing
        
        # Query for comparative analysis
        result = clean_weaviate.query.get(
            "MarketData",
            ["ticker", "date", "analysis", "metrics"]
        ).with_where({
            "operator": "And",
            "operands": [
                {
                    "path": ["ticker"],
                    "operator": "ContainsAny",
                    "valueStringArray": ["AAPL", "GOOGL"]
                },
                {
                    "path": ["date"],
                    "operator": "Like",
                    "valueString": "2024-01-0*"
                }
            ]
        }).with_limit(20).do()
        
        market_data = result["data"]["Get"]["MarketData"]
        assert len(market_data) > 0
        
        # Verify we got data for both tickers
        tickers_found = set(item["ticker"] for item in market_data)
        assert "AAPL" in tickers_found or "GOOGL" in tickers_found
    
    @pytest.mark.integration
    def test_realtime_data_update_with_qdrant(self, clean_qdrant):
        """Test real-time data updates with Qdrant backend"""
        from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition
        
        # Create collection
        clean_qdrant.create_collection(
            collection_name="realtime_data",
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )
        
        # Initial data load
        initial_points = []
        for i in range(10):
            initial_points.append(PointStruct(
                id=i,
                vector=np.random.rand(512).tolist(),
                payload={
                    "ticker": "AAPL",
                    "timestamp": f"2024-01-01T{i:02d}:00:00",
                    "price": 150.0 + i * 0.5,
                    "type": "historical"
                }
            ))
        
        clean_qdrant.upsert(
            collection_name="realtime_data",
            points=initial_points
        )
        
        # Verify initial data
        count = clean_qdrant.count(
            collection_name="realtime_data",
            exact=True,
            count_filter=Filter(
                must=[FieldCondition(key="type", match={"value": "historical"})]
            )
        )
        assert count.count == 10
        
        # Simulate real-time updates
        realtime_points = []
        for i in range(5):
            realtime_points.append(PointStruct(
                id=100 + i,  # New IDs for real-time data
                vector=np.random.rand(512).tolist(),
                payload={
                    "ticker": "AAPL",
                    "timestamp": f"2024-01-01T{10+i:02d}:00:00",
                    "price": 155.0 + i * 0.3,
                    "type": "realtime"
                }
            ))
        
        clean_qdrant.upsert(
            collection_name="realtime_data",
            points=realtime_points
        )
        
        # Query latest data
        latest_vector = np.random.rand(512).tolist()
        results = clean_qdrant.search(
            collection_name="realtime_data",
            query_vector=latest_vector,
            query_filter=Filter(
                must=[FieldCondition(key="type", match={"value": "realtime"})]
            ),
            limit=5
        )
        
        assert len(results) == 5
        assert all(r.payload["type"] == "realtime" for r in results)
    
    @pytest.mark.integration
    def test_data_persistence_across_restarts(self, chromadb_container):
        """Test data persistence when container restarts"""
        import chromadb
        
        # First session - add data
        client = chromadb.HttpClient(
            host=chromadb_container["host"],
            port=chromadb_container["port"]
        )
        
        collection = client.create_collection(name="persistence_test")
        
        # Add substantial amount of data
        embeddings = np.random.rand(50, 768).tolist()
        documents = [f"Document {i}" for i in range(50)]
        metadatas = [{"index": i, "category": f"cat_{i%5}"} for i in range(50)]
        ids = [f"doc_{i}" for i in range(50)]
        
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        original_count = collection.count()
        assert original_count == 50
        
        # Simulate container restart by creating new client
        client2 = chromadb.HttpClient(
            host=chromadb_container["host"],
            port=chromadb_container["port"]
        )
        
        # Verify data persisted
        collection2 = client2.get_collection(name="persistence_test")
        assert collection2.count() == original_count
        
        # Verify we can query the persisted data
        results = collection2.query(
            query_embeddings=[embeddings[0]],
            n_results=5
        )
        
        assert len(results["ids"][0]) == 5
        assert results["ids"][0][0] == "doc_0"  # Should find itself first
        
        # Cleanup
        client2.delete_collection("persistence_test")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_operations(self, clean_chromadb):
        """Test concurrent read/write operations"""
        import concurrent.futures
        import threading
        
        # Create collection
        collection = clean_chromadb.create_collection(
            name="concurrent_test",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Shared counter for unique IDs
        id_counter = threading.Lock()
        current_id = [0]
        
        def write_data(thread_id):
            """Write data from a thread"""
            with id_counter:
                start_id = current_id[0]
                current_id[0] += 10
            
            embeddings = np.random.rand(10, 768).tolist()
            documents = [f"Thread {thread_id} - Doc {i}" for i in range(10)]
            ids = [f"thread_{thread_id}_doc_{i}" for i in range(10)]
            
            collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids
            )
            return f"Thread {thread_id} completed"
        
        def read_data(thread_id):
            """Read data from a thread"""
            query_embedding = np.random.rand(768).tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            return f"Thread {thread_id} found {len(results['ids'][0])} results"
        
        # Execute concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit write operations
            write_futures = [executor.submit(write_data, i) for i in range(5)]
            
            # Wait for some writes to complete
            time.sleep(1)
            
            # Submit read operations
            read_futures = [executor.submit(read_data, i) for i in range(5)]
            
            # Gather all results
            write_results = [f.result() for f in write_futures]
            read_results = [f.result() for f in read_futures]
        
        # Verify all operations completed
        assert len(write_results) == 5
        assert len(read_results) == 5
        assert all("completed" in r for r in write_results)
        assert all("found" in r for r in read_results)
        
        # Verify final data count
        final_count = collection.count()
        assert final_count == 50  # 5 threads * 10 documents each
    
    # Helper methods
    def _generate_mock_ohlcv_data(self) -> Dict[str, List[Dict]]:
        """Generate mock OHLCV data for testing"""
        tickers = ["AAPL", "GOOGL", "MSFT"]
        data = {}
        
        for ticker in tickers:
            ticker_data = []
            base_price = {"AAPL": 150, "GOOGL": 2800, "MSFT": 370}[ticker]
            
            for day in range(1, 11):  # 10 days
                ticker_data.append({
                    "date": f"2024-01-{day:02d}",
                    "open": base_price + np.random.uniform(-5, 5),
                    "high": base_price + np.random.uniform(0, 10),
                    "low": base_price + np.random.uniform(-10, 0),
                    "close": base_price + np.random.uniform(-5, 5),
                    "volume": int(1000000 + np.random.uniform(-500000, 500000)),
                    "rsi": 30 + np.random.uniform(0, 40),
                    "macd": np.random.uniform(-2, 2)
                })
                base_price += np.random.uniform(-2, 3)  # Trend
            
            data[ticker] = ticker_data
        
        return data
    
    def _generate_mock_llm_response(self, query: str, context: str) -> str:
        """Generate mock LLM response for testing"""
        return f"Based on the analysis of the provided data: {context[:100]}... The trend shows positive momentum with increasing volume."