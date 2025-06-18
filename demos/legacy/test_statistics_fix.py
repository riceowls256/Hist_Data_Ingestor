#!/usr/bin/env python3
"""
Test script to verify statistics record storage fix.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.pipeline_orchestrator import PipelineOrchestrator
from src.core.config_manager import ConfigManager
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

def test_statistics_ingestion():
    """Test statistics data ingestion with the fix."""
    try:
        # Initialize orchestrator
        config_manager = ConfigManager()
        orchestrator = PipelineOrchestrator(config_manager)
        
        # Define test job configuration
        job_config = {
            'name': 'test_statistics_fix',
            'api': 'databento',
            'dataset': 'GLBX.MDP3',
            'schema': 'statistics',
            'symbols': ['ES.c.0'],
            'stype_in': 'continuous',
            'start_date': '2025-06-09',
            'end_date': '2025-06-16'
        }
        
        logger.info("Starting statistics ingestion test", job_config=job_config)
        
        # Execute ingestion
        success = orchestrator.execute_ingestion(
            api_type='databento',
            job_name=None,
            overrides=job_config
        )
        
        if success:
            logger.info("✅ Statistics ingestion completed successfully!")
            print("\n✅ SUCCESS: Statistics records were stored successfully!")
            print(f"   Records fetched: {orchestrator.stats.records_fetched}")
            print(f"   Records transformed: {orchestrator.stats.records_transformed}")
            print(f"   Records stored: {orchestrator.stats.records_stored}")
            print(f"   Errors encountered: {orchestrator.stats.errors_encountered}")
        else:
            logger.error("❌ Statistics ingestion failed")
            print("\n❌ FAILED: Statistics ingestion encountered errors")
            print(f"   Records fetched: {orchestrator.stats.records_fetched}")
            print(f"   Records transformed: {orchestrator.stats.records_transformed}")
            print(f"   Records stored: {orchestrator.stats.records_stored}")
            print(f"   Errors encountered: {orchestrator.stats.errors_encountered}")
            
        return success
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        print(f"\n❌ ERROR: Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Statistics Record Storage Fix...")
    print("-" * 50)
    
    success = test_statistics_ingestion()
    
    print("-" * 50)
    sys.exit(0 if success else 1)