"""
Tests for ApplicationState statistics and tracking functionality
"""

import pytest
import time
from datetime import datetime
from .application import ApplicationState


class TestApplicationStateTracking:
    """Test ApplicationState tracks queries, errors, and uptime correctly"""
    
    def test_initial_state_values(self):
        """Test ApplicationState starts with correct initial values"""
        state = ApplicationState()
        
        assert state.application_status == 'initializing'
        assert state.total_queries == 0
        assert state.successful_queries == 0
        assert len(state.ingested_tickers) == 0
        assert state.current_operation is None
        assert state.last_error is None
        assert state.last_ingestion is None
        assert state.last_query is None
    
    def test_query_tracking(self):
        """Test tracking of query statistics"""
        state = ApplicationState()
        
        # Simulate queries
        state.total_queries = 5
        state.successful_queries = 4
        
        assert state.total_queries == 5
        assert state.successful_queries == 4
        
        # Add more queries
        state.total_queries += 3
        state.successful_queries += 2
        
        assert state.total_queries == 8
        assert state.successful_queries == 6
    
    def test_success_rate_calculation(self):
        """Test query success rate calculation"""
        state = ApplicationState()
        
        # No queries - 0% success rate
        state_dict = state.to_dict()
        assert state_dict['statistics']['success_rate'] == 0.0
        
        # 80% success rate
        state.total_queries = 10
        state.successful_queries = 8
        state_dict = state.to_dict()
        assert state_dict['statistics']['success_rate'] == 80.0
        
        # 100% success rate
        state.total_queries = 5
        state.successful_queries = 5
        state_dict = state.to_dict()
        assert state_dict['statistics']['success_rate'] == 100.0
        
        # 0% success rate (all failed)
        state.total_queries = 3
        state.successful_queries = 0
        state_dict = state.to_dict()
        assert state_dict['statistics']['success_rate'] == 0.0
    
    def test_ticker_tracking(self):
        """Test tracking of ingested tickers"""
        state = ApplicationState()
        
        # Add tickers
        state.ingested_tickers.append('AAPL')
        state.ingested_tickers.append('GOOGL')
        state.ingested_tickers.append('MSFT')
        
        assert len(state.ingested_tickers) == 3
        assert 'AAPL' in state.ingested_tickers
        assert 'GOOGL' in state.ingested_tickers
        assert 'MSFT' in state.ingested_tickers
        
        # Clear tickers
        state.ingested_tickers.clear()
        assert len(state.ingested_tickers) == 0
    
    def test_error_tracking(self):
        """Test error message tracking"""
        state = ApplicationState()
        
        assert state.last_error is None
        
        # Set error
        state.last_error = "Connection timeout"
        assert state.last_error == "Connection timeout"
        
        # Update error
        state.last_error = "API rate limit exceeded"
        assert state.last_error == "API rate limit exceeded"
        
        # Clear error
        state.last_error = None
        assert state.last_error is None
    
    def test_operation_tracking(self):
        """Test current operation tracking"""
        state = ApplicationState()
        
        # Track different operations
        state.current_operation = 'data_ingestion'
        assert state.current_operation == 'data_ingestion'
        
        state.current_operation = 'query_processing'
        assert state.current_operation == 'query_processing'
        
        state.current_operation = 'analysis'
        assert state.current_operation == 'analysis'
        
        state.current_operation = None
        assert state.current_operation is None
    
    def test_timestamp_tracking(self):
        """Test timestamp tracking for operations"""
        state = ApplicationState()
        
        # Set timestamps
        now = datetime.now()
        state.last_ingestion = now
        state.last_query = now
        
        assert state.last_ingestion == now
        assert state.last_query == now
        
        state_dict = state.to_dict()
        assert state_dict['last_ingestion'] == str(now)
        assert state_dict['last_query'] == str(now)
    
    def test_uptime_calculation(self):
        """Test uptime tracking in seconds"""
        state = ApplicationState()
        
        # Get initial uptime
        state_dict = state.to_dict()
        uptime1 = state_dict['statistics']['uptime_seconds']
        assert uptime1 >= 0
        
        # Wait a bit
        time.sleep(0.1)
        
        # Uptime should increase
        state_dict = state.to_dict()
        uptime2 = state_dict['statistics']['uptime_seconds']
        assert uptime2 > uptime1
        assert uptime2 >= 0.1
    
    def test_state_serialization(self):
        """Test complete state serialization to dictionary"""
        state = ApplicationState()
        
        # Set various state values
        state.application_status = 'ready'
        state.ingested_tickers = ['AAPL', 'GOOGL']
        state.total_queries = 100
        state.successful_queries = 95
        state.last_error = "Test error"
        state.current_operation = 'idle'
        
        # Serialize
        state_dict = state.to_dict()
        
        # Verify all fields
        assert state_dict['status'] == 'ready'
        assert state_dict['ingested_tickers'] == ['AAPL', 'GOOGL']
        assert state_dict['current_operation'] == 'idle'
        assert state_dict['last_error'] == "Test error"
        assert state_dict['statistics']['total_queries'] == 100
        assert state_dict['statistics']['successful_queries'] == 95
        assert state_dict['statistics']['success_rate'] == 95.0
        assert 'uptime_seconds' in state_dict['statistics']
        assert 'components' in state_dict