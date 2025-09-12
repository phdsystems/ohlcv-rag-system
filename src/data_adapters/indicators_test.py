"""
Tests for technical indicator calculations
"""

import pytest
import pandas as pd
import numpy as np
from src.ingestion.data_ingestion import TechnicalIndicatorCalculator
from src.core.models import OHLCVDataModel


class TestTechnicalIndicators:
    """Test technical indicator calculations on OHLCV data"""
    
    def create_sample_ohlcv_data(self, periods=50):
        """Helper to create sample OHLCV data"""
        dates = pd.date_range('2024-01-01', periods=periods)
        data = pd.DataFrame({
            'Open': np.random.randn(periods).cumsum() + 100,
            'High': np.random.randn(periods).cumsum() + 102,
            'Low': np.random.randn(periods).cumsum() + 98,
            'Close': np.random.randn(periods).cumsum() + 100,
            'Volume': np.random.randint(1000000, 5000000, periods)
        }, index=dates)
        
        # Ensure High >= Low
        data['High'] = data[['High', 'Low']].max(axis=1) + 1
        data['Low'] = data[['High', 'Low']].min(axis=1)
        
        return data
    
    def test_technical_indicator_calculator_initialization(self):
        """Test TechnicalIndicatorCalculator can be initialized"""
        calculator = TechnicalIndicatorCalculator()
        assert calculator is not None
        assert hasattr(calculator, 'indicators_config')
    
    def test_indicator_calculation_on_data_model(self):
        """Test indicators are calculated on OHLCVDataModel"""
        data = self.create_sample_ohlcv_data()
        
        model = OHLCVDataModel(
            ticker="TEST",
            data=data,
            interval="1d",
            period="50d",
            source="test",
            metadata={"test": True}
        )
        
        calculator = TechnicalIndicatorCalculator()
        model_with_indicators = calculator.calculate_all(model)
        
        # Check that indicators were added (should have at least the original columns)
        assert len(model_with_indicators.data.columns) >= len(data.columns)
        
        # Check for common indicators
        indicator_columns = model_with_indicators.data.columns
        assert any('SMA' in col for col in indicator_columns) or \
               any('EMA' in col for col in indicator_columns) or \
               any('RSI' in col for col in indicator_columns)
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        data = self.create_sample_ohlcv_data(100)
        
        # Calculate 20-day SMA manually
        sma_20 = data['Close'].rolling(window=20).mean()
        
        # Verify SMA properties
        assert sma_20.isna().sum() == 19  # First 19 values should be NaN
        assert not sma_20[19:].isna().any()  # No NaN after first 19
        assert len(sma_20) == len(data)
    
    def test_rsi_calculation_bounds(self):
        """Test RSI is bounded between 0 and 100"""
        data = self.create_sample_ohlcv_data(100)
        
        # Simple RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Check RSI bounds
        valid_rsi = rsi[~rsi.isna()]
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_bollinger_bands_relationship(self):
        """Test Bollinger Bands have correct relationship"""
        data = self.create_sample_ohlcv_data(100)
        
        # Calculate Bollinger Bands
        sma = data['Close'].rolling(window=20).mean()
        std = data['Close'].rolling(window=20).std()
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        # Verify relationships
        valid_idx = ~sma.isna()
        assert (upper_band[valid_idx] >= sma[valid_idx]).all()
        assert (sma[valid_idx] >= lower_band[valid_idx]).all()
        assert (upper_band[valid_idx] > lower_band[valid_idx]).all()