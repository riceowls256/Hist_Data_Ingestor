"""
Test suite for the CLI configuration management system.

Tests cover configuration loading, saving, validation, environment detection,
and integration with CLI components.
"""

import os
import sys
import tempfile
import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli.config_manager import (
    ConfigManager, EnvironmentAdapter, CLIConfig, ProgressConfig,
    ColorsConfig, DisplayConfig, BehaviorConfig, ProgressStyle,
    UpdateFrequency, TimeFormat, get_config_manager, get_config
)


class TestProgressConfig:
    """Test ProgressConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default progress configuration initialization."""
        config = ProgressConfig()
        
        assert config.style == "advanced"
        assert config.show_eta is True
        assert config.show_speed is True
        assert config.show_metrics is True
        assert config.update_frequency == "adaptive"
        assert config.use_adaptive_eta is True
        assert config.use_throttling is True
        
    def test_custom_initialization(self):
        """Test custom progress configuration initialization."""
        config = ProgressConfig(
            style="simple",
            show_eta=False,
            show_speed=False,
            update_frequency="slow"
        )
        
        assert config.style == "simple"
        assert config.show_eta is False
        assert config.show_speed is False
        assert config.update_frequency == "slow"


class TestColorsConfig:
    """Test ColorsConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default colors configuration initialization."""
        config = ColorsConfig()
        
        assert config.progress_bar == "cyan"
        assert config.success == "green"
        assert config.error == "red"
        assert config.warning == "yellow"
        assert config.info == "blue"
        assert config.accent == "magenta"
        
    def test_custom_initialization(self):
        """Test custom colors configuration initialization."""
        config = ColorsConfig(
            progress_bar="blue",
            success="bright_green",
            error="bright_red"
        )
        
        assert config.progress_bar == "blue"
        assert config.success == "bright_green"
        assert config.error == "bright_red"


class TestDisplayConfig:
    """Test DisplayConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default display configuration initialization."""
        config = DisplayConfig()
        
        assert config.max_table_rows == 50
        assert config.truncate_columns is True
        assert config.show_timestamps is True
        assert config.time_format == "relative"
        assert config.auto_width is True
        assert config.use_icons is True


class TestBehaviorConfig:
    """Test BehaviorConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default behavior configuration initialization."""
        config = BehaviorConfig()
        
        assert config.confirm_operations is True
        assert config.auto_retry is True
        assert config.max_retries == 3
        assert config.default_batch_size == 10
        assert config.save_history is True
        assert config.cleanup_on_exit is True


class TestCLIConfig:
    """Test CLIConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default CLI configuration initialization."""
        config = CLIConfig(
            progress=ProgressConfig(),
            colors=ColorsConfig(),
            display=DisplayConfig(),
            behavior=BehaviorConfig()
        )
        
        assert isinstance(config.progress, ProgressConfig)
        assert isinstance(config.colors, ColorsConfig)
        assert isinstance(config.display, DisplayConfig)
        assert isinstance(config.behavior, BehaviorConfig)
        
    def test_dict_initialization(self):
        """Test CLI configuration initialization from dictionaries."""
        config_dict = {
            'progress': {'style': 'simple', 'show_eta': False},
            'colors': {'success': 'bright_green'},
            'display': {'max_table_rows': 25},
            'behavior': {'max_retries': 5}
        }
        
        config = CLIConfig(**config_dict)
        
        assert config.progress.style == 'simple'
        assert config.progress.show_eta is False
        assert config.colors.success == 'bright_green'
        assert config.display.max_table_rows == 25
        assert config.behavior.max_retries == 5


class TestEnvironmentAdapter:
    """Test EnvironmentAdapter class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.adapter = EnvironmentAdapter()
        
    def test_initialization(self):
        """Test environment adapter initialization."""
        assert self.adapter.platform in ['windows', 'linux', 'darwin']
        assert isinstance(self.adapter.is_tty, bool)
        assert isinstance(self.adapter.terminal_width, int)
        assert isinstance(self.adapter.terminal_height, int)
        assert isinstance(self.adapter.supports_color, bool)
        assert isinstance(self.adapter.supports_unicode, bool)
        assert isinstance(self.adapter.is_ci, bool)
        assert isinstance(self.adapter.is_ssh, bool)
        assert isinstance(self.adapter.is_container, bool)
        assert isinstance(self.adapter.cpu_cores, int)
        assert self.adapter.cpu_cores >= 1
        
    def test_progress_style_detection(self):
        """Test progress style detection based on environment."""
        style = self.adapter.get_optimal_progress_style()
        assert style in ['simple', 'advanced', 'compact', 'minimal']
        
    def test_update_frequency_detection(self):
        """Test update frequency detection based on environment."""
        frequency = self.adapter.get_optimal_update_frequency()
        assert frequency in ['fast', 'normal', 'slow', 'adaptive']
        
    @patch.dict(os.environ, {'CI': 'true'}, clear=False)
    def test_ci_environment_detection(self):
        """Test CI environment detection."""
        adapter = EnvironmentAdapter()
        assert adapter.is_ci is True
        assert adapter.get_optimal_progress_style() == 'simple'
        assert adapter.get_optimal_update_frequency() == 'slow'
        
    @patch.dict(os.environ, {'SSH_CLIENT': '127.0.0.1'}, clear=False)
    def test_ssh_environment_detection(self):
        """Test SSH environment detection."""
        adapter = EnvironmentAdapter()
        assert adapter.is_ssh is True
        
    @patch('os.path.exists')
    def test_container_environment_detection(self, mock_exists):
        """Test container environment detection."""
        mock_exists.return_value = True
        adapter = EnvironmentAdapter()
        assert adapter.is_container is True
        
    def test_environment_summary(self):
        """Test environment summary generation."""
        summary = self.adapter.get_environment_summary()
        
        required_keys = [
            'platform', 'is_tty', 'terminal_size', 'supports_color',
            'supports_unicode', 'is_ci', 'is_ssh', 'is_container',
            'is_windows', 'cpu_cores', 'recommended_workers',
            'optimal_progress_style', 'optimal_update_frequency'
        ]
        
        for key in required_keys:
            assert key in summary
            
    def test_recommended_config(self):
        """Test recommended configuration generation."""
        config = self.adapter.get_recommended_config()
        
        assert 'progress' in config
        assert 'colors' in config
        assert 'display' in config
        assert 'behavior' in config
        
        # Validate progress section
        assert 'style' in config['progress']
        assert 'show_eta' in config['progress']
        assert 'show_speed' in config['progress']
        assert 'show_metrics' in config['progress']
        assert 'update_frequency' in config['progress']
        assert 'use_adaptive_eta' in config['progress']
        assert 'use_throttling' in config['progress']


class TestConfigManager:
    """Test ConfigManager class."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".hdi"
        self.config_manager = ConfigManager(self.config_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """Test configuration manager initialization."""
        assert self.config_manager.config_dir == self.config_dir
        assert self.config_dir.exists()
        assert isinstance(self.config_manager.environment, EnvironmentAdapter)
        assert isinstance(self.config_manager.get_config(), CLIConfig)
        
    def test_default_config_loading(self):
        """Test loading default configuration."""
        config = self.config_manager.get_config()
        
        assert isinstance(config, CLIConfig)
        assert isinstance(config.progress, ProgressConfig)
        assert isinstance(config.colors, ColorsConfig)
        assert isinstance(config.display, DisplayConfig)
        assert isinstance(config.behavior, BehaviorConfig)
        
    def test_config_saving_and_loading(self):
        """Test saving and loading configuration to/from file."""
        # Modify configuration
        self.config_manager.update_config({
            'progress': {'style': 'simple', 'show_eta': False},
            'colors': {'success': 'bright_green'}
        })
        
        # Create new manager with same config directory
        new_manager = ConfigManager(self.config_dir)
        config = new_manager.get_config()
        
        assert config.progress.style == 'simple'
        assert config.progress.show_eta is False
        assert config.colors.success == 'bright_green'
        
    def test_setting_operations(self):
        """Test getting and setting individual settings."""
        # Test setting
        self.config_manager.set_setting('progress.style', 'compact')
        self.config_manager.set_setting('display.max_table_rows', 25)
        
        # Test getting
        assert self.config_manager.get_setting('progress.style') == 'compact'
        assert self.config_manager.get_setting('display.max_table_rows') == 25
        assert self.config_manager.get_setting('nonexistent.key', 'default') == 'default'
        
    def test_config_reset(self):
        """Test configuration reset functionality."""
        # Modify configuration
        self.config_manager.set_setting('progress.style', 'simple')
        self.config_manager.set_setting('colors.success', 'bright_green')
        
        # Reset specific section
        self.config_manager.reset_config('progress')
        
        # Check that progress section is reset but colors remain
        assert self.config_manager.get_setting('progress.style') == 'advanced'  # Default
        assert self.config_manager.get_setting('colors.success') == 'bright_green'  # Modified
        
        # Reset entire configuration
        self.config_manager.reset_config()
        
        # Check that everything is reset
        assert self.config_manager.get_setting('colors.success') == 'green'  # Default
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration should pass
        errors = self.config_manager.validate_config()
        assert len(errors) == 0
        
        # Invalid configuration should fail
        self.config_manager.update_config({
            'progress': {'style': 'invalid_style'},
            'display': {'max_table_rows': -1},
            'behavior': {'max_retries': -5}
        }, save=False)
        
        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any('Invalid progress style' in error for error in errors)
        assert any('max_table_rows must be at least 1' in error for error in errors)
        assert any('max_retries cannot be negative' in error for error in errors)
        
    def test_config_export_import_yaml(self):
        """Test configuration export and import in YAML format."""
        # Modify configuration
        self.config_manager.update_config({
            'progress': {'style': 'compact'},
            'colors': {'accent': 'bright_blue'}
        })
        
        # Export configuration
        export_file = Path(self.temp_dir) / "exported_config.yaml"
        self.config_manager.export_config(export_file, format="yaml")
        
        assert export_file.exists()
        
        # Create new manager and import
        new_manager = ConfigManager(Path(self.temp_dir) / ".hdi_new")
        new_manager.import_config(export_file, merge=False)
        
        # Verify imported configuration
        assert new_manager.get_setting('progress.style') == 'compact'
        assert new_manager.get_setting('colors.accent') == 'bright_blue'
        
    def test_config_export_import_json(self):
        """Test configuration export and import in JSON format."""
        # Modify configuration
        self.config_manager.update_config({
            'display': {'max_table_rows': 75},
            'behavior': {'default_batch_size': 20}
        })
        
        # Export configuration
        export_file = Path(self.temp_dir) / "exported_config.json"
        self.config_manager.export_config(export_file, format="json")
        
        assert export_file.exists()
        
        # Create new manager and import
        new_manager = ConfigManager(Path(self.temp_dir) / ".hdi_new")
        new_manager.import_config(export_file, merge=True)
        
        # Verify imported configuration
        assert new_manager.get_setting('display.max_table_rows') == 75
        assert new_manager.get_setting('behavior.default_batch_size') == 20
        
    @patch.dict(os.environ, {
        'HDI_PROGRESS_STYLE': 'minimal',
        'HDI_SHOW_ETA': 'false',
        'HDI_COLORS': 'false',
        'HDI_MAX_RETRIES': '5'
    }, clear=False)
    def test_environment_variable_overrides(self):
        """Test configuration overrides from environment variables."""
        manager = ConfigManager(Path(self.temp_dir) / ".hdi_env")
        
        assert manager.get_setting('progress.style') == 'minimal'
        assert manager.get_setting('progress.show_eta') is False
        assert manager.get_setting('colors.progress_bar') == 'white'  # No colors
        assert manager.get_setting('behavior.max_retries') == 5
        
    def test_list_settings(self):
        """Test listing configuration settings."""
        # List all settings
        all_settings = self.config_manager.list_settings()
        assert 'progress' in all_settings
        assert 'colors' in all_settings
        assert 'display' in all_settings
        assert 'behavior' in all_settings
        
        # List specific section
        progress_settings = self.config_manager.list_settings('progress')
        assert 'style' in progress_settings
        assert 'show_eta' in progress_settings
        assert 'show_speed' in progress_settings
        
    def test_apply_environment_optimizations(self):
        """Test applying environment-specific optimizations."""
        original_style = self.config_manager.get_setting('progress.style')
        
        # Apply environment optimizations
        self.config_manager.apply_environment_optimizations(save=False)
        
        # Configuration should be updated with environment recommendations
        optimized_style = self.config_manager.get_setting('progress.style')
        assert optimized_style in ['simple', 'advanced', 'compact', 'minimal']
        
    def test_deep_merge(self):
        """Test deep merging of configuration dictionaries."""
        base = {
            'progress': {'style': 'advanced', 'show_eta': True},
            'colors': {'success': 'green', 'error': 'red'}
        }
        
        overlay = {
            'progress': {'style': 'simple'},
            'colors': {'success': 'bright_green'},
            'new_section': {'new_key': 'new_value'}
        }
        
        result = self.config_manager._deep_merge(base, overlay)
        
        # Check merged values
        assert result['progress']['style'] == 'simple'  # Overridden
        assert result['progress']['show_eta'] is True   # Preserved
        assert result['colors']['success'] == 'bright_green'  # Overridden
        assert result['colors']['error'] == 'red'      # Preserved
        assert result['new_section']['new_key'] == 'new_value'  # Added


class TestGlobalFunctions:
    """Test global configuration functions."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear global config manager
        import cli.config_manager
        cli.config_manager._config_manager = None
        
    def test_get_config_manager(self):
        """Test global configuration manager access."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # Should return the same instance (singleton pattern)
        assert manager1 is manager2
        assert isinstance(manager1, ConfigManager)
        
    def test_get_config(self):
        """Test global configuration access."""
        config = get_config()
        assert isinstance(config, CLIConfig)
        
    def test_global_setting_operations(self):
        """Test global setting operations."""
        from cli.config_manager import update_config, get_setting, set_setting
        
        # Test setting and getting
        set_setting('progress.style', 'compact')
        assert get_setting('progress.style') == 'compact'
        
        # Test batch update
        update_config({
            'colors': {'accent': 'bright_magenta'},
            'display': {'show_timestamps': False}
        })
        
        assert get_setting('colors.accent') == 'bright_magenta'
        assert get_setting('display.show_timestamps') is False


class TestConfigurationIntegration:
    """Test configuration integration scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".hdi"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_user_config_file_loading(self):
        """Test loading user configuration from file."""
        # Create user config file
        config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        user_config = {
            'cli': {
                'progress': {
                    'style': 'simple',
                    'show_speed': False
                },
                'colors': {
                    'success': 'bright_green',
                    'warning': 'bright_yellow'
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(user_config, f)
            
        # Load configuration
        manager = ConfigManager(self.config_dir)
        
        # Verify user settings are applied
        assert manager.get_setting('progress.style') == 'simple'
        assert manager.get_setting('progress.show_speed') is False
        assert manager.get_setting('colors.success') == 'bright_green'
        assert manager.get_setting('colors.warning') == 'bright_yellow'
        
        # Verify defaults are preserved for unspecified settings
        assert manager.get_setting('progress.show_eta') is True  # Default
        assert manager.get_setting('colors.error') == 'red'     # Default
        
    def test_corrupted_config_file_handling(self):
        """Test handling of corrupted configuration files."""
        # Create corrupted config file
        config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
            
        # Should fall back to defaults without crashing
        manager = ConfigManager(self.config_dir)
        config = manager.get_config()
        
        # Should have default values
        assert config.progress.style == 'advanced'
        assert config.colors.success == 'green'
        
    def test_migration_and_upgrade_scenarios(self):
        """Test configuration migration and upgrade scenarios."""
        # Create old-style configuration
        config_file = self.config_dir / "config.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        old_config = {
            'progress_style': 'simple',  # Old key name
            'show_progress_speed': False,  # Old key name
            'cli': {
                'colors': {
                    'success': 'bright_green'
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(old_config, f)
            
        # Load and verify it doesn't crash
        manager = ConfigManager(self.config_dir)
        
        # Should use defaults for unknown keys
        assert manager.get_setting('progress.style') == 'advanced'  # Default
        assert manager.get_setting('colors.success') == 'bright_green'  # From CLI section


if __name__ == "__main__":
    pytest.main([__file__])