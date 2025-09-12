"""
Tests for Yahoo Finance data fetching functionality
"""

import pytest
import yfinance as yf
import pandas as pd


class TestYahooFinance:
    """Test Yahoo Finance API integration"""
    
    def test_yahoo_finance_api_returns_data(self):
        """Test that Yahoo Finance API returns real stock data"""
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="5d")
        
        assert not data.empty, "Yahoo Finance returned empty data"
        assert len(data) > 0
        assert 'Close' in data.columns
        assert 'Volume' in data.columns
    
    def test_yahoo_finance_data_quality(self):
        """Test that Yahoo Finance data has expected quality"""
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="5d")
        
        # Check data quality
        assert data['Close'].notna().all(), "Close prices have NaN values"
        assert data['Volume'].notna().all(), "Volume has NaN values"
        assert (data['High'] >= data['Low']).all(), "High is not always >= Low"
        assert (data['Close'] > 0).all(), "Close prices should be positive"
    
    def test_multiple_tickers_fetch(self):
        """Test fetching data for multiple tickers"""
        tickers = ["AAPL", "MSFT", "GOOGL"]
        results = {}
        
        for symbol in tickers:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            results[symbol] = data
        
        assert len(results) == 3
        for symbol in tickers:
            assert symbol in results
            assert not results[symbol].empty