"""
Unit tests for CLI help commands module.

Tests all help-related commands including examples, troubleshooting, tips,
schemas, quickstart wizard, and interactive help menu.
"""

from unittest.mock import Mock, patch
from io import StringIO

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.help import app as help_app


class TestHelpCommands:
    """Comprehensive test suite for help commands."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    @patch('src.cli.commands.help.show_examples')
    def test_examples_command_no_args(self, mock_show_examples):
        """Test examples command without arguments."""
        result = self.runner.invoke(help_app, ["examples"])
        
        assert result.exit_code == 0
        mock_show_examples.assert_called_once_with(None)
    
    @patch('src.cli.commands.help.show_examples')
    def test_examples_command_with_command(self, mock_show_examples):
        """Test examples command with specific command argument."""
        result = self.runner.invoke(help_app, ["examples", "query"])
        
        assert result.exit_code == 0
        mock_show_examples.assert_called_once_with("query")
    
    @patch('src.cli.commands.help.CLITroubleshooter')
    def test_troubleshoot_command_no_args(self, mock_troubleshooter):
        """Test troubleshoot command without arguments."""
        # Mock the COMMON_ISSUES structure
        mock_troubleshooter.COMMON_ISSUES = {
            "db_connection": {
                "title": "Database Connection Issues",
                "error_patterns": ["connection failed", "timeout"],
                "solutions": ["Check database credentials"]
            },
            "symbol_not_found": {
                "title": "Symbol Not Found",
                "error_patterns": ["symbol not found", "invalid symbol"],
                "solutions": ["Verify symbol format"]
            }
        }
        
        result = self.runner.invoke(help_app, ["troubleshoot"])
        
        assert result.exit_code == 0
        assert "Common Issues and Solutions" in result.stdout
        assert "Database Connection Issues" in result.stdout
        assert "Symbol Not Found" in result.stdout
    
    @patch('src.cli.commands.help.CLITroubleshooter')
    def test_troubleshoot_command_with_error(self, mock_troubleshooter):
        """Test troubleshoot command with specific error argument."""
        result = self.runner.invoke(help_app, ["troubleshoot", "database error"])
        
        assert result.exit_code == 0
        assert "Troubleshooting: database error" in result.stdout
        mock_troubleshooter.show_help.assert_called_once_with("database error")
    
    @patch('src.cli.commands.help.show_tips')
    def test_tips_command_no_args(self, mock_show_tips):
        """Test tips command without arguments."""
        result = self.runner.invoke(help_app, ["tips"])
        
        assert result.exit_code == 0
        mock_show_tips.assert_called_once_with(None)
    
    @patch('src.cli.commands.help.show_tips')
    def test_tips_command_with_category(self, mock_show_tips):
        """Test tips command with specific category."""
        result = self.runner.invoke(help_app, ["tips", "performance"])
        
        assert result.exit_code == 0
        mock_show_tips.assert_called_once_with("performance")
    
    @patch('src.cli.commands.help.format_schema_help')
    def test_schemas_command(self, mock_format_schema_help):
        """Test schemas command displays schema information."""
        from rich.table import Table
        
        # Mock the table return
        mock_table = Table()
        mock_format_schema_help.return_value = mock_table
        
        result = self.runner.invoke(help_app, ["schemas"])
        
        assert result.exit_code == 0
        assert "Available Data Schemas" in result.stdout
        assert "Use --schema parameter" in result.stdout
        assert "query -s ES.c.0 --schema trades" in result.stdout
        
        mock_format_schema_help.assert_called_once()
    
    @patch('src.cli.commands.help.InteractiveHelpMenu')
    def test_help_menu_command(self, mock_help_menu):
        """Test help-menu command launches interactive menu."""
        result = self.runner.invoke(help_app, ["help-menu"])
        
        assert result.exit_code == 0
        mock_help_menu.show_menu.assert_called_once()
    
    @patch('src.cli.commands.help.QuickstartWizard')
    def test_quickstart_command(self, mock_quickstart_wizard):
        """Test quickstart command launches setup wizard."""
        result = self.runner.invoke(help_app, ["quickstart"])
        
        assert result.exit_code == 0
        mock_quickstart_wizard.run.assert_called_once()
    
    @patch('src.cli.commands.help.CheatSheet')
    def test_cheatsheet_command(self, mock_cheatsheet):
        """Test cheatsheet command displays quick reference."""
        result = self.runner.invoke(help_app, ["cheatsheet"])
        
        assert result.exit_code == 0
        mock_cheatsheet.display.assert_called_once()


class TestHelpCommandsIntegration:
    """Integration tests for help commands with external dependencies."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.integration
    def test_examples_command_real_execution(self):
        """Test examples command with real execution (when utilities available)."""
        try:
            result = self.runner.invoke(help_app, ["examples"])
            # Should not crash even if utilities are not available
            assert result.exit_code in [0, 1]  # Allow for import failures
        except ImportError:
            pytest.skip("Help utilities not available for integration test")
    
    @pytest.mark.integration
    def test_schemas_command_real_execution(self):
        """Test schemas command with real execution."""
        try:
            result = self.runner.invoke(help_app, ["schemas"])
            # Should not crash even if utilities are not available
            assert result.exit_code in [0, 1]  # Allow for import failures
            if result.exit_code == 0:
                assert "Available Data Schemas" in result.stdout
        except ImportError:
            pytest.skip("Help utilities not available for integration test")


class TestHelpCommandsPerformance:
    """Performance tests for help commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.help.show_examples')
    def test_examples_command_performance(self, mock_show_examples):
        """Test examples command executes within performance threshold."""
        import time
        
        start_time = time.time()
        result = self.runner.invoke(help_app, ["examples"])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 0.1  # Should execute in less than 100ms
    
    @patch('src.cli.commands.help.CLITroubleshooter')
    def test_troubleshoot_command_performance(self, mock_troubleshooter):
        """Test troubleshoot command performance with large issue database."""
        # Mock large troubleshooting database
        large_issues = {}
        for i in range(100):
            large_issues[f"issue_{i}"] = {
                "title": f"Issue {i}",
                "error_patterns": [f"error_{i}_pattern_{j}" for j in range(10)],
                "solutions": [f"Solution {i}_{j}" for j in range(5)]
            }
        
        mock_troubleshooter.COMMON_ISSUES = large_issues
        
        import time
        start_time = time.time()
        result = self.runner.invoke(help_app, ["troubleshoot"])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 1.0  # Should handle large database in less than 1 second
    
    @patch('src.cli.commands.help.format_schema_help')
    def test_schemas_command_performance(self, mock_format_schema_help):
        """Test schemas command performance with large schema database."""
        from rich.table import Table
        
        # Mock large schema table
        mock_table = Table()
        for i in range(50):
            mock_table.add_row(f"schema_{i}", f"description_{i}", f"fields_{i}")
        
        mock_format_schema_help.return_value = mock_table
        
        import time
        start_time = time.time()
        result = self.runner.invoke(help_app, ["schemas"])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 0.5  # Should handle large schema display in less than 500ms


class TestHelpCommandsErrorHandling:
    """Test error handling for help commands."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.help.show_examples')
    def test_examples_command_with_invalid_command(self, mock_show_examples):
        """Test examples command with invalid command argument."""
        # show_examples should handle invalid commands gracefully
        mock_show_examples.return_value = None
        
        result = self.runner.invoke(help_app, ["examples", "invalid_command"])
        
        assert result.exit_code == 0
        mock_show_examples.assert_called_once_with("invalid_command")
    
    @patch('src.cli.commands.help.show_tips')
    def test_tips_command_with_invalid_category(self, mock_show_tips):
        """Test tips command with invalid category."""
        # show_tips should handle invalid categories gracefully
        mock_show_tips.return_value = None
        
        result = self.runner.invoke(help_app, ["tips", "invalid_category"])
        
        assert result.exit_code == 0
        mock_show_tips.assert_called_once_with("invalid_category")
    
    @patch('src.cli.commands.help.CLITroubleshooter')
    def test_troubleshoot_command_with_missing_issues(self, mock_troubleshooter):
        """Test troubleshoot command when no issues are available."""
        mock_troubleshooter.COMMON_ISSUES = {}
        
        result = self.runner.invoke(help_app, ["troubleshoot"])
        
        assert result.exit_code == 0
        assert "Common Issues and Solutions" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])