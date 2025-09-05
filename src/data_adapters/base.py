from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta


@dataclass
class OHLCVData:
    """Standard OHLCV data structure"""
    ticker: str
    data: pd.DataFrame
    metadata: Dict[str, Any]
    
    def validate(self) -> bool:
        """Validate that DataFrame has required OHLCV columns"""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in self.data.columns for col in required_columns)


class DataSourceAdapter(ABC):
    """Abstract base class for data source adapters"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter with configuration
        
        Args:
            config: Adapter-specific configuration (API keys, endpoints, etc.)
        """
        self.config = config or {}
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate adapter configuration"""
        pass
    
    @abstractmethod
    def fetch_ohlcv(self, 
                   ticker: str, 
                   period: str = "1y",
                   interval: str = "1d",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> OHLCVData:
        """
        Fetch OHLCV data for a single ticker
        
        Args:
            ticker: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            OHLCVData object containing the fetched data
        """
        pass
    
    @abstractmethod
    def fetch_multiple(self,
                      tickers: List[str],
                      period: str = "1y", 
                      interval: str = "1d",
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict[str, OHLCVData]:
        """
        Fetch OHLCV data for multiple tickers
        
        Args:
            tickers: List of stock symbols
            period: Time period
            interval: Data interval
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary mapping ticker to OHLCVData
        """
        pass
    
    @abstractmethod
    def get_available_tickers(self) -> List[str]:
        """Get list of available tickers from this data source"""
        pass
    
    @abstractmethod
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the adapter"""
        pass
    
    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame columns to OHLCV format
        
        Args:
            df: Raw DataFrame from data source
            
        Returns:
            Standardized DataFrame with Open, High, Low, Close, Volume columns
        """
        column_mappings = {
            # Common variations
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'adj close': 'Adj Close',
            'adjusted close': 'Adj Close',
            # Add more mappings as needed
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume',
        }
        
        # Rename columns to standard format
        df_copy = df.copy()
        for old_col, new_col in column_mappings.items():
            if old_col in df_copy.columns:
                df_copy.rename(columns={old_col: new_col}, inplace=True)
            elif old_col.upper() in df_copy.columns:
                df_copy.rename(columns={old_col.upper(): new_col}, inplace=True)
                
        return df_copy
    
    def parse_period_to_dates(self, period: str) -> tuple[datetime, datetime]:
        """
        Convert period string to start and end dates
        
        Args:
            period: Period string (1d, 1mo, 1y, etc.)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now()
        
        period_mappings = {
            '1d': timedelta(days=1),
            '5d': timedelta(days=5),
            '1mo': timedelta(days=30),
            '3mo': timedelta(days=90),
            '6mo': timedelta(days=180),
            '1y': timedelta(days=365),
            '2y': timedelta(days=730),
            '5y': timedelta(days=1825),
            '10y': timedelta(days=3650),
        }
        
        if period in period_mappings:
            start_date = end_date - period_mappings[period]
        elif period == 'ytd':
            start_date = datetime(end_date.year, 1, 1)
        elif period == 'max':
            start_date = datetime(1970, 1, 1)
        else:
            # Default to 1 year
            start_date = end_date - timedelta(days=365)
            
        return start_date, end_date
    
    def validate_interval(self, interval: str) -> bool:
        """
        Validate that interval is supported
        
        Args:
            interval: Interval string
            
        Returns:
            True if valid, False otherwise
        """
        valid_intervals = [
            '1m', '2m', '5m', '15m', '30m', '60m', '90m',
            '1h', '1d', '5d', '1wk', '1mo', '3mo'
        ]
        return interval in valid_intervals