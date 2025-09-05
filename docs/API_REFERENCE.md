# API Reference

Complete API documentation for the OHLCV RAG System.

## Table of Contents

- [Application](#application)
- [Data Ingestion](#data-ingestion)
- [RAG Pipeline](#rag-pipeline)
- [Vector Stores](#vector-stores)
- [Data Models](#data-models)
- [Exceptions](#exceptions)

## Application

### OHLCVRAGApplication

Main application class that orchestrates all components.

```python
from src.application import OHLCVRAGApplication
```

#### Constructor

```python
OHLCVRAGApplication(
    name: str = "OHLCVRAGApplication",
    config: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `name`: Application identifier
- `config`: Configuration dictionary with sections for ingestion, vector_store, pipeline, retriever

#### Methods

##### initialize()
```python
def initialize() -> None
```
Initialize all application components. Must be called before using other methods.

**Raises:**
- `OHLCVRAGException`: If initialization fails

##### ingest_data()
```python
def ingest_data(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]
```
Ingest OHLCV data for specified tickers.

**Parameters:**
- `tickers`: List of ticker symbols (e.g., ['AAPL', 'MSFT'])
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format

**Returns:**
```python
{
    'success': bool,
    'tickers': List[str],
    'chunks_created': int,
    'documents_indexed': int,
    'error': Optional[str]
}
```

##### query()
```python
def query(
    query: str,
    query_type: str = "general",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```
Process a query through the RAG pipeline.

**Parameters:**
- `query`: User's question or request
- `query_type`: Type of query ('general', 'pattern', 'comparison', 'prediction', 'technical')
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

##### analyze()
```python
def analyze(
    analysis_type: str,
    tickers: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```
Perform specific analysis.

**Parameters:**
- `analysis_type`: Type of analysis ('pattern', 'trend', 'comparison', 'indicator')
- `tickers`: Optional list of tickers to analyze
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

## Data Ingestion

### DataIngestionEngine

Handles data fetching, processing, and chunk creation.

```python
from src.ingestion import DataIngestionEngine
```

#### Constructor

```python
DataIngestionEngine(
    name: str = "DataIngestionEngine",
    config: Optional[Dict[str, Any]] = None
)
```

**Configuration Options:**
```python
{
    'source': str,          # 'yahoo', 'alpha_vantage', 'polygon', 'csv'
    'interval': str,        # '1d', '1h', '5m', etc.
    'period': str,          # '1y', '6mo', '3mo', etc.
    'window_size': int,     # Chunk window size (default: 30)
    'adapter_config': Dict  # Source-specific configuration
}
```

#### Methods

##### fetch_data()
```python
def fetch_data(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]
```
Fetch OHLCV data for given tickers.

**Returns:** Dictionary mapping tickers to DataFrames with OHLCV data and indicators.

##### add_indicators()
```python
def add_indicators(data: pd.DataFrame) -> pd.DataFrame
```
Add technical indicators to OHLCV data.

**Indicators Added:**
- Moving Averages: SMA(20, 50), EMA(12, 26)
- Momentum: RSI(14)
- Trend: MACD with signal line
- Volatility: Bollinger Bands
- Volume: VWAP
- Price Changes: 1d, 5d, 20d returns

##### create_chunks()
```python
def create_chunks(
    data: Dict[str, pd.DataFrame],
    window_size: int
) -> List[Dict[str, Any]]
```
Create overlapping chunks for vector storage.

**Returns:** List of chunk dictionaries with data, metadata, and summaries.

### TechnicalIndicatorCalculator

Calculates technical indicators for OHLCV data.

```python
from src.ingestion import TechnicalIndicatorCalculator
```

#### Methods

##### calculate_all()
```python
def calculate_all(model: OHLCVDataModel) -> OHLCVDataModel
```
Calculate all indicators for data model.

##### add_to_dataframe()
```python
def add_to_dataframe(df: pd.DataFrame) -> pd.DataFrame
```
Add indicators directly to dataframe.

## RAG Pipeline

### RAGPipeline

Implements the Retrieval-Augmented Generation flow.

```python
from src.pipeline import RAGPipeline
```

#### Constructor

```python
RAGPipeline(
    name: str = "RAGPipeline",
    config: Optional[Dict[str, Any]] = None
)
```

**Configuration:**
```python
{
    'model': str,           # 'gpt-3.5-turbo', 'gpt-4'
    'temperature': float,   # 0.0 to 2.0
    'max_tokens': int,      # Maximum response tokens
    'cache_ttl': int,       # Cache time-to-live in seconds
    'openai_api_key': str   # API key (or from environment)
}
```

#### Methods

##### set_retriever()
```python
def set_retriever(retriever: IRetriever) -> None
```
Set the retriever component.

##### generate_response()
```python
def generate_response(prompt: str, context: str) -> str
```
Generate response using LLM.

##### format_context()
```python
def format_context(chunks: List[Dict[str, Any]]) -> str
```
Format retrieved chunks as context.

##### evaluate_response()
```python
def evaluate_response(
    response: str,
    query: str,
    context: str
) -> Dict[str, Any]
```
Evaluate generated response quality.

**Returns:**
```python
{
    'confidence': float,
    'completeness': float,
    'relevance': float,
    'quality_score': float,
    'issues': List[str]
}
```

### EnhancedRetriever

Advanced retrieval with ranking and filtering.

```python
from src.pipeline import EnhancedRetriever
```

#### Methods

##### retrieve()
```python
def retrieve(
    query: str,
    n_results: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]
```
Retrieve relevant documents.

##### retrieve_by_pattern()
```python
def retrieve_by_pattern(
    pattern_type: str,
    ticker: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]
```
Retrieve documents by pattern type.

**Pattern Types:**
- 'uptrend', 'downtrend'
- 'breakout', 'reversal'
- 'consolidation'

##### retrieve_by_indicator()
```python
def retrieve_by_indicator(
    indicator: str,
    condition: str,
    threshold: float,
    ticker: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]
```
Retrieve by technical indicator conditions.

**Example:**
```python
retriever.retrieve_by_indicator('RSI', '>', 70, ticker='AAPL')
```

## Vector Stores

### VectorStoreManager

Unified interface for vector databases.

```python
from src.vector_stores import VectorStoreManager
```

#### Class Methods

##### create_adapter()
```python
@classmethod
def create_adapter(
    cls,
    store_type: str,
    collection_name: str = "ohlcv_data",
    embedding_model: str = "all-MiniLM-L6-v2",
    config: Optional[Dict[str, Any]] = None
) -> VectorStoreManager
```
Factory method to create vector store adapter.

**Store Types:**
- 'chromadb': Embedded, no server required
- 'weaviate': Feature-rich, optional server
- 'qdrant': High performance
- 'faiss': Large-scale similarity search
- 'milvus': Enterprise, distributed

##### get_available_stores()
```python
@classmethod
def get_available_stores(cls) -> List[str]
```
Get list of available vector stores.

##### get_recommended_store()
```python
@classmethod
def get_recommended_store(
    cls,
    requirements: Dict[str, Any]
) -> str
```
Get recommended store based on requirements.

**Requirements:**
```python
{
    'need_server': bool,
    'need_filtering': bool,
    'need_persistence': bool,
    'scale': str,  # 'small', 'medium', 'large'
    'priority': str  # 'speed', 'accuracy', 'features'
}
```

#### Instance Methods

##### add_documents()
```python
def add_documents(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    ids: Optional[List[str]] = None
) -> List[str]
```
Add documents to vector store.

##### search()
```python
def search(
    query: str,
    n_results: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[SearchResult]
```
Search for similar documents.

##### batch_add_documents()
```python
def batch_add_documents(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    batch_size: int = 100
) -> List[str]
```
Add documents in batches.

## Data Models

### OHLCVDataModel

Model for OHLCV data with indicators.

```python
from src.core.models import OHLCVDataModel

@dataclass
class OHLCVDataModel:
    ticker: str
    data: pd.DataFrame
    interval: str
    period: str
    source: str
    metadata: Dict[str, Any]
    indicators: Dict[str, pd.Series]
    validated: bool
    fetched_at: datetime
```

#### Methods

##### add_indicator()
```python
def add_indicator(name: str, values: pd.Series) -> None
```
Add technical indicator to model.

##### get_statistics()
```python
def get_statistics() -> Dict[str, Any]
```
Get data statistics.

### ChunkModel

Model for data chunks.

```python
from src.core.models import ChunkModel

@dataclass
class ChunkModel:
    id: str
    ticker: str
    start_date: str
    end_date: str
    data: List[Dict[str, Any]]
    summary: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]
    created_at: datetime
```

### QueryResult

Model for query results.

```python
from src.core.models import QueryResult

@dataclass
class QueryResult:
    query: str
    query_type: QueryType
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
    created_at: datetime
```

### AnalysisResult

Model for analysis results.

```python
from src.core.models import AnalysisResult

@dataclass
class AnalysisResult:
    analysis_type: str
    ticker: Optional[str]
    period: Tuple[str, str]
    findings: Dict[str, Any]
    recommendations: List[str]
    risk_factors: List[str]
    confidence_level: str
    metadata: Dict[str, Any]
    created_at: datetime
```

## Exceptions

### Exception Hierarchy

```python
from src.core.exceptions import *

OHLCVRAGException  # Base exception
├── DataIngestionError
├── VectorStoreError
├── RetrieverError
├── PipelineError
├── ConfigurationError
├── DataValidationError
├── AdapterError
└── LLMError
```

### Usage

```python
try:
    result = app.query(user_query)
except PipelineError as e:
    print(f"Pipeline failed: {e.message}")
    print(f"Error code: {e.error_code}")
    print(f"Details: {e.details}")
```

## CLI Interface

### Commands

#### setup
```bash
python main_oop.py setup [options]
```

**Options:**
- `--tickers`: List of tickers (default: AAPL MSFT GOOGL AMZN)
- `--source`: Data source (yahoo, alpha_vantage, polygon, csv)
- `--period`: Time period (1y, 6mo, 3mo, etc.)
- `--interval`: Data interval (1d, 1h, 5m, etc.)

#### query
```bash
python main_oop.py query "question" [options]
```

**Options:**
- `--type`: Query type (general, pattern, comparison, prediction, technical)
- `--n-results`: Number of results to retrieve

#### analyze
```bash
python main_oop.py analyze <analysis_type> [options]
```

**Options:**
- `--tickers`: Tickers to analyze
- `--pattern`: Pattern type for pattern analysis
- `--indicator`: Indicator for indicator analysis

#### interactive
```bash
python main_oop.py interactive
```
Enter interactive query mode.

#### status
```bash
python main_oop.py status
```
Show system status.

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Data Configuration
DATA_SOURCE=yahoo
TICKER_SYMBOLS=AAPL,MSFT,GOOGL
DATA_PERIOD=1y
DATA_INTERVAL=1d
CHUNK_WINDOW_SIZE=30

# Vector Store
VECTOR_STORE_TYPE=chromadb
COLLECTION_NAME=ohlcv_data
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Weaviate
WEAVIATE_MODE=embedded
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Qdrant
QDRANT_MODE=memory
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# FAISS
FAISS_INDEX_TYPE=flat

# Milvus
MILVUS_MODE=lite
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM Settings
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Retrieval
DEFAULT_N_RESULTS=5
SIMILARITY_THRESHOLD=0.7
RERANK_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

## Code Examples

### Basic Usage

```python
from src.application import OHLCVRAGApplication

# Initialize
app = OHLCVRAGApplication()
app.initialize()

# Ingest data
app.ingest_data(['AAPL', 'MSFT'])

# Query
result = app.query("What are the trends?")
print(result['answer'])
```

### Custom Configuration

```python
config = {
    'ingestion': {
        'source': 'alpha_vantage',
        'window_size': 60
    },
    'vector_store': {
        'store_type': 'weaviate',
        'collection_name': 'my_ohlcv_data'
    },
    'pipeline': {
        'model': 'gpt-4',
        'temperature': 0.2
    }
}

app = OHLCVRAGApplication(config=config)
```

### Advanced Retrieval

```python
from src.pipeline import EnhancedRetriever
from src.pipeline import VectorStoreAdapter

# Setup retriever
vector_store = VectorStoreAdapter(config={'store_type': 'qdrant'})
retriever = EnhancedRetriever(config={'similarity_threshold': 0.8})
retriever.set_vector_store(vector_store)

# Pattern retrieval
patterns = retriever.retrieve_by_pattern('breakout', ticker='AAPL')

# Indicator retrieval
overbought = retriever.retrieve_by_indicator('RSI', '>', 70)
```

### Batch Processing

```python
# Process multiple queries
queries = [
    "Trend analysis for AAPL",
    "Support levels for MSFT",
    "Volatility comparison"
]

results = []
for query in queries:
    result = app.query(query)
    results.append(result)
```

## Testing

### Unit Test Example

```python
import pytest
from src.ingestion import DataIngestionEngine

def test_data_ingestion():
    engine = DataIngestionEngine(
        config={'source': 'yahoo', 'window_size': 30}
    )
    engine.initialize()
    
    data = engine.fetch_data(['AAPL'], start_date='2024-01-01')
    assert 'AAPL' in data
    assert not data['AAPL'].empty
```

### Integration Test Example

```python
def test_rag_pipeline():
    app = OHLCVRAGApplication()
    app.initialize()
    
    # Test full flow
    app.ingest_data(['AAPL'])
    result = app.query("What is the trend?")
    
    assert result['success'] is not False
    assert len(result['sources']) > 0
    assert result['confidence'] > 0
```

## Performance Tips

1. **Use batch operations** for multiple documents
2. **Enable caching** for repeated queries
3. **Choose appropriate vector store** for your scale
4. **Optimize chunk size** based on your data
5. **Use filters** to narrow search space

## Migration Guide

### From v1 to v2 (OOP)

```python
# Old way
from src.data_ingestion import OHLCVDataIngestion
ingestion = OHLCVDataIngestion(tickers=['AAPL'])

# New way
from src.application import OHLCVRAGApplication
app = OHLCVRAGApplication()
app.initialize()
app.ingest_data(['AAPL'])
```