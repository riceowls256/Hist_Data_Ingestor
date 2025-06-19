"""
Test suite for CLI symbols commands module.

This module tests all symbol management commands including groups, symbols,
symbol-lookup, and exchange-mapping functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typer.testing import CliRunner
from rich.console import Console

# Test the symbols commands module
from src.cli.commands.symbols import app


class TestSymbolsModule:
    """Test symbols module initialization and basic functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console = Console()
    
    def test_symbols_app_creation(self):
        """Test that symbols app is created correctly."""
        assert app is not None
        assert app.info.name == "symbols"
        assert "symbol management commands" in app.info.help.lower()
    
    def test_symbols_app_commands_available(self):
        """Test that all expected commands are registered."""
        # Test that commands can be invoked (functional test instead of introspection)
        runner = CliRunner()
        
        # Test that each command exists by invoking help
        expected_commands = ["groups", "symbols", "symbol-lookup", "exchange-mapping"]
        for cmd in expected_commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"Command '{cmd}' help failed"
            assert "Usage:" in result.stdout, f"Command '{cmd}' help output invalid"


class TestGroupsCommand:
    """Test the groups command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_list_command(self, mock_manager_class):
        """Test groups --list command."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_groups.return_value = {
            "SP500_SAMPLE": {
                "category": "Equity", 
                "symbols": ["ES.c.0", "SPY"], 
                "description": "S&P 500 sample"
            },
            "ENERGY_FUTURES": {
                "category": "Energy", 
                "symbols": ["CL.c.0", "NG.c.0"], 
                "description": "Energy futures"
            }
        }
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--list"])
        
        # Verify
        assert result.exit_code == 0
        assert "SP500_SAMPLE" in result.stdout
        assert "ENERGY_FUTURES" in result.stdout
        assert "Symbol Groups" in result.stdout
        mock_manager.list_groups.assert_called_once_with(category=None)
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_list_with_category_filter(self, mock_manager_class):
        """Test groups --list with category filter."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_groups.return_value = {
            "ENERGY_FUTURES": {
                "category": "Energy", 
                "symbols": ["CL.c.0", "NG.c.0"], 
                "description": "Energy futures"
            }
        }
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--list", "--category", "Energy"])
        
        # Verify
        assert result.exit_code == 0
        assert "ENERGY_FUTURES" in result.stdout
        mock_manager.list_groups.assert_called_once_with(category="Energy")
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_info_command(self, mock_manager_class):
        """Test groups --info command for specific group."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_group_info.return_value = {
            "name": "SP500_SAMPLE",
            "category": "Equity",
            "symbols": ["ES.c.0", "SPY", "QQQ"],
            "description": "Sample S&P 500 symbols"
        }
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--info", "SP500_SAMPLE"])
        
        # Verify
        assert result.exit_code == 0
        assert "SP500_SAMPLE" in result.stdout
        assert "ES.c.0" in result.stdout
        assert "3" in result.stdout  # Symbol count
        mock_manager.get_group_info.assert_called_once_with("SP500_SAMPLE")
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_info_not_found(self, mock_manager_class):
        """Test groups --info command for non-existent group."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_group_info.return_value = None
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--info", "NONEXISTENT"])
        
        # Verify
        assert result.exit_code == 1
        assert "not found" in result.stdout
        mock_manager.get_group_info.assert_called_once_with("NONEXISTENT")
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_create_command(self, mock_manager_class):
        """Test groups --create command."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.create_group.return_value = True
        
        # Execute command
        result = self.runner.invoke(app, [
            "groups", "--create", "MY_GROUP", 
            "--symbols", "ES.c.0,NQ.c.0", 
            "--description", "My custom group"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "created successfully" in result.stdout
        mock_manager.create_group.assert_called_once_with(
            "MY_GROUP", ["ES.c.0", "NQ.c.0"], "My custom group"
        )
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_create_missing_symbols(self, mock_manager_class):
        """Test groups --create command without symbols parameter."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--create", "MY_GROUP"])
        
        # Verify
        assert result.exit_code == 1
        assert "--symbols required" in result.stdout
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_create_failed(self, mock_manager_class):
        """Test groups --create command failure."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.create_group.return_value = False
        
        # Execute command
        result = self.runner.invoke(app, [
            "groups", "--create", "MY_GROUP", 
            "--symbols", "ES.c.0,NQ.c.0"
        ])
        
        # Verify
        assert result.exit_code == 1
        assert "Failed to create" in result.stdout
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_delete_command(self, mock_manager_class):
        """Test groups --delete command."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.delete_group.return_value = True
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--delete", "MY_GROUP"])
        
        # Verify
        assert result.exit_code == 0
        assert "deleted successfully" in result.stdout
        mock_manager.delete_group.assert_called_once_with("MY_GROUP")
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_delete_failed(self, mock_manager_class):
        """Test groups --delete command failure."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.delete_group.return_value = False
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--delete", "PREDEFINED_GROUP"])
        
        # Verify
        assert result.exit_code == 1
        assert "Failed to delete" in result.stdout
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_default_list_behavior(self, mock_manager_class):
        """Test groups command default behavior (list)."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_groups.return_value = {
            "SP500_SAMPLE": {
                "category": "Equity", 
                "symbols": ["ES.c.0"], 
                "description": "Sample"
            }
        }
        
        # Execute command without any options
        result = self.runner.invoke(app, ["groups"])
        
        # Verify
        assert result.exit_code == 0
        assert "Available Symbol Groups" in result.stdout
        mock_manager.list_groups.assert_called_once_with(category=None)
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_empty_list(self, mock_manager_class):
        """Test groups command with empty groups list."""
        # Setup mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_groups.return_value = {}
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--list"])
        
        # Verify
        assert result.exit_code == 0
        assert "No groups found" in result.stdout


class TestSymbolsCommand:
    """Test the symbols command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.symbols.SymbolHelper')
    def test_symbols_basic_command(self, mock_helper_class):
        """Test basic symbols command."""
        # Setup mock
        mock_helper = Mock()
        mock_helper_class.return_value = mock_helper
        
        # Execute command
        result = self.runner.invoke(app, ["symbols"])
        
        # Verify
        assert result.exit_code == 0
        assert "Symbol Discovery" in result.stdout
        mock_helper.show_symbols.assert_called_once_with(category=None, search=None)
    
    @patch('src.cli.commands.symbols.SymbolHelper')
    def test_symbols_category_filter(self, mock_helper_class):
        """Test symbols command with category filter."""
        # Setup mock
        mock_helper = Mock()
        mock_helper_class.return_value = mock_helper
        
        # Execute command
        result = self.runner.invoke(app, ["symbols", "--category", "Energy"])
        
        # Verify
        assert result.exit_code == 0
        assert "category: Energy" in result.stdout
        mock_helper.show_symbols.assert_called_once_with(category="Energy", search=None)
    
    @patch('src.cli.commands.symbols.SymbolHelper')
    def test_symbols_search_filter(self, mock_helper_class):
        """Test symbols command with search filter."""
        # Setup mock
        mock_helper = Mock()
        mock_helper_class.return_value = mock_helper
        
        # Execute command
        result = self.runner.invoke(app, ["symbols", "--search", "crude"])
        
        # Verify
        assert result.exit_code == 0
        assert "searching symbols for: crude" in result.stdout.lower()
        mock_helper.show_symbols.assert_called_once_with(category=None, search="crude")
    
    @patch('src.cli.commands.symbols.SymbolHelper')
    def test_symbols_both_filters(self, mock_helper_class):
        """Test symbols command with both category and search filters."""
        # Setup mock
        mock_helper = Mock()
        mock_helper_class.return_value = mock_helper
        
        # Execute command
        result = self.runner.invoke(app, ["symbols", "--category", "Energy", "--search", "oil"])
        
        # Verify
        assert result.exit_code == 0
        mock_helper.show_symbols.assert_called_once_with(category="Energy", search="oil")


class TestSymbolLookupCommand:
    """Test the symbol-lookup command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_valid_symbol(self, mock_validator_func):
        """Test symbol-lookup command with valid symbol."""
        # Setup mock
        mock_validator = Mock()
        mock_validator_func.return_value = mock_validator
        
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.metadata = {
            "asset_class": "Future",
            "sector": "Index", 
            "trading_status": "Active",
            "exchange": "CME"
        }
        mock_validator.validate_symbol.return_value = mock_result
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "ES.c.0"])
        
        # Verify
        assert result.exit_code == 0
        assert "ES.c.0' is valid" in result.stdout
        assert "Future" in result.stdout
        assert "Index" in result.stdout
        mock_validator.validate_symbol.assert_called_once_with("ES.c.0")
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_invalid_symbol(self, mock_validator_func):
        """Test symbol-lookup command with invalid symbol."""
        # Setup mock
        mock_validator = Mock()
        mock_validator_func.return_value = mock_validator
        
        mock_result = Mock()
        mock_result.is_valid = False
        mock_validator.validate_symbol.return_value = mock_result
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "INVALID"])
        
        # Verify
        assert result.exit_code == 0
        assert "not found" in result.stdout
        mock_validator.validate_symbol.assert_called_once_with("INVALID")
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_fuzzy_search(self, mock_validator_func):
        """Test symbol-lookup command with fuzzy search."""
        # Setup mock
        mock_validator = Mock()
        mock_validator_func.return_value = mock_validator
        
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.suggestions = [
            {"symbol": "ES.c.0", "asset_class": "Future", "sector": "Index"},
            {"symbol": "ESH4", "asset_class": "Future", "sector": "Index"}
        ]
        mock_validator.validate_symbol.return_value = mock_result
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "ES", "--fuzzy"])
        
        # Verify
        assert result.exit_code == 0
        assert "Similar symbols found" in result.stdout
        assert "ES.c.0" in result.stdout
        assert "ESH4" in result.stdout
        mock_validator.validate_symbol.assert_called_once_with("ES")
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_fuzzy_no_suggestions(self, mock_validator_func):
        """Test symbol-lookup command with fuzzy search but no suggestions."""
        # Setup mock
        mock_validator = Mock()
        mock_validator_func.return_value = mock_validator
        
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.suggestions = []
        mock_validator.validate_symbol.return_value = mock_result
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "XYZ", "--fuzzy"])
        
        # Verify
        assert result.exit_code == 0
        assert "No similar symbols found" in result.stdout
        mock_validator.validate_symbol.assert_called_once_with("XYZ")
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_suggestions_limit(self, mock_validator_func):
        """Test symbol-lookup command with custom suggestions limit."""
        # Setup mock
        mock_validator = Mock()
        mock_validator_func.return_value = mock_validator
        
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.suggestions = [
            {"symbol": f"ES{i}", "asset_class": "Future", "sector": "Index"} 
            for i in range(10)
        ]
        mock_validator.validate_symbol.return_value = mock_result
        
        # Execute command with limit
        result = self.runner.invoke(app, ["symbol-lookup", "ES", "--fuzzy", "--suggestions", "3"])
        
        # Verify
        assert result.exit_code == 0
        # Should only show first 3 suggestions
        stdout_lines = result.stdout.split('\n')
        symbol_lines = [line for line in stdout_lines if 'ES' in line and '│' in line]
        assert len(symbol_lines) <= 3


class TestExchangeMappingCommand:
    """Test the exchange-mapping command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_list_exchanges(self, mock_mapper_func):
        """Test exchange-mapping --list command."""
        # Setup mock - the command calls get_exchange_info for each exchange
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Mock get_exchange_info to return exchange details
        def mock_exchange_info(exchange):
            exchange_data = {
                "NYSE": {"name": "New York Stock Exchange", "trading_hours": "09:30-16:00 ET"},
                "NASDAQ": {"name": "NASDAQ Stock Market", "trading_hours": "09:30-16:00 ET"},
                "CME_Equity": {"name": "CME Equity Index Futures", "trading_hours": "17:00-16:00 CT (nearly 24h)"},
                "CME_Energy": {"name": "CME Energy Futures", "trading_hours": "17:00-16:00 CT (nearly 24h)"},
                "CME_Commodity": {"name": "CME Agricultural & Metals", "trading_hours": "Various by product"},
                "CME_FX": {"name": "CME_FX", "trading_hours": "Unknown"},
                "CME_InterestRate": {"name": "CME_InterestRate", "trading_hours": "Unknown"},
                "LSE": {"name": "London Stock Exchange", "trading_hours": "08:00-16:30 GMT"},
                "XETR": {"name": "XETR", "trading_hours": "Unknown"}
            }
            return exchange_data.get(exchange, {"name": exchange, "trading_hours": "Unknown"})
        
        mock_mapper.get_exchange_info.side_effect = mock_exchange_info
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--list"])
        
        # Verify
        assert result.exit_code == 0
        assert "Supported Exchange Calendars" in result.stdout
        assert "NYSE" in result.stdout
        assert "NASDAQ" in result.stdout
        assert "CME_Equity" in result.stdout
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_show_mappings(self, mock_mapper_func):
        """Test exchange-mapping --mappings command."""
        # Setup mock - this command shows predefined patterns, doesn't call mapper methods
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--mappings"])
        
        # Verify
        assert result.exit_code == 0
        assert "Exchange Mapping Rules" in result.stdout
        assert "Pattern-based mapping rules" in result.stdout
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_exchange_info(self, mock_mapper_func):
        """Test exchange-mapping --info command."""
        # Setup mock
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        mock_mapper.get_exchange_info.return_value = {
            "name": "New York Stock Exchange",
            "description": "Primary US equity exchange",
            "calendar": "NYSE"
        }
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--info", "NYSE"])
        
        # Verify
        assert result.exit_code == 0
        assert "Exchange Information: NYSE" in result.stdout
        assert "New York Stock Exchange" in result.stdout
        mock_mapper.get_exchange_info.assert_called_once_with("NYSE")
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_info_not_found(self, mock_mapper_func):
        """Test exchange-mapping --info command for non-existent exchange."""
        # Setup mock
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        mock_mapper.get_exchange_info.return_value = None
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--info", "NONEXISTENT"])
        
        # Verify
        assert result.exit_code == 1
        assert "not found" in result.stdout
        mock_mapper.get_exchange_info.assert_called_once_with("NONEXISTENT")
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_test_symbol(self, mock_mapper_func):
        """Test exchange-mapping --test command."""
        # Setup mock - uses map_symbol_to_exchange which returns (exchange, confidence, mapping_info)
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Create mock mapping_info object with required attributes
        mock_mapping_info = Mock()
        mock_mapping_info.asset_class.value = "futures"
        mock_mapping_info.region.value = "us"
        mock_mapping_info.description = "CME Equity index futures"
        
        mock_mapper.map_symbol_to_exchange.return_value = ("CME_Equity", 0.95, mock_mapping_info)
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--test", "ES.c.0"])
        
        # Verify
        assert result.exit_code == 0
        assert "Testing symbol mapping: ES.c.0" in result.stdout
        assert "CME_Equity" in result.stdout
        assert "95.0%" in result.stdout
        assert "futures" in result.stdout
        assert "us" in result.stdout
        mock_mapper.map_symbol_to_exchange.assert_called_once_with("ES.c.0")
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_test_no_mapping(self, mock_mapper_func):
        """Test exchange-mapping --test command with no mapping found."""
        # Setup mock - return None or very low confidence to indicate no mapping
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        mock_mapper.map_symbol_to_exchange.return_value = (None, 0.0, {})
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--test", "UNKNOWN"])
        
        # Verify
        assert result.exit_code == 0  # Command doesn't fail, just shows no result
        assert "Testing symbol mapping: UNKNOWN" in result.stdout
        mock_mapper.map_symbol_to_exchange.assert_called_once_with("UNKNOWN")
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_batch_analysis(self, mock_mapper_func):
        """Test exchange-mapping with multiple symbols."""
        # Setup mock - for batch analysis, the implementation calls map_symbol_to_exchange for each symbol
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Create proper mock mapping_info objects with asset_class.value
        def create_mock_mapping_info(asset_class_value):
            mock_mapping_info = Mock()
            mock_mapping_info.asset_class.value = asset_class_value
            mock_mapping_info.region.value = "us"
            mock_mapping_info.description = f"Mock {asset_class_value} mapping"
            return mock_mapping_info
        
        # Mock individual symbol mappings
        def mock_map_symbol(symbol):
            mapping = {
                "ES.c.0": ("CME_Equity", 0.95, create_mock_mapping_info("futures")),
                "CL.c.0": ("CME_Energy", 0.92, create_mock_mapping_info("futures")), 
                "SPY": ("NYSE", 0.88, create_mock_mapping_info("equity"))
            }
            return mapping.get(symbol, (None, 0.0, {}))
        
        mock_mapper.map_symbol_to_exchange.side_effect = mock_map_symbol
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "ES.c.0,CL.c.0,SPY"])
        
        # Verify
        assert result.exit_code == 0
        assert "Exchange Mapping Analysis" in result.stdout
        assert "ES.c.0" in result.stdout
        assert "CL.c.0" in result.stdout
        assert "SPY" in result.stdout
        assert "CME_Equity" in result.stdout
        assert "CME_Energy" in result.stdout
        assert "NYSE" in result.stdout
        
        # Should call map_symbol_to_exchange for each symbol
        assert mock_mapper.map_symbol_to_exchange.call_count == 3
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_confidence_filter(self, mock_mapper_func):
        """Test exchange-mapping with confidence threshold filtering."""
        # Setup mock
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Create proper mock mapping_info objects with asset_class.value
        def create_mock_mapping_info(asset_class_value):
            mock_mapping_info = Mock()
            mock_mapping_info.asset_class.value = asset_class_value
            mock_mapping_info.region.value = "us"
            mock_mapping_info.description = f"Mock {asset_class_value} mapping"
            return mock_mapping_info
        
        # Mock individual symbol mappings
        def mock_map_symbol(symbol):
            mapping = {
                "ES.c.0": ("CME_Equity", 0.95, create_mock_mapping_info("futures")),
                "SPY": ("NYSE", 0.70, create_mock_mapping_info("equity"))  # Below threshold
            }
            return mapping.get(symbol, (None, 0.0, {}))
        
        mock_mapper.map_symbol_to_exchange.side_effect = mock_map_symbol
        
        # Execute command with high confidence threshold
        result = self.runner.invoke(app, [
            "exchange-mapping", "ES.c.0,SPY", "--min-confidence", "0.8"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "ES.c.0" in result.stdout  # Should be included
        assert "95.0%" in result.stdout
        # SPY should be filtered out due to low confidence
        spy_lines = [line for line in result.stdout.split('\n') if 'SPY' in line and '│' in line]
        assert len(spy_lines) == 0
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_no_results_above_threshold(self, mock_mapper_func):
        """Test exchange-mapping with no results above confidence threshold."""
        # Setup mock
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        mock_mapper.map_symbol_to_exchange.return_value = ("NYSE", 0.30, {"asset_class": "ETF"})
        
        # Execute command with high threshold
        result = self.runner.invoke(app, [
            "exchange-mapping", "UNKNOWN", "--min-confidence", "0.8"
        ])
        
        # Verify
        assert result.exit_code == 1
        assert "No results above confidence threshold" in result.stdout
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_default_help(self, mock_mapper_func):
        """Test exchange-mapping command with no options (shows help)."""
        # Setup mock
        mock_mapper = Mock()
        mock_mapper_func.return_value = mock_mapper
        
        # Execute command without any options
        result = self.runner.invoke(app, ["exchange-mapping"])
        
        # Verify
        assert result.exit_code == 0
        assert "Exchange Mapping Tool" in result.stdout
        assert "Available actions:" in result.stdout
        assert "--list" in result.stdout
        assert "--mappings" in result.stdout


class TestSymbolsCommandIntegration:
    """Integration tests for symbols commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_symbols_help_command(self):
        """Test symbols --help shows all available commands."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "groups" in result.stdout
        assert "symbols" in result.stdout
        assert "symbol-lookup" in result.stdout
        assert "exchange-mapping" in result.stdout
    
    def test_groups_help_command(self):
        """Test groups --help command."""
        result = self.runner.invoke(app, ["groups", "--help"])
        
        assert result.exit_code == 0
        assert "--list" in result.stdout
        assert "--category" in result.stdout
        assert "--info" in result.stdout
        assert "--create" in result.stdout
        assert "--delete" in result.stdout
    
    def test_symbol_lookup_help_command(self):
        """Test symbol-lookup --help command."""
        result = self.runner.invoke(app, ["symbol-lookup", "--help"])
        
        assert result.exit_code == 0
        assert "--fuzzy" in result.stdout
        assert "--suggestions" in result.stdout
        assert "SYMBOL" in result.stdout
    
    @patch('src.cli.commands.symbols.logger')
    def test_error_handling_and_logging(self, mock_logger):
        """Test error handling and logging in symbols commands."""
        # Test with a command that would cause an exception
        with patch('src.cli.commands.symbols.SymbolGroupManager', side_effect=Exception("Mock error")):
            result = self.runner.invoke(app, ["groups", "--list"])
            
            # Should handle error gracefully
            assert result.exit_code == 1
            assert "Groups command error" in result.stdout
            
            # Should log the exception
            mock_logger.exception.assert_called()


class TestSymbolsErrorHandling:
    """Test error handling in symbols commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.symbols.SymbolGroupManager')
    def test_groups_exception_handling(self, mock_manager_class):
        """Test groups command exception handling."""
        # Setup mock to raise exception
        mock_manager_class.side_effect = Exception("Database connection failed")
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--list"])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Groups command error" in result.stdout
        assert "troubleshoot groups" in result.stdout
    
    @patch('src.cli.commands.symbols.create_smart_validator')
    def test_symbol_lookup_exception_handling(self, mock_validator_func):
        """Test symbol-lookup command exception handling."""
        # Setup mock to raise exception
        mock_validator_func.side_effect = Exception("Validation service unavailable")
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "ES.c.0"])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Symbol lookup error" in result.stdout
        assert "troubleshoot symbol-lookup" in result.stdout
    
    @patch('src.cli.commands.symbols.get_exchange_mapper')
    def test_exchange_mapping_exception_handling(self, mock_mapper_func):
        """Test exchange-mapping command exception handling."""
        # Setup mock to raise exception
        mock_mapper_func.side_effect = Exception("Exchange service down")
        
        # Execute command
        result = self.runner.invoke(app, ["exchange-mapping", "--list"])
        
        # Verify error handling
        assert result.exit_code == 1
        assert "Exchange mapping error" in result.stdout
        assert "troubleshoot exchange-mapping" in result.stdout


# Test fixtures and utilities
@pytest.fixture
def mock_symbol_group_manager():
    """Fixture for mocked SymbolGroupManager."""
    with patch('src.cli.commands.symbols.SymbolGroupManager') as mock:
        manager = Mock()
        mock.return_value = manager
        yield manager


@pytest.fixture  
def mock_symbol_helper():
    """Fixture for mocked SymbolHelper."""
    with patch('src.cli.commands.symbols.SymbolHelper') as mock:
        helper = Mock()
        mock.return_value = helper
        yield helper


@pytest.fixture
def mock_smart_validator():
    """Fixture for mocked SmartValidator."""
    with patch('src.cli.commands.symbols.create_smart_validator') as mock:
        validator = Mock()
        mock.return_value = validator
        yield validator


@pytest.fixture
def mock_exchange_mapper():
    """Fixture for mocked ExchangeMapper."""
    with patch('src.cli.commands.symbols.get_exchange_mapper') as mock:
        mapper = Mock()
        mock.return_value = mapper
        yield mapper


class TestSymbolsWithFixtures:
    """Test symbols commands using pytest fixtures."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_groups_with_fixture(self, mock_symbol_group_manager):
        """Test groups command using fixture."""
        # Setup fixture
        mock_symbol_group_manager.list_groups.return_value = {
            "TEST_GROUP": {"symbols": ["ES.c.0"], "category": "Test", "description": "Test group"}
        }
        
        # Execute command
        result = self.runner.invoke(app, ["groups", "--list"])
        
        # Verify
        assert result.exit_code == 0
        assert "TEST_GROUP" in result.stdout
        mock_symbol_group_manager.list_groups.assert_called_once()
    
    def test_symbol_lookup_with_fixture(self, mock_smart_validator):
        """Test symbol-lookup command using fixture."""
        # Setup fixture
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.metadata = {"asset_class": "Future", "sector": "Index"}
        mock_smart_validator.validate_symbol.return_value = mock_result
        
        # Execute command
        result = self.runner.invoke(app, ["symbol-lookup", "ES.c.0"])
        
        # Verify
        assert result.exit_code == 0
        assert "is valid" in result.stdout
        assert "Future" in result.stdout
        mock_smart_validator.validate_symbol.assert_called_once_with("ES.c.0")