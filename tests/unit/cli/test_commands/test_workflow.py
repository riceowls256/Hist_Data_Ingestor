"""
Unit tests for CLI workflow commands module.

Tests all workflow-related commands including workflows and workflow builder
with comprehensive parameter validation and execution scenarios.
"""

from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.workflow import (
    app as workflow_app,
    _list_workflows,
    _load_workflow,
    _run_workflow,
    _get_mock_workflows
)


class TestWorkflowCommands:
    """Comprehensive test suite for workflow commands."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    # Test workflows command
    @patch('src.cli.commands.workflow.WorkflowExamples')
    def test_workflows_command_no_args(self, mock_workflow_examples):
        """Test workflows command without arguments (list all)."""
        mock_workflow_examples.show_workflow = Mock()
        
        result = self.runner.invoke(workflow_app, ["workflows"])
        
        assert result.exit_code == 0
        mock_workflow_examples.show_workflow.assert_called_once_with(None)
    
    @patch('src.cli.commands.workflow.WorkflowExamples')
    def test_workflows_command_specific_workflow(self, mock_workflow_examples):
        """Test workflows command with specific workflow name."""
        mock_workflow_examples.show_workflow = Mock()
        
        result = self.runner.invoke(workflow_app, ["workflows", "daily_analysis"])
        
        assert result.exit_code == 0
        mock_workflow_examples.show_workflow.assert_called_once_with("daily_analysis")
    
    @patch('src.cli.commands.workflow.WorkflowExamples')
    def test_workflows_command_error_handling(self, mock_workflow_examples):
        """Test workflows command error handling."""
        mock_workflow_examples.show_workflow.side_effect = Exception("Test error")
        
        result = self.runner.invoke(workflow_app, ["workflows"])
        
        assert result.exit_code == 1
        assert "Error displaying workflows" in result.stdout
    
    # Test workflow command - create action
    @patch('src.cli.commands.workflow.create_interactive_workflow')
    def test_workflow_create_command_basic(self, mock_create_workflow):
        """Test workflow create command without type specification."""
        mock_workflow = Mock()
        mock_workflow.name = "Test Workflow"
        mock_workflow.workflow_type.value = "custom"
        mock_workflow.steps = ["step1", "step2"]
        mock_workflow.id = "test-id-123"
        mock_create_workflow.return_value = mock_workflow
        
        result = self.runner.invoke(workflow_app, ["workflow", "create"])
        
        assert result.exit_code == 0
        assert "Creating Interactive Workflow" in result.stdout
        assert "Workflow 'Test Workflow' created successfully" in result.stdout
        mock_create_workflow.assert_called_once_with(None)
    
    @patch('src.cli.commands.workflow.create_interactive_workflow')
    @patch('src.cli.commands.workflow.WorkflowType')
    def test_workflow_create_command_with_type(self, mock_workflow_type, mock_create_workflow):
        """Test workflow create command with workflow type."""
        mock_type_enum = Mock()
        mock_workflow_type.return_value = mock_type_enum
        
        mock_workflow = Mock()
        mock_workflow.name = "Backfill Workflow"
        mock_workflow.workflow_type.value = "backfill"
        mock_workflow.steps = ["step1", "step2", "step3"]
        mock_workflow.id = "backfill-id-456"
        mock_create_workflow.return_value = mock_workflow
        
        result = self.runner.invoke(workflow_app, [
            "workflow", "create", "--type", "backfill"
        ])
        
        assert result.exit_code == 0
        assert "Creating Interactive Workflow" in result.stdout
        assert "Workflow 'Backfill Workflow' created successfully" in result.stdout
        mock_workflow_type.assert_called_once_with("backfill")
        mock_create_workflow.assert_called_once_with(mock_type_enum)
    
    @patch('src.cli.commands.workflow.WorkflowType')
    def test_workflow_create_command_invalid_type(self, mock_workflow_type):
        """Test workflow create command with invalid workflow type."""
        mock_workflow_type.side_effect = ValueError("Invalid type")
        
        result = self.runner.invoke(workflow_app, [
            "workflow", "create", "--type", "invalid_type"
        ])
        
        assert result.exit_code == 1
        assert "Invalid workflow type: invalid_type" in result.stdout
        assert "Valid types:" in result.stdout
    
    @patch('src.cli.commands.workflow.create_interactive_workflow')
    def test_workflow_create_command_cancelled(self, mock_create_workflow):
        """Test workflow create command when user cancels."""
        mock_create_workflow.return_value = None
        
        result = self.runner.invoke(workflow_app, ["workflow", "create"])
        
        assert result.exit_code == 0
        assert "Workflow creation cancelled" in result.stdout
    
    @patch('src.cli.commands.workflow.create_interactive_workflow')
    def test_workflow_create_command_error(self, mock_create_workflow):
        """Test workflow create command with creation error."""
        mock_create_workflow.side_effect = Exception("Creation failed")
        
        result = self.runner.invoke(workflow_app, ["workflow", "create"])
        
        assert result.exit_code == 1
        assert "Failed to create workflow: Creation failed" in result.stdout
    
    # Test workflow command - list action
    @patch('src.cli.commands.workflow._list_workflows')
    def test_workflow_list_command(self, mock_list_workflows):
        """Test workflow list command."""
        result = self.runner.invoke(workflow_app, ["workflow", "list"])
        
        assert result.exit_code == 0
        assert "Saved Workflows" in result.stdout
        mock_list_workflows.assert_called_once()
    
    # Test workflow command - load action
    @patch('src.cli.commands.workflow._load_workflow')
    def test_workflow_load_command_with_name(self, mock_load_workflow):
        """Test workflow load command with workflow name."""
        result = self.runner.invoke(workflow_app, [
            "workflow", "load", "--name", "Test Workflow"
        ])
        
        assert result.exit_code == 0
        assert "Loading Workflow: Test Workflow" in result.stdout
        mock_load_workflow.assert_called_once_with("Test Workflow")
    
    def test_workflow_load_command_missing_name(self):
        """Test workflow load command without workflow name."""
        result = self.runner.invoke(workflow_app, ["workflow", "load"])
        
        assert result.exit_code == 1
        assert "Workflow name is required for load action" in result.stdout
    
    # Test workflow command - run action
    @patch('src.cli.commands.workflow._run_workflow')
    def test_workflow_run_command_with_name(self, mock_run_workflow):
        """Test workflow run command with workflow name."""
        result = self.runner.invoke(workflow_app, [
            "workflow", "run", "--name", "Test Workflow"
        ])
        
        assert result.exit_code == 0
        assert "Running Workflow: Test Workflow" in result.stdout
        mock_run_workflow.assert_called_once_with("Test Workflow")
    
    def test_workflow_run_command_missing_name(self):
        """Test workflow run command without workflow name."""
        result = self.runner.invoke(workflow_app, ["workflow", "run"])
        
        assert result.exit_code == 1
        assert "Workflow name is required for run action" in result.stdout
    
    # Test workflow command - invalid action
    def test_workflow_command_invalid_action(self):
        """Test workflow command with invalid action."""
        result = self.runner.invoke(workflow_app, ["workflow", "invalid_action"])
        
        assert result.exit_code == 1
        assert "Invalid action: invalid_action" in result.stdout
        assert "Valid actions: create, list, load, run" in result.stdout


class TestWorkflowUtilityFunctions:
    """Test suite for workflow utility functions."""
    
    def setup_method(self):
        """Set up test fixtures for utility function tests."""
        self.console = Console(file=StringIO(), force_terminal=True)
    
    def test_get_mock_workflows(self):
        """Test mock workflows data generation."""
        workflows = _get_mock_workflows()
        
        assert isinstance(workflows, list)
        assert len(workflows) > 0
        
        # Verify structure of first workflow
        first_workflow = workflows[0]
        required_fields = ["name", "type", "steps", "created", "status", "description", "step_details"]
        for field in required_fields:
            assert field in first_workflow
        
        assert isinstance(first_workflow["steps"], int)
        assert isinstance(first_workflow["step_details"], list)
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    def test_list_workflows_with_data(self, mock_console, mock_get_workflows):
        """Test list workflows with existing workflow data."""
        mock_workflows = [
            {
                "name": "Test Workflow",
                "type": "custom",
                "steps": 3,
                "created": "2024-01-01",
                "status": "ready"
            }
        ]
        mock_get_workflows.return_value = mock_workflows
        
        _list_workflows()
        
        # Verify console.print was called with table
        assert mock_console.print.called
        mock_get_workflows.assert_called_once()
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    def test_list_workflows_empty(self, mock_console, mock_get_workflows):
        """Test list workflows with no workflow data."""
        mock_get_workflows.return_value = []
        
        _list_workflows()
        
        mock_console.print.assert_any_call("📭 [yellow]No saved workflows found[/yellow]")
        mock_get_workflows.assert_called_once()
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    def test_load_workflow_found(self, mock_console, mock_get_workflows):
        """Test load workflow with existing workflow."""
        mock_workflows = [
            {
                "name": "Test Workflow",
                "type": "custom",
                "steps": 3,
                "created": "2024-01-01",
                "status": "ready",
                "description": "Test description",
                "step_details": ["Step 1", "Step 2", "Step 3"]
            }
        ]
        mock_get_workflows.return_value = mock_workflows
        
        _load_workflow("Test Workflow")
        
        # Verify workflow details were printed
        assert mock_console.print.called
        mock_get_workflows.assert_called_once()
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    def test_load_workflow_not_found(self, mock_console, mock_get_workflows):
        """Test load workflow with non-existent workflow."""
        mock_get_workflows.return_value = []
        
        _load_workflow("Nonexistent Workflow")
        
        mock_console.print.assert_any_call("❌ [red]Workflow 'Nonexistent Workflow' not found[/red]")
        mock_get_workflows.assert_called_once()
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    @patch('src.cli.commands.workflow.EnhancedProgress')
    def test_run_workflow_found(self, mock_progress, mock_console, mock_get_workflows):
        """Test run workflow with existing workflow."""
        mock_workflows = [
            {
                "name": "Test Workflow",
                "type": "custom",
                "steps": 2,
                "created": "2024-01-01",
                "status": "ready",
                "step_details": ["Step 1", "Step 2"]
            }
        ]
        mock_get_workflows.return_value = mock_workflows
        
        # Mock progress context manager
        mock_progress_instance = Mock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance
        mock_progress.return_value.__exit__.return_value = None
        
        _run_workflow("Test Workflow")
        
        # Verify workflow execution was initiated
        assert mock_console.print.called
        mock_get_workflows.assert_called_once()
    
    @patch('src.cli.commands.workflow._get_mock_workflows')
    @patch('src.cli.commands.workflow.console')
    def test_run_workflow_not_found(self, mock_console, mock_get_workflows):
        """Test run workflow with non-existent workflow."""
        mock_get_workflows.return_value = []
        
        _run_workflow("Nonexistent Workflow")
        
        mock_console.print.assert_any_call("❌ [red]Workflow 'Nonexistent Workflow' not found[/red]")
        mock_get_workflows.assert_called_once()


class TestWorkflowCommandErrorHandling:
    """Test error handling for workflow commands."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.workflow._list_workflows')
    def test_workflow_list_with_exception(self, mock_list_workflows):
        """Test workflow list command with internal exception."""
        mock_list_workflows.side_effect = Exception("Internal error")
        
        result = self.runner.invoke(workflow_app, ["workflow", "list"])
        
        assert result.exit_code == 1
        assert "Workflow command failed" in result.stdout
    
    @patch('src.cli.commands.workflow._load_workflow')
    def test_workflow_load_with_exception(self, mock_load_workflow):
        """Test workflow load command with internal exception."""
        mock_load_workflow.side_effect = Exception("Load error")
        
        result = self.runner.invoke(workflow_app, [
            "workflow", "load", "--name", "Test"
        ])
        
        assert result.exit_code == 1
        assert "Workflow command failed" in result.stdout


class TestWorkflowCommandIntegration:
    """Integration tests for workflow commands."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.integration
    def test_workflows_command_all_workflows(self):
        """Test workflows command with all available workflow types."""
        workflow_types = ["daily_analysis", "historical_research", "intraday_analysis"]
        
        for workflow_type in workflow_types:
            with patch('src.cli.commands.workflow.WorkflowExamples') as mock_examples:
                mock_examples.show_workflow = Mock()
                
                result = self.runner.invoke(workflow_app, ["workflows", workflow_type])
                
                assert result.exit_code == 0
                mock_examples.show_workflow.assert_called_once_with(workflow_type)
    
    @pytest.mark.integration
    def test_workflow_command_all_actions(self):
        """Test workflow command with all available actions."""
        actions_tests = [
            (["workflow", "create"], 0),  # Should work with mocked dependencies
            (["workflow", "list"], 0),    # Should work with mock data
            (["workflow", "load"], 1),    # Should fail without name
            (["workflow", "run"], 1),     # Should fail without name
        ]
        
        for cmd_args, expected_exit_code in actions_tests:
            with patch('src.cli.commands.workflow.create_interactive_workflow') as mock_create:
                mock_create.return_value = None  # Simulate cancellation
                
                result = self.runner.invoke(workflow_app, cmd_args)
                assert result.exit_code == expected_exit_code


class TestWorkflowCommandPerformance:
    """Performance tests for workflow commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    def test_workflows_command_performance(self):
        """Test workflows command executes within performance threshold."""
        with patch('src.cli.commands.workflow.WorkflowExamples') as mock_examples:
            mock_examples.show_workflow = Mock()
            
            import time
            start_time = time.time()
            
            result = self.runner.invoke(workflow_app, ["workflows"])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            assert execution_time < 2.0  # Should execute in less than 2 seconds
    
    def test_get_mock_workflows_performance(self):
        """Test mock workflows generation performance."""
        import time
        
        start_time = time.time()
        workflows = _get_mock_workflows()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert len(workflows) > 0
        assert execution_time < 0.1  # Should generate mock data very quickly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])