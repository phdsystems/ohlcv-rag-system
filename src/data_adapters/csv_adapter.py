import pandas as pd
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from tqdm import tqdm

from .base import DataSourceAdapter, OHLCVData


class CSVAdapter(DataSourceAdapter):
    """CSV file data source adapter for local OHLCV data"""
    
    def _validate_config(self) -> None:
        """Validate that data directory is provided"""
        if 'data_dir' not in self.config:
            self.config['data_dir'] = './data/csv'
        
        # Create directory if it doesn't exist
        Path(self.config['data_dir']).mkdir(parents=True, exist_ok=True)
    
    def fetch_ohlcv(self,
                   ticker: str,
                   period: str = "1y",
                   interval: str = "1d",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> OHLCVData:
        """
        Load OHLCV data from CSV file
        """
        try:
            # Construct file path
            file_path = self._get_file_path(ticker)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            # Read CSV with various date formats
            df = self._read_csv(file_path)
            
            if df.empty:
                raise ValueError(f"No data in CSV file for {ticker}")
            
            # Standardize column names
            df = self.standardize_dataframe(df)
            
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Filter by date range
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            elif not start_date and period != 'max':
                # Apply period filter
                start, _ = self.parse_period_to_dates(period)
                df = df[df.index >= start]
            
            # Resample data if needed based on interval
            if interval != '1d' and interval in ['1wk', '1mo', '3mo']:
                df = self._resample_data(df, interval)
            
            metadata = {
                'source': 'CSV File',
                'ticker': ticker,
                'period': period,
                'interval': interval,
                'records': len(df),
                'start_date': df.index[0].strftime('%Y-%m-%d') if not df.empty else None,
                'end_date': df.index[-1].strftime('%Y-%m-%d') if not df.empty else None,
                'file_path': file_path
            }
            
            return OHLCVData(ticker=ticker, data=df, metadata=metadata)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load data for {ticker} from CSV: {str(e)}")
    
    def _get_file_path(self, ticker: str) -> str:
        """Get file path for ticker"""
        # Support different naming conventions
        possible_files = [
            f"{ticker}.csv",
            f"{ticker.lower()}.csv",
            f"{ticker.upper()}.csv",
            f"{ticker}_ohlcv.csv",
            f"{ticker}_data.csv"
        ]
        
        for filename in possible_files:
            file_path = os.path.join(self.config['data_dir'], filename)
            if os.path.exists(file_path):
                return file_path
        
        # Default to standard naming
        return os.path.join(self.config['data_dir'], f"{ticker}.csv")
    
    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """Read CSV file with automatic date parsing"""
        # Try different date column names
        date_columns = ['Date', 'date', 'DATE', 'Timestamp', 'timestamp', 'DateTime', 'datetime']
        
        for date_col in date_columns:
            try:
                df = pd.read_csv(file_path, parse_dates=[date_col], index_col=date_col)
                df.index.name = 'Date'
                return df
            except:
                continue
        
        # Try reading without specific date column
        try:
            df = pd.read_csv(file_path, parse_dates=True, index_col=0)
            return df
        except:
            # Read without index and try to identify date column
            df = pd.read_csv(file_path)
            
            # Find date column
            for col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                    df.index.name = 'Date'
                    return df
                except:
                    continue
            
            raise ValueError("Could not identify date column in CSV file")
    
    def _resample_data(self, df: pd.DataFrame, interval: str) -> pd.DataFrame:
        """Resample data to different intervals"""
        resample_map = {
            '1wk': 'W',
            '1mo': 'M',
            '3mo': '3M'
        }
        
        if interval not in resample_map:
            return df
        
        rule = resample_map[interval]
        
        # Resample OHLCV data properly
        resampled = pd.DataFrame()
        resampled['Open'] = df['Open'].resample(rule).first()
        resampled['High'] = df['High'].resample(rule).max()
        resampled['Low'] = df['Low'].resample(rule).min()
        resampled['Close'] = df['Close'].resample(rule).last()
        resampled['Volume'] = df['Volume'].resample(rule).sum()
        
        # Drop NaN rows
        resampled.dropna(inplace=True)
        
        return resampled
    
    def fetch_multiple(self,
                      tickers: List[str],
                      period: str = "1y",
                      interval: str = "1d",
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict[str, OHLCVData]:
        """
        Load OHLCV data for multiple tickers from CSV files
        """
        results = {}
        
        for ticker in tqdm(tickers, desc="Loading from CSV files"):
            try:
                ohlcv_data = self.fetch_ohlcv(
                    ticker=ticker,
                    period=period,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date
                )
                results[ticker] = ohlcv_data
                print(f"✓ Loaded {ticker}: {ohlcv_data.metadata['records']} records")
                
            except Exception as e:
                print(f"✗ Failed to load {ticker}: {str(e)}")
                continue
                
        return results
    
    def get_available_tickers(self) -> List[str]:
        """Get list of available tickers from CSV files in data directory"""
        tickers = []
        
        if not os.path.exists(self.config['data_dir']):
            return tickers
        
        # Look for CSV files
        for file in os.listdir(self.config['data_dir']):
            if file.endswith('.csv'):
                # Extract ticker from filename
                ticker = file.replace('.csv', '').replace('_ohlcv', '').replace('_data', '').upper()
                if ticker not in tickers:
                    tickers.append(ticker)
        
        return sorted(tickers)
    
    def save_to_csv(self, ohlcv_data: OHLCVData, overwrite: bool = False) -> str:
        """
        Save OHLCVData to CSV file
        
        Args:
            ohlcv_data: OHLCVData object to save
            overwrite: Whether to overwrite existing file
            
        Returns:
            Path to saved file
        """
        file_path = self._get_file_path(ohlcv_data.ticker)
        
        if os.path.exists(file_path) and not overwrite:
            raise FileExistsError(f"File already exists: {file_path}. Set overwrite=True to replace.")
        
        # Save to CSV
        ohlcv_data.data.to_csv(file_path)
        
        print(f"✓ Saved {ohlcv_data.ticker} data to {file_path}")
        return file_path
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the CSV adapter"""
        return {
            'name': 'CSV File',
            'adapter_class': 'CSVAdapter',
            'requires_api_key': False,
            'free_tier': True,
            'rate_limits': 'None - local files',
            'supported_intervals': [
                '1d', '1wk', '1mo', '3mo'
            ],
            'data_directory': self.config['data_dir'],
            'available_tickers': self.get_available_tickers(),
            'file_format': 'CSV with date index',
            'required_columns': ['Open', 'High', 'Low', 'Close', 'Volume'],
            'optional_columns': ['Adj Close', 'Dividends', 'Stock Splits'],
            'features': [
                'Load historical data from CSV files',
                'Automatic date parsing',
                'Column name standardization',
                'Data resampling',
                'Save OHLCVData to CSV'
            ],
            'use_cases': [
                'Offline data analysis',
                'Custom data sources',
                'Backtesting with historical data',
                'Data archival and sharing'
            ]
        }