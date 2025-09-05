from typing import Dict, Any, Optional
from .base import DataSourceAdapter
from .yahoo_finance import YahooFinanceAdapter
from .alpha_vantage import AlphaVantageAdapter
from .polygon_io import PolygonIOAdapter
from .csv_adapter import CSVAdapter


class DataSourceManager:
    """Manager for creating and managing data source adapters"""
    
    # Registry of available adapters
    ADAPTERS = {
        'yahoo': YahooFinanceAdapter,
        'yahoo_finance': YahooFinanceAdapter,
        'yfinance': YahooFinanceAdapter,
        'alpha_vantage': AlphaVantageAdapter,
        'alphavantage': AlphaVantageAdapter,
        'polygon': PolygonIOAdapter,
        'polygon_io': PolygonIOAdapter,
        'csv': CSVAdapter,
        'file': CSVAdapter,
        'local': CSVAdapter
    }
    
    @classmethod
    def create_adapter(cls, 
                      source: str, 
                      config: Optional[Dict[str, Any]] = None) -> DataSourceAdapter:
        """
        Create a data source adapter
        
        Args:
            source: Name of the data source (yahoo, alpha_vantage, polygon, csv)
            config: Configuration for the adapter (API keys, paths, etc.)
            
        Returns:
            Instance of the specified adapter
            
        Raises:
            ValueError: If source is not recognized
        """
        source_lower = source.lower()
        
        if source_lower not in cls.ADAPTERS:
            available = ', '.join(cls.get_available_sources())
            raise ValueError(f"Unknown data source: {source}. Available: {available}")
        
        adapter_class = cls.ADAPTERS[source_lower]
        return adapter_class(config=config)
    
    @classmethod
    def get_available_sources(cls) -> list[str]:
        """Get list of available data sources"""
        # Return unique source names
        sources = set()
        for key in cls.ADAPTERS.keys():
            if key in ['yahoo', 'alpha_vantage', 'polygon', 'csv']:
                sources.add(key)
        return sorted(list(sources))
    
    @classmethod
    def get_adapter_info(cls, source: str) -> Dict[str, Any]:
        """
        Get information about a specific adapter
        
        Args:
            source: Name of the data source
            
        Returns:
            Dictionary with adapter information
        """
        adapter = cls.create_adapter(source)
        return adapter.get_adapter_info()
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> DataSourceAdapter:
        """
        Create adapter from configuration dictionary
        
        Args:
            config: Configuration with 'source' key and adapter-specific config
            
        Example:
            config = {
                'source': 'polygon',
                'api_key': 'your_api_key'
            }
        """
        source = config.pop('source', 'yahoo')  # Default to Yahoo Finance
        return cls.create_adapter(source, config)
    
    @classmethod
    def get_all_adapters_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all available adapters"""
        info = {}
        for source in cls.get_available_sources():
            try:
                # Create adapter with empty config to get info
                adapter = cls.create_adapter(source, {})
                info[source] = adapter.get_adapter_info()
            except ValueError:
                # Skip adapters that require config for initialization
                info[source] = {
                    'name': source,
                    'error': 'Requires configuration to initialize'
                }
        return info