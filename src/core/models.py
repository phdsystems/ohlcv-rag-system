"""
Data models for the OHLCV RAG System
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pandas as pd
from enum import Enum


class TrendType(Enum):
    """Trend types"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    MIXED = "mixed"


class QueryType(Enum):
    """Query types"""
    GENERAL = "general"
    PATTERN = "pattern"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    TECHNICAL = "technical"


class IndicatorType(Enum):
    """Technical indicator types"""
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    VOLUME = "volume"


@dataclass
class OHLCVDataModel:
    """Model for OHLCV data"""
    ticker: str
    data: pd.DataFrame
    interval: str
    period: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    indicators: Dict[str, pd.Series] = field(default_factory=dict)
    validated: bool = False
    fetched_at: datetime = field(default_factory=datetime.now)
    
    def add_indicator(self, name: str, values: pd.Series) -> None:
        """Add technical indicator"""
        self.indicators[name] = values
    
    def get_date_range(self) -> tuple:
        """Get date range of data"""
        if not self.data.empty:
            return (self.data.index.min(), self.data.index.max())
        return (None, None)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data statistics"""
        if self.data.empty:
            return {}
        
        return {
            'ticker': self.ticker,
            'rows': len(self.data),
            'start_date': str(self.data.index.min()),
            'end_date': str(self.data.index.max()),
            'avg_volume': float(self.data['Volume'].mean()),
            'price_range': {
                'high': float(self.data['High'].max()),
                'low': float(self.data['Low'].min())
            },
            'missing_values': self.data.isnull().sum().to_dict()
        }


@dataclass
class ChunkModel:
    """Model for data chunks"""
    id: str
    ticker: str
    start_date: str
    end_date: str
    data: List[Dict[str, Any]]
    summary: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_document(self) -> str:
        """Convert to document string for vector storage"""
        return f"""
        {self.ticker} OHLCV Data
        Period: {self.start_date} to {self.end_date}
        {self.summary}
        Metadata: {self.metadata}
        """
    
    def get_trend(self) -> TrendType:
        """Get trend from metadata"""
        trend_str = self.metadata.get('trend', 'mixed').lower()
        return TrendType(trend_str)


@dataclass
class QueryResult:
    """Model for query results"""
    query: str
    query_type: QueryType
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_source(self, source: Dict[str, Any]) -> None:
        """Add source to results"""
        self.sources.append(source)
    
    def get_top_sources(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get top N sources by relevance"""
        sorted_sources = sorted(
            self.sources, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        return sorted_sources[:n]


@dataclass
class AnalysisResult:
    """Model for analysis results"""
    analysis_type: str
    ticker: Optional[str]
    period: tuple
    findings: Dict[str, Any]
    recommendations: List[str]
    risk_factors: List[str]
    confidence_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_finding(self, key: str, value: Any) -> None:
        """Add finding to analysis"""
        self.findings[key] = value
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add recommendation"""
        self.recommendations.append(recommendation)
    
    def add_risk_factor(self, risk: str) -> None:
        """Add risk factor"""
        self.risk_factors.append(risk)
    
    def to_report(self) -> str:
        """Generate analysis report"""
        report = f"""
        Analysis Type: {self.analysis_type}
        Ticker: {self.ticker or 'Multiple'}
        Period: {self.period[0]} to {self.period[1]}
        Confidence: {self.confidence_level}
        
        Findings:
        """
        for key, value in self.findings.items():
            report += f"\n- {key}: {value}"
        
        if self.recommendations:
            report += "\n\nRecommendations:"
            for rec in self.recommendations:
                report += f"\n- {rec}"
        
        if self.risk_factors:
            report += "\n\nRisk Factors:"
            for risk in self.risk_factors:
                report += f"\n- {risk}"
        
        return report


@dataclass
class VectorSearchResult:
    """Model for vector search results"""
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float
    chunk: Optional[ChunkModel] = None
    
    def get_ticker(self) -> str:
        """Get ticker from metadata"""
        return self.metadata.get('ticker', 'Unknown')
    
    def get_period(self) -> tuple:
        """Get period from metadata"""
        return (
            self.metadata.get('start_date'),
            self.metadata.get('end_date')
        )