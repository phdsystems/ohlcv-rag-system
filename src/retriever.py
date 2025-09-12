import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.vector_store import OHLCVVectorStore

class OHLCVRetriever:
    def __init__(self, vector_store: OHLCVVectorStore, chunks_file: str = "./data/ohlcv_chunks.json"):
        self.vector_store = vector_store
        self.chunks_file = chunks_file
        
        # Load chunks data for detailed retrieval
        with open(chunks_file, 'r') as f:
            self.chunks = json.load(f)
            
    def retrieve_relevant_context(self, query: str, n_results: int = 5, 
                                 ticker: Optional[str] = None,
                                 date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
        # Build filter
        filter_dict = {}
        if ticker:
            filter_dict['ticker'] = ticker
            
        # Perform vector search
        search_results = self.vector_store.search(query, n_results, filter_dict)
        
        # Enhance results with full chunk data
        enhanced_results = []
        for result in search_results['results']:
            chunk_index = result['metadata'].get('chunk_index')
            
            if chunk_index is not None and chunk_index < len(self.chunks):
                chunk_data = self.chunks[chunk_index]
                
                # Apply date range filter if specified
                if date_range:
                    start_filter, end_filter = date_range
                    chunk_start = datetime.strptime(chunk_data['start_date'], '%Y-%m-%d')
                    chunk_end = datetime.strptime(chunk_data['end_date'], '%Y-%m-%d')
                    filter_start = datetime.strptime(start_filter, '%Y-%m-%d')
                    filter_end = datetime.strptime(end_filter, '%Y-%m-%d')
                    
                    if not (chunk_start <= filter_end and chunk_end >= filter_start):
                        continue
                        
                enhanced_result = {
                    'relevance_score': result['relevance_score'],
                    'ticker': result['metadata']['ticker'],
                    'period': f"{result['metadata']['start_date']} to {result['metadata']['end_date']}",
                    'summary': chunk_data['summary'],
                    'metadata': result['metadata']
                }
                
                # Add data preview and full data if available
                if 'data' in chunk_data and chunk_data['data']:
                    enhanced_result['data_preview'] = self._create_data_preview(chunk_data['data'])
                    enhanced_result['full_data'] = chunk_data['data']
                else:
                    enhanced_result['data_preview'] = "No detailed data available"
                    enhanced_result['full_data'] = []
                enhanced_results.append(enhanced_result)
                
        return enhanced_results
    
    def _create_data_preview(self, data: List[Dict]) -> str:
        """Create a preview of OHLCV data with robust error handling"""
        if not data or not isinstance(data, list):
            return "No data available"
        
        try:
            df = pd.DataFrame(data)
            
            if df.empty:
                return "No data available"
            
            # Select key columns for preview
            preview_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in preview_columns if col in df.columns]
            
            if not available_columns:
                # If no standard OHLCV columns, show first few columns
                if len(df.columns) > 0:
                    available_columns = df.columns[:min(5, len(df.columns))]
                else:
                    return "No preview available"
            
            # Get first and last few rows
            if len(df) > 6:
                preview_df = pd.concat([df[available_columns].head(3), 
                                       df[available_columns].tail(3)])
            else:
                preview_df = df[available_columns]
                
            return preview_df.to_string()
            
        except Exception as e:
            return f"Data preview unavailable: {str(e)}"
    
    def retrieve_by_pattern(self, pattern_type: str, ticker: Optional[str] = None,
                           n_results: int = 5) -> List[Dict[str, Any]]:
        # Use pattern-specific search
        search_results = self.vector_store.search_by_pattern(pattern_type, ticker, n_results)
        
        # Enhance with full data
        return self._enhance_search_results(search_results)
    
    def retrieve_by_technical_indicator(self, indicator: str, condition: str,
                                       threshold: float, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        # Build query based on technical indicator
        indicator_queries = {
            'RSI': {
                '>': f"RSI above {threshold} overbought conditions",
                '<': f"RSI below {threshold} oversold conditions",
                '=': f"RSI around {threshold}"
            },
            'volume': {
                '>': f"High volume above average {threshold} heavy trading",
                '<': f"Low volume below average {threshold} light trading",
                '=': f"Average volume around {threshold}"
            },
            'volatility': {
                '>': f"High volatility above {threshold} large price swings",
                '<': f"Low volatility below {threshold} stable prices",
                '=': f"Moderate volatility around {threshold}"
            }
        }
        
        query = indicator_queries.get(indicator, {}).get(condition, 
                                                         f"{indicator} {condition} {threshold}")
        
        filter_dict = {'ticker': ticker} if ticker else None
        search_results = self.vector_store.search(query, n_results=10, filter_dict=filter_dict)
        
        # Filter results based on actual indicator values
        filtered_results = []
        for result in search_results['results']:
            chunk_index = result['metadata'].get('chunk_index')
            if chunk_index is not None and chunk_index < len(self.chunks):
                chunk_data = self.chunks[chunk_index]
                
                # Check if indicator condition is met
                if self._check_indicator_condition(chunk_data, indicator, condition, threshold):
                    enhanced_result = {
                        'relevance_score': result['relevance_score'],
                        'ticker': result['metadata']['ticker'],
                        'period': f"{result['metadata']['start_date']} to {result['metadata']['end_date']}",
                        'summary': chunk_data['summary'],
                        'metadata': result['metadata'],
                        'indicator_value': self._get_indicator_value(chunk_data, indicator),
                        'condition_met': True
                    }
                    filtered_results.append(enhanced_result)
                    
        return filtered_results[:n_results]
    
    def _check_indicator_condition(self, chunk_data: Dict, indicator: str, 
                                  condition: str, threshold: float) -> bool:
        value = self._get_indicator_value(chunk_data, indicator)
        
        if value is None:
            return False
            
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '=':
            return abs(value - threshold) < threshold * 0.1  # Within 10% of threshold
        return False
    
    def _get_indicator_value(self, chunk_data: Dict, indicator: str) -> Optional[float]:
        metadata = chunk_data.get('metadata', {})
        
        if indicator == 'RSI':
            return metadata.get('rsi_avg')
        elif indicator == 'volume':
            return metadata.get('avg_volume')
        elif indicator == 'volatility':
            return metadata.get('volatility')
        return None
    
    def retrieve_similar_patterns(self, ticker: str, date: str, 
                                 n_results: int = 5) -> List[Dict[str, Any]]:
        # Find the chunk containing the specified date
        target_chunk = None
        for chunk in self.chunks:
            if chunk['ticker'] == ticker:
                chunk_start = datetime.strptime(chunk['start_date'], '%Y-%m-%d')
                chunk_end = datetime.strptime(chunk['end_date'], '%Y-%m-%d')
                target_date = datetime.strptime(date, '%Y-%m-%d')
                
                if chunk_start <= target_date <= chunk_end:
                    target_chunk = chunk
                    break
                    
        if not target_chunk:
            return []
            
        # Create query from target chunk characteristics
        query = f"""
        Find similar price patterns to {ticker} around {date}:
        Trend: {target_chunk['metadata']['trend']}
        Volatility: {target_chunk['metadata']['volatility']:.4f}
        Price action characteristics
        """
        
        # Search for similar patterns
        results = self.vector_store.search(query, n_results + 1)  # +1 to exclude self
        
        # Filter out the target chunk itself and enhance results
        enhanced_results = []
        for result in results['results']:
            if (result['metadata']['ticker'] == ticker and 
                result['metadata']['start_date'] == target_chunk['start_date']):
                continue
                
            chunk_index = result['metadata'].get('chunk_index')
            if chunk_index is not None and chunk_index < len(self.chunks):
                chunk_data = self.chunks[chunk_index]
                enhanced_results.append({
                    'relevance_score': result['relevance_score'],
                    'ticker': result['metadata']['ticker'],
                    'period': f"{result['metadata']['start_date']} to {result['metadata']['end_date']}",
                    'summary': chunk_data['summary'],
                    'metadata': result['metadata'],
                    'similarity_metrics': {
                        'trend_match': target_chunk['metadata']['trend'] == result['metadata']['trend'],
                        'volatility_diff': abs(target_chunk['metadata']['volatility'] - 
                                             result['metadata']['volatility'])
                    }
                })
                
        return enhanced_results[:n_results]
    
    def _enhance_search_results(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        enhanced_results = []
        
        for result in search_results['results']:
            chunk_index = result['metadata'].get('chunk_index')
            
            if chunk_index is not None and chunk_index < len(self.chunks):
                chunk_data = self.chunks[chunk_index]
                enhanced_result = {
                    'relevance_score': result['relevance_score'],
                    'ticker': result['metadata']['ticker'],
                    'period': f"{result['metadata']['start_date']} to {result['metadata']['end_date']}",
                    'summary': chunk_data['summary'],
                    'metadata': result['metadata']
                }
                enhanced_results.append(enhanced_result)
                
        return enhanced_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the retriever component"""
        return {
            'component': 'OHLCVRetriever',
            'chunks_loaded': len(self.chunks),
            'chunks_file': self.chunks_file,
            'vector_store_connected': self.vector_store is not None,
            'initialized': True
        }
