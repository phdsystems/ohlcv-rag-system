"""
Tests for BaseComponent abstract class
"""

import pytest
from .base import BaseComponent


class TestBaseComponent:
    """Test BaseComponent abstract class functionality"""
    
    def test_base_component_requires_implementation(self):
        """Test BaseComponent cannot be instantiated directly"""
        with pytest.raises(TypeError):
            # Should fail because abstract methods not implemented
            BaseComponent("test")
    
    def test_base_component_with_concrete_implementation(self):
        """Test BaseComponent works with concrete implementation"""
        
        class ConcreteComponent(BaseComponent):
            def initialize(self):
                self._initialized = True
                return self
            
            def validate_config(self):
                return self.config.get("valid", True)
            
            def get_status(self):
                return {
                    "name": self.name,
                    "initialized": self._initialized,
                    "config": self.config
                }
        
        # Test instantiation
        component = ConcreteComponent("test_component", {"valid": True})
        assert component.name == "test_component"
        assert component.config == {"valid": True}
        assert hasattr(component, '_logger')
        assert component._initialized == False
        
        # Test initialization
        component.initialize()
        assert component._initialized == True
        
        # Test validation
        assert component.validate_config() == True
        
        # Test status
        status = component.get_status()
        assert status["name"] == "test_component"
        assert status["initialized"] == True
        assert status["config"] == {"valid": True}
    
    def test_base_component_logging(self):
        """Test BaseComponent provides logging functionality"""
        
        class LoggingComponent(BaseComponent):
            def initialize(self):
                self.log_info("Initializing")
                self._initialized = True
            
            def validate_config(self):
                self.log_debug("Validating config")
                return True
            
            def get_status(self):
                self.log_warning("Getting status")
                return {"status": "ok"}
        
        component = LoggingComponent("logger_test")
        
        # Test logging methods exist and don't error
        component.log_info("Test info")
        component.log_debug("Test debug")
        component.log_warning("Test warning")
        component.log_error("Test error")
        
        # Should not raise any exceptions
        component.initialize()
        component.validate_config()
        component.get_status()