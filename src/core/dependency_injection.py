"""
Dependency Injection Framework for OHLCV RAG System

Provides a clean way to inject dependencies and create test doubles,
solving the deep integration issues by making components more testable.
"""

from typing import Dict, Any, Optional, Type, TypeVar, Callable, Protocol
from abc import ABC, abstractmethod
import os
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass


T = TypeVar('T')


class Provider(Protocol):
    """Protocol for dependency providers"""
    def get(self, interface: Type[T]) -> T:
        """Get an instance of the requested interface"""
        ...


@dataclass 
class ServiceConfig:
    """Configuration for a service registration"""
    implementation: Type
    singleton: bool = True
    factory: Optional[Callable[[], Any]] = None
    mock_in_tests: bool = False


class DependencyContainer:
    """
    Dependency injection container with support for:
    - Singleton and transient services
    - Factory methods
    - Test doubles and mocks
    - Environment-based configuration
    """
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self._services: Dict[Type, ServiceConfig] = {}
        self._instances: Dict[Type, Any] = {}
        self._mocks: Dict[Type, Any] = {}
        
    def register(self, 
                 interface: Type[T], 
                 implementation: Type[T], 
                 singleton: bool = True,
                 factory: Optional[Callable[[], T]] = None,
                 mock_in_tests: bool = False) -> None:
        """
        Register a service implementation
        
        Args:
            interface: The interface/abstract class
            implementation: The concrete implementation
            singleton: Whether to use singleton pattern
            factory: Optional factory function
            mock_in_tests: Whether to auto-mock in test mode
        """
        self._services[interface] = ServiceConfig(
            implementation=implementation,
            singleton=singleton,
            factory=factory,
            mock_in_tests=mock_in_tests
        )
        
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service"""
        self.register(interface, implementation, singleton=True)
        
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service"""
        self.register(interface, implementation, singleton=False)
        
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function"""
        self.register(interface, None, factory=factory)
        
    def register_mock(self, interface: Type[T], mock_instance: Any = None) -> None:
        """Register a mock for testing"""
        if mock_instance is None:
            mock_instance = Mock(spec=interface)
        self._mocks[interface] = mock_instance
        
    def get(self, interface: Type[T]) -> T:
        """
        Get an instance of the requested interface
        
        Args:
            interface: The interface to resolve
            
        Returns:
            Instance of the requested interface
        """
        # In test mode, return mock if available
        if self.test_mode and interface in self._mocks:
            return self._mocks[interface]
            
        # Check if we have a registered service
        if interface not in self._services:
            raise ValueError(f"No service registered for {interface}")
            
        config = self._services[interface]
        
        # Return mock in test mode if configured
        if self.test_mode and config.mock_in_tests:
            if interface not in self._mocks:
                self._mocks[interface] = Mock(spec=interface)
            return self._mocks[interface]
            
        # Return cached singleton
        if config.singleton and interface in self._instances:
            return self._instances[interface]
            
        # Create new instance
        if config.factory:
            instance = config.factory()
        else:
            instance = self._create_instance(config.implementation)
            
        # Cache singleton
        if config.singleton:
            self._instances[interface] = instance
            
        return instance
        
    def _create_instance(self, implementation: Type[T]) -> T:
        """Create an instance with dependency injection"""
        # For now, simple construction - could be extended with constructor injection
        return implementation()
        
    def clear_cache(self) -> None:
        """Clear all cached instances"""
        self._instances.clear()
        
    def clear_mocks(self) -> None:
        """Clear all mocks"""
        self._mocks.clear()
        
    def set_test_mode(self, test_mode: bool) -> None:
        """Enable/disable test mode"""
        self.test_mode = test_mode
        if not test_mode:
            self.clear_mocks()


# Global container instance
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    return _container


def configure_for_testing() -> DependencyContainer:
    """Configure container for testing with appropriate mocks"""
    container = get_container()
    container.set_test_mode(True)
    return container


def configure_for_production() -> DependencyContainer:
    """Configure container for production"""
    container = get_container()
    container.set_test_mode(False)
    return container


# Convenience functions
def register(interface: Type[T], implementation: Type[T], **kwargs) -> None:
    """Register a service in the global container"""
    _container.register(interface, implementation, **kwargs)
    

def get(interface: Type[T]) -> T:
    """Get a service from the global container"""
    return _container.get(interface)


def mock(interface: Type[T], mock_instance: Any = None) -> Any:
    """Register a mock in the global container"""
    _container.register_mock(interface, mock_instance)
    return _container._mocks[interface]


# Decorator for dependency injection
def inject(dependencies: Dict[str, Type]):
    """
    Decorator to inject dependencies into a class
    
    Usage:
        @inject({'vector_store': IVectorStore, 'llm': ILanguageModel})
        class MyService:
            def __init__(self, vector_store, llm):
                self.vector_store = vector_store
                self.llm = llm
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # Inject dependencies
            for param_name, interface in dependencies.items():
                if param_name not in kwargs:
                    kwargs[param_name] = get(interface)
            
            original_init(self, *args, **kwargs)
            
        cls.__init__ = new_init
        return cls
    
    return decorator


# Interface definitions for major components
class IDataIngestion(ABC):
    """Interface for data ingestion services"""
    
    @abstractmethod
    def fetch_ohlcv_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def create_contextual_chunks(self, window_size: int = 30) -> list:
        pass


class IVectorStore(ABC):
    """Interface for vector store services"""
    
    @abstractmethod
    def index_chunks(self, chunks: list, batch_size: int = 100) -> None:
        pass
        
    @abstractmethod
    def search(self, query: str, n_results: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass


class IRetriever(ABC):
    """Interface for retrieval services"""
    
    @abstractmethod
    def retrieve_relevant_context(self, query: str, n_results: int = 5, **kwargs) -> list:
        pass


class ILanguageModel(ABC):
    """Interface for language model services"""
    
    @abstractmethod
    def query(self, query: str, query_type: str = "general", **kwargs) -> Dict[str, Any]:
        pass


# Factory functions for creating configured instances
def create_test_data_ingestion() -> IDataIngestion:
    """Create a test-friendly data ingestion instance"""
    from unittest.mock import Mock
    mock_ingestion = Mock(spec=IDataIngestion)
    
    # Configure mock behavior
    mock_ingestion.fetch_ohlcv_data.return_value = {
        'AAPL': Mock(validate=lambda: True, data=[])
    }
    mock_ingestion.create_contextual_chunks.return_value = []
    
    return mock_ingestion


def create_test_vector_store() -> IVectorStore:
    """Create a test-friendly vector store instance"""
    mock_store = Mock(spec=IVectorStore)
    mock_store.search.return_value = {'results': [], 'total_results': 0}
    return mock_store


def create_test_retriever() -> IRetriever:
    """Create a test-friendly retriever instance"""
    mock_retriever = Mock(spec=IRetriever)
    mock_retriever.retrieve_relevant_context.return_value = []
    return mock_retriever


def create_test_language_model() -> ILanguageModel:
    """Create a test-friendly language model instance"""
    mock_llm = Mock(spec=ILanguageModel)
    mock_llm.query.return_value = {
        'query': 'test query',
        'answer': 'test response',
        'sources': []
    }
    return mock_llm


# Auto-configuration based on environment
def auto_configure_container():
    """Auto-configure the container based on environment"""
    is_test = os.getenv('PYTEST_CURRENT_TEST') is not None or os.getenv('TESTING') == 'true'
    
    if is_test:
        configure_for_testing()
        # Register test factories
        _container.register_factory(IDataIngestion, create_test_data_ingestion)
        _container.register_factory(IVectorStore, create_test_vector_store)
        _container.register_factory(IRetriever, create_test_retriever)
        _container.register_factory(ILanguageModel, create_test_language_model)
    else:
        configure_for_production()


# Initialize on import
auto_configure_container()