import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import ta
from tqdm import tqdm
import os
import json

from src.data_adapters import DataSourceManager, DataSourceAdapter, OHLCVData


class OHLCVDataIngestion:
    """
    Flexible OHLCV data ingestion system with pluggable data source adapters
    """
    
    def __init__(self, 
                 tickers: List[str],
                 source: str = "yahoo",
                 period: str = "1y",
                 interval: str = "1d",
                 adapter_config: Optional[Dict[str, Any]] = None):
        """
        Initialize data ingestion with specified adapter
        
        Args:
            tickers: List of ticker symbols
            source: Data source name (yahoo, alpha_vantage, polygon, csv)
            period: Time period for data
            interval: Data interval
            adapter_config: Configuration for the adapter (API keys, paths, etc.)
        """
        self.tickers = tickers
        self.period = period
        self.interval = interval
        self.source = source
        
        # Create adapter
        self.adapter = DataSourceManager.create_adapter(source, adapter_config or {})
        
        # Store fetched data
        self.data = {}
        
        print(f"Initialized {source} data adapter")
        adapter_info = self.adapter.get_adapter_info()
        if adapter_info.get('requires_api_key') and not adapter_config:
            print(f"⚠️  Warning: {source} requires API key configuration")
    
    def fetch_ohlcv_data(self, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data using the configured adapter
        
        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping ticker to DataFrame
        """
        print(f"\nFetching data from {self.source}...")
        
        # Fetch data using adapter
        ohlcv_data_dict = self.adapter.fetch_multiple(
            tickers=self.tickers,
            period=self.period,
            interval=self.interval,
            start_date=start_date,
            end_date=end_date
        )
        
        # Process and add technical indicators
        for ticker, ohlcv_data in ohlcv_data_dict.items():
            if ohlcv_data.validate():
                df = ohlcv_data.data
                df = self._add_technical_indicators(df)
                self.data[ticker] = df
            else:
                print(f"⚠️  Invalid data for {ticker}, skipping technical indicators")
                self.data[ticker] = ohlcv_data.data
        
        return self.data
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to DataFrame"""
        if len(df) < 20:  # Not enough data for indicators
            return df
            
        try:
            # Add moving averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # Add RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # Add MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            df['MACD_diff'] = macd.macd_diff()
            
            # Add Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'])
            df['BB_upper'] = bb.bollinger_hband()
            df['BB_middle'] = bb.bollinger_mavg()
            df['BB_lower'] = bb.bollinger_lband()
            
            # Add Volume indicators
            df['Volume_SMA'] = ta.volume.volume_weighted_average_price(
                df['High'], df['Low'], df['Close'], df['Volume']
            )
            
            # Calculate price changes
            df['Price_Change'] = df['Close'].pct_change()
            df['Price_Change_5d'] = df['Close'].pct_change(periods=5)
            df['Price_Change_20d'] = df['Close'].pct_change(periods=20)
            
            # Add pattern identification
            df['Trend'] = self._identify_trend(df)
            df['Support_Resistance'] = self._identify_support_resistance(df)
            
        except Exception as e:
            print(f"Warning: Could not add all technical indicators: {e}")
            
        return df
    
    def _identify_trend(self, df: pd.DataFrame) -> pd.Series:
        """Identify market trend"""
        conditions = [
            (df['SMA_20'] > df['SMA_50']) & (df['Close'] > df['SMA_20']),
            (df['SMA_20'] < df['SMA_50']) & (df['Close'] < df['SMA_20']),
        ]
        choices = ['Uptrend', 'Downtrend']
        return pd.Series(np.select(conditions, choices, default='Sideways'), index=df.index)
    
    def _identify_support_resistance(self, df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Identify support and resistance levels"""
        highs = df['High'].rolling(window=window, center=True).max()
        lows = df['Low'].rolling(window=window, center=True).min()
        
        support_resistance = []
        for i in range(len(df)):
            if pd.notna(highs.iloc[i]) and df['High'].iloc[i] == highs.iloc[i]:
                support_resistance.append('Resistance')
            elif pd.notna(lows.iloc[i]) and df['Low'].iloc[i] == lows.iloc[i]:
                support_resistance.append('Support')
            else:
                support_resistance.append('Normal')
                
        return pd.Series(support_resistance, index=df.index)
    
    def create_contextual_chunks(self, window_size: int = 30) -> List[Dict[str, Any]]:
        """Create contextual chunks for vector storage"""
        chunks = []
        
        for ticker, df in self.data.items():
            df = df.dropna()
            
            for i in range(0, len(df) - window_size + 1, window_size // 2):
                window_df = df.iloc[i:i + window_size]
                
                chunk = {
                    'ticker': ticker,
                    'start_date': window_df.index[0].strftime('%Y-%m-%d'),
                    'end_date': window_df.index[-1].strftime('%Y-%m-%d'),
                    'data': window_df.to_dict('records'),
                    'summary': self._create_window_summary(window_df, ticker),
                    'metadata': {
                        'source': self.source,
                        'window_size': window_size,
                        'avg_volume': float(window_df['Volume'].mean()),
                        'price_range': {
                            'high': float(window_df['High'].max()),
                            'low': float(window_df['Low'].min()),
                            'open': float(window_df['Open'].iloc[0]),
                            'close': float(window_df['Close'].iloc[-1])
                        },
                        'trend': window_df['Trend'].mode()[0] if len(window_df['Trend'].mode()) > 0 else 'Mixed',
                        'volatility': float(window_df['Price_Change'].std()) if 'Price_Change' in window_df else 0,
                        'rsi_avg': float(window_df['RSI'].mean()) if 'RSI' in window_df else None
                    }
                }
                chunks.append(chunk)
                
        return chunks
    
    def _create_window_summary(self, window_df: pd.DataFrame, ticker: str) -> str:
        """Create summary for a data window"""
        start_date = window_df.index[0].strftime('%Y-%m-%d')
        end_date = window_df.index[-1].strftime('%Y-%m-%d')
        
        price_change = ((window_df['Close'].iloc[-1] - window_df['Close'].iloc[0]) / 
                       window_df['Close'].iloc[0] * 100)
        
        trend = window_df['Trend'].mode()[0] if 'Trend' in window_df and len(window_df['Trend'].mode()) > 0 else 'Mixed'
        avg_volume = window_df['Volume'].mean()
        
        rsi_avg = window_df['RSI'].mean() if 'RSI' in window_df else 0
        
        summary = f"""
        {ticker} OHLCV data from {start_date} to {end_date}:
        - Price movement: {price_change:.2f}% (${window_df['Close'].iloc[0]:.2f} to ${window_df['Close'].iloc[-1]:.2f})
        - Dominant trend: {trend}
        - Average volume: {avg_volume:,.0f}
        - Price range: ${window_df['Low'].min():.2f} - ${window_df['High'].max():.2f}
        """
        
        if 'RSI' in window_df:
            summary += f"\n        - Average RSI: {rsi_avg:.2f}"
        
        if 'Price_Change' in window_df:
            summary += f"\n        - Volatility (std of returns): {window_df['Price_Change'].std():.4f}"
        
        # Add notable events
        if price_change > 10:
            summary += f"\n        - Significant upward movement detected ({price_change:.2f}%)"
        elif price_change < -10:
            summary += f"\n        - Significant downward movement detected ({price_change:.2f}%)"
            
        if rsi_avg > 70:
            summary += "\n        - Overbought conditions (RSI > 70)"
        elif rsi_avg < 30:
            summary += "\n        - Oversold conditions (RSI < 30)"
            
        return summary.strip()
    
    def save_data(self, output_dir: str = "./data"):
        """Save data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save raw data as CSV
        for ticker, df in self.data.items():
            df.to_csv(f"{output_dir}/{ticker}_ohlcv.csv")
            
        # Save chunks as JSON
        chunks = self.create_contextual_chunks()
        with open(f"{output_dir}/ohlcv_chunks.json", 'w') as f:
            json.dump(chunks, f, default=str, indent=2)
            
        # Save metadata
        metadata = {
            'source': self.source,
            'tickers': self.tickers,
            'period': self.period,
            'interval': self.interval,
            'total_chunks': len(chunks),
            'adapter_info': self.adapter.get_adapter_info()
        }
        
        with open(f"{output_dir}/ingestion_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"✓ Saved {len(chunks)} chunks to {output_dir}/")
        print(f"✓ Data source: {self.source}")
        
        return chunks
    
    def switch_adapter(self, source: str, adapter_config: Optional[Dict[str, Any]] = None):
        """
        Switch to a different data adapter
        
        Args:
            source: New data source name
            adapter_config: Configuration for the new adapter
        """
        self.source = source
        self.adapter = DataSourceManager.create_adapter(source, adapter_config or {})
        print(f"Switched to {source} data adapter")
    
    @staticmethod
    def list_available_sources() -> List[str]:
        """List all available data sources"""
        return DataSourceManager.get_available_sources()
    
    @staticmethod
    def get_source_info(source: str) -> Dict[str, Any]:
        """Get information about a specific data source"""
        return DataSourceManager.get_adapter_info(source)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the data ingestion component"""
        return {
            'component': 'OHLCVDataIngestion',
            'tickers': self.tickers,
            'source': self.source,
            'period': self.period,
            'interval': self.interval,
            'data_loaded': len(self.data) > 0,
            'tickers_loaded': list(self.data.keys()) if self.data else [],
            'adapter_info': self.adapter.get_adapter_info() if hasattr(self.adapter, 'get_adapter_info') else {}
        }