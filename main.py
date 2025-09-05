#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from src.data_ingestion import OHLCVDataIngestion
from src.vector_store import OHLCVVectorStore
from src.retriever import OHLCVRetriever
from src.rag_pipeline import OHLCVRAGPipeline
import json

load_dotenv()

def setup_system():
    print("=" * 60)
    print("OHLCV RAG System Setup")
    print("=" * 60)
    
    # Configuration
    tickers = os.getenv("TICKER_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN").split(",")
    period = os.getenv("DATA_PERIOD", "1y")
    interval = os.getenv("DATA_INTERVAL", "1d")
    data_source = os.getenv("DATA_SOURCE", "yahoo")
    
    # Build adapter configuration based on source
    adapter_config = {}
    if data_source == "alpha_vantage":
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if api_key:
            adapter_config['api_key'] = api_key
    elif data_source == "polygon":
        api_key = os.getenv("POLYGON_API_KEY")
        if api_key:
            adapter_config['api_key'] = api_key
    elif data_source == "csv":
        adapter_config['data_dir'] = os.getenv("CSV_DATA_DIR", "./data/csv")
    
    print(f"\nConfiguration:")
    print(f"- Data Source: {data_source}")
    print(f"- Tickers: {', '.join(tickers)}")
    print(f"- Period: {period}")
    print(f"- Interval: {interval}")
    
    # Step 1: Data Ingestion
    print("\n[1/4] Fetching OHLCV data...")
    ingestion = OHLCVDataIngestion(
        tickers=tickers,
        source=data_source,
        period=period,
        interval=interval,
        adapter_config=adapter_config
    )
    ohlcv_data = ingestion.fetch_ohlcv_data()
    
    if not ohlcv_data:
        print("✗ No data fetched. Please check your internet connection and ticker symbols.")
        return None, None, None
    
    # Save data
    chunks = ingestion.save_data()
    
    # Step 2: Initialize Vector Store
    print("\n[2/4] Initializing vector store...")
    vector_store = OHLCVVectorStore()
    
    # Step 3: Index chunks
    print("\n[3/4] Indexing data chunks...")
    vector_store.clear_collection()  # Clear existing data
    vector_store.index_chunks(chunks)
    
    # Step 4: Initialize retriever and RAG pipeline
    print("\n[4/4] Setting up RAG pipeline...")
    retriever = OHLCVRetriever(vector_store)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("   The RAG pipeline will not work without it.")
        print("   Please set it in your .env file to use LLM features.")
        rag_pipeline = None
    else:
        rag_pipeline = OHLCVRAGPipeline(vector_store, retriever)
        print("✓ RAG pipeline ready with LLM integration")
    
    print("\n✓ System setup complete!")
    
    # Print stats
    stats = vector_store.get_collection_stats()
    print(f"\nVector Store Stats:")
    print(f"- Total chunks indexed: {stats['total_chunks']}")
    print(f"- Embedding model: {stats['embedding_model']}")
    
    return vector_store, retriever, rag_pipeline

def run_examples(vector_store, retriever, rag_pipeline):
    print("\n" + "=" * 60)
    print("Running Example Queries")
    print("=" * 60)
    
    if not rag_pipeline:
        print("\nRunning retrieval-only examples (no LLM)...")
        
        # Example 1: Pattern search
        print("\n📊 Example 1: Finding uptrend patterns")
        results = retriever.retrieve_by_pattern("uptrend", n_results=3)
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  - Ticker: {result['ticker']}")
            print(f"  - Period: {result['period']}")
            print(f"  - Score: {result['relevance_score']:.2f}")
            print(f"  - Trend: {result['metadata']['trend']}")
        
        # Example 2: RSI search
        print("\n📊 Example 2: Finding oversold conditions (RSI < 30)")
        results = retriever.retrieve_by_technical_indicator("RSI", "<", 30, n_results=3)
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  - Ticker: {result['ticker']}")
            print(f"  - Period: {result['period']}")
            if 'indicator_value' in result:
                print(f"  - RSI: {result['indicator_value']:.2f}")
        
        # Example 3: General search
        print("\n📊 Example 3: Searching for high volatility periods")
        results = vector_store.search("high volatility large price swings", n_results=3)
        for i, result in enumerate(results['results'], 1):
            print(f"\n  Result {i}:")
            print(f"  - Ticker: {result['metadata']['ticker']}")
            print(f"  - Period: {result['metadata']['start_date']} to {result['metadata']['end_date']}")
            print(f"  - Volatility: {result['metadata']['volatility']:.4f}")
            
    else:
        print("\nRunning full RAG examples with LLM...")
        
        # Example 1: General market analysis
        print("\n📊 Example 1: Market Analysis Query")
        query = "What are the recent trends in the tech stocks and how volatile have they been?"
        result = rag_pipeline.query(query, query_type="general", n_results=5)
        print(f"Query: {query}")
        print(f"Answer: {result['answer'][:500]}...")
        print(f"Sources used: {result['num_sources']}")
        
        # Example 2: Pattern analysis
        print("\n📊 Example 2: Pattern Recognition")
        result = rag_pipeline.analyze_pattern("breakout", n_results=3)
        print(f"Pattern: Breakout")
        print(f"Analysis: {result['analysis'][:500]}...")
        print(f"Matches found: {result['num_matches']}")
        
        # Example 3: Technical indicator analysis
        print("\n📊 Example 3: Technical Indicator Analysis")
        result = rag_pipeline.analyze_indicators("RSI", ">", 70)
        print(f"Indicator: RSI > 70 (Overbought)")
        print(f"Analysis: {result['analysis'][:500]}...")
        print(f"Periods found: {result['num_matches']}")

def interactive_mode(vector_store, retriever, rag_pipeline):
    print("\n" + "=" * 60)
    print("Interactive Query Mode")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  1. 'query <your question>' - Ask any question about the OHLCV data")
    print("  2. 'pattern <type>' - Analyze patterns (uptrend/downtrend/breakout/reversal)")
    print("  3. 'indicator <name> <condition> <value>' - Search by indicator (e.g., 'RSI > 70')")
    print("  4. 'similar <ticker> <date>' - Find similar historical patterns")
    print("  5. 'stats' - Show vector store statistics")
    print("  6. 'exit' - Exit the program")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
                
            elif user_input.lower() == 'stats':
                stats = vector_store.get_collection_stats()
                print(f"\nVector Store Statistics:")
                for key, value in stats.items():
                    print(f"  - {key}: {value}")
                    
            elif user_input.startswith('query '):
                if not rag_pipeline:
                    print("⚠️  LLM not available. Please set OPENAI_API_KEY in .env file.")
                    continue
                    
                query = user_input[6:]
                print("\nProcessing query...")
                result = rag_pipeline.query(query)
                print(f"\nAnswer:\n{result['answer']}")
                print(f"\nSources: {result['num_sources']} documents used")
                
            elif user_input.startswith('pattern '):
                pattern_type = user_input[8:]
                
                if rag_pipeline:
                    print(f"\nAnalyzing {pattern_type} patterns...")
                    result = rag_pipeline.analyze_pattern(pattern_type)
                    print(f"\nAnalysis:\n{result['analysis']}")
                else:
                    print(f"\nSearching for {pattern_type} patterns...")
                    results = retriever.retrieve_by_pattern(pattern_type, n_results=5)
                    for i, result in enumerate(results[:3], 1):
                        print(f"\n  Result {i}: {result['ticker']} ({result['period']})")
                        print(f"  Score: {result['relevance_score']:.2f}")
                        
            elif user_input.startswith('indicator '):
                parts = user_input[10:].split()
                if len(parts) >= 3:
                    indicator = parts[0]
                    condition = parts[1]
                    threshold = float(parts[2])
                    
                    if rag_pipeline:
                        print(f"\nAnalyzing {indicator} {condition} {threshold}...")
                        result = rag_pipeline.analyze_indicators(indicator, condition, threshold)
                        print(f"\nAnalysis:\n{result['analysis']}")
                    else:
                        print(f"\nSearching for {indicator} {condition} {threshold}...")
                        results = retriever.retrieve_by_technical_indicator(
                            indicator, condition, threshold
                        )
                        for i, result in enumerate(results[:3], 1):
                            print(f"\n  Result {i}: {result['ticker']} ({result['period']})")
                else:
                    print("Invalid format. Use: indicator <name> <condition> <value>")
                    print("Example: indicator RSI > 70")
                    
            elif user_input.startswith('similar '):
                parts = user_input[8:].split()
                if len(parts) >= 2:
                    ticker = parts[0].upper()
                    date = parts[1]
                    
                    if rag_pipeline:
                        print(f"\nFinding patterns similar to {ticker} on {date}...")
                        result = rag_pipeline.find_similar_patterns(ticker, date)
                        print(f"\nAnalysis:\n{result['analysis']}")
                    else:
                        print(f"\nSearching for patterns similar to {ticker} on {date}...")
                        results = retriever.retrieve_similar_patterns(ticker, date)
                        for i, result in enumerate(results[:3], 1):
                            print(f"\n  Result {i}: {result['ticker']} ({result['period']})")
                            print(f"  Score: {result['relevance_score']:.2f}")
                else:
                    print("Invalid format. Use: similar <ticker> <date>")
                    print("Example: similar AAPL 2024-01-15")
                    
            else:
                print("Unknown command. Type 'exit' to quit or try one of the available commands.")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"Error: {e}")

def main():
    # Setup the system
    vector_store, retriever, rag_pipeline = setup_system()
    
    if not vector_store:
        print("\n✗ Setup failed. Exiting...")
        return
    
    # Run examples
    print("\nWould you like to:")
    print("1. Run example queries")
    print("2. Enter interactive mode")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        run_examples(vector_store, retriever, rag_pipeline)
        print("\nWould you like to enter interactive mode? (y/n): ", end="")
        if input().strip().lower() == 'y':
            interactive_mode(vector_store, retriever, rag_pipeline)
    elif choice == "2":
        interactive_mode(vector_store, retriever, rag_pipeline)
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()