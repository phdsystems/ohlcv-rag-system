import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from time import sleep
from tqdm import tqdm

from .base import DataSourceAdapter, OHLCVData


class AlphaVantageAdapter(DataSourceAdapter):
    """Alpha Vantage data source adapter"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def _validate_config(self) -> None:
        """Validate that API key is provided"""
        if 'api_key' not in self.config:
            raise ValueError("Alpha Vantage requires an API key. Get one at https://www.alphavantage.co/support/#api-key")
    
    def fetch_ohlcv(self,
                   ticker: str,
                   period: str = "1y",
                   interval: str = "1d",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> OHLCVData:
        """
        Fetch OHLCV data from Alpha Vantage
        """
        try:
            # Map interval to Alpha Vantage function and interval
            function, av_interval = self._map_interval(interval)
            
            params = {
                'function': function,
                'symbol': ticker,
                'apikey': self.config['api_key'],
                'outputsize': 'full',  # Get full data
                'datatype': 'json'
            }
            
            # Add interval for intraday data
            if function == 'TIME_SERIES_INTRADAY':
                params['interval'] = av_interval
            
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if 'Note' in data:
                raise ValueError(f"API Limit: {data['Note']}")
            
            # Parse response based on function
            df = self._parse_response(data, function)
            
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Filter by date range if provided
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            elif not start_date:
                # Apply period filter if no explicit dates
                start, _ = self.parse_period_to_dates(period)
                df = df[df.index >= start]
            
            metadata = {
                'source': 'Alpha Vantage',
                'ticker': ticker,
                'period': period,
                'interval': interval,
                'records': len(df),
                'start_date': df.index[0].strftime('%Y-%m-%d') if not df.empty else None,
                'end_date': df.index[-1].strftime('%Y-%m-%d') if not df.empty else None,
                'api_function': function
            }
            
            return OHLCVData(ticker=ticker, data=df, metadata=metadata)
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {ticker} from Alpha Vantage: {str(e)}")
    
    def _map_interval(self, interval: str) -> tuple[str, str]:
        """Map interval to Alpha Vantage function and interval parameter"""
        interval_mapping = {
            '1m': ('TIME_SERIES_INTRADAY', '1min'),
            '5m': ('TIME_SERIES_INTRADAY', '5min'),
            '15m': ('TIME_SERIES_INTRADAY', '15min'),
            '30m': ('TIME_SERIES_INTRADAY', '30min'),
            '60m': ('TIME_SERIES_INTRADAY', '60min'),
            '1h': ('TIME_SERIES_INTRADAY', '60min'),
            '1d': ('TIME_SERIES_DAILY', None),
            '1wk': ('TIME_SERIES_WEEKLY', None),
            '1mo': ('TIME_SERIES_MONTHLY', None)
        }
        
        if interval not in interval_mapping:
            # Default to daily
            return 'TIME_SERIES_DAILY', None
            
        return interval_mapping[interval]
    
    def _parse_response(self, data: Dict, function: str) -> pd.DataFrame:
        """Parse Alpha Vantage response to DataFrame"""
        # Find the time series key
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if not time_series_key:
            raise ValueError("No time series data found in response")
        
        time_series = data[time_series_key]
        
        # Convert to DataFrame
        df_data = []
        for timestamp, values in time_series.items():
            row = {
                'timestamp': timestamp,
                'Open': float(values.get('1. open', values.get('1. Open', 0))),
                'High': float(values.get('2. high', values.get('2. High', 0))),
                'Low': float(values.get('3. low', values.get('3. Low', 0))),
                'Close': float(values.get('4. close', values.get('4. Close', 0))),
                'Volume': float(values.get('5. volume', values.get('5. Volume', 0)))
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def fetch_multiple(self,
                      tickers: List[str],
                      period: str = "1y",
                      interval: str = "1d",
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Dict[str, OHLCVData]:
        """
        Fetch OHLCV data for multiple tickers
        Note: Alpha Vantage has rate limits (5 calls/min for free tier)
        """
        results = {}
        rate_limit_delay = 12  # 12 seconds between calls for free tier (5 calls/min)
        
        for i, ticker in enumerate(tqdm(tickers, desc="Fetching from Alpha Vantage")):
            try:
                ohlcv_data = self.fetch_ohlcv(
                    ticker=ticker,
                    period=period,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date
                )
                results[ticker] = ohlcv_data
                print(f"✓ Fetched {ticker}: {ohlcv_data.metadata['records']} records")
                
                # Rate limiting
                if i < len(tickers) - 1:
                    sleep(rate_limit_delay)
                    
            except Exception as e:
                print(f"✗ Failed to fetch {ticker}: {str(e)}")
                continue
                
        return results
    
    def get_available_tickers(self) -> List[str]:
        """
        Get list of available tickers
        Alpha Vantage supports US stocks primarily
        """
        # Alpha Vantage doesn't provide a list endpoint
        # Return common US tickers
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            "JPM", "V", "JNJ", "WMT", "PG", "UNH", "HD", "DIS",
            "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"
        ]
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the Alpha Vantage adapter"""
        return {
            'name': 'Alpha Vantage',
            'adapter_class': 'AlphaVantageAdapter',
            'requires_api_key': True,
            'free_tier': True,
            'rate_limits': {
                'free': '5 API calls per minute, 500 calls per day',
                'premium': 'Up to 75-1200 calls per minute depending on plan'
            },
            'supported_intervals': [
                '1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo'
            ],
            'supported_functions': [
                'TIME_SERIES_INTRADAY',
                'TIME_SERIES_DAILY',
                'TIME_SERIES_WEEKLY',
                'TIME_SERIES_MONTHLY'
            ],
            'data_delay': 'Real-time for premium, 15min delay for free',
            'historical_data': '20+ years of historical data',
            'markets': 'US stocks, forex, crypto, commodities',
            'additional_features': [
                'Technical indicators',
                'Fundamental data',
                'Economic indicators',
                'Sector performance'
            ],
            'api_key_url': 'https://www.alphavantage.co/support/#api-key'
        }