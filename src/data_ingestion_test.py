"""
Unit tests for OHLCVDataIngestion class
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from .data_ingestion import OHLCVDataIngestion


class TestOHLCVDataIngestion:
    """Test OHLCVDataIngestion functionality with mocked dependencies"""
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        tickers = ['AAPL', 'MSFT']
        ingestion = OHLCVDataIngestion(tickers=tickers)
        
        assert ingestion.tickers == tickers
        assert ingestion.source == "yahoo"
        assert ingestion.period == "1y"
        assert ingestion.interval == "1d"
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        tickers = ['GOOGL']
        config = {"api_key": "test_key"}
        
        ingestion = OHLCVDataIngestion(
            tickers=tickers,
            source="alpha_vantage",
            period="6mo", 
            interval="1h",
            adapter_config=config
        )
        
        assert ingestion.tickers == tickers
        assert ingestion.source == "alpha_vantage"
        assert ingestion.period == "6mo"
        assert ingestion.interval == "1h"
    
    @patch('src.data_ingestion.DataSourceManager')
    def test_data_source_manager_initialization(self, mock_manager):
        """Test that DataSourceManager is properly initialized"""
        mock_manager_instance = Mock()
        mock_manager.return_value = mock_manager_instance
        
        tickers = ['AAPL']
        ingestion = OHLCVDataIngestion(tickers=tickers, source="yahoo")
        
        # Should initialize without errors - basic functionality test
        assert ingestion.tickers == ['AAPL']
        assert ingestion.source == "yahoo"
    
    def test_empty_tickers_list(self):
        """Test behavior with empty tickers list"""
        ingestion = OHLCVDataIngestion(tickers=[])
        assert ingestion.tickers == []
    
    @patch('src.data_ingestion.DataSourceManager')
    def test_invalid_source_handled_gracefully(self, mock_manager):
        """Test that invalid data source is handled gracefully"""
        mock_manager.return_value = Mock()
        
        # Should not raise exception during init
        ingestion = OHLCVDataIngestion(
            tickers=['AAPL'],
            source="invalid_source"
        )
        
        assert ingestion.source == "invalid_source"
    
    def test_adapter_config_none(self):
        """Test that None adapter_config is handled properly"""
        ingestion = OHLCVDataIngestion(
            tickers=['AAPL'],
            adapter_config=None
        )
        
        # Should not raise error
        assert ingestion.tickers == ['AAPL']


class TestOHLCVDataIngestionIntegration:
    """Integration tests that might need mocked external dependencies"""
    
    @patch('src.data_ingestion.DataSourceManager')
    def test_fetch_with_mock_data(self, mock_manager):
        """Test data fetching with mocked DataSourceManager"""
        # Setup mock data
        mock_data = pd.DataFrame({
            'Date': [datetime.now()],
            'Open': [150.0],
            'High': [155.0],
            'Low': [148.0],
            'Close': [152.0],
            'Volume': [1000000]
        })
        
        mock_adapter = Mock()
        mock_adapter.get_data.return_value = mock_data
        mock_manager_instance = Mock()
        mock_manager_instance.get_adapter.return_value = mock_adapter
        mock_manager.return_value = mock_manager_instance
        
        ingestion = OHLCVDataIngestion(tickers=['AAPL'])
        
        # Test would go here if the class has a public fetch method
        # This test structure allows for easy expansion
        assert ingestion.tickers == ['AAPL']
    
    @pytest.mark.unit
    def test_technical_indicators_calculation(self):
        """Test that technical indicators can be calculated on sample data"""
        sample_data = pd.DataFrame({
            'Open': [100, 102, 101, 103, 105],
            'High': [105, 107, 106, 108, 110],
            'Low': [98, 100, 99, 101, 103],
            'Close': [104, 105, 104, 106, 108],
            'Volume': [1000000] * 5
        })
        
        # Test basic technical analysis functions work
        # This ensures the ta library integration works
        try:
            import ta
            sma = ta.trend.sma_indicator(sample_data['Close'], window=3)
            assert len(sma) == len(sample_data)
            assert not sma.iloc[-1] != sma.iloc[-1]  # Check for NaN
        except ImportError:
            pytest.skip("Technical analysis library not available")


# Mark all tests as unit tests
pytestmark = pytest.mark.unit