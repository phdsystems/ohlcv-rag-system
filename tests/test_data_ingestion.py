import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.data_ingestion import OHLCVDataIngestion


class TestOHLCVDataIngestion:
    
    def test_initialization(self, sample_tickers):
        """Test data ingestion initialization"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(
                tickers=sample_tickers,
                source='yahoo',
                period='1y',
                interval='1d'
            )
            
            assert ingestion.tickers == sample_tickers
            assert ingestion.source == 'yahoo'
            assert ingestion.period == '1y'
            assert ingestion.interval == '1d'
            mock_create.assert_called_once_with('yahoo', {})
    
    def test_fetch_ohlcv_data(self, sample_tickers, sample_ohlcv_data):
        """Test fetching OHLCV data"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_adapter.fetch_data.return_value = sample_ohlcv_data
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=sample_tickers)
            ingestion.fetch_ohlcv_data()
            
            assert len(ingestion.data) == len(sample_tickers)
            for ticker in sample_tickers:
                assert ticker in ingestion.data
                mock_adapter.fetch_data.assert_any_call(
                    ticker=ticker,
                    period='1y',
                    interval='1d'
                )
    
    def test_calculate_technical_indicators(self, sample_tickers, sample_ohlcv_data):
        """Test technical indicator calculation"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_adapter.fetch_data.return_value = sample_ohlcv_data
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=['AAPL'])
            ingestion.data['AAPL'] = sample_ohlcv_data
            
            result = ingestion.calculate_technical_indicators()
            
            assert 'AAPL' in result
            df = result['AAPL']
            
            # Check if technical indicators are added
            expected_indicators = ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_middle', 'BB_lower']
            for indicator in expected_indicators:
                assert indicator in df.columns
    
    def test_prepare_documents(self, sample_tickers, sample_ohlcv_data):
        """Test document preparation for vector store"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=['AAPL'])
            
            # Add technical indicators to data
            sample_data_with_indicators = sample_ohlcv_data.copy()
            sample_data_with_indicators['RSI'] = 55.0
            sample_data_with_indicators['MACD'] = 0.5
            sample_data_with_indicators['MACD_signal'] = 0.3
            
            ingestion.data['AAPL'] = sample_data_with_indicators
            
            documents = ingestion.prepare_documents()
            
            assert len(documents) > 0
            assert all(hasattr(doc, 'page_content') for doc in documents)
            assert all(hasattr(doc, 'metadata') for doc in documents)
            
            # Check metadata structure
            first_doc = documents[0]
            assert 'ticker' in first_doc.metadata
            assert 'date' in first_doc.metadata
            assert first_doc.metadata['ticker'] == 'AAPL'
    
    def test_prepare_documents_with_chunking(self, sample_tickers):
        """Test document preparation with chunking"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=['AAPL'])
            
            # Create large dataset
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
            large_data = pd.DataFrame({
                'Date': dates,
                'Open': np.random.uniform(100, 200, len(dates)),
                'High': np.random.uniform(150, 250, len(dates)),
                'Low': np.random.uniform(50, 150, len(dates)),
                'Close': np.random.uniform(100, 200, len(dates)),
                'Volume': np.random.randint(1000000, 10000000, len(dates)),
                'RSI': np.random.uniform(30, 70, len(dates)),
                'MACD': np.random.uniform(-2, 2, len(dates))
            })
            
            ingestion.data['AAPL'] = large_data
            
            chunk_size = 30
            documents = ingestion.prepare_documents(chunk_size=chunk_size)
            
            # Check that documents are chunked appropriately
            assert len(documents) > 0
            
            # Each document should represent a chunk of data
            for doc in documents:
                assert 'ticker' in doc.metadata
                assert 'date_range' in doc.metadata or 'date' in doc.metadata
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_adapter.fetch_data.return_value = pd.DataFrame()
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=['INVALID'])
            ingestion.fetch_ohlcv_data()
            
            documents = ingestion.prepare_documents()
            assert len(documents) == 0
    
    def test_error_handling_in_fetch(self):
        """Test error handling during data fetching"""
        with patch('src.data_ingestion.DataSourceManager.create_adapter') as mock_create:
            mock_adapter = MagicMock()
            mock_adapter.get_adapter_info.return_value = {'requires_api_key': False}
            mock_adapter.fetch_data.side_effect = Exception("API Error")
            mock_create.return_value = mock_adapter
            
            ingestion = OHLCVDataIngestion(tickers=['AAPL'])
            ingestion.fetch_ohlcv_data()
            
            # Should handle error gracefully
            assert 'AAPL' not in ingestion.data or ingestion.data['AAPL'] is None