# Vector Store Adapters Documentation

The OHLCV RAG System now supports **5 open-source vector databases** through a pluggable adapter system. You can easily switch between different vector stores based on your requirements.

## 🚀 Quick Start

```python
# In .env file
VECTOR_STORE_TYPE=chromadb  # Options: chromadb, weaviate, qdrant, faiss, milvus

# Or programmatically
from src.vector_stores import VectorStoreManager

# Create any vector store
adapter = VectorStoreManager.create_adapter(
    store_type="chromadb",  # or weaviate, qdrant, faiss, milvus
    collection_name="ohlcv_data",
    embedding_model="all-MiniLM-L6-v2"
)
```

## 📊 Comparison Table

| Feature | ChromaDB | Weaviate | Qdrant | FAISS | Milvus |
|---------|----------|----------|--------|-------|--------|
| **License** | Apache 2.0 | BSD-3 | Apache 2.0 | MIT | Apache 2.0 |
| **Language** | Python | Go | Rust | C++ | Go/C++ |
| **Requires Server** | ❌ No | Optional | Optional | ❌ No | Optional |
| **Embedded Mode** | ✅ Yes | ✅ Yes | ❌ No* | ✅ Yes | ✅ Yes |
| **Cloud Option** | ❌ No | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **GPU Support** | ❌ No | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Metadata Filtering** | ✅ Yes | ✅ Yes | ✅ Yes | Limited | ✅ Yes |
| **Update Support** | ✅ Yes | ✅ Yes | ✅ Yes | Limited | Limited |
| **Best For** | Dev/Small | Production | High Perf | Large Scale | Enterprise |

*Qdrant has in-memory mode but not true embedded

## 🔧 Available Vector Stores

### 1. ChromaDB (Default)

**Best for:** Local development, small to medium datasets, simplicity

```python
# Configuration
config = {
    'persist_directory': './data/chroma_db'
}

adapter = VectorStoreManager.create_adapter(
    store_type="chromadb",
    config=config
)
```

**Features:**
- No server required
- Automatic persistence
- Simple setup
- Good metadata filtering

**Environment Variables:**
```bash
VECTOR_STORE_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
```

### 2. Weaviate

**Best for:** Production systems, GraphQL users, feature-rich applications

```python
# Embedded mode (no server)
config = {'mode': 'embedded'}

# Local server
config = {
    'mode': 'local',
    'url': 'http://localhost:8080'
}

# Cloud
config = {
    'mode': 'cloud',
    'url': 'https://your-cluster.weaviate.network',
    'api_key': 'your-api-key'
}
```

**Features:**
- GraphQL API
- Hybrid search
- Multi-tenancy
- Embedded or server mode

**Environment Variables:**
```bash
VECTOR_STORE_TYPE=weaviate
WEAVIATE_MODE=embedded  # or local, cloud
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-key  # for cloud
```

### 3. Qdrant

**Best for:** High performance, production systems, advanced filtering

```python
# In-memory mode (testing)
config = {'mode': 'memory'}

# Local persistent
config = {
    'mode': 'local',
    'path': './data/qdrant_db'
}

# Remote server
config = {
    'mode': 'remote',
    'url': 'http://localhost:6333',
    'api_key': 'optional-api-key'
}
```

**Features:**
- Written in Rust (very fast)
- Advanced filtering
- Snapshot support
- REST and gRPC APIs

**Environment Variables:**
```bash
VECTOR_STORE_TYPE=qdrant
QDRANT_MODE=memory  # or local, remote
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-key  # optional
```

### 4. FAISS

**Best for:** Large-scale similarity search, research, speed priority

```python
config = {
    'persist_directory': './data/faiss_db',
    'index_type': 'flat'  # or 'ivf', 'hnsw'
}
```

**Index Types:**
- `flat`: Exact search, slowest but most accurate
- `ivf`: Inverted file index, faster for large datasets
- `hnsw`: Hierarchical Navigable Small World, good balance

**Features:**
- Fastest similarity search
- GPU acceleration support
- Multiple index types
- Facebook/Meta maintained

**Environment Variables:**
```bash
VECTOR_STORE_TYPE=faiss
FAISS_INDEX_TYPE=flat  # or ivf, hnsw
```

### 5. Milvus

**Best for:** Large-scale production, distributed systems, enterprise

```python
# Embedded Lite mode (no server)
config = {
    'mode': 'lite',
    'uri': './data/milvus_lite.db'
}

# Standalone server
config = {
    'mode': 'standalone',
    'host': 'localhost',
    'port': 19530,
    'user': 'username',  # optional
    'password': 'password'  # optional
}
```

**Features:**
- Distributed architecture
- GPU acceleration
- Time Travel queries
- Partition support
- High availability

**Environment Variables:**
```bash
VECTOR_STORE_TYPE=milvus
MILVUS_MODE=lite  # or standalone, cluster
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## 🎯 Choosing the Right Vector Store

### Decision Tree

```
Need GPU acceleration?
├─ Yes → FAISS or Milvus
└─ No → Continue
    │
    Need a server?
    ├─ No (embedded only) → ChromaDB or FAISS
    └─ Yes/Optional → Continue
        │
        Scale requirement?
        ├─ Small (<100k vectors) → ChromaDB
        ├─ Medium (<1M vectors) → Weaviate or Qdrant
        └─ Large (>1M vectors) → Milvus or FAISS
```

### Recommendations by Use Case

| Use Case | Recommended | Why |
|----------|-------------|-----|
| **Local Development** | ChromaDB | Simple, no server, auto-persist |
| **Prototyping** | ChromaDB or Qdrant (memory) | Quick setup |
| **Production API** | Weaviate or Qdrant | Features, reliability |
| **High Performance** | Qdrant or FAISS | Speed optimized |
| **Large Scale** | Milvus or FAISS | Designed for scale |
| **Research** | FAISS | Flexible, GPU support |
| **Enterprise** | Milvus | Distributed, HA |

## 💻 Installation

### Basic (ChromaDB only)
```bash
uv sync  # Includes ChromaDB by default
```

### All Vector Stores
```bash
# Install all vector store dependencies
uv sync

# Or install specific ones
pip install weaviate-client  # Weaviate
pip install qdrant-client    # Qdrant
pip install faiss-cpu        # FAISS (CPU)
pip install faiss-gpu        # FAISS (GPU)
pip install pymilvus         # Milvus
```

## 🔄 Switching Vector Stores

### Method 1: Environment Variable
```bash
# In .env file
VECTOR_STORE_TYPE=weaviate  # Switch to Weaviate

# Run normally
uv run python main.py
```

### Method 2: Programmatic
```python
from src.vector_stores import VectorStoreManager

# Get recommendation based on requirements
store_type = VectorStoreManager.get_recommended_store({
    'need_server': False,
    'need_filtering': True,
    'scale': 'medium',
    'priority': 'balance'
})
# Returns: 'chromadb'

# Create the recommended store
adapter = VectorStoreManager.create_adapter(store_type)
```

### Method 3: Runtime Comparison
```python
# Compare all stores
comparison = VectorStoreManager.compare_stores()
for store, info in comparison.items():
    print(f"{store}: Best for {info['best_for']}")

# Get info about specific store
info = VectorStoreManager.get_store_info('qdrant')
print(f"Qdrant features: {info['features']}")
```

## 📝 API Usage

All adapters follow the same interface:

```python
from src.vector_stores import VectorStoreManager

# Create adapter
adapter = VectorStoreManager.create_adapter("chromadb")

# Add documents
ids = adapter.add_documents(
    documents=["Doc 1", "Doc 2"],
    metadatas=[{"key": "value1"}, {"key": "value2"}]
)

# Search
results = adapter.search(
    query="Find similar documents",
    n_results=5,
    filter_dict={"key": "value1"}
)

# Update documents
adapter.update_documents(
    ids=ids,
    documents=["Updated doc 1", "Updated doc 2"]
)

# Delete documents
adapter.delete_documents(ids)

# Get statistics
count = adapter.get_document_count()
info = adapter.get_adapter_info()
```

## 🐳 Docker Setup

### ChromaDB (Embedded) - No Docker needed

### Weaviate
```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  semitechnologies/weaviate:latest
```

### Qdrant
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/data/qdrant:/qdrant/storage \
  qdrant/qdrant
```

### Milvus
```bash
# Download docker-compose
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.yml

# Start Milvus
docker-compose -f docker/docker-compose.yml up -d
```

## 🚨 Troubleshooting

### ChromaDB Issues
- **Persistence not working**: Check directory permissions
- **Slow on large datasets**: Consider switching to FAISS or Qdrant

### Weaviate Issues
- **Embedded mode fails**: Requires Java 11+ installed
- **Connection refused**: Check if server is running

### Qdrant Issues
- **Memory mode loses data**: Expected behavior, use local/remote for persistence
- **Filtering not working**: Check filter syntax matches Qdrant format

### FAISS Issues
- **No GPU acceleration**: Install faiss-gpu instead of faiss-cpu
- **Updates not working**: FAISS has limited update support, may need to rebuild index

### Milvus Issues
- **Lite mode limitations**: Some features only in server mode
- **Connection failed**: Check if Milvus server is running

## 🔮 Future Additions

Potential vector stores to add:
- **Vespa** - Yahoo's search engine
- **Elasticsearch** - With vector search plugin
- **OpenSearch** - AWS fork of Elasticsearch
- **Typesense** - Simple alternative
- **LanceDB** - Rust-based embedded DB

## 📚 Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [Weaviate Docs](https://weaviate.io/developers/weaviate)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [Milvus Docs](https://milvus.io/docs)

## License

All implemented vector stores are open source:
- ChromaDB: Apache 2.0
- Weaviate: BSD-3-Clause
- Qdrant: Apache 2.0
- FAISS: MIT
- Milvus: Apache 2.0