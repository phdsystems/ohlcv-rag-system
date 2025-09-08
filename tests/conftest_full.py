import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import tempfile
import os
from unittest.mock import MagicMock


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(150, 250, len(dates)),
        'Low': np.random.uniform(50, 150, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    })
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    return data


@pytest.fixture
def sample_tickers():
    """Sample ticker symbols for testing"""
    return ['AAPL', 'GOOGL', 'MSFT']


@pytest.fixture
def mock_api_response():
    """Mock API response for testing data adapters"""
    return {
        'AAPL': {
            'prices': [
                {'date': '2024-01-01', 'open': 150.0, 'high': 155.0, 'low': 149.0, 'close': 154.0, 'volume': 5000000},
                {'date': '2024-01-02', 'open': 154.0, 'high': 158.0, 'low': 153.0, 'close': 157.0, 'volume': 6000000},
            ]
        }
    }


@pytest.fixture
def temp_csv_file(sample_ohlcv_data):
    """Create a temporary CSV file with sample OHLCV data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_ohlcv_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)


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


@pytest.fixture
def sample_documents():
    """Sample documents for vector store testing"""
    return [
        {
            'ticker': 'AAPL',
            'date': '2024-01-01',
            'close': 150.0,
            'volume': 5000000,
            'rsi': 55.0,
            'macd': 0.5,
            'content': 'AAPL technical analysis for 2024-01-01'
        },
        {
            'ticker': 'GOOGL',
            'date': '2024-01-01',
            'close': 2800.0,
            'volume': 2000000,
            'rsi': 60.0,
            'macd': 1.2,
            'content': 'GOOGL technical analysis for 2024-01-01'
        }
    ]


@pytest.fixture
def env_setup(monkeypatch):
    """Set up environment variables for testing"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test-api-key')
    monkeypatch.setenv('ALPHA_VANTAGE_API_KEY', 'test-av-key')
    monkeypatch.setenv('POLYGON_API_KEY', 'test-polygon-key')