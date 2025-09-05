import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from tqdm import tqdm

from .base import DataSourceAdapter, OHLCVData


class YahooFinanceAdapter(DataSourceAdapter):
    """Yahoo Finance data source adapter using yfinance"""
    
    def _validate_config(self) -> None:
        """Yahoo Finance doesn't require API keys"""
        pass
    
    def fetch_ohlcv(self,
                   ticker: str,
                   period: str = "1y",
                   interval: str = "1d",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> OHLCVData:
        """
        Fetch OHLCV data from Yahoo Finance
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Use date range if provided, otherwise use period
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date, interval=interval)
            else:
                df = stock.history(period=period, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Standardize column names
            df = self.standardize_dataframe(df)
            
            # Get additional metadata
            info = {}
            try:
                info = stock.info
            except:
                # Sometimes info fails, continue without it
                pass
            
            metadata = {
                'source': 'Yahoo Finance',
                'ticker': ticker,
                'period': period,
                'interval': interval,
                'records': len(df),
                'start_date': df.index[0].strftime('%Y-%m-%d') if not df.empty else None,
                'end_date': df.index[-1].strftime('%Y-%m-%d') if not df.empty else None,
                'company_name': info.get('longName', ticker),
                'exchange': info.get('exchange', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'timezone': info.get('exchangeTimezoneName', 'Unknown')
            }
            
            return OHLCVData(ticker=ticker, data=df, metadata=metadata)
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {ticker} from Yahoo Finance: {str(e)}")
    
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
        
        for ticker in tqdm(tickers, desc="Fetching from Yahoo Finance"):
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
        Get list of available tickers
        Note: Yahoo Finance doesn't provide a full list API, 
        so we return common tickers or allow any ticker
        """
        # Return some common tickers as example
        # In practice, Yahoo Finance accepts most global tickers
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            "JPM", "V", "JNJ", "WMT", "PG", "UNH", "HD", "DIS",
            "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
            "BTC-USD", "ETH-USD", "EUR=X", "GC=F", "CL=F"
        ]
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the Yahoo Finance adapter"""
        return {
            'name': 'Yahoo Finance',
            'adapter_class': 'YahooFinanceAdapter',
            'requires_api_key': False,
            'free_tier': True,
            'rate_limits': 'Undocumented, but generous',
            'supported_intervals': [
                '1m', '2m', '5m', '15m', '30m', '60m', '90m',
                '1h', '1d', '5d', '1wk', '1mo', '3mo'
            ],
            'supported_periods': [
                '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
            ],
            'data_delay': '15-20 minutes for real-time',
            'historical_data': 'Extensive historical data available',
            'markets': 'Global - stocks, ETFs, forex, crypto, commodities',
            'additional_features': [
                'Dividends and stock splits',
                'Company info and fundamentals',
                'Options data',
                'Institutional holders'
            ]
        }
    
    def fetch_with_fundamentals(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """
        Fetch OHLCV data along with fundamental data
        
        This is a Yahoo Finance specific feature
        """
        ohlcv_data = self.fetch_ohlcv(ticker, period)
        
        stock = yf.Ticker(ticker)
        
        # Get additional fundamental data
        fundamentals = {
            'info': stock.info,
            'financials': stock.financials.to_dict() if not stock.financials.empty else {},
            'balance_sheet': stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else {},
            'cashflow': stock.cashflow.to_dict() if not stock.cashflow.empty else {},
            'earnings': stock.earnings.to_dict() if not stock.earnings.empty else {},
            'dividends': stock.dividends.to_dict() if not stock.dividends.empty else {},
            'splits': stock.splits.to_dict() if not stock.splits.empty else {},
        }
        
        return {
            'ohlcv': ohlcv_data,
            'fundamentals': fundamentals
        }