import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from langchain.schema import Document
from langchain.chains import LLMChain
import json
from src.vector_store import OHLCVVectorStore
from src.retriever import OHLCVRetriever

load_dotenv()

class OHLCVRAGPipeline:
    def __init__(self, vector_store: OHLCVVectorStore, retriever: OHLCVRetriever,
                 llm_provider: str = "openai", api_key: Optional[str] = None, 
                 model: Optional[str] = None):
        self.vector_store = vector_store
        self.retriever = retriever
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm(llm_provider, api_key, model)
        
        # Define prompts for different query types
        self.prompts = self._create_prompts()
    
    def _initialize_llm(self, provider: str, api_key: Optional[str], model: Optional[str]) -> LLM:
        """Initialize LLM based on provider"""
        provider = provider.lower()
        
        if provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError("Please install langchain-openai: pip install langchain-openai")
            
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
            return ChatOpenAI(
                api_key=api_key,
                model=model or "gpt-3.5-turbo",
                temperature=0.1
            )
        
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError("Please install langchain-anthropic: pip install langchain-anthropic")
            
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
            return ChatAnthropic(
                api_key=api_key,
                model=model or "claude-3-sonnet-20240229",
                temperature=0.1
            )
        
        elif provider == "ollama":
            try:
                from langchain_community.llms import Ollama
            except ImportError:
                raise ImportError("Please install langchain-community: pip install langchain-community")
            
            # Ollama runs locally, no API key needed
            return Ollama(
                model=model or "llama2",
                temperature=0.1
            )
        
        elif provider == "mock":
            # Mock LLM for testing - no external dependencies
            from unittest.mock import MagicMock
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = "Mock response for testing"
            return mock_llm
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. "
                           f"Supported: openai, anthropic, ollama, mock")
        
    def _create_prompts(self) -> Dict[str, PromptTemplate]:
        prompts = {}
        
        # General market analysis prompt
        prompts['general'] = PromptTemplate(
            input_variables=["query", "context"],
            template="""You are a financial analyst assistant specializing in technical analysis of OHLCV data.
            
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

Base your answer strictly on the provided data. If the data doesn't contain enough information to fully answer the question, please state what additional data would be needed."""
        )
        
        # Pattern recognition prompt
        prompts['pattern'] = PromptTemplate(
            input_variables=["pattern_type", "context"],
            template="""You are a technical analysis expert. Analyze the following OHLCV data for {pattern_type} patterns:

{context}

Provide:
1. Confirmation of whether the {pattern_type} pattern is present
2. Strength of the pattern (weak/moderate/strong)
3. Key supporting indicators
4. Entry/exit points if applicable
5. Risk/reward considerations

Be specific and reference the actual data values in your analysis."""
        )
        
        # Comparison prompt
        prompts['comparison'] = PromptTemplate(
            input_variables=["tickers", "context"],
            template="""Compare the following stocks based on their OHLCV data:

Stocks to compare: {tickers}

Data:
{context}

Provide a comprehensive comparison including:
1. Performance comparison over the time period
2. Volatility analysis
3. Volume patterns
4. Trend strength comparison
5. Which stock shows better technical setup and why

Use specific numbers and percentages from the data."""
        )
        
        # Prediction prompt
        prompts['prediction'] = PromptTemplate(
            input_variables=["ticker", "context"],
            template="""Based on the historical OHLCV data and technical indicators for {ticker}:

{context}

Provide:
1. Current market structure analysis
2. Key support and resistance levels
3. Probable scenarios based on the technical setup
4. Risk factors to monitor
5. Technical indicators suggesting potential direction

NOTE: This is technical analysis only, not financial advice. Always mention the uncertainty inherent in market predictions."""
        )
        
        return prompts
    
    def query(self, query: str, query_type: str = "general", 
              ticker: Optional[str] = None, n_results: int = 5) -> Dict[str, Any]:
        # Retrieve relevant context
        relevant_chunks = self.retriever.retrieve_relevant_context(
            query, n_results=n_results, ticker=ticker
        )
        
        if not relevant_chunks:
            return {
                'query': query,
                'answer': "No relevant data found for your query. Please try a different question or check if the ticker symbol is correct.",
                'sources': []
            }
        
        # Format context for LLM
        context = self._format_context(relevant_chunks)
        
        # Select appropriate prompt
        prompt = self.prompts.get(query_type, self.prompts['general'])
        
        # Prepare input based on query type
        if query_type == 'general':
            prompt_input = {'query': query, 'context': context}
        elif query_type == 'pattern':
            pattern_type = self._extract_pattern_type(query)
            prompt_input = {'pattern_type': pattern_type, 'context': context}
        elif query_type == 'comparison':
            tickers = self._extract_tickers(relevant_chunks)
            prompt_input = {'tickers': ', '.join(tickers), 'context': context}
        elif query_type == 'prediction':
            prompt_input = {'ticker': ticker or 'the stock', 'context': context}
        else:
            prompt_input = {'query': query, 'context': context}
        
        # Create chain and get response
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(**prompt_input)
        
        # Format sources
        sources = self._format_sources(relevant_chunks)
        
        return {
            'query': query,
            'query_type': query_type,
            'answer': response,
            'sources': sources,
            'num_sources': len(relevant_chunks)
        }
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_part = f"""
Source {i}:
Ticker: {chunk['ticker']}
Period: {chunk['period']}
Relevance Score: {chunk['relevance_score']:.2f}

{chunk['summary']}

Key Metrics:
- Trend: {chunk['metadata']['trend']}
- Average Volume: {chunk['metadata']['avg_volume']:,.0f}
- Volatility: {chunk['metadata']['volatility']:.4f}
- Price Range: ${chunk['metadata']['price_low']:.2f} - ${chunk['metadata']['price_high']:.2f}
"""
            if chunk['metadata'].get('rsi_avg'):
                context_part += f"- Average RSI: {chunk['metadata']['rsi_avg']:.2f}\n"
                
            if 'data_preview' in chunk:
                context_part += f"\nData Preview:\n{chunk['data_preview']}\n"
                
            context_parts.append(context_part)
            
        return "\n---\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        sources = []
        for chunk in chunks:
            sources.append({
                'ticker': chunk['ticker'],
                'period': chunk['period'],
                'relevance_score': f"{chunk['relevance_score']:.2f}",
                'trend': chunk['metadata']['trend']
            })
        return sources
    
    def _extract_pattern_type(self, query: str) -> str:
        query_lower = query.lower()
        patterns = {
            'uptrend': ['uptrend', 'bullish', 'ascending'],
            'downtrend': ['downtrend', 'bearish', 'descending'],
            'breakout': ['breakout', 'breakthrough', 'break above'],
            'reversal': ['reversal', 'reverse', 'turnaround'],
            'consolidation': ['consolidation', 'sideways', 'ranging']
        }
        
        for pattern, keywords in patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return pattern
                
        return 'general pattern'
    
    def _extract_tickers(self, chunks: List[Dict[str, Any]]) -> List[str]:
        tickers = []
        for chunk in chunks:
            if chunk['ticker'] not in tickers:
                tickers.append(chunk['ticker'])
        return tickers
    
    def analyze_pattern(self, pattern_type: str, ticker: Optional[str] = None,
                        n_results: int = 5) -> Dict[str, Any]:
        # Retrieve patterns
        relevant_chunks = self.retriever.retrieve_by_pattern(
            pattern_type, ticker=ticker, n_results=n_results
        )
        
        if not relevant_chunks:
            return {
                'pattern': pattern_type,
                'analysis': f"No {pattern_type} patterns found in the data.",
                'sources': []
            }
        
        # Use pattern-specific prompt
        context = self._format_context(relevant_chunks)
        prompt = self.prompts['pattern']
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(pattern_type=pattern_type, context=context)
        
        return {
            'pattern': pattern_type,
            'ticker': ticker,
            'analysis': response,
            'sources': self._format_sources(relevant_chunks),
            'num_matches': len(relevant_chunks)
        }
    
    def analyze_indicators(self, indicator: str, condition: str, threshold: float,
                          ticker: Optional[str] = None) -> Dict[str, Any]:
        # Retrieve based on indicator
        relevant_chunks = self.retriever.retrieve_by_technical_indicator(
            indicator, condition, threshold, ticker=ticker
        )
        
        if not relevant_chunks:
            return {
                'indicator': indicator,
                'condition': f"{condition} {threshold}",
                'analysis': f"No data found matching {indicator} {condition} {threshold}",
                'sources': []
            }
        
        # Create analysis
        query = f"Analyze periods where {indicator} is {condition} {threshold}"
        context = self._format_context(relevant_chunks)
        
        prompt = self.prompts['general']
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(query=query, context=context)
        
        return {
            'indicator': indicator,
            'condition': f"{condition} {threshold}",
            'analysis': response,
            'sources': self._format_sources(relevant_chunks),
            'num_matches': len(relevant_chunks)
        }
    
    def find_similar_patterns(self, ticker: str, date: str, n_results: int = 5) -> Dict[str, Any]:
        # Find similar historical patterns
        similar_patterns = self.retriever.retrieve_similar_patterns(
            ticker, date, n_results=n_results
        )
        
        if not similar_patterns:
            return {
                'reference': f"{ticker} on {date}",
                'analysis': "No similar patterns found.",
                'similar_periods': []
            }
        
        # Analyze similarities
        query = f"Compare these similar patterns to {ticker} on {date} and identify common outcomes"
        context = self._format_context(similar_patterns)
        
        prompt = self.prompts['general']
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(query=query, context=context)
        
        return {
            'reference': f"{ticker} on {date}",
            'analysis': response,
            'similar_periods': self._format_sources(similar_patterns),
            'num_similar': len(similar_patterns)
        }