"""
Simple test configuration that doesn't require heavy dependencies
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_data():
    """Simple mock data for testing"""
    return {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [104, 105, 106],
        'Volume': [1000000, 1100000, 1200000]
    }


@pytest.fixture
def sample_tickers():
    """Sample ticker symbols for testing"""
    return ['AAPL', 'GOOGL', 'MSFT']


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    store = MagicMock()
    store.add_documents = MagicMock(return_value=True)
    store.similarity_search = MagicMock(return_value=[])
    store.search_by_date_range = MagicMock(return_value=[])
    return store


@pytest.fixture
def mock_llm():
    """Mock LLM for testing RAG pipeline"""
    llm = MagicMock()
    llm.invoke = MagicMock(return_value="Test response from LLM")
    return llm