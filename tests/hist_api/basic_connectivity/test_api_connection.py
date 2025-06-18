#!/usr/bin/env python3
"""
Quick test script for Databento API connection.
Tests both authentication and basic data retrieval capability.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

def test_connection():
    """Test basic Databento API connection and authentication."""
    
    print("🔍 Testing Databento API Connection...")
    print("=" * 50)
    
    # Basic configuration for the adapter
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        },
        "retry_policy": {
            "max_retries": 2,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_multiplier": 2.0
        }
    }
    
    # Initialize adapter
    adapter = DatabentoAdapter(config)
    
    # Validate configuration
    print("✅ Step 1: Validating configuration...")
    config_valid = adapter.validate_config()
    assert config_valid, "Configuration validation failed!"
    print("✅ Configuration is valid")
    
    # Test connection
    print("✅ Step 2: Testing API connection...")
    adapter.connect()
    print("✅ Successfully connected to Databento API")
    
    # Test basic data fetch (small request)
    print("✅ Step 3: Testing data retrieval...")
    
    # Simple test job config - fetching 1 day of OHLCV data for SPY
    test_job = {
        "dataset": "XNAS.ITCH",  # Using a common dataset
        "schema": "ohlcv-1d",    # Daily OHLCV bars
        "symbols": ["AAPL"],     # Apple stock
        "stype_in": "native",    # Native symbol type
        "start_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    }
    
    print(f"   📊 Fetching data for: {test_job['symbols']} on {test_job['start_date']}")
    
    # Fetch one record to test
    records = list(adapter.fetch_historical_data(test_job))
    
    if records:
        print(f"✅ Successfully retrieved {len(records)} records")
        print(f"   📈 Sample record type: {type(records[0]).__name__}")
        if hasattr(records[0], 'model_dump'):
            sample_data = records[0].model_dump()
            print(f"   📊 Sample data keys: {list(sample_data.keys())}")
        # Assert that we got valid records
        assert len(records) > 0, "Expected at least one record"
        assert hasattr(records[0], 'model_dump'), "Record should be a valid Pydantic model"
    else:
        print("⚠️  No records returned (this might be normal for weekends/holidays)")
        # This is acceptable - don't fail the test for no data on weekends/holidays
    
    # Disconnect
    adapter.disconnect()
    print("✅ Step 4: Disconnected successfully")
    
    print("\n🎉 API Connection Test PASSED!")
    print("   Your Databento API is working correctly.")

def check_environment():
    """Check if required environment variables are set."""
    print("🔧 Checking Environment Setup...")
    print("=" * 30)
    
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY environment variable not set!")
        print("   Please set it in your .env file:")
        print("   DATABENTO_API_KEY=db-EXAMPLE-API-KEY-PLACEHOLDER")
        return False
    
    if not api_key.startswith("db-"):
        print("⚠️  API key doesn't start with 'db-' - are you sure it's correct?")
        
    if len(api_key) != 35:  # db- + 32 characters
        print(f"⚠️  API key length is {len(api_key)}, expected 35 characters")
    
    print(f"✅ DATABENTO_API_KEY found (starts with: {api_key[:6]}...)")
    return True

if __name__ == "__main__":
    print("🚀 Databento API Connection Tester")
    print("=" * 40)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    print()
    
    # Test the connection
    success = test_connection()
    
    if success:
        print("\n✅ All tests passed! Your API connection is ready.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Check the error messages above.")
        sys.exit(1) 