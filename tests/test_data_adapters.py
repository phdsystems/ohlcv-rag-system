import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
import json

from src.data_adapters.base import DataSourceAdapter, OHLCVData
from src.data_adapters.data_source_manager import DataSourceManager
from src.data_adapters.yahoo_finance import YahooFinanceAdapter
from src.data_adapters.alpha_vantage import AlphaVantageAdapter
from src.data_adapters.polygon_io import PolygonAdapter
from src.data_adapters.csv_adapter import CSVAdapter


class TestOHLCVData:
    
    def test_ohlcv_data_creation(self, sample_ohlcv_data):
        """Test OHLCVData creation and validation"""
        ohlcv = OHLCVData(
            ticker="AAPL",
            data=sample_ohlcv_data,
            metadata={"source": "test"}
        )
        
        assert ohlcv.ticker == "AAPL"
        assert ohlcv.data.equals(sample_ohlcv_data)
        assert ohlcv.metadata["source"] == "test"
        assert ohlcv.validate() is True
    
    def test_ohlcv_data_validation_missing_columns(self):
        """Test OHLCVData validation with missing columns"""
        incomplete_data = pd.DataFrame({
            'Open': [100, 101],
            'Close': [102, 103]
            # Missing High, Low, Volume
        })
        
        ohlcv = OHLCVData(
            ticker="TEST",
            data=incomplete_data,
            metadata={}
        )
        
        assert ohlcv.validate() is False


class TestDataSourceManager:
    
    def test_register_adapter(self):
        """Test registering a custom adapter"""
        class CustomAdapter(DataSourceAdapter):
            def _validate_config(self):
                pass
            
            def fetch_ohlcv(self, ticker, **kwargs):
                return OHLCVData(ticker=ticker, data=pd.DataFrame(), metadata={})
            
            def fetch_data(self, ticker, **kwargs):
                return pd.DataFrame()
            
            def get_adapter_info(self):
                return {"name": "custom"}
        
        DataSourceManager.register_adapter("custom", CustomAdapter)
        
        assert "custom" in DataSourceManager._adapters
        assert DataSourceManager._adapters["custom"] == CustomAdapter
    
    def test_create_adapter_yahoo(self):
        """Test creating Yahoo Finance adapter"""
        with patch('src.data_adapters.yahoo_finance.yf'):
            adapter = DataSourceManager.create_adapter("yahoo")
            assert isinstance(adapter, YahooFinanceAdapter)
    
    def test_create_adapter_alpha_vantage(self):
        """Test creating Alpha Vantage adapter"""
        config = {"api_key": "test_key"}
        adapter = DataSourceManager.create_adapter("alpha_vantage", config)
        assert isinstance(adapter, AlphaVantageAdapter)
        assert adapter.config["api_key"] == "test_key"
    
    def test_create_adapter_polygon(self):
        """Test creating Polygon adapter"""
        config = {"api_key": "test_key"}
        adapter = DataSourceManager.create_adapter("polygon", config)
        assert isinstance(adapter, PolygonAdapter)
        assert adapter.config["api_key"] == "test_key"
    
    def test_create_adapter_csv(self):
        """Test creating CSV adapter"""
        config = {"file_path": "/tmp/test.csv"}
        adapter = DataSourceManager.create_adapter("csv", config)
        assert isinstance(adapter, CSVAdapter)
        assert adapter.config["file_path"] == "/tmp/test.csv"
    
    def test_create_adapter_invalid(self):
        """Test creating invalid adapter raises error"""
        with pytest.raises(ValueError, match="Unknown adapter"):
            DataSourceManager.create_adapter("invalid_adapter")
    
    def test_list_available_adapters(self):
        """Test listing available adapters"""
        adapters = DataSourceManager.list_available_adapters()
        
        expected_adapters = ["yahoo", "alpha_vantage", "polygon", "csv"]
        for adapter in expected_adapters:
            assert adapter in adapters


class TestYahooFinanceAdapter:
    
    @patch('src.data_adapters.yahoo_finance.yf.Ticker')
    def test_fetch_ohlcv(self, mock_ticker_class, sample_ohlcv_data):
        """Test fetching OHLCV data from Yahoo Finance"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker
        
        adapter = YahooFinanceAdapter()
        result = adapter.fetch_ohlcv("AAPL", period="1mo", interval="1d")
        
        assert isinstance(result, OHLCVData)
        assert result.ticker == "AAPL"
        assert result.validate()
        mock_ticker.history.assert_called_once_with(period="1mo", interval="1d")
    
    @patch('src.data_adapters.yahoo_finance.yf.Ticker')
    def test_fetch_data(self, mock_ticker_class, sample_ohlcv_data):
        """Test fetch_data method"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker
        
        adapter = YahooFinanceAdapter()
        result = adapter.fetch_data("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
    
    def test_get_adapter_info(self):
        """Test getting adapter info"""
        adapter = YahooFinanceAdapter()
        info = adapter.get_adapter_info()
        
        assert info["name"] == "Yahoo Finance"
        assert info["requires_api_key"] is False
        assert "supported_intervals" in info


class TestAlphaVantageAdapter:
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key raises error"""
        with pytest.raises(ValueError, match="API key is required"):
            AlphaVantageAdapter()
    
    @patch('requests.get')
    def test_fetch_ohlcv(self, mock_get):
        """Test fetching OHLCV data from Alpha Vantage"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2024-01-01": {
                    "1. open": "150.00",
                    "2. high": "155.00",
                    "3. low": "149.00",
                    "4. close": "154.00",
                    "5. volume": "5000000"
                }
            }
        }
        mock_get.return_value = mock_response
        
        adapter = AlphaVantageAdapter({"api_key": "test_key"})
        result = adapter.fetch_ohlcv("AAPL")
        
        assert isinstance(result, OHLCVData)
        assert result.ticker == "AAPL"
        mock_get.assert_called_once()
    
    def test_get_adapter_info(self):
        """Test getting adapter info"""
        adapter = AlphaVantageAdapter({"api_key": "test"})
        info = adapter.get_adapter_info()
        
        assert info["name"] == "Alpha Vantage"
        assert info["requires_api_key"] is True


class TestPolygonAdapter:
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key raises error"""
        with pytest.raises(ValueError, match="API key is required"):
            PolygonAdapter()
    
    @patch('requests.get')
    def test_fetch_ohlcv(self, mock_get):
        """Test fetching OHLCV data from Polygon"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "t": 1704067200000,  # timestamp
                    "o": 150.0,
                    "h": 155.0,
                    "l": 149.0,
                    "c": 154.0,
                    "v": 5000000
                }
            ]
        }
        mock_get.return_value = mock_response
        
        adapter = PolygonAdapter({"api_key": "test_key"})
        result = adapter.fetch_ohlcv("AAPL")
        
        assert isinstance(result, OHLCVData)
        assert result.ticker == "AAPL"
        mock_get.assert_called_once()
    
    def test_get_adapter_info(self):
        """Test getting adapter info"""
        adapter = PolygonAdapter({"api_key": "test"})
        info = adapter.get_adapter_info()
        
        assert info["name"] == "Polygon.io"
        assert info["requires_api_key"] is True


class TestCSVAdapter:
    
    def test_initialization_without_file_path(self):
        """Test initialization without file path raises error"""
        with pytest.raises(ValueError, match="file_path is required"):
            CSVAdapter()
    
    def test_fetch_ohlcv_single_ticker(self, temp_csv_file):
        """Test fetching OHLCV data from CSV file"""
        adapter = CSVAdapter({"file_path": temp_csv_file})
        result = adapter.fetch_ohlcv("AAPL")
        
        assert isinstance(result, OHLCVData)
        assert result.ticker == "AAPL"
        assert result.validate()
    
    def test_fetch_ohlcv_multi_ticker_csv(self, temp_csv_file, sample_ohlcv_data):
        """Test fetching from multi-ticker CSV"""
        # Create a CSV with ticker column
        multi_ticker_data = sample_ohlcv_data.copy()
        multi_ticker_data['Ticker'] = 'AAPL'
        
        with patch('pandas.read_csv') as mock_read:
            mock_read.return_value = multi_ticker_data
            
            adapter = CSVAdapter({
                "file_path": temp_csv_file,
                "ticker_column": "Ticker"
            })
            result = adapter.fetch_ohlcv("AAPL")
            
            assert result.ticker == "AAPL"
    
    def test_fetch_data_directory(self):
        """Test fetching data from directory of CSV files"""
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = True
            
            with patch('os.listdir') as mock_listdir:
                mock_listdir.return_value = ['AAPL.csv', 'GOOGL.csv']
                
                with patch('pandas.read_csv') as mock_read:
                    mock_read.return_value = pd.DataFrame({
                        'Date': pd.date_range('2024-01-01', periods=5),
                        'Open': [150] * 5,
                        'High': [155] * 5,
                        'Low': [149] * 5,
                        'Close': [154] * 5,
                        'Volume': [5000000] * 5
                    })
                    
                    adapter = CSVAdapter({"file_path": "/tmp/data"})
                    result = adapter.fetch_data("AAPL")
                    
                    assert isinstance(result, pd.DataFrame)
    
    def test_get_adapter_info(self):
        """Test getting adapter info"""
        adapter = CSVAdapter({"file_path": "/tmp/test.csv"})
        info = adapter.get_adapter_info()
        
        assert info["name"] == "CSV File"
        assert info["requires_api_key"] is False
        assert "supported_formats" in info