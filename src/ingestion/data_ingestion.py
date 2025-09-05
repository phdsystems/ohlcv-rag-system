"""
OOP-based Data Ingestion Module for OHLCV RAG System
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import ta
from tqdm import tqdm
import os
import json
import time

from src.core.base import DataProcessor
from src.core.interfaces import IDataIngestion
from src.core.models import OHLCVDataModel, ChunkModel, TrendType
from src.core.exceptions import DataIngestionError, DataValidationError
from src.data_adapters import DataSourceManager


class DataIngestionEngine(DataProcessor, IDataIngestion):
    """
    Main data ingestion engine implementing OOP principles
    """
    
    def __init__(self, name: str = "DataIngestionEngine", config: Optional[Dict[str, Any]] = None):
        """
        Initialize data ingestion engine
        
        Args:
            name: Engine name
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # Configuration
        self.source = config.get('source', 'yahoo')
        self.interval = config.get('interval', '1d')
        self.period = config.get('period', '1y')
        self.window_size = config.get('window_size', 30)
        
        # Components
        self.adapter = None
        self.indicator_calculator = TechnicalIndicatorCalculator()
        self.chunk_creator = ChunkCreator(window_size=self.window_size)
        self.data_validator = DataValidator()
        
        # Data storage
        self.data_models: Dict[str, OHLCVDataModel] = {}
        
    def initialize(self) -> None:
        """Initialize the data ingestion engine"""
        self.log_info("Initializing data ingestion engine")
        
        # Validate configuration
        if not self.validate_config():
            raise DataIngestionError("Invalid configuration")
        
        # Initialize adapter
        adapter_config = self.config.get('adapter_config', {})
        self.adapter = DataSourceManager.create_adapter(self.source, adapter_config)
        
        self._initialized = True
        self.log_info(f"Initialized with source: {self.source}")
    
    def validate_config(self) -> bool:
        """Validate engine configuration"""
        required_fields = ['source']
        for field in required_fields:
            if field not in self.config and not hasattr(self, field):
                self.log_error(f"Missing required configuration: {field}")
                return False
        
        # Validate source
        available_sources = DataSourceManager.get_available_sources()
        if self.source not in available_sources:
            self.log_error(f"Invalid source: {self.source}. Available: {available_sources}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'name': self.name,
            'initialized': self._initialized,
            'source': self.source,
            'interval': self.interval,
            'period': self.period,
            'tickers_loaded': list(self.data_models.keys()),
            'processing_stats': self.get_processing_stats()
        }
    
    def fetch_data(self, tickers: List[str], start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for given tickers
        
        Args:
            tickers: List of ticker symbols
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary mapping tickers to DataFrames
        """
        if not self._initialized:
            self.initialize()
        
        self.log_info(f"Fetching data for {len(tickers)} tickers from {self.source}")
        
        # Fetch data using adapter
        start_time = time.time()
        try:
            ohlcv_data_dict = self.adapter.fetch_multiple(
                tickers=tickers,
                period=self.period,
                interval=self.interval,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            raise DataIngestionError(f"Failed to fetch data: {str(e)}", source=self.source)
        
        # Process fetched data
        result = {}
        for ticker, ohlcv_data in ohlcv_data_dict.items():
            # Create data model
            model = OHLCVDataModel(
                ticker=ticker,
                data=ohlcv_data.data,
                interval=self.interval,
                period=self.period,
                source=self.source,
                metadata=ohlcv_data.metadata
            )
            
            # Validate data
            if self.data_validator.validate(model):
                model.validated = True
                # Add indicators
                model = self.indicator_calculator.calculate_all(model)
                self.data_models[ticker] = model
                result[ticker] = model.data
            else:
                self.log_warning(f"Validation failed for {ticker}")
        
        processing_time = time.time() - start_time
        self.update_stats(success=True, processing_time=processing_time)
        
        self.log_info(f"Successfully fetched data for {len(result)} tickers in {processing_time:.2f}s")
        return result
    
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to data"""
        return self.indicator_calculator.add_to_dataframe(data)
    
    def create_chunks(self, data: Dict[str, pd.DataFrame], window_size: int) -> List[Dict[str, Any]]:
        """Create data chunks for vector storage"""
        chunks = []
        
        for ticker, df in data.items():
            if ticker in self.data_models:
                model = self.data_models[ticker]
                ticker_chunks = self.chunk_creator.create_chunks(model, window_size)
                chunks.extend(ticker_chunks)
        
        self.log_info(f"Created {len(chunks)} chunks")
        return chunks
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate OHLCV data"""
        return self.data_validator.validate_dataframe(data)
    
    def save_data(self, data: Any, output_path: str) -> None:
        """Save processed data"""
        os.makedirs(output_path, exist_ok=True)
        
        # Save data models
        for ticker, model in self.data_models.items():
            # Save CSV
            csv_path = os.path.join(output_path, f"{ticker}_ohlcv.csv")
            model.data.to_csv(csv_path)
            
            # Save metadata
            metadata_path = os.path.join(output_path, f"{ticker}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(model.get_statistics(), f, indent=2, default=str)
        
        # Save chunks
        chunks = self.create_chunks(
            {ticker: model.data for ticker, model in self.data_models.items()},
            self.window_size
        )
        
        chunks_path = os.path.join(output_path, "chunks.json")
        with open(chunks_path, 'w') as f:
            json.dump([self._chunk_to_dict(chunk) for chunk in chunks], f, indent=2, default=str)
        
        self.log_info(f"Saved data to {output_path}")
    
    def process(self, data: Any) -> Any:
        """Process data (implementation of DataProcessor abstract method)"""
        return self.preprocess(data)
    
    def preprocess(self, data: Any) -> Any:
        """Preprocess data"""
        if isinstance(data, pd.DataFrame):
            return self.data_validator.clean_dataframe(data)
        return data
    
    def postprocess(self, data: Any) -> Any:
        """Postprocess data"""
        if isinstance(data, pd.DataFrame):
            return self.add_indicators(data)
        return data
    
    def _chunk_to_dict(self, chunk: Any) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        if isinstance(chunk, ChunkModel):
            return {
                'id': chunk.id,
                'ticker': chunk.ticker,
                'start_date': chunk.start_date,
                'end_date': chunk.end_date,
                'summary': chunk.summary,
                'metadata': chunk.metadata
            }
        return chunk


class TechnicalIndicatorCalculator:
    """Calculate technical indicators for OHLCV data"""
    
    def __init__(self):
        self.indicators_config = {
            'sma': [20, 50],
            'ema': [12, 26],
            'rsi_period': 14,
            'bb_period': 20,
            'volume_ma': 20
        }
    
    def calculate_all(self, model: OHLCVDataModel) -> OHLCVDataModel:
        """Calculate all indicators for data model"""
        df = model.data
        
        if len(df) < 20:  # Not enough data
            return model
        
        try:
            # Moving averages
            for period in self.indicators_config['sma']:
                model.add_indicator(f'SMA_{period}', ta.trend.sma_indicator(df['Close'], window=period))
            
            for period in self.indicators_config['ema']:
                model.add_indicator(f'EMA_{period}', ta.trend.ema_indicator(df['Close'], window=period))
            
            # RSI
            model.add_indicator('RSI', ta.momentum.rsi(df['Close'], window=self.indicators_config['rsi_period']))
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            model.add_indicator('MACD', macd.macd())
            model.add_indicator('MACD_signal', macd.macd_signal())
            model.add_indicator('MACD_diff', macd.macd_diff())
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'], window=self.indicators_config['bb_period'])
            model.add_indicator('BB_upper', bb.bollinger_hband())
            model.add_indicator('BB_middle', bb.bollinger_mavg())
            model.add_indicator('BB_lower', bb.bollinger_lband())
            
            # Volume indicators
            model.add_indicator('Volume_MA', ta.volume.volume_weighted_average_price(
                df['High'], df['Low'], df['Close'], df['Volume']
            ))
            
            # Price changes
            model.add_indicator('Price_Change', df['Close'].pct_change())
            model.add_indicator('Price_Change_5d', df['Close'].pct_change(periods=5))
            model.add_indicator('Price_Change_20d', df['Close'].pct_change(periods=20))
            
            # Add indicators to dataframe
            for name, series in model.indicators.items():
                df[name] = series
            
            model.data = df
            
        except Exception as e:
            print(f"Warning: Could not calculate all indicators: {e}")
        
        return model
    
    def add_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicators directly to dataframe"""
        temp_model = OHLCVDataModel(
            ticker="temp",
            data=df.copy(),
            interval="1d",
            period="1y",
            source="unknown"
        )
        
        result_model = self.calculate_all(temp_model)
        return result_model.data


class ChunkCreator:
    """Create chunks from OHLCV data"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.overlap_ratio = 0.5
    
    def create_chunks(self, model: OHLCVDataModel, window_size: Optional[int] = None) -> List[ChunkModel]:
        """Create chunks from data model"""
        window_size = window_size or self.window_size
        chunks = []
        
        df = model.data.dropna()
        if df.empty:
            return chunks
        
        step = int(window_size * (1 - self.overlap_ratio))
        
        for i in range(0, len(df) - window_size + 1, step):
            window_df = df.iloc[i:i + window_size]
            
            chunk = self._create_single_chunk(window_df, model.ticker, model.source)
            chunks.append(chunk)
        
        return chunks
    
    def _create_single_chunk(self, window_df: pd.DataFrame, ticker: str, source: str) -> ChunkModel:
        """Create a single chunk from window data"""
        import uuid
        
        chunk_id = str(uuid.uuid4())
        start_date = window_df.index[0].strftime('%Y-%m-%d')
        end_date = window_df.index[-1].strftime('%Y-%m-%d')
        
        # Create summary
        summary = self._create_summary(window_df, ticker)
        
        # Create metadata
        metadata = self._create_metadata(window_df, source)
        
        return ChunkModel(
            id=chunk_id,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            data=window_df.to_dict('records'),
            summary=summary,
            metadata=metadata
        )
    
    def _create_summary(self, window_df: pd.DataFrame, ticker: str) -> str:
        """Create summary for window"""
        start_date = window_df.index[0].strftime('%Y-%m-%d')
        end_date = window_df.index[-1].strftime('%Y-%m-%d')
        
        price_change = ((window_df['Close'].iloc[-1] - window_df['Close'].iloc[0]) / 
                       window_df['Close'].iloc[0] * 100)
        
        avg_volume = window_df['Volume'].mean()
        
        summary = f"""
        {ticker} from {start_date} to {end_date}:
        - Price movement: {price_change:.2f}%
        - Price range: ${window_df['Low'].min():.2f} - ${window_df['High'].max():.2f}
        - Average volume: {avg_volume:,.0f}
        """
        
        if 'RSI' in window_df.columns:
            rsi_avg = window_df['RSI'].mean()
            summary += f"\n- Average RSI: {rsi_avg:.2f}"
        
        return summary.strip()
    
    def _create_metadata(self, window_df: pd.DataFrame, source: str) -> Dict[str, Any]:
        """Create metadata for chunk"""
        metadata = {
            'source': source,
            'window_size': len(window_df),
            'avg_volume': float(window_df['Volume'].mean()),
            'price_range': {
                'high': float(window_df['High'].max()),
                'low': float(window_df['Low'].min()),
                'open': float(window_df['Open'].iloc[0]),
                'close': float(window_df['Close'].iloc[-1])
            },
            'volatility': float(window_df['Close'].pct_change().std()),
            'trend': self._identify_trend(window_df)
        }
        
        if 'RSI' in window_df.columns:
            metadata['rsi_avg'] = float(window_df['RSI'].mean())
        
        return metadata
    
    def _identify_trend(self, df: pd.DataFrame) -> str:
        """Identify trend in window"""
        if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
            if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1]:
                if df['Close'].iloc[-1] > df['SMA_20'].iloc[-1]:
                    return TrendType.UPTREND.value
                return TrendType.SIDEWAYS.value
            else:
                if df['Close'].iloc[-1] < df['SMA_20'].iloc[-1]:
                    return TrendType.DOWNTREND.value
                return TrendType.SIDEWAYS.value
        
        # Fallback: use price change
        price_change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
        if price_change > 0.05:
            return TrendType.UPTREND.value
        elif price_change < -0.05:
            return TrendType.DOWNTREND.value
        return TrendType.SIDEWAYS.value


class DataValidator:
    """Validate OHLCV data"""
    
    def __init__(self):
        self.required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        self.min_rows = 10
    
    def validate(self, model: OHLCVDataModel) -> bool:
        """Validate data model"""
        return self.validate_dataframe(model.data)
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate dataframe"""
        if df is None or df.empty:
            return False
        
        # Check required columns
        for col in self.required_columns:
            if col not in df.columns:
                return False
        
        # Check minimum rows
        if len(df) < self.min_rows:
            return False
        
        # Check for valid values
        if df[self.required_columns].isnull().all().any():
            return False
        
        # Check price consistency
        if not self._validate_price_consistency(df):
            return False
        
        return True
    
    def _validate_price_consistency(self, df: pd.DataFrame) -> bool:
        """Validate price consistency (High >= Low, etc.)"""
        try:
            # High should be >= Low
            if (df['High'] < df['Low']).any():
                return False
            
            # High should be >= Close and Open
            if (df['High'] < df['Close']).any() or (df['High'] < df['Open']).any():
                return False
            
            # Low should be <= Close and Open
            if (df['Low'] > df['Close']).any() or (df['Low'] > df['Open']).any():
                return False
            
            # Volume should be positive
            if (df['Volume'] < 0).any():
                return False
            
            return True
        except:
            return False
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataframe"""
        if df is None or df.empty:
            return df
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by index
        df = df.sort_index()
        
        # Forward fill missing values (limited)
        df = df.fillna(method='ffill', limit=2)
        
        # Remove rows with all NaN
        df = df.dropna(how='all')
        
        return df