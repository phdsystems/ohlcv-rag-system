# RAG Pipeline Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Data Flow](#data-flow)
- [Implementation Details](#implementation-details)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The RAG (Retrieval-Augmented Generation) Pipeline is the core intelligence system of the OHLCV RAG application. It combines vector similarity search with Large Language Models (LLMs) to provide accurate, context-aware analysis of financial market data.

### What is RAG?

RAG is a pattern that enhances LLM responses by:
1. **Retrieving** relevant information from a knowledge base
2. **Augmenting** the user's query with this context
3. **Generating** responses based on both the query and retrieved context

### Why RAG for Financial Data?

- **Accuracy**: Responses are grounded in actual OHLCV data
- **Timeliness**: Analysis based on your specific data timeframe
- **Specificity**: Answers relate to your exact tickers and indicators
- **Reduced Hallucination**: LLM can't invent financial data when given real context

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Architecture                │
└─────────────────────────────────────────────────────────────┘

User Query
    │
    ▼
┌─────────────────┐
│  Query Parser   │ ← Identifies query type & parameters
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│       RETRIEVAL PHASE               │
│ ┌─────────────────────────────────┐ │
│ │   Enhanced Retriever            │ │
│ │   - Semantic Search             │ │
│ │   - Metadata Filtering          │ │
│ │   - Result Ranking              │ │
│ └──────────┬──────────────────────┘ │
│            │                         │
│            ▼                         │
│ ┌─────────────────────────────────┐ │
│ │   Vector Store                  │ │
│ │   - ChromaDB/Weaviate/etc       │ │
│ │   - Embeddings + Metadata       │ │
│ └─────────────────────────────────┘ │
└────────────────┬─────────────────────┘
                 │
                 ▼
         Retrieved Chunks
         (OHLCV data + indicators)
                 │
                 ▼
┌─────────────────────────────────────┐
│      AUGMENTATION PHASE             │
│ ┌─────────────────────────────────┐ │
│ │   Context Formatter             │ │
│ │   - Structure chunks            │ │
│ │   - Add metadata               │ │
│ │   - Format for LLM             │ │
│ └──────────┬──────────────────────┘ │
│            │                         │
│            ▼                         │
│ ┌─────────────────────────────────┐ │
│ │   Prompt Manager                │ │
│ │   - Select template             │ │
│ │   - Insert context              │ │
│ │   - Add instructions            │ │
│ └─────────────────────────────────┘ │
└────────────────┬─────────────────────┘
                 │
                 ▼
           Augmented Prompt
                 │
                 ▼
┌─────────────────────────────────────┐
│       GENERATION PHASE              │
│ ┌─────────────────────────────────┐ │
│ │   LLM (GPT-3.5/GPT-4)          │ │
│ │   - Process context             │ │
│ │   - Generate analysis           │ │
│ │   - Provide insights            │ │
│ └──────────┬──────────────────────┘ │
│            │                         │
│            ▼                         │
│ ┌─────────────────────────────────┐ │
│ │   Response Evaluator            │ │
│ │   - Quality assessment          │ │
│ │   - Confidence scoring          │ │
│ │   - Source tracking             │ │
│ └─────────────────────────────────┘ │
└────────────────┬─────────────────────┘
                 │
                 ▼
           Final Response
                 │
                 ▼
              User
```

## Components

### 1. RAGPipeline Class (`src/pipeline/rag_pipeline.py`)

The main orchestrator that coordinates all pipeline components.

```python
class RAGPipeline(BaseComponent, IRAGPipeline):
    """
    Main RAG pipeline implementing OOP principles
    """
```

**Key Responsibilities:**
- Query processing and routing
- Component coordination
- Response caching
- Error handling

### 2. EnhancedRetriever (`src/pipeline/retriever.py`)

Handles intelligent retrieval of relevant OHLCV data chunks.

```python
class EnhancedRetriever(BaseComponent, IRetriever):
    """
    Enhanced retriever with advanced retrieval strategies
    """
```

**Features:**
- Semantic similarity search
- Metadata filtering (ticker, date range, indicators)
- Result ranking and reranking
- Pattern-specific retrieval

### 3. PromptManager

Manages different prompt templates for various query types.

```python
class PromptManager:
    """Manage prompts for different query types"""
```

**Query Types:**
- `general`: Open-ended market analysis
- `pattern`: Pattern recognition (uptrend, breakout, etc.)
- `comparison`: Multi-ticker comparison
- `prediction`: Technical analysis predictions
- `technical`: Indicator-specific analysis

### 4. ContextFormatter

Formats retrieved chunks into structured context for the LLM.

```python
class ContextFormatter:
    """Format context for LLM consumption"""
```

**Formatting includes:**
- Chunk metadata (ticker, period, relevance)
- Key metrics (trend, volume, volatility)
- Technical indicators (RSI, MACD, etc.)

### 5. ResponseEvaluator

Evaluates the quality of generated responses.

```python
class ResponseEvaluator:
    """Evaluate LLM response quality"""
```

**Evaluation Metrics:**
- Completeness
- Relevance
- Confidence score
- Quality assessment

## Data Flow

### 1. Query Processing Flow

```python
User Query: "What are the recent trends in tech stocks?"
    │
    ├─→ Parse query type: "general"
    ├─→ Extract entities: ["tech stocks", "trends", "recent"]
    └─→ Set retrieval parameters: n_results=5, filters=None
```

### 2. Retrieval Flow

```python
Retrieval Request
    │
    ├─→ Generate query embedding
    ├─→ Search vector store
    ├─→ Apply similarity threshold (0.7)
    ├─→ Rerank results
    └─→ Return top N chunks

Example Retrieved Chunk:
{
    'ticker': 'AAPL',
    'period': '2024-01-01 to 2024-01-30',
    'summary': 'AAPL showed strong uptrend...',
    'metadata': {
        'trend': 'uptrend',
        'avg_volume': 75000000,
        'volatility': 0.023,
        'rsi_avg': 65.4
    },
    'relevance_score': 0.89
}
```

### 3. Context Generation Flow

```python
Retrieved Chunks → Context Formatter
    │
    └─→ Formatted Context:
        """
        Source 1:
        Ticker: AAPL
        Period: 2024-01-01 to 2024-01-30
        Relevance Score: 0.89
        
        AAPL showed strong uptrend with RSI at 65.4
        
        Key Metrics:
        - Trend: uptrend
        - Average Volume: 75,000,000
        - Volatility: 0.0230
        - Price Range: $180.50 - $195.20
        - Average RSI: 65.40
        """
```

### 4. Response Generation Flow

```python
Augmented Prompt → LLM
    │
    └─→ Generated Response:
        """
        Based on the recent OHLCV data for tech stocks:
        
        1. AAPL shows a strong uptrend with healthy momentum
           - RSI at 65.4 indicates bullish but not overbought
           - Volume averaging 75M shares shows strong interest
           
        2. Technical indicators suggest continuation...
        """
```

## Implementation Details

### Query Processing

```python
def query(self, query: str, query_type: str = "general",
         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a query through the RAG pipeline
    """
    # 1. Validate and parse query
    q_type = QueryType(query_type.lower())
    
    # 2. Retrieve relevant context
    retrieved_chunks = self.retriever.retrieve(
        query, 
        n_results=context.get('n_results', 5),
        filters=context.get('filters')
    )
    
    # 3. Format context
    formatted_context = self.format_context(retrieved_chunks)
    
    # 4. Generate response
    prompt = self.prompt_manager.get_prompt(q_type, query, formatted_context)
    response = self.generate_response(prompt, formatted_context)
    
    # 5. Evaluate and return
    evaluation = self.evaluate_response(response, query, formatted_context)
    
    return QueryResult(
        query=query,
        answer=response,
        sources=retrieved_chunks,
        confidence=evaluation['confidence']
    )
```

### Retrieval Strategies

#### Semantic Search
```python
# Uses embedding similarity for conceptual matching
query = "bullish momentum indicators"
# Finds chunks with similar meaning, not just keyword matches
```

#### Metadata Filtering
```python
# Filter by specific criteria
filters = {
    'ticker': 'AAPL',
    'trend': 'uptrend',
    'rsi_avg': {'$gte': 60}
}
```

#### Pattern-Specific Retrieval
```python
# Specialized queries for patterns
retriever.retrieve_by_pattern('breakout', ticker='MSFT')
```

### Prompt Engineering

#### General Analysis Template
```python
"""
You are a financial analyst assistant specializing in technical analysis of OHLCV data.

Based on the following retrieved OHLCV data and technical indicators:

{context}

Please answer the following question:
{query}

Provide a detailed analysis including:
1. Key observations from the data
2. Relevant patterns or trends
3. Technical indicator insights
4. Potential implications for traders
5. Risk considerations if applicable

Base your answer strictly on the provided data.
"""
```

#### Pattern Recognition Template
```python
"""
Analyze the following OHLCV data for {pattern_type} patterns:

{context}

Provide:
1. Confirmation of whether the {pattern_type} pattern is present
2. Strength of the pattern (weak/moderate/strong)
3. Key supporting indicators
4. Entry/exit points if applicable
5. Risk/reward considerations
"""
```

## Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
OPENAI_API_KEY=your-api-key

# Retrieval Configuration
DEFAULT_N_RESULTS=5
SIMILARITY_THRESHOLD=0.7
RERANK_ENABLED=true

# Caching
CACHE_TTL=3600  # 1 hour
```

### Pipeline Configuration

```python
config = {
    'pipeline': {
        'model': 'gpt-3.5-turbo',
        'temperature': 0.1,
        'max_tokens': 2000,
        'cache_ttl': 3600
    },
    'retriever': {
        'default_n_results': 5,
        'similarity_threshold': 0.7,
        'rerank_enabled': True
    }
}

pipeline = RAGPipeline(config=config['pipeline'])
```

## Usage Examples

### Basic Query

```python
from src.application import OHLCVRAGApplication

# Initialize application
app = OHLCVRAGApplication()
app.initialize()

# Simple market analysis
result = app.query(
    "What are the recent trends in AAPL?",
    query_type="general"
)

print(result['answer'])
```

### Pattern Analysis

```python
# Analyze specific patterns
result = app.query(
    "Show me breakout patterns",
    query_type="pattern",
    context={'pattern_type': 'breakout', 'n_results': 10}
)

print(f"Found {len(result['sources'])} potential breakouts")
print(result['answer'])
```

### Indicator Analysis

```python
# Analyze technical indicators
result = app.analyze(
    analysis_type="indicator",
    parameters={
        'indicators': ['RSI', 'MACD'],
        'condition': 'overbought'
    }
)

print(result['findings'])
```

### Comparison Query

```python
# Compare multiple tickers
result = app.query(
    "Compare the performance of AAPL, MSFT, and GOOGL",
    query_type="comparison",
    context={'tickers': ['AAPL', 'MSFT', 'GOOGL']}
)

print(result['answer'])
```

### Custom Retrieval

```python
# Direct retrieval with custom parameters
retriever = EnhancedRetriever(config={'similarity_threshold': 0.8})
retriever.set_vector_store(vector_store)

# Retrieve by specific pattern
chunks = retriever.retrieve_by_pattern(
    pattern_type='uptrend',
    ticker='AAPL',
    n_results=5
)

# Retrieve by indicator condition
chunks = retriever.retrieve_by_indicator(
    indicator='RSI',
    condition='above',
    threshold=70,
    ticker='MSFT'
)
```

## API Reference

### RAGPipeline Methods

#### query()
```python
def query(
    query: str,
    query_type: str = "general",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `query`: User's question or request
- `query_type`: Type of query (general, pattern, comparison, prediction, technical)
- `context`: Additional context (n_results, filters, parameters)

**Returns:**
```python
{
    'query': str,
    'query_type': str,
    'answer': str,
    'sources': List[Dict],
    'confidence': float,
    'processing_time': float,
    'metadata': Dict
}
```

#### analyze()
```python
def analyze(
    analysis_type: str,
    data: Any,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `analysis_type`: Type of analysis (pattern, trend, comparison, indicator)
- `data`: Data to analyze
- `parameters`: Analysis-specific parameters

**Returns:**
```python
{
    'analysis_type': str,
    'ticker': Optional[str],
    'period': Tuple[str, str],
    'findings': Dict,
    'recommendations': List[str],
    'risk_factors': List[str],
    'confidence_level': str
}
```

### EnhancedRetriever Methods

#### retrieve()
```python
def retrieve(
    query: str,
    n_results: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]
```

#### retrieve_by_pattern()
```python
def retrieve_by_pattern(
    pattern_type: str,
    ticker: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]
```

#### retrieve_by_indicator()
```python
def retrieve_by_indicator(
    indicator: str,
    condition: str,
    threshold: float,
    ticker: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]
```

## Best Practices

### 1. Query Formulation

**Good Queries:**
- "What is the trend for AAPL in the last month?"
- "Show me stocks with RSI above 70"
- "Compare volatility between tech stocks"

**Poor Queries:**
- "Stock?" (too vague)
- "Everything about AAPL" (too broad)
- "Predict exact price" (beyond capability)

### 2. Context Management

```python
# Provide specific context for better results
context = {
    'n_results': 10,  # More context for complex queries
    'filters': {
        'ticker': 'AAPL',
        'start_date': '2024-01-01'
    }
}
```

### 3. Result Interpretation

```python
# Check confidence and sources
if result['confidence'] > 0.7:
    print("High confidence analysis:")
    print(result['answer'])
    print(f"Based on {len(result['sources'])} data points")
else:
    print("Low confidence - consider gathering more data")
```

### 4. Performance Optimization

```python
# Use caching for repeated queries
pipeline.config['cache_ttl'] = 7200  # 2 hours

# Batch similar queries
queries = ["AAPL trend", "MSFT trend", "GOOGL trend"]
results = [app.query(q) for q in queries]
```

### 5. Error Handling

```python
try:
    result = app.query(query)
except PipelineError as e:
    print(f"Pipeline error: {e.message}")
    print(f"Stage: {e.details.get('stage')}")
except LLMError as e:
    print(f"LLM error: {e.message}")
    # Fallback to retrieval-only mode
```

## Troubleshooting

### Common Issues

#### 1. No Results Returned

**Problem:** Query returns empty results

**Solutions:**
- Lower similarity threshold: `config['similarity_threshold'] = 0.5`
- Broaden search terms
- Check if data is properly indexed
- Verify ticker symbols are correct

#### 2. Generic Responses

**Problem:** LLM gives generic answers not based on data

**Solutions:**
- Ensure retrieval is working: check `result['sources']`
- Increase `n_results` to provide more context
- Make queries more specific
- Check if context formatting is correct

#### 3. Slow Response Time

**Problem:** Queries take too long

**Solutions:**
- Enable caching: `config['cache_ttl'] = 3600`
- Reduce `n_results` for faster retrieval
- Use smaller embedding model
- Consider using GPT-3.5 instead of GPT-4

#### 4. API Rate Limits

**Problem:** OpenAI API rate limit errors

**Solutions:**
- Implement exponential backoff
- Use response caching
- Batch queries when possible
- Consider upgrading API tier

#### 5. Out of Context

**Problem:** Response doesn't match the time period of data

**Solutions:**
- Add date filters to retrieval
- Include date range in query
- Update prompts to emphasize temporal context

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check pipeline status
status = app.get_status()
print(f"Pipeline status: {status['components']['pipeline']}")

# Inspect retrieved chunks
result = app.query(query)
for chunk in result['sources']:
    print(f"Chunk: {chunk['ticker']} - {chunk['period']}")
    print(f"Score: {chunk['relevance_score']}")
```

### Performance Metrics

```python
# Monitor pipeline performance
stats = app.get_status()['state']['statistics']

print(f"Total queries: {stats['total_queries']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg response time: {stats.get('avg_response_time', 'N/A')}")

# Check retriever stats
retriever_stats = retriever.get_status()['statistics']
print(f"Avg results returned: {retriever_stats['avg_results_returned']}")
```

## Advanced Topics

### Custom Prompt Templates

```python
# Add custom prompt for specific analysis
custom_prompt = PromptTemplate(
    input_variables=["context", "query"],
    template="""
    As a quantitative analyst, analyze the following data:
    {context}
    
    Question: {query}
    
    Provide statistical analysis with specific numbers.
    """
)

pipeline.prompt_manager.prompts['quantitative'] = custom_prompt
```

### Retrieval Strategies

```python
# Implement custom ranking
class CustomRanker(ResultRanker):
    def _calculate_score(self, result, query):
        # Custom scoring logic
        base_score = super()._calculate_score(result, query)
        
        # Boost recent data
        recency_boost = self._calculate_recency_score(result) * 0.3
        
        # Boost high volume periods
        volume = result.get('metadata', {}).get('avg_volume', 0)
        volume_boost = min(volume / 100000000, 1.0) * 0.2
        
        return base_score + recency_boost + volume_boost
```

### Multi-Stage Retrieval

```python
# Implement two-stage retrieval for complex queries
def multi_stage_retrieve(query, initial_n=20, final_n=5):
    # Stage 1: Broad retrieval
    broad_results = retriever.retrieve(
        query, 
        n_results=initial_n,
        filters=None
    )
    
    # Stage 2: Rerank and filter
    refined_results = ranker.rank(broad_results, query)[:final_n]
    
    return refined_results
```

### Response Post-Processing

```python
# Add post-processing for structured output
def structure_response(raw_response):
    return {
        'summary': extract_summary(raw_response),
        'key_points': extract_bullet_points(raw_response),
        'metrics': extract_numbers(raw_response),
        'recommendations': extract_recommendations(raw_response),
        'risks': extract_risks(raw_response)
    }
```

## Conclusion

The RAG Pipeline is the intelligence layer of the OHLCV RAG System, combining the precision of vector search with the analytical power of LLMs. By grounding responses in actual financial data, it provides accurate, relevant, and timely market analysis.

Key takeaways:
- RAG ensures factual accuracy by using your actual OHLCV data
- The pipeline is highly configurable and extensible
- Proper query formulation and context management improve results
- Caching and optimization techniques enhance performance
- The OOP architecture makes it easy to customize and extend

For more information, see:
- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Vector Store Documentation](./VECTOR_STORES.md)