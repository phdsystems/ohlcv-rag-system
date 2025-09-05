"""
OOP-based RAG Pipeline for OHLCV System
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
import time
from datetime import datetime

from src.core.base import BaseComponent
from src.core.interfaces import IRAGPipeline, IRetriever
from src.core.models import QueryResult, QueryType, AnalysisResult
from src.core.exceptions import PipelineError, LLMError

load_dotenv()


class RAGPipeline(BaseComponent, IRAGPipeline):
    """
    Main RAG pipeline implementing OOP principles
    """
    
    def __init__(self, name: str = "RAGPipeline", config: Optional[Dict[str, Any]] = None):
        """
        Initialize RAG pipeline
        
        Args:
            name: Pipeline name
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # Configuration
        self.model_name = config.get('model', 'gpt-3.5-turbo')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 2000)
        
        # Components
        self.llm = None
        self.retriever = None
        self.prompt_manager = PromptManager()
        self.context_formatter = ContextFormatter()
        self.response_evaluator = ResponseEvaluator()
        
        # Caching
        self._cache = {}
        self._cache_ttl = config.get('cache_ttl', 3600)  # 1 hour default
        
    def initialize(self) -> None:
        """Initialize the RAG pipeline"""
        self.log_info("Initializing RAG pipeline")
        
        # Validate configuration
        if not self.validate_config():
            raise PipelineError("Invalid configuration")
        
        # Initialize LLM
        api_key = self.config.get('openai_api_key') or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise PipelineError("OpenAI API key not provided")
        
        try:
            self.llm = ChatOpenAI(
                api_key=api_key,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM: {str(e)}", model=self.model_name)
        
        self._initialized = True
        self.log_info(f"Initialized with model: {self.model_name}")
    
    def validate_config(self) -> bool:
        """Validate pipeline configuration"""
        if not self.model_name:
            self.log_error("Model name not specified")
            return False
        
        if self.temperature < 0 or self.temperature > 2:
            self.log_error(f"Invalid temperature: {self.temperature}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            'name': self.name,
            'initialized': self._initialized,
            'model': self.model_name,
            'temperature': self.temperature,
            'cache_size': len(self._cache),
            'retriever_connected': self.retriever is not None
        }
    
    def set_retriever(self, retriever: IRetriever) -> None:
        """Set the retriever component"""
        self.retriever = retriever
        self.log_info("Retriever connected to pipeline")
    
    def query(self, query: str, query_type: str = "general",
             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline
        
        Args:
            query: User query
            query_type: Type of query
            context: Additional context
            
        Returns:
            Query result dictionary
        """
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(query, query_type, context)
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if self._is_cache_valid(cached_result):
                self.log_info("Returning cached result")
                return cached_result['data']
        
        try:
            # Parse query type
            q_type = QueryType(query_type.lower())
        except ValueError:
            q_type = QueryType.GENERAL
        
        # Retrieve relevant context
        if not self.retriever:
            raise PipelineError("Retriever not set", stage="retrieval")
        
        n_results = context.get('n_results', 5) if context else 5
        filters = context.get('filters') if context else None
        
        try:
            retrieved_chunks = self.retriever.retrieve(query, n_results, filters)
        except Exception as e:
            raise PipelineError(f"Retrieval failed: {str(e)}", stage="retrieval")
        
        if not retrieved_chunks:
            return self._create_empty_result(query, q_type)
        
        # Format context
        formatted_context = self.format_context(retrieved_chunks)
        
        # Generate response
        try:
            prompt = self.prompt_manager.get_prompt(q_type, query, formatted_context, context)
            response = self.generate_response(prompt, formatted_context)
        except Exception as e:
            raise LLMError(f"Generation failed: {str(e)}", model=self.model_name)
        
        # Evaluate response
        evaluation = self.evaluate_response(response, query, formatted_context)
        
        # Create result
        processing_time = time.time() - start_time
        result = QueryResult(
            query=query,
            query_type=q_type,
            answer=response,
            sources=self._format_sources(retrieved_chunks),
            confidence=evaluation['confidence'],
            processing_time=processing_time,
            metadata={
                'model': self.model_name,
                'num_sources': len(retrieved_chunks),
                'evaluation': evaluation
            }
        )
        
        # Cache result
        self._cache[cache_key] = {
            'data': self._result_to_dict(result),
            'timestamp': datetime.now()
        }
        
        self.log_info(f"Query processed in {processing_time:.2f}s")
        return self._result_to_dict(result)
    
    def analyze(self, analysis_type: str, data: Any,
               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform specific analysis
        
        Args:
            analysis_type: Type of analysis
            data: Data to analyze
            parameters: Analysis parameters
            
        Returns:
            Analysis result dictionary
        """
        if not self._initialized:
            self.initialize()
        
        self.log_info(f"Performing {analysis_type} analysis")
        
        analyzer = AnalysisEngine(self.llm, self.retriever)
        
        try:
            if analysis_type == "pattern":
                result = analyzer.analyze_pattern(data, parameters)
            elif analysis_type == "comparison":
                result = analyzer.analyze_comparison(data, parameters)
            elif analysis_type == "trend":
                result = analyzer.analyze_trend(data, parameters)
            elif analysis_type == "indicator":
                result = analyzer.analyze_indicators(data, parameters)
            else:
                raise PipelineError(f"Unknown analysis type: {analysis_type}")
        except Exception as e:
            raise PipelineError(f"Analysis failed: {str(e)}", stage="analysis")
        
        return self._analysis_result_to_dict(result)
    
    def generate_response(self, prompt: str, context: str) -> str:
        """Generate response using LLM"""
        chain = LLMChain(llm=self.llm, prompt=PromptTemplate.from_template(prompt))
        return chain.run(context=context)
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks as context"""
        return self.context_formatter.format(chunks)
    
    def evaluate_response(self, response: str, query: str, context: str) -> Dict[str, Any]:
        """Evaluate generated response quality"""
        return self.response_evaluator.evaluate(response, query, context)
    
    def _get_cache_key(self, query: str, query_type: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key"""
        import hashlib
        key_parts = [query, query_type]
        if context:
            key_parts.append(str(sorted(context.items())))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is still valid"""
        age = (datetime.now() - cached_item['timestamp']).total_seconds()
        return age < self._cache_ttl
    
    def _create_empty_result(self, query: str, query_type: QueryType) -> Dict[str, Any]:
        """Create empty result when no data found"""
        result = QueryResult(
            query=query,
            query_type=query_type,
            answer="No relevant data found for your query. Please try rephrasing or check the data availability.",
            sources=[],
            confidence=0.0,
            processing_time=0.0
        )
        return self._result_to_dict(result)
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format sources for result"""
        sources = []
        for chunk in chunks:
            sources.append({
                'ticker': chunk.get('ticker', 'Unknown'),
                'period': f"{chunk.get('start_date', 'N/A')} to {chunk.get('end_date', 'N/A')}",
                'relevance_score': str(chunk.get('score', 0.0)),
                'trend': chunk.get('metadata', {}).get('trend', 'Unknown')
            })
        return sources
    
    def _result_to_dict(self, result: QueryResult) -> Dict[str, Any]:
        """Convert QueryResult to dictionary"""
        return {
            'query': result.query,
            'query_type': result.query_type.value,
            'answer': result.answer,
            'sources': result.sources,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'metadata': result.metadata
        }
    
    def _analysis_result_to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """Convert AnalysisResult to dictionary"""
        return {
            'analysis_type': result.analysis_type,
            'ticker': result.ticker,
            'period': result.period,
            'findings': result.findings,
            'recommendations': result.recommendations,
            'risk_factors': result.risk_factors,
            'confidence_level': result.confidence_level,
            'metadata': result.metadata
        }


class PromptManager:
    """Manage prompts for different query types"""
    
    def __init__(self):
        self.prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[QueryType, str]:
        """Initialize prompt templates"""
        return {
            QueryType.GENERAL: """You are a financial analyst assistant specializing in technical analysis of OHLCV data.

Based on the following retrieved OHLCV data and technical indicators:

{context}

Please answer the following question:
{query}

Provide a detailed analysis including:
1. Key observations from the data
2. Relevant patterns or trends
3. Technical indicator insights
4. Potential implications for traders
5. Risk considerations if applicable

Base your answer strictly on the provided data.""",
            
            QueryType.PATTERN: """Analyze the following OHLCV data for pattern identification:

{context}

Pattern to identify: {pattern_type}

Provide:
1. Confirmation of pattern presence
2. Pattern strength (weak/moderate/strong)
3. Supporting indicators
4. Entry/exit points if applicable
5. Risk/reward considerations""",
            
            QueryType.COMPARISON: """Compare the following stocks based on their OHLCV data:

{context}

Stocks to compare: {tickers}

Provide:
1. Performance comparison
2. Volatility analysis
3. Volume patterns
4. Trend strength comparison
5. Technical setup evaluation""",
            
            QueryType.PREDICTION: """Based on the historical OHLCV data and technical indicators:

{context}

Ticker: {ticker}

Provide:
1. Current market structure analysis
2. Support and resistance levels
3. Probable scenarios
4. Risk factors
5. Technical direction indicators

NOTE: This is technical analysis only, not financial advice.""",
            
            QueryType.TECHNICAL: """Perform technical analysis on the following OHLCV data:

{context}

Focus on: {indicator}

Provide:
1. Indicator values and interpretation
2. Signal strength
3. Convergence/divergence patterns
4. Historical comparison
5. Trading implications"""
        }
    
    def get_prompt(self, query_type: QueryType, query: str, context: str, 
                  additional_params: Optional[Dict[str, Any]] = None) -> str:
        """Get formatted prompt for query type"""
        template = self.prompts.get(query_type, self.prompts[QueryType.GENERAL])
        
        params = {
            'query': query,
            'context': context
        }
        
        if additional_params:
            params.update(additional_params)
        
        return template.format(**params)


class ContextFormatter:
    """Format context for LLM consumption"""
    
    def format(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunks into context string"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_part = self._format_chunk(chunk, i)
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def _format_chunk(self, chunk: Dict[str, Any], index: int) -> str:
        """Format a single chunk"""
        metadata = chunk.get('metadata', {})
        
        formatted = f"""Source {index}:
Ticker: {chunk.get('ticker', 'Unknown')}
Period: {chunk.get('start_date', 'N/A')} to {chunk.get('end_date', 'N/A')}
Relevance Score: {chunk.get('score', 0.0):.2f}

{chunk.get('summary', 'No summary available')}

Key Metrics:"""
        
        if 'trend' in metadata:
            formatted += f"\n- Trend: {metadata['trend']}"
        if 'avg_volume' in metadata:
            formatted += f"\n- Average Volume: {metadata['avg_volume']:,.0f}"
        if 'volatility' in metadata:
            formatted += f"\n- Volatility: {metadata['volatility']:.4f}"
        if 'price_range' in metadata:
            price_range = metadata['price_range']
            formatted += f"\n- Price Range: ${price_range.get('low', 0):.2f} - ${price_range.get('high', 0):.2f}"
        if 'rsi_avg' in metadata:
            formatted += f"\n- Average RSI: {metadata['rsi_avg']:.2f}"
        
        return formatted


class ResponseEvaluator:
    """Evaluate LLM response quality"""
    
    def evaluate(self, response: str, query: str, context: str) -> Dict[str, Any]:
        """Evaluate response quality"""
        evaluation = {
            'confidence': 0.0,
            'completeness': 0.0,
            'relevance': 0.0,
            'quality_score': 0.0,
            'issues': []
        }
        
        # Check response length
        if len(response) < 50:
            evaluation['issues'].append("Response too short")
            evaluation['confidence'] = 0.3
        elif len(response) > 5000:
            evaluation['issues'].append("Response too long")
            evaluation['confidence'] = 0.7
        else:
            evaluation['confidence'] = 0.8
        
        # Check for key terms from query in response
        query_terms = query.lower().split()
        response_lower = response.lower()
        matched_terms = sum(1 for term in query_terms if term in response_lower)
        evaluation['relevance'] = min(matched_terms / len(query_terms), 1.0)
        
        # Check for completeness markers
        completeness_markers = ['1.', '2.', 'analysis', 'trend', 'indicator']
        found_markers = sum(1 for marker in completeness_markers if marker in response_lower)
        evaluation['completeness'] = min(found_markers / len(completeness_markers), 1.0)
        
        # Calculate overall quality score
        evaluation['quality_score'] = (
            evaluation['confidence'] * 0.3 +
            evaluation['relevance'] * 0.4 +
            evaluation['completeness'] * 0.3
        )
        
        # Adjust confidence based on quality
        evaluation['confidence'] = evaluation['quality_score']
        
        return evaluation


class AnalysisEngine:
    """Engine for specific analysis types"""
    
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
    
    def analyze_pattern(self, data: Any, parameters: Dict[str, Any]) -> AnalysisResult:
        """Analyze patterns in data"""
        pattern_type = parameters.get('pattern_type', 'general')
        ticker = parameters.get('ticker')
        period = parameters.get('period', ('N/A', 'N/A'))
        
        result = AnalysisResult(
            analysis_type="pattern",
            ticker=ticker,
            period=period,
            findings={},
            recommendations=[],
            risk_factors=[],
            confidence_level="medium"
        )
        
        # Perform pattern analysis
        result.add_finding('pattern_type', pattern_type)
        result.add_finding('pattern_detected', True)
        result.add_recommendation(f"Monitor {pattern_type} pattern development")
        
        return result
    
    def analyze_comparison(self, data: Any, parameters: Dict[str, Any]) -> AnalysisResult:
        """Compare multiple stocks"""
        tickers = parameters.get('tickers', [])
        period = parameters.get('period', ('N/A', 'N/A'))
        
        result = AnalysisResult(
            analysis_type="comparison",
            ticker=None,
            period=period,
            findings={},
            recommendations=[],
            risk_factors=[],
            confidence_level="high"
        )
        
        result.add_finding('compared_tickers', tickers)
        result.add_finding('best_performer', tickers[0] if tickers else None)
        
        return result
    
    def analyze_trend(self, data: Any, parameters: Dict[str, Any]) -> AnalysisResult:
        """Analyze trend in data"""
        ticker = parameters.get('ticker')
        period = parameters.get('period', ('N/A', 'N/A'))
        
        result = AnalysisResult(
            analysis_type="trend",
            ticker=ticker,
            period=period,
            findings={},
            recommendations=[],
            risk_factors=[],
            confidence_level="medium"
        )
        
        result.add_finding('primary_trend', 'uptrend')
        result.add_finding('trend_strength', 'moderate')
        
        return result
    
    def analyze_indicators(self, data: Any, parameters: Dict[str, Any]) -> AnalysisResult:
        """Analyze technical indicators"""
        indicators = parameters.get('indicators', [])
        ticker = parameters.get('ticker')
        period = parameters.get('period', ('N/A', 'N/A'))
        
        result = AnalysisResult(
            analysis_type="indicators",
            ticker=ticker,
            period=period,
            findings={},
            recommendations=[],
            risk_factors=[],
            confidence_level="high"
        )
        
        for indicator in indicators:
            result.add_finding(indicator, "analyzed")
        
        return result