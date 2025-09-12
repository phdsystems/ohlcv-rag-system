"""
Base classes for the OHLCV RAG System
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
from datetime import datetime


class BaseComponent(ABC):
    """Base class for all system components"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base component
        
        Args:
            name: Component name
            config: Component configuration
        """
        self.name = name
        self.config = config or {}
        self._logger = self._setup_logger()
        self._initialized = False
        self._created_at = datetime.now()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup component logger"""
        logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the component"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate component configuration"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get component status"""
        pass
    
    def log_info(self, message: str) -> None:
        """Log info message"""
        self._logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log error message"""
        self._logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log warning message"""
        self._logger.warning(f"[{self.name}] {message}")
    
    def log_debug(self, message: str) -> None:
        """Log debug message"""
        self._logger.debug(f"[{self.name}] {message}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', initialized={self._initialized})"


class Configurable(ABC):
    """Mixin for configurable components"""
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        pass
    
    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration"""
        pass
    
    @abstractmethod
    def reset_config(self) -> None:
        """Reset to default configuration"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration"""
        pass


class DataProcessor(BaseComponent):
    """Base class for data processing components"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._processing_stats = {
            'total_processed': 0,
            'total_failed': 0,
            'last_processed': None,
            'processing_time_total': 0
        }
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data"""
        pass
    
    @abstractmethod
    def preprocess(self, data: Any) -> Any:
        """Preprocess data before main processing"""
        pass
    
    @abstractmethod
    def postprocess(self, data: Any) -> Any:
        """Postprocess data after main processing"""
        pass
    
    def process_batch(self, data_list: List[Any], batch_size: int = 32) -> List[Any]:
        """Process data in batches"""
        results = []
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            batch_results = [self.process(item) for item in batch]
            results.extend(batch_results)
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self._processing_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics"""
        self._processing_stats = {
            'total_processed': 0,
            'total_failed': 0,
            'last_processed': None,
            'processing_time_total': 0
        }
    
    def update_stats(self, success: bool, processing_time: float) -> None:
        """Update processing statistics"""
        if success:
            self._processing_stats['total_processed'] += 1
        else:
            self._processing_stats['total_failed'] += 1
        
        self._processing_stats['last_processed'] = datetime.now()
        self._processing_stats['processing_time_total'] += processing_time