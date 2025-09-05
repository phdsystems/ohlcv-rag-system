"""
OOP-based Retriever for OHLCV RAG System
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from src.core.base import BaseComponent
from src.core.interfaces import IRetriever, IVectorStore
from src.core.exceptions import RetrieverError


class EnhancedRetriever(BaseComponent, IRetriever):
    """
    Enhanced retriever with advanced retrieval strategies
    """
    
    def __init__(self, name: str = "EnhancedRetriever", config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced retriever
        
        Args:
            name: Retriever name
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # Configuration
        self.default_n_results = config.get('default_n_results', 5)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.rerank_enabled = config.get('rerank_enabled', True)
        
        # Components
        self.vector_store: Optional[IVectorStore] = None
        self.ranker = ResultRanker()
        
        # Statistics
        self._retrieval_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_results_returned': 0
        }
    
    def initialize(self) -> None:
        """Initialize the retriever"""
        self.log_info("Initializing enhanced retriever")
        
        if not self.validate_config():
            raise RetrieverError("Invalid configuration")
        
        self._initialized = True
        self.log_info("Retriever initialized")
    
    def validate_config(self) -> bool:
        """Validate retriever configuration"""
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            self.log_error(f"Invalid similarity threshold: {self.similarity_threshold}")
            return False
        
        if self.default_n_results < 1:
            self.log_error(f"Invalid default_n_results: {self.default_n_results}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get retriever status"""
        return {
            'name': self.name,
            'initialized': self._initialized,
            'vector_store_connected': self.vector_store is not None,
            'default_n_results': self.default_n_results,
            'similarity_threshold': self.similarity_threshold,
            'rerank_enabled': self.rerank_enabled,
            'statistics': self._retrieval_stats
        }
    
    def set_vector_store(self, vector_store: IVectorStore) -> None:
        """Set the vector store"""
        self.vector_store = vector_store
        self.log_info("Vector store connected")
    
    def retrieve(self, query: str, n_results: int = 5,
                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of relevant documents
        """
        if not self._initialized:
            self.initialize()
        
        if not self.vector_store:
            raise RetrieverError("Vector store not set", query=query)
        
        self.log_info(f"Retrieving for query: {query[:50]}...")
        
        try:
            # Perform vector search
            results = self.vector_store.search(query, n_results * 2, filters)  # Get more for reranking
            
            # Filter by similarity threshold
            filtered_results = [
                r for r in results 
                if r.get('score', 0) >= self.similarity_threshold
            ]
            
            # Rerank if enabled
            if self.rerank_enabled and len(filtered_results) > 0:
                filtered_results = self.rank_results(filtered_results, query)
            
            # Limit to requested number
            final_results = filtered_results[:n_results]
            
            # Update statistics
            self._update_stats(success=True, num_results=len(final_results))
            
            self.log_info(f"Retrieved {len(final_results)} results")
            return final_results
            
        except Exception as e:
            self._update_stats(success=False, num_results=0)
            raise RetrieverError(f"Retrieval failed: {str(e)}", query=query, num_results=n_results)
    
    def retrieve_by_similarity(self, reference: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents to a reference
        
        Args:
            reference: Reference document or text
            n_results: Number of results to return
            
        Returns:
            List of similar documents
        """
        # Use standard retrieve with the reference as query
        return self.retrieve(reference, n_results)
    
    def retrieve_by_metadata(self, metadata_filters: Dict[str, Any],
                            n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve by metadata filters
        
        Args:
            metadata_filters: Metadata filters
            n_results: Number of results to return
            
        Returns:
            List of documents matching filters
        """
        # Create a generic query and use filters
        generic_query = "OHLCV data analysis"
        return self.retrieve(generic_query, n_results, metadata_filters)
    
    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank retrieval results
        
        Args:
            results: List of results to rank
            query: Original query
            
        Returns:
            Ranked list of results
        """
        return self.ranker.rank(results, query)
    
    def retrieve_by_pattern(self, pattern_type: str, ticker: Optional[str] = None,
                           n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents by pattern type
        
        Args:
            pattern_type: Type of pattern to search for
            ticker: Optional ticker filter
            n_results: Number of results
            
        Returns:
            List of documents matching pattern
        """
        # Create pattern-specific query
        pattern_queries = {
            'uptrend': "strong uptrend bullish momentum higher highs ascending",
            'downtrend': "downtrend bearish momentum lower lows descending",
            'breakout': "breakout resistance breakthrough volume surge",
            'reversal': "trend reversal bottom top turning point",
            'consolidation': "sideways consolidation ranging flat"
        }
        
        query = pattern_queries.get(pattern_type.lower(), pattern_type)
        
        # Add ticker filter if provided
        filters = {'ticker': ticker} if ticker else None
        
        return self.retrieve(query, n_results, filters)
    
    def retrieve_by_indicator(self, indicator: str, condition: str, 
                            threshold: float, ticker: Optional[str] = None,
                            n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents by technical indicator conditions
        
        Args:
            indicator: Indicator name (e.g., 'RSI', 'MACD')
            condition: Condition ('above', 'below', 'equals')
            threshold: Threshold value
            ticker: Optional ticker filter
            n_results: Number of results
            
        Returns:
            List of documents matching indicator condition
        """
        # Create indicator-specific query
        query = f"{indicator} {condition} {threshold}"
        
        # Build metadata filter
        filters = {}
        if ticker:
            filters['ticker'] = ticker
        
        # Add indicator-specific filter if supported
        if indicator.upper() == 'RSI':
            if condition == 'above' and 'rsi_avg' in filters:
                filters['rsi_avg'] = {'$gte': threshold}
            elif condition == 'below' and 'rsi_avg' in filters:
                filters['rsi_avg'] = {'$lte': threshold}
        
        return self.retrieve(query, n_results, filters)
    
    def _update_stats(self, success: bool, num_results: int) -> None:
        """Update retrieval statistics"""
        self._retrieval_stats['total_queries'] += 1
        
        if success:
            self._retrieval_stats['successful_queries'] += 1
            
            # Update average results
            current_avg = self._retrieval_stats['avg_results_returned']
            total_successful = self._retrieval_stats['successful_queries']
            new_avg = ((current_avg * (total_successful - 1)) + num_results) / total_successful
            self._retrieval_stats['avg_results_returned'] = new_avg
        else:
            self._retrieval_stats['failed_queries'] += 1


class ResultRanker:
    """Rank and reorder retrieval results"""
    
    def __init__(self):
        self.weights = {
            'similarity_score': 0.4,
            'recency': 0.2,
            'completeness': 0.2,
            'relevance': 0.2
        }
    
    def rank(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank results based on multiple factors
        
        Args:
            results: List of results to rank
            query: Original query
            
        Returns:
            Ranked list of results
        """
        if not results:
            return results
        
        # Calculate scores for each result
        scored_results = []
        for result in results:
            score = self._calculate_score(result, query)
            result_with_score = result.copy()
            result_with_score['ranking_score'] = score
            scored_results.append(result_with_score)
        
        # Sort by ranking score
        ranked_results = sorted(scored_results, key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked_results
    
    def _calculate_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate ranking score for a result"""
        scores = {}
        
        # Similarity score (from vector search)
        scores['similarity_score'] = result.get('score', 0.0)
        
        # Recency score
        scores['recency'] = self._calculate_recency_score(result)
        
        # Completeness score
        scores['completeness'] = self._calculate_completeness_score(result)
        
        # Relevance score
        scores['relevance'] = self._calculate_relevance_score(result, query)
        
        # Calculate weighted sum
        total_score = sum(
            scores[factor] * weight 
            for factor, weight in self.weights.items()
        )
        
        return total_score
    
    def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """Calculate recency score based on date"""
        try:
            end_date_str = result.get('metadata', {}).get('end_date', '')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                days_old = (datetime.now() - end_date).days
                # Score decreases with age (max 1.0 for today, min 0.0 for >365 days)
                return max(0.0, 1.0 - (days_old / 365.0))
        except:
            pass
        return 0.5  # Default middle score
    
    def _calculate_completeness_score(self, result: Dict[str, Any]) -> float:
        """Calculate completeness score based on metadata"""
        metadata = result.get('metadata', {})
        
        # Check for important fields
        important_fields = ['trend', 'avg_volume', 'volatility', 'price_range', 'rsi_avg']
        present_fields = sum(1 for field in important_fields if field in metadata)
        
        return present_fields / len(important_fields)
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score based on query terms"""
        query_terms = query.lower().split()
        
        # Check document and summary for query terms
        document = result.get('document', '').lower()
        summary = result.get('summary', '').lower()
        content = document + ' ' + summary
        
        if not content:
            return 0.0
        
        # Count matching terms
        matching_terms = sum(1 for term in query_terms if term in content)
        
        return min(matching_terms / len(query_terms), 1.0)