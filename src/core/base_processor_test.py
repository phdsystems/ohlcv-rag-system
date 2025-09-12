"""
Tests for DataProcessor abstract class
"""

import pytest
from .base import DataProcessor


class TestDataProcessor:
    """Test DataProcessor abstract class and interface"""
    
    def test_data_processor_requires_process_method(self):
        """Test DataProcessor requires process method implementation"""
        
        class IncompleteProcessor(DataProcessor):
            def initialize(self):
                self._initialized = True
            
            def validate_config(self):
                return True
            
            def get_status(self):
                return {"status": "ok"}
            # Missing process() method
        
        with pytest.raises(TypeError):
            # Should fail because process() not implemented
            IncompleteProcessor("test")
    
    def test_data_processor_with_implementation(self):
        """Test DataProcessor with complete implementation"""
        
        class TextProcessor(DataProcessor):
            def initialize(self):
                self._initialized = True
            
            def validate_config(self):
                return True
            
            def get_status(self):
                return {"status": "ok", "processed_count": getattr(self, 'count', 0)}
            
            def preprocess(self, data):
                """Preprocess data"""
                return data
            
            def postprocess(self, data):
                """Postprocess data"""
                return data
            
            def process(self, data):
                """Process text data"""
                self.count = getattr(self, 'count', 0) + 1
                if isinstance(data, str):
                    return data.upper()
                elif isinstance(data, list):
                    return [s.upper() for s in data if isinstance(s, str)]
                return data
        
        processor = TextProcessor("text_processor")
        processor.initialize()
        
        # Test processing single string
        result = processor.process("hello world")
        assert result == "HELLO WORLD"
        
        # Test processing list
        result = processor.process(["hello", "world"])
        assert result == ["HELLO", "WORLD"]
        
        # Test status tracking
        status = processor.get_status()
        assert status["processed_count"] == 2
    
    def test_data_processor_chaining(self):
        """Test multiple DataProcessors can be chained"""
        
        class UpperProcessor(DataProcessor):
            def initialize(self):
                self._initialized = True
            def validate_config(self):
                return True
            def get_status(self):
                return {"type": "upper"}
            def preprocess(self, data):
                return data
            def postprocess(self, data):
                return data
            def process(self, data):
                return data.upper() if isinstance(data, str) else data
        
        class ReverseProcessor(DataProcessor):
            def initialize(self):
                self._initialized = True
            def validate_config(self):
                return True
            def get_status(self):
                return {"type": "reverse"}
            def preprocess(self, data):
                return data
            def postprocess(self, data):
                return data
            def process(self, data):
                return data[::-1] if isinstance(data, str) else data
        
        # Create processors
        upper = UpperProcessor("upper")
        reverse = ReverseProcessor("reverse")
        
        # Chain processing
        data = "hello"
        data = upper.process(data)  # "HELLO"
        data = reverse.process(data)  # "OLLEH"
        
        assert data == "OLLEH"