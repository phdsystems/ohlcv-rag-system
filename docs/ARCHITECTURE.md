# System Architecture

## Overview

The OHLCV RAG System is built with a modular, object-oriented architecture that emphasizes separation of concerns, extensibility, and maintainability. The system follows SOLID principles and uses design patterns to ensure clean, testable code.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   API    │  │  Docker  │  │    UI    │   │
│  │(main_oop)│  │ (Future) │  │ Compose  │  │ (Future) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼──────────────┼──────────────┼────────┘
        │             │              │              │
┌───────▼─────────────▼──────────────▼──────────────▼────────┐
│                    Application Layer                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │          OHLCVRAGApplication (Orchestrator)        │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │     │
│  │  │  State   │  │  Config  │  │  Logger  │        │     │
│  │  │  Manager │  │  Manager │  │  System  │        │     │
│  │  └──────────┘  └──────────┘  └──────────┘        │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                      Business Logic Layer                     │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Data Ingestion  │  │   RAG Pipeline    │                 │
│  │     Engine       │  │                   │                 │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                 │
│  │ │ Data Sources │ │  │ │  Retriever   │ │                 │
│  │ │   Adapters   │ │  │ ├──────────────┤ │                 │
│  │ ├──────────────┤ │  │ │   Augmentor  │ │                 │
│  │ │  Indicators  │ │  │ ├──────────────┤ │                 │
│  │ │  Calculator  │ │  │ │   Generator  │ │                 │
│  │ ├──────────────┤ │  │ └──────────────┘ │                 │
│  │ │    Chunk     │ │  └──────────────────┘                 │
│  │ │   Creator    │ │                                        │
│  │ └──────────────┘ │                                        │
│  └──────────────────┘                                        │
└───────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                        Data Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Vector Store    │  │   File System    │                 │
│  │     Manager      │  │                   │                 │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                 │
│  │ │  ChromaDB    │ │  │ │  CSV Files   │ │                 │
│  │ ├──────────────┤ │  │ ├──────────────┤ │                 │
│  │ │  Weaviate    │ │  │ │  JSON Chunks │ │                 │
│  │ ├──────────────┤ │  │ ├──────────────┤ │                 │
│  │ │   Qdrant     │ │  │ │     Logs     │ │                 │
│  │ ├──────────────┤ │  │ └──────────────┘ │                 │
│  │ │    FAISS     │ │  └──────────────────┘                 │
│  │ ├──────────────┤ │                                        │
│  │ │   Milvus     │ │                                        │
│  │ └──────────────┘ │                                        │
│  └──────────────────┘                                        │
└───────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Layer

#### OHLCVRAGApplication
**Location**: `src/application.py`

The main orchestrator that coordinates all system components:

```python
class OHLCVRAGApplication(BaseComponent):
    - Manages component lifecycle
    - Handles configuration
    - Coordinates data flow
    - Provides unified API
```

**Responsibilities**:
- Component initialization and dependency injection
- State management across the application
- Error handling and recovery
- Resource cleanup

### 2. Core Module

#### Base Classes and Interfaces
**Location**: `src/core/`

Defines the contracts and base implementations:

```python
src/core/
├── base.py           # BaseComponent, Configurable, DataProcessor
├── interfaces.py     # IDataIngestion, IVectorStore, IRetriever, IRAGPipeline
├── models.py         # OHLCVDataModel, ChunkModel, QueryResult
└── exceptions.py     # Custom exception hierarchy
```

**Key Abstractions**:
- `BaseComponent`: Foundation for all components
- `DataProcessor`: Base for data processing components
- `IRAGPipeline`: Interface for RAG implementations
- `IVectorStore`: Interface for vector databases

### 3. Data Ingestion

#### DataIngestionEngine
**Location**: `src/ingestion/data_ingestion.py`

Handles all data acquisition and preprocessing:

```python
class DataIngestionEngine(DataProcessor, IDataIngestion):
    - Fetches data from multiple sources
    - Calculates technical indicators
    - Creates vector-ready chunks
    - Validates and cleans data
```

**Components**:
- `DataSourceManager`: Factory for data adapters
- `TechnicalIndicatorCalculator`: Computes 15+ indicators
- `ChunkCreator`: Creates overlapping data windows
- `DataValidator`: Ensures data quality

### 4. RAG Pipeline

#### RAGPipeline
**Location**: `src/pipeline/rag_pipeline.py`

Implements the Retrieval-Augmented Generation flow:

```python
class RAGPipeline(BaseComponent, IRAGPipeline):
    - Processes queries through RAG flow
    - Manages prompt templates
    - Handles response generation
    - Implements caching
```

**Sub-components**:
- `EnhancedRetriever`: Advanced retrieval strategies
- `PromptManager`: Query-specific prompts
- `ContextFormatter`: Structures retrieved data
- `ResponseEvaluator`: Assesses response quality
- `AnalysisEngine`: Specialized analysis types

### 5. Vector Store Management

#### VectorStoreManager
**Location**: `src/vector_stores/vector_store_manager.py`

Provides unified interface to multiple vector databases:

```python
class VectorStoreManager:
    - Abstracts vector store operations
    - Enables runtime store switching
    - Handles store-specific configurations
    - Provides store recommendations
```

**Supported Stores**:
- ChromaDB (embedded, default)
- Weaviate (feature-rich)
- Qdrant (high-performance)
- FAISS (large-scale)
- Milvus (enterprise)

## Design Patterns

### 1. Factory Pattern

Used for creating data source adapters and vector stores:

```python
# Data Source Factory
adapter = DataSourceManager.create_adapter("yahoo", config)

# Vector Store Factory
store = VectorStoreManager.create_adapter("chromadb", config)
```

### 2. Strategy Pattern

Different retrieval and analysis strategies:

```python
# Retrieval strategies
retriever.retrieve_by_pattern("uptrend")
retriever.retrieve_by_indicator("RSI", ">", 70)
retriever.retrieve_by_similarity(reference)
```

### 3. Template Method Pattern

Base classes define algorithm structure:

```python
class DataProcessor(BaseComponent):
    def process(self, data):
        preprocessed = self.preprocess(data)
        result = self.process_core(preprocessed)
        return self.postprocess(result)
```

### 4. Adapter Pattern

Uniform interface for diverse data sources:

```python
class DataSourceAdapter(ABC):
    @abstractmethod
    def fetch(self, symbol, **kwargs): pass
    
class YahooFinanceAdapter(DataSourceAdapter):
    def fetch(self, symbol, **kwargs):
        # Yahoo-specific implementation
```

### 5. Singleton Pattern

Application state management:

```python
class ApplicationState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## Data Flow

### 1. Data Ingestion Flow

```
User Request
    │
    ▼
DataIngestionEngine
    │
    ├─→ DataSourceManager.create_adapter()
    │      │
    │      ▼
    │   Fetch from Source (Yahoo/Alpha Vantage/etc)
    │      │
    │      ▼
    │   Validate Data
    │      │
    │      ▼
    ├─→ TechnicalIndicatorCalculator.calculate_all()
    │      │
    │      ▼
    │   Add RSI, MACD, Bollinger Bands, etc.
    │      │
    │      ▼
    ├─→ ChunkCreator.create_chunks()
    │      │
    │      ▼
    │   Create overlapping windows
    │      │
    │      ▼
    └─→ VectorStoreManager.add_documents()
           │
           ▼
       Store in Vector DB
```

### 2. Query Processing Flow

```
User Query
    │
    ▼
RAGPipeline.query()
    │
    ├─→ Parse Query Type
    │
    ├─→ EnhancedRetriever.retrieve()
    │      │
    │      ├─→ Generate Query Embedding
    │      ├─→ Search Vector Store
    │      ├─→ Apply Filters
    │      └─→ Rank Results
    │
    ├─→ ContextFormatter.format()
    │      │
    │      └─→ Structure Retrieved Chunks
    │
    ├─→ PromptManager.get_prompt()
    │      │
    │      └─→ Select Template by Query Type
    │
    ├─→ LLM.generate()
    │      │
    │      └─→ Generate Response with Context
    │
    └─→ ResponseEvaluator.evaluate()
           │
           └─→ Assess Quality & Confidence
```

## Configuration Management

### Environment-Based Configuration

```python
# .env file
OPENAI_API_KEY=sk-...
DATA_SOURCE=yahoo
VECTOR_STORE_TYPE=chromadb
LLM_MODEL=gpt-3.5-turbo

# Loaded in application
config = {
    'ingestion': {
        'source': os.getenv('DATA_SOURCE', 'yahoo'),
        'interval': os.getenv('DATA_INTERVAL', '1d')
    },
    'vector_store': {
        'store_type': os.getenv('VECTOR_STORE_TYPE', 'chromadb')
    }
}
```

### Component Configuration

Each component accepts configuration during initialization:

```python
ingestion_engine = DataIngestionEngine(
    config={
        'source': 'yahoo',
        'window_size': 30,
        'batch_size': 100
    }
)
```

## Error Handling

### Custom Exception Hierarchy

```python
OHLCVRAGException
├── DataIngestionError
├── VectorStoreError
├── RetrieverError
├── PipelineError
├── ConfigurationError
├── DataValidationError
├── AdapterError
└── LLMError
```

### Error Propagation

```python
try:
    result = app.query(user_query)
except PipelineError as e:
    logger.error(f"Pipeline failed at {e.details['stage']}: {e.message}")
    fallback_result = retriever_only_mode(user_query)
except LLMError as e:
    logger.error(f"LLM failed: {e.message}")
    return cached_result_if_available(user_query)
```

## Scalability Considerations

### 1. Horizontal Scaling

- **Stateless Components**: Most components are stateless
- **Load Balancing**: Multiple app instances behind load balancer
- **Distributed Vector Stores**: Milvus, Weaviate support clustering

### 2. Vertical Scaling

- **Batch Processing**: Configurable batch sizes
- **Streaming**: Support for data streaming (future)
- **Caching**: Multi-level caching strategy

### 3. Performance Optimizations

- **Parallel Processing**: Data fetching and processing
- **Async Operations**: Where applicable
- **Connection Pooling**: For database connections
- **Lazy Loading**: Components loaded on demand

## Security Architecture

### 1. Authentication & Authorization

- API key management for external services
- User authentication (future)
- Role-based access control (future)

### 2. Data Security

- Encryption at rest (vector stores)
- Encryption in transit (HTTPS/TLS)
- Sensitive data masking in logs

### 3. Container Security

- Non-root user execution
- Read-only file systems where possible
- Secret management via environment variables
- Network isolation between services

## Monitoring & Observability

### 1. Logging

```python
# Structured logging
logger.info("Query processed", extra={
    'query_id': query_id,
    'query_type': query_type,
    'processing_time': elapsed,
    'result_count': len(results)
})
```

### 2. Metrics

- Query response times
- Retrieval accuracy
- Cache hit rates
- Error rates by component

### 3. Health Checks

```python
def health_check():
    return {
        'status': 'healthy',
        'components': {
            'ingestion': ingestion_engine.get_status(),
            'vector_store': vector_store.get_status(),
            'pipeline': rag_pipeline.get_status()
        }
    }
```

## Testing Architecture

### 1. Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Focus on business logic

### 2. Integration Tests

- Test component interactions
- Use test databases
- Verify data flow

### 3. End-to-End Tests

- Complete user workflows
- Real data sources (test accounts)
- Performance benchmarks

## Future Architecture Enhancements

### 1. Microservices Migration

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│Ingestion│  │   RAG   │  │   API   │
│ Service │  │ Service │  │ Gateway │
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     └────────────┼────────────┘
                  │
            Message Queue
```

### 2. Event-Driven Architecture

- Event sourcing for data updates
- Real-time processing with Kafka/RabbitMQ
- WebSocket for live updates

### 3. Cloud-Native Features

- Kubernetes deployment
- Service mesh (Istio)
- Serverless functions for specific tasks
- Multi-region deployment

## Development Workflow

### 1. Local Development

```bash
# Standard development
python main_oop.py interactive

# With Docker
make dev
```

### 2. Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

### 3. Deployment

```bash
# Build production image
make build-prod

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Conclusion

The OHLCV RAG System architecture is designed to be:

- **Modular**: Easy to extend and modify
- **Scalable**: Handles growth in data and users
- **Maintainable**: Clear structure and patterns
- **Testable**: Dependency injection and interfaces
- **Flexible**: Supports multiple data sources and vector stores

The architecture follows best practices and is ready for production deployment while remaining simple enough for development and experimentation.