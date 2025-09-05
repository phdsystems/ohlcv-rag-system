import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from tqdm import tqdm

from .base import DataSourceAdapter, OHLCVData


class PolygonIOAdapter(DataSourceAdapter):
    """Polygon.io data source adapter"""
    
    BASE_URL = "https://api.polygon.io"
    
    def _validate_config(self) -> None:
        """Validate that API key is provided"""
        if 'api_key' not in self.config:
            raise ValueError("Polygon.io requires an API key. Get one at https://polygon.io")
    
    def fetch_ohlcv(self,
                   ticker: str,
                   period: str = "1y",
                   interval: str = "1d",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> OHLCVData:
        """
        Fetch OHLCV data from Polygon.io
        """
        try:
            # Parse dates
            if start_date and end_date:
                start = start_date
                end = end_date
            else:
                start_dt, end_dt = self.parse_period_to_dates(period)
                start = start_dt.strftime('%Y-%m-%d')
                end = end_dt.strftime('%Y-%m-%d')
            
            # Map interval to Polygon.io parameters
            multiplier, timespan = self._map_interval(interval)
            
            # Construct API endpoint
            endpoint = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start}/{end}"
            
            params = {
                'apiKey': self.config['api_key'],
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000  # Max limit
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if data.get('status') != 'OK':
                raise ValueError(f"API Error: {data.get('message', 'Unknown error')}")
            
            # Parse response
            df = self._parse_response(data)
            
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            metadata = {
                'source': 'Polygon.io',
                'ticker': ticker,
                'period': period,
                'interval': interval,
                'records': len(df),
                'start_date': df.index[0].strftime('%Y-%m-%d') if not df.empty else None,
                'end_date': df.index[-1].strftime('%Y-%m-%d') if not df.empty else None,
                'results_count': data.get('resultsCount', 0),
                'query_count': data.get('queryCount', 0)
            }
            
            return OHLCVData(ticker=ticker, data=df, metadata=metadata)
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {ticker} from Polygon.io: {str(e)}")
    
    def _map_interval(self, interval: str) -> tuple[int, str]:
        """Map interval to Polygon.io multiplier and timespan"""
        interval_mapping = {
            '1m': (1, 'minute'),
            '5m': (5, 'minute'),
            '15m': (15, 'minute'),
            '30m': (30, 'minute'),
            '1h': (1, 'hour'),
            '60m': (1, 'hour'),
            '1d': (1, 'day'),
            '1wk': (1, 'week'),
            '1mo': (1, 'month'),
            '3mo': (3, 'month')
        }
        
        if interval not in interval_mapping:
            # Default to daily
            return 1, 'day'
            
        return interval_mapping[interval]
    
    def _parse_response(self, data: Dict) -> pd.DataFrame:
        """Parse Polygon.io response to DataFrame"""
        if 'results' not in data or not data['results']:
            return pd.DataFrame()
        
        results = data['results']
        
        # Convert to DataFrame
        df_data = []
        for bar in results:
            row = {
                'timestamp': pd.to_datetime(bar['t'], unit='ms'),
                'Open': bar['o'],
                'High': bar['h'],
                'Low': bar['l'],
                'Close': bar['c'],
                'Volume': bar['v'],
                'VWAP': bar.get('vw', 0),  # Volume weighted average price
                'Transactions': bar.get('n', 0)  # Number of transactions
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
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
        """
        results = {}
        
        for ticker in tqdm(tickers, desc="Fetching from Polygon.io"):
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
                
            except Exception as e:
                print(f"✗ Failed to fetch {ticker}: {str(e)}")
                continue
                
        return results
    
    def get_available_tickers(self) -> List[str]:
        """
        Get list of available tickers from Polygon.io
        """
        try:
            endpoint = f"{self.BASE_URL}/v3/reference/tickers"
            params = {
                'apiKey': self.config['api_key'],
                'market': 'stocks',
                'active': 'true',
                'limit': 100
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                tickers = [item['ticker'] for item in data.get('results', [])]
                return tickers
            else:
                # Return default list if API call fails
                return self._default_tickers()
                
        except:
            return self._default_tickers()
    
    def _default_tickers(self) -> List[str]:
        """Return default list of tickers"""
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            "JPM", "V", "JNJ", "WMT", "PG", "UNH", "HD", "DIS"
        ]
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the Polygon.io adapter"""
        return {
            'name': 'Polygon.io',
            'adapter_class': 'PolygonIOAdapter',
            'requires_api_key': True,
            'free_tier': True,
            'rate_limits': {
                'free': '5 API calls per minute',
                'basic': 'Unlimited',
                'professional': 'Unlimited with priority'
            },
            'supported_intervals': [
                '1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo', '3mo'
            ],
            'supported_timespans': [
                'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'
            ],
            'data_delay': 'Real-time for all tiers',
            'historical_data': '20+ years of historical data',
            'markets': 'US stocks, options, forex, crypto',
            'additional_features': [
                'Real-time WebSocket streaming',
                'News and sentiment data',
                'Options chain data',
                'Technical indicators',
                'Market holidays and hours',
                'Ticker details and fundamentals',
                'Aggregates and trades',
                'Snapshots'
            ],
            'api_key_url': 'https://polygon.io/dashboard/api-keys',
            'documentation': 'https://polygon.io/docs/stocks'
        }
    
    def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed information about a ticker
        This is a Polygon.io specific feature
        """
        endpoint = f"{self.BASE_URL}/v3/reference/tickers/{ticker}"
        params = {'apiKey': self.config['api_key']}
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'OK':
            return data.get('results', {})
        else:
            raise ValueError(f"Failed to get ticker details: {data.get('message', 'Unknown error')}")