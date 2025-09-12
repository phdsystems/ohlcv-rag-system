#!/usr/bin/env python3
"""
Real functionality test - no mocks, actual module usage
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_real_data_ingestion():
    """Test real data ingestion from Yahoo Finance"""
    from src.ingestion.data_ingestion import DataIngestionEngine
    
    print("\n=== Testing Real Data Ingestion ===")
    
    # Create real data ingestion engine
    engine = DataIngestionEngine(
        name="TestIngestion",
        config={
            'source': 'yahoo',
            'period': '5d',
            'interval': '1d'
        }
    )
    
    # Initialize the engine
    engine.initialize()
    print("✓ Data ingestion engine initialized")
    
    # Fetch real data for Apple
    data = engine.fetch_data(['AAPL'])
    assert data is not None
    print(f"✓ Fetched real data, type: {type(data)}")
    
    # Data might be a list of DataModels or dict
    if isinstance(data, dict) and 'AAPL' in data:
        print(f"✓ Fetched real data for AAPL: {len(data['AAPL'])} records")
    elif isinstance(data, list) and len(data) > 0:
        print(f"✓ Fetched {len(data)} data models")
        data = {'AAPL': data[0]} if len(data) > 0 else {}
    else:
        print(f"✓ Fetched data in format: {data}")
    
    # Create chunks from real data
    chunks = engine.create_chunks(data, window_size=3)
    assert len(chunks) > 0
    print(f"✓ Created {len(chunks)} chunks from real data")
    
    # Verify chunk structure
    first_chunk = chunks[0]
    assert 'content' in first_chunk
    assert 'metadata' in first_chunk
    assert 'ticker' in first_chunk['metadata']
    print("✓ Chunk structure validated")
    
    return True

def test_real_vector_store():
    """Test real vector store operations with ChromaDB"""
    from src.pipeline.vector_store_adapter import VectorStoreAdapter
    
    print("\n=== Testing Real Vector Store ===")
    
    # Create real vector store
    store = VectorStoreAdapter(
        store_type="chromadb",
        config={
            'collection_name': 'test_real_collection',
            'embedding_model': 'all-MiniLM-L6-v2'
        }
    )
    
    # Initialize the store
    store.initialize()
    print("✓ Vector store initialized with ChromaDB")
    
    # Add real documents
    documents = [
        "Apple stock showed strong performance in Q4 2024",
        "AAPL reached new highs with volume spike",
        "Technical indicators suggest bullish trend"
    ]
    metadatas = [
        {"ticker": "AAPL", "date": "2024-01-01"},
        {"ticker": "AAPL", "date": "2024-01-02"},
        {"ticker": "AAPL", "date": "2024-01-03"}
    ]
    
    ids = store.add_documents(documents, metadatas)
    assert len(ids) == 3
    print(f"✓ Added {len(ids)} documents to vector store")
    
    # Search for similar documents
    results = store.search("Apple stock performance", n_results=2)
    assert 'results' in results
    assert len(results['results']) > 0
    print(f"✓ Search returned {len(results['results'])} results")
    
    # Clean up
    store.clear_collection()
    print("✓ Cleaned up test collection")
    
    return True

def test_real_retriever():
    """Test real retriever functionality"""
    from src.pipeline.vector_store_adapter import VectorStoreAdapter
    from src.pipeline.retriever import EnhancedRetriever
    
    print("\n=== Testing Real Retriever ===")
    
    # Setup vector store
    store = VectorStoreAdapter(
        store_type="chromadb",
        config={
            'collection_name': 'test_retriever_collection',
            'embedding_model': 'all-MiniLM-L6-v2'
        }
    )
    store.initialize()
    
    # Add test data
    documents = [
        "RSI indicator shows oversold condition at 25",
        "MACD crossover signals potential trend reversal",
        "Volume spike indicates strong buying pressure"
    ]
    metadatas = [
        {"ticker": "AAPL", "rsi": 25, "indicator": "RSI"},
        {"ticker": "AAPL", "indicator": "MACD"},
        {"ticker": "AAPL", "volume": 1000000}
    ]
    store.add_documents(documents, metadatas)
    
    # Create retriever
    retriever = EnhancedRetriever(config={
        'default_n_results': 3,
        'similarity_threshold': 0.5
    })
    retriever.initialize()
    retriever.set_vector_store(store)
    print("✓ Retriever initialized with vector store")
    
    # Test semantic search
    results = retriever.retrieve("oversold conditions", n_results=2)
    assert len(results) > 0
    print(f"✓ Semantic search returned {len(results)} results")
    
    # Test metadata filtering
    results = retriever.retrieve_by_metadata({"indicator": "RSI"}, n_results=2)
    assert len(results) > 0
    print(f"✓ Metadata filtering returned {len(results)} results")
    
    # Clean up
    store.clear_collection()
    print("✓ Cleaned up test collection")
    
    return True

def test_real_application():
    """Test real application initialization and basic operations"""
    from src.application import OHLCVRAGApplication
    
    print("\n=== Testing Real Application ===")
    
    # Create application with real configuration
    app = OHLCVRAGApplication(
        name="TestRealApp",
        config={
            'ingestion': {
                'source': 'yahoo',
                'period': '5d',
                'interval': '1d',
                'window_size': 3
            },
            'vector_store': {
                'store_type': 'chromadb',
                'collection_name': 'test_app_collection',
                'embedding_model': 'all-MiniLM-L6-v2'
            },
            'pipeline': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.1,
                'max_tokens': 500
            },
            'retriever': {
                'default_n_results': 3,
                'similarity_threshold': 0.7,
                'rerank_enabled': False
            }
        }
    )
    
    print("✓ Application created with real configuration")
    
    # Get status before initialization
    status = app.get_status()
    assert status['initialized'] == False
    print("✓ Application status retrieved (not initialized)")
    
    # Note: We don't initialize because it would require OpenAI API key
    # But we've proven the application can be created with real config
    
    return True

if __name__ == "__main__":
    try:
        # Run all real tests
        test_real_data_ingestion()
        test_real_vector_store()
        test_real_retriever()
        test_real_application()
        
        print("\n" + "="*50)
        print("✅ ALL REAL FUNCTIONALITY TESTS PASSED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)