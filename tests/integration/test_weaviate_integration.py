"""
Integration tests for Weaviate using Testcontainers
"""

import pytest
import numpy as np
from typing import List, Dict, Any
import time


class TestWeaviateIntegration:
    
    @pytest.mark.integration
    def test_weaviate_connection(self, clean_weaviate):
        """Test basic connection to Weaviate container"""
        # Test that we can connect and check schema
        schema = clean_weaviate.schema.get()
        assert "classes" in schema
        assert isinstance(schema["classes"], list)
    
    @pytest.mark.integration
    def test_weaviate_schema_creation(self, clean_weaviate):
        """Test creating schema in Weaviate"""
        # Define schema for OHLCV data
        schema = {
            "class": "OHLCVData",
            "description": "OHLCV financial data with technical indicators",
            "properties": [
                {
                    "name": "ticker",
                    "dataType": ["string"],
                    "description": "Stock ticker symbol"
                },
                {
                    "name": "date",
                    "dataType": ["date"],
                    "description": "Trading date"
                },
                {
                    "name": "price",
                    "dataType": ["number"],
                    "description": "Closing price"
                },
                {
                    "name": "volume",
                    "dataType": ["int"],
                    "description": "Trading volume"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Technical analysis content"
                }
            ]
        }
        
        # Create schema
        clean_weaviate.schema.create_class(schema)
        
        # Verify schema was created
        result = clean_weaviate.schema.get("OHLCVData")
        assert result["class"] == "OHLCVData"
        assert len(result["properties"]) == 5
    
    @pytest.mark.integration
    def test_weaviate_crud_operations(self, clean_weaviate):
        """Test CRUD operations with Weaviate"""
        # Create schema
        schema = {
            "class": "TestData",
            "properties": [
                {"name": "ticker", "dataType": ["string"]},
                {"name": "price", "dataType": ["number"]},
                {"name": "description", "dataType": ["text"]}
            ]
        }
        clean_weaviate.schema.create_class(schema)
        
        # Create object
        data_object = {
            "ticker": "AAPL",
            "price": 150.0,
            "description": "Apple stock data"
        }
        
        result = clean_weaviate.data_object.create(
            data_object=data_object,
            class_name="TestData"
        )
        object_id = result
        
        assert object_id is not None
        
        # Read object
        retrieved = clean_weaviate.data_object.get_by_id(
            object_id,
            class_name="TestData"
        )
        assert retrieved["properties"]["ticker"] == "AAPL"
        assert retrieved["properties"]["price"] == 150.0
        
        # Update object
        clean_weaviate.data_object.update(
            data_object={"price": 155.0},
            class_name="TestData",
            uuid=object_id
        )
        
        updated = clean_weaviate.data_object.get_by_id(
            object_id,
            class_name="TestData"
        )
        assert updated["properties"]["price"] == 155.0
        
        # Delete object
        clean_weaviate.data_object.delete(
            uuid=object_id,
            class_name="TestData"
        )
        
        # Verify deletion
        deleted = clean_weaviate.data_object.get_by_id(
            object_id,
            class_name="TestData"
        )
        assert deleted is None
    
    @pytest.mark.integration
    def test_weaviate_batch_import(self, clean_weaviate):
        """Test batch import operations"""
        # Create schema
        schema = {
            "class": "BatchData",
            "properties": [
                {"name": "ticker", "dataType": ["string"]},
                {"name": "date", "dataType": ["string"]},
                {"name": "price", "dataType": ["number"]}
            ]
        }
        clean_weaviate.schema.create_class(schema)
        
        # Prepare batch data
        batch_data = []
        for i in range(100):
            batch_data.append({
                "ticker": f"TICK{i%5}",
                "date": f"2024-01-{(i%30)+1:02d}",
                "price": 100.0 + i
            })
        
        # Batch import
        with clean_weaviate.batch as batch:
            for data in batch_data:
                batch.add_data_object(
                    data_object=data,
                    class_name="BatchData"
                )
        
        # Wait for indexing
        time.sleep(1)
        
        # Verify import
        result = clean_weaviate.query.aggregate("BatchData").with_meta_count().do()
        assert result["data"]["Aggregate"]["BatchData"][0]["meta"]["count"] == 100
    
    @pytest.mark.integration
    def test_weaviate_graphql_query(self, clean_weaviate):
        """Test GraphQL queries in Weaviate"""
        # Create schema and data
        schema = {
            "class": "StockData",
            "properties": [
                {"name": "ticker", "dataType": ["string"]},
                {"name": "price", "dataType": ["number"]},
                {"name": "analysis", "dataType": ["text"]}
            ]
        }
        clean_weaviate.schema.create_class(schema)
        
        # Add test data
        stocks = [
            {"ticker": "AAPL", "price": 150.0, "analysis": "Strong buy signal"},
            {"ticker": "GOOGL", "price": 2800.0, "analysis": "Moderate buy"},
            {"ticker": "MSFT", "price": 370.0, "analysis": "Hold position"}
        ]
        
        for stock in stocks:
            clean_weaviate.data_object.create(
                data_object=stock,
                class_name="StockData"
            )
        
        # Wait for indexing
        time.sleep(1)
        
        # Query with filters
        result = clean_weaviate.query.get(
            "StockData",
            ["ticker", "price", "analysis"]
        ).with_where({
            "path": ["price"],
            "operator": "GreaterThan",
            "valueNumber": 200.0
        }).do()
        
        # Should return GOOGL and MSFT
        assert len(result["data"]["Get"]["StockData"]) == 2
        tickers = [item["ticker"] for item in result["data"]["Get"]["StockData"]]
        assert "GOOGL" in tickers
        assert "MSFT" in tickers
    
    @pytest.mark.integration
    def test_weaviate_vector_search(self, clean_weaviate):
        """Test vector similarity search"""
        # Create schema with vector indexing
        schema = {
            "class": "VectorData",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "ticker", "dataType": ["string"]}
            ]
        }
        clean_weaviate.schema.create_class(schema)
        
        # Add data with vectors
        vectors = np.random.rand(5, 128).tolist()
        for i, vector in enumerate(vectors):
            clean_weaviate.data_object.create(
                data_object={
                    "content": f"Document {i}",
                    "ticker": f"TICK{i}"
                },
                class_name="VectorData",
                vector=vector
            )
        
        # Wait for indexing
        time.sleep(1)
        
        # Search with vector
        query_vector = vectors[0]  # Use first vector as query
        result = clean_weaviate.query.get(
            "VectorData",
            ["content", "ticker"]
        ).with_near_vector({
            "vector": query_vector
        }).with_limit(3).do()
        
        # Should return results ordered by similarity
        assert len(result["data"]["Get"]["VectorData"]) == 3
        # First result should be the same document
        assert result["data"]["Get"]["VectorData"][0]["content"] == "Document 0"
    
    @pytest.mark.integration
    def test_weaviate_cross_references(self, clean_weaviate):
        """Test cross-references between classes"""
        # Create two related schemas
        ticker_schema = {
            "class": "Ticker",
            "properties": [
                {"name": "symbol", "dataType": ["string"]},
                {"name": "name", "dataType": ["string"]}
            ]
        }
        
        price_schema = {
            "class": "Price",
            "properties": [
                {"name": "value", "dataType": ["number"]},
                {"name": "date", "dataType": ["string"]},
                {
                    "name": "hasTicker",
                    "dataType": ["Ticker"],
                    "description": "Reference to ticker"
                }
            ]
        }
        
        clean_weaviate.schema.create_class(ticker_schema)
        clean_weaviate.schema.create_class(price_schema)
        
        # Create ticker
        ticker_id = clean_weaviate.data_object.create(
            data_object={"symbol": "AAPL", "name": "Apple Inc."},
            class_name="Ticker"
        )
        
        # Create price with reference
        price_id = clean_weaviate.data_object.create(
            data_object={"value": 150.0, "date": "2024-01-01"},
            class_name="Price"
        )
        
        # Add reference
        clean_weaviate.data_object.reference.add(
            from_class_name="Price",
            from_uuid=price_id,
            from_property_name="hasTicker",
            to_class_name="Ticker",
            to_uuid=ticker_id
        )
        
        # Query with reference
        result = clean_weaviate.query.get(
            "Price",
            ["value", "date"]
        ).with_additional(["id"]).do()
        
        assert len(result["data"]["Get"]["Price"]) == 1
        assert result["data"]["Get"]["Price"][0]["value"] == 150.0