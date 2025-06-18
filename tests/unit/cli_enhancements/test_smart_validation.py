"""
Tests for smart validation and interactive workflow components.

Tests the Phase 3 enhanced interactive features including smart validation,
symbol autocomplete, market calendar awareness, and workflow building.
"""

import pytest
import json
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.cli.smart_validation import (
    SmartValidator, SymbolCache, MarketCalendar, ValidationResult, ValidationLevel,
    validate_cli_input
)
from src.cli.interactive_workflows import (
    WorkflowBuilder, WorkflowType, WorkflowTemplate, Workflow, WorkflowStep, StepStatus
)


class TestSymbolCache:
    """Test suite for SymbolCache."""
    
    def test_initialization_empty(self):
        """Test cache initialization without existing data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = SymbolCache(cache_file)
            
            # Should have default symbols loaded
            assert len(cache.symbols) > 0
            assert "ES.C.0" in cache.symbols
            assert "AAPL" in cache.symbols
            
    def test_initialization_with_existing_cache(self):
        """Test cache initialization with existing data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            
            # Create test cache file
            test_data = {
                "symbols": ["TEST1", "TEST2"],
                "metadata": {
                    "TEST1": {"type": "test", "asset_class": "test_class"}
                }
            }
            with open(cache_file, 'w') as f:
                json.dump(test_data, f)
                
            cache = SymbolCache(cache_file)
            
            assert "TEST1" in cache.symbols
            assert "TEST2" in cache.symbols
            assert cache.symbol_metadata["TEST1"]["type"] == "test"
            
    def test_add_symbol(self):
        """Test adding symbols to cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            cache = SymbolCache(cache_file)
            
            metadata = {"type": "equity", "sector": "tech"}
            cache.add_symbol("NEWTEST", metadata)
            
            assert "NEWTEST" in cache.symbols
            assert cache.symbol_metadata["NEWTEST"] == metadata
            
    def test_is_valid_symbol(self):
        """Test symbol validation."""
        cache = SymbolCache()
        
        assert cache.is_valid_symbol("ES.c.0")
        assert cache.is_valid_symbol("AAPL")
        assert not cache.is_valid_symbol("NOTEXIST")
        
        # Test case insensitive
        assert cache.is_valid_symbol("es.c.0")
        assert cache.is_valid_symbol("aapl")
        
    def test_fuzzy_search_exact_prefix(self):
        """Test fuzzy search with exact prefix matches."""
        cache = SymbolCache()
        
        results = cache.fuzzy_search("ES", limit=3)
        
        # Should have results
        assert len(results) > 0
        
        # Should prioritize exact prefix matches
        symbols = [r[0] for r in results]
        prefix_matches = [s for s in symbols if s.startswith("ES")]
        assert len(prefix_matches) > 0
        
        # Scores should be reasonable
        for symbol, score in results:
            assert 0 <= score <= 1
            
    def test_fuzzy_search_similar_matches(self):
        """Test fuzzy search with similar matches."""
        cache = SymbolCache()
        
        # Test with a typo
        results = cache.fuzzy_search("APPL", limit=5)  # Missing A
        
        symbols = [r[0] for r in results]
        assert "AAPL" in symbols  # Should suggest AAPL
        
    def test_get_symbols_by_category(self):
        """Test getting symbols by category."""
        cache = SymbolCache()
        
        futures = cache.get_symbols_by_category("futures")
        assert len(futures) > 0
        
        # Should contain expected futures
        futures_set = set(futures)
        expected_futures = {"ES.C.0", "CL.C.0", "GC.C.0"}
        assert expected_futures.issubset(futures_set)
        
    def test_get_symbol_info(self):
        """Test getting symbol metadata."""
        cache = SymbolCache()
        
        # Test known symbol
        info = cache.get_symbol_info("ES.c.0")
        assert info is not None
        assert "asset_class" in info
        
        # Test unknown symbol
        info = cache.get_symbol_info("UNKNOWN")
        assert info is None


class TestMarketCalendar:
    """Test suite for MarketCalendar."""
    
    def test_is_trading_day_weekdays(self):
        """Test trading day detection for weekdays."""
        calendar = MarketCalendar()
        
        # Monday - Friday should be trading days (if not holidays)
        monday = date(2024, 1, 8)  # A Monday that's not a holiday
        assert calendar.is_trading_day(monday)
        
        friday = date(2024, 1, 12)  # A Friday that's not a holiday
        assert calendar.is_trading_day(friday)
        
    def test_is_trading_day_weekends(self):
        """Test trading day detection for weekends."""
        calendar = MarketCalendar()
        
        # Saturday and Sunday should not be trading days
        saturday = date(2024, 1, 6)
        sunday = date(2024, 1, 7)
        
        assert not calendar.is_trading_day(saturday)
        assert not calendar.is_trading_day(sunday)
        
    def test_is_trading_day_holidays(self):
        """Test trading day detection for holidays."""
        calendar = MarketCalendar()
        
        # New Year's Day
        new_years = date(2024, 1, 1)
        assert not calendar.is_trading_day(new_years)
        
        # Christmas
        christmas = date(2024, 12, 25)
        assert not calendar.is_trading_day(christmas)
        
    def test_get_trading_days(self):
        """Test getting trading days in a range."""
        calendar = MarketCalendar()
        
        # Get trading days for a week
        start_date = date(2024, 1, 8)  # Monday
        end_date = date(2024, 1, 14)   # Sunday
        
        trading_days = calendar.get_trading_days(start_date, end_date)
        
        # Should have 5 trading days (Mon-Fri)
        assert len(trading_days) == 5
        
        # All should be weekdays
        for day in trading_days:
            assert day.weekday() < 5
            
    def test_get_next_trading_day(self):
        """Test getting next trading day."""
        calendar = MarketCalendar()
        
        # From Friday, next trading day should be Monday
        friday = date(2024, 1, 12)
        next_day = calendar.get_next_trading_day(friday)
        
        assert next_day.weekday() == 0  # Monday
        assert next_day > friday
        
    def test_get_previous_trading_day(self):
        """Test getting previous trading day."""
        calendar = MarketCalendar()
        
        # From Monday, previous trading day should be Friday
        monday = date(2024, 1, 8)
        prev_day = calendar.get_previous_trading_day(monday)
        
        assert prev_day.weekday() == 4  # Friday
        assert prev_day < monday


class TestSmartValidator:
    """Test suite for SmartValidator."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = SmartValidator()
        
        assert validator.symbol_cache is not None
        assert validator.market_calendar is not None
        assert len(validator.schema_rules) > 0
        
    def test_validate_symbol_valid(self):
        """Test validating a valid symbol."""
        validator = SmartValidator()
        
        result = validator.validate_symbol("ES.c.0", interactive=False)
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        assert "ES.C.0" in result.message
        
    def test_validate_symbol_invalid_with_suggestions(self):
        """Test validating invalid symbol with suggestions."""
        validator = SmartValidator()
        
        result = validator.validate_symbol("ESX", interactive=False)  # Close to ES.c.0
        
        assert not result.is_valid
        assert result.level in [ValidationLevel.WARNING, ValidationLevel.ERROR]
        assert len(result.suggestions) > 0
        
    def test_validate_symbol_empty(self):
        """Test validating empty symbol."""
        validator = SmartValidator()
        
        result = validator.validate_symbol("", interactive=False)
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert "empty" in result.message.lower()
        
    def test_validate_date_range_valid(self):
        """Test validating valid date range."""
        validator = SmartValidator()
        
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        result = validator.validate_date_range(start_date, end_date, interactive=False)
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        assert "trading days" in result.message
        assert result.metadata is not None
        
    def test_validate_date_range_invalid_format(self):
        """Test validating invalid date format."""
        validator = SmartValidator()
        
        result = validator.validate_date_range("invalid", "2024-01-31", interactive=False)
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert "format" in result.message.lower()
        
    def test_validate_date_range_start_after_end(self):
        """Test validating date range where start is after end."""
        validator = SmartValidator()
        
        result = validator.validate_date_range("2024-01-31", "2024-01-01", interactive=False)
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert "before" in result.message.lower()
        
    def test_validate_schema_valid(self):
        """Test validating valid schema."""
        validator = SmartValidator()
        
        result = validator.validate_schema("ohlcv-1d")
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        assert result.metadata is not None
        
    def test_validate_schema_invalid(self):
        """Test validating invalid schema."""
        validator = SmartValidator()
        
        result = validator.validate_schema("invalid-schema")
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert len(result.suggestions) > 0
        
    def test_validate_symbol_list_valid(self):
        """Test validating valid symbol list."""
        validator = SmartValidator()
        
        result = validator.validate_symbol_list("ES.c.0,NQ.c.0,AAPL", interactive=False)
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        assert result.metadata["total_count"] == 3
        assert result.metadata["valid_count"] == 3
        
    def test_validate_symbol_list_partial_valid(self):
        """Test validating partially valid symbol list."""
        validator = SmartValidator()
        
        result = validator.validate_symbol_list("ES.c.0,INVALID,AAPL", interactive=False)
        
        assert not result.is_valid
        assert result.level == ValidationLevel.WARNING
        assert result.metadata["valid_count"] == 2
        assert result.metadata["total_count"] == 3
        
    def test_validate_symbol_list_empty(self):
        """Test validating empty symbol list."""
        validator = SmartValidator()
        
        result = validator.validate_symbol_list("", interactive=False)
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert "empty" in result.message.lower()
        
    def test_parse_date_various_formats(self):
        """Test parsing dates in various formats."""
        validator = SmartValidator()
        
        # Test various valid formats
        test_cases = [
            ("2024-01-01", date(2024, 1, 1)),
            ("01/01/2024", date(2024, 1, 1)),
            ("2024/01/01", date(2024, 1, 1)),
        ]
        
        for date_str, expected in test_cases:
            result = validator._parse_date(date_str)
            assert result == expected
            
    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format."""
        validator = SmartValidator()
        
        with pytest.raises(ValueError):
            validator._parse_date("invalid-date")
            
    def test_get_completion_suggestions_symbol(self):
        """Test getting completion suggestions for symbols."""
        validator = SmartValidator()
        
        suggestions = validator.get_completion_suggestions("ES", context="symbol")
        
        assert len(suggestions) > 0
        assert any("ES" in s for s in suggestions)
        
    def test_get_completion_suggestions_schema(self):
        """Test getting completion suggestions for schemas."""
        validator = SmartValidator()
        
        suggestions = validator.get_completion_suggestions("oh", context="schema")
        
        assert len(suggestions) > 0
        assert "ohlcv-1d" in suggestions


class TestValidationResult:
    """Test suite for ValidationResult."""
    
    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(
            is_valid=True,
            level=ValidationLevel.SUCCESS,
            message="Test message",
            suggestions=["suggestion1", "suggestion2"],
            corrected_value="corrected",
            metadata={"key": "value"}
        )
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        assert result.message == "Test message"
        assert len(result.suggestions) == 2
        assert result.corrected_value == "corrected"
        assert result.metadata["key"] == "value"
        
    def test_validation_result_defaults(self):
        """Test validation result with default values."""
        result = ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message="Error message"
        )
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert result.suggestions == []
        assert result.corrected_value is None
        assert result.metadata == {}


class TestWorkflowBuilder:
    """Test suite for WorkflowBuilder."""
    
    def test_initialization(self):
        """Test workflow builder initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            workflows_dir = Path(temp_dir) / "workflows"
            
            builder = WorkflowBuilder(
                templates_dir=templates_dir,
                workflows_dir=workflows_dir
            )
            
            assert builder.templates_dir == templates_dir
            assert builder.workflows_dir == workflows_dir
            assert templates_dir.exists()
            assert workflows_dir.exists()
            assert len(builder.templates) > 0  # Should have builtin templates
            
    def test_load_builtin_templates(self):
        """Test loading built-in templates."""
        builder = WorkflowBuilder()
        templates = builder._load_builtin_templates()
        
        assert len(templates) > 0
        
        # Check for expected templates
        template_types = [t.workflow_type for t in templates]
        assert WorkflowType.BACKFILL in template_types
        assert WorkflowType.DAILY_UPDATE in template_types
        
    def test_save_and_load_workflow(self):
        """Test saving and loading workflows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir) / "workflows"
            builder = WorkflowBuilder(workflows_dir=workflows_dir)
            
            # Create test workflow
            workflow = Workflow(
                id="test-workflow-id",
                name="Test Workflow",
                description="Test Description",
                workflow_type=WorkflowType.CUSTOM,
                steps=[
                    WorkflowStep(
                        id="step1",
                        name="Test Step",
                        description="Test step description",
                        step_type="test",
                        parameters={"param1": "value1"}
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={"test": "metadata"}
            )
            
            # Save workflow
            builder._save_workflow(workflow)
            
            # Check file exists
            workflow_file = workflows_dir / f"{workflow.id}.json"
            assert workflow_file.exists()
            
            # Load workflow
            loaded_workflow = builder.load_workflow(workflow.id)
            
            assert loaded_workflow is not None
            assert loaded_workflow.id == workflow.id
            assert loaded_workflow.name == workflow.name
            assert loaded_workflow.workflow_type == workflow.workflow_type
            assert len(loaded_workflow.steps) == 1
            assert loaded_workflow.steps[0].name == "Test Step"
            
    def test_list_workflows(self):
        """Test listing workflows."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workflows_dir = Path(temp_dir) / "workflows"
            builder = WorkflowBuilder(workflows_dir=workflows_dir)
            
            # Create test workflow files
            workflow_data = {
                "id": "test-id",
                "name": "Test Workflow",
                "workflow_type": "custom",
                "steps": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            workflow_file = workflows_dir / "test-id.json"
            with open(workflow_file, 'w') as f:
                json.dump(workflow_data, f)
                
            # List workflows
            workflows = builder.list_workflows()
            
            assert len(workflows) == 1
            assert workflows[0]["id"] == "test-id"
            assert workflows[0]["name"] == "Test Workflow"
            
    def test_load_nonexistent_workflow(self):
        """Test loading non-existent workflow."""
        builder = WorkflowBuilder()
        
        workflow = builder.load_workflow("nonexistent-id")
        assert workflow is None


class TestWorkflowComponents:
    """Test suite for workflow data classes."""
    
    def test_workflow_step_creation(self):
        """Test creating workflow step."""
        step = WorkflowStep(
            id="test-step",
            name="Test Step",
            description="Test description",
            step_type="test",
            parameters={"param": "value"}
        )
        
        assert step.id == "test-step"
        assert step.name == "Test Step"
        assert step.status == StepStatus.PENDING
        assert step.validation_results == []
        assert step.execution_time is None
        
    def test_workflow_template_creation(self):
        """Test creating workflow template."""
        template = WorkflowTemplate(
            id="test-template",
            name="Test Template",
            description="Test template description",
            workflow_type=WorkflowType.CUSTOM,
            default_parameters={"param": "default"},
            steps=[{"name": "Step 1", "type": "test"}]
        )
        
        assert template.id == "test-template"
        assert template.workflow_type == WorkflowType.CUSTOM
        assert template.tags == []
        assert len(template.steps) == 1
        
    def test_workflow_creation(self):
        """Test creating workflow."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test description",
            workflow_type=WorkflowType.BACKFILL,
            steps=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert workflow.id == "test-workflow"
        assert workflow.workflow_type == WorkflowType.BACKFILL
        assert workflow.metadata == {}
        assert len(workflow.steps) == 0


class TestValidationConvenienceFunctions:
    """Test suite for convenience validation functions."""
    
    def test_validate_cli_input_symbol(self):
        """Test convenience function for symbol validation."""
        result = validate_cli_input("ES.c.0", "symbol", interactive=False)
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        
    def test_validate_cli_input_symbol_list(self):
        """Test convenience function for symbol list validation."""
        result = validate_cli_input("ES.c.0,AAPL", "symbol_list", interactive=False)
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        
    def test_validate_cli_input_schema(self):
        """Test convenience function for schema validation."""
        result = validate_cli_input("ohlcv-1d", "schema")
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        
    def test_validate_cli_input_date_range(self):
        """Test convenience function for date range validation."""
        result = validate_cli_input(
            "", "date_range", 
            start_date="2024-01-01", 
            end_date="2024-01-31",
            interactive=False
        )
        
        assert result.is_valid
        assert result.level == ValidationLevel.SUCCESS
        
    def test_validate_cli_input_unknown_type(self):
        """Test convenience function with unknown validation type."""
        result = validate_cli_input("test", "unknown_type")
        
        assert not result.is_valid
        assert result.level == ValidationLevel.ERROR
        assert "Unknown validation type" in result.message


class TestMarketCalendarEdgeCases:
    """Test edge cases for MarketCalendar."""
    
    def test_get_trading_days_no_trading_days(self):
        """Test getting trading days when none exist."""
        calendar = MarketCalendar()
        
        # Weekend range
        saturday = date(2024, 1, 6)
        sunday = date(2024, 1, 7)
        
        trading_days = calendar.get_trading_days(saturday, sunday)
        assert len(trading_days) == 0
        
    def test_get_next_trading_day_across_holiday(self):
        """Test getting next trading day across holiday."""
        calendar = MarketCalendar()
        
        # From New Year's Eve (assume it's not a holiday but next day is)
        dec_31 = date(2023, 12, 31)  # Sunday
        next_day = calendar.get_next_trading_day(dec_31)
        
        # Should skip New Year's Day and weekend
        assert next_day > date(2024, 1, 1)
        assert calendar.is_trading_day(next_day)
        
    def test_get_previous_trading_day_across_holiday(self):
        """Test getting previous trading day across holiday."""
        calendar = MarketCalendar()
        
        # From day after New Year's Day
        jan_2 = date(2024, 1, 2)
        prev_day = calendar.get_previous_trading_day(jan_2)
        
        # Should skip New Year's Day and weekend
        assert prev_day < date(2024, 1, 1)
        assert calendar.is_trading_day(prev_day)


class TestSymbolCacheAdvanced:
    """Advanced tests for SymbolCache."""
    
    def test_fuzzy_search_empty_input(self):
        """Test fuzzy search with empty input."""
        cache = SymbolCache()
        
        results = cache.fuzzy_search("", limit=5)
        assert len(results) == 0
        
    def test_fuzzy_search_no_matches(self):
        """Test fuzzy search with no matches."""
        cache = SymbolCache()
        
        # Very unlikely to match anything
        results = cache.fuzzy_search("XYZQWERTY123", limit=5)
        assert len(results) == 0
        
    def test_get_symbols_by_category_unknown(self):
        """Test getting symbols by unknown category."""
        cache = SymbolCache()
        
        symbols = cache.get_symbols_by_category("unknown_category")
        assert len(symbols) == 0
        
    def test_case_insensitive_operations(self):
        """Test that all operations are case insensitive."""
        cache = SymbolCache()
        
        # Add lowercase symbol
        cache.add_symbol("testlower", {"type": "test"})
        
        # Should find with different cases
        assert cache.is_valid_symbol("TESTLOWER")
        assert cache.is_valid_symbol("TestLower")
        assert cache.is_valid_symbol("testlower")
        
        # Fuzzy search should be case insensitive
        results = cache.fuzzy_search("testlow")
        symbols = [r[0] for r in results]
        assert "TESTLOWER" in symbols


if __name__ == "__main__":
    pytest.main([__file__])