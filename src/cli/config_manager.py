"""
Configuration management system for the CLI.

Provides user preferences, environment detection, and configuration persistence
for optimal CLI behavior across different environments.
"""

import os
import sys
import shutil
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import json
from dataclasses import dataclass, asdict
from enum import Enum

from rich.console import Console
from src.utils.custom_logger import get_logger

console = Console()
logger = get_logger(__name__)


class ProgressStyle(Enum):
    """Available progress display styles."""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    COMPACT = "compact"
    MINIMAL = "minimal"


class UpdateFrequency(Enum):
    """Update frequency settings."""
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    ADAPTIVE = "adaptive"


class TimeFormat(Enum):
    """Time display formats."""
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    BOTH = "both"


@dataclass
class ProgressConfig:
    """Progress display configuration."""
    style: str = "advanced"
    show_eta: bool = True
    show_speed: bool = True
    show_metrics: bool = True
    update_frequency: str = "adaptive"
    use_adaptive_eta: bool = True
    use_throttling: bool = True


@dataclass
class ColorsConfig:
    """Color scheme configuration."""
    progress_bar: str = "cyan"
    success: str = "green"
    error: str = "red"
    warning: str = "yellow"
    info: str = "blue"
    accent: str = "magenta"


@dataclass
class DisplayConfig:
    """Display configuration."""
    max_table_rows: int = 50
    truncate_columns: bool = True
    show_timestamps: bool = True
    time_format: str = "relative"
    auto_width: bool = True
    use_icons: bool = True


@dataclass
class BehaviorConfig:
    """Behavior configuration."""
    confirm_operations: bool = True
    auto_retry: bool = True
    max_retries: int = 3
    default_batch_size: int = 10
    save_history: bool = True
    cleanup_on_exit: bool = True


@dataclass
class CLIConfig:
    """Complete CLI configuration."""
    progress: ProgressConfig
    colors: ColorsConfig
    display: DisplayConfig
    behavior: BehaviorConfig
    
    def __post_init__(self):
        """Ensure all nested configs are proper dataclass instances."""
        if isinstance(self.progress, dict):
            self.progress = ProgressConfig(**self.progress)
        if isinstance(self.colors, dict):
            self.colors = ColorsConfig(**self.colors)
        if isinstance(self.display, dict):
            self.display = DisplayConfig(**self.display)
        if isinstance(self.behavior, dict):
            self.behavior = BehaviorConfig(**self.behavior)


class EnvironmentAdapter:
    """Adapt CLI output based on environment capabilities.
    
    Detects terminal capabilities and environment context to optimize
    the CLI experience for different deployment scenarios.
    """
    
    def __init__(self):
        """Initialize environment adapter."""
        logger.info("environment_adapter_init_started")
        self.platform = platform.system().lower()
        self.is_tty = sys.stdout.isatty()
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        
        # Environment detection - set is_windows first since other methods depend on it
        self.is_windows = self.platform == "windows"
        self.is_ci = self._detect_ci_environment()
        self.is_ssh = self._detect_ssh_session()
        self.is_container = self._detect_container_environment()
        self.supports_color = self._detect_color_support()
        self.supports_unicode = self._detect_unicode_support()
        
        # Performance characteristics
        self.cpu_cores = os.cpu_count() or 1
        self.recommended_workers = min(4, max(1, self.cpu_cores // 2))
        
        logger.info("environment_adapter_init_completed", 
                    platform=self.platform,
                    is_tty=self.is_tty,
                    terminal_size=f"{self.terminal_width}x{self.terminal_height}",
                    supports_color=self.supports_color,
                    supports_unicode=self.supports_unicode,
                    is_ci=self.is_ci,
                    is_ssh=self.is_ssh,
                    is_container=self.is_container,
                    cpu_cores=self.cpu_cores,
                    recommended_workers=self.recommended_workers)
        
    def get_optimal_progress_style(self) -> str:
        """Determine optimal progress style for current environment.
        
        Returns:
            Recommended progress style name
        """
        logger.debug("progress_style_optimization_started", 
                     is_tty=self.is_tty, 
                     is_ci=self.is_ci, 
                     is_ssh=self.is_ssh, 
                     terminal_width=self.terminal_width)
        
        if not self.is_tty or self.is_ci:
            style = "simple"  # Basic progress for non-interactive
        elif self.is_ssh and not self.supports_color:
            return "minimal"  # Very basic for SSH without color
        elif self.is_ssh:
            return "compact"  # Reduced updates for SSH
        elif self.terminal_width < 80:
            return "compact"  # Narrow terminal
        elif self.terminal_width < 120:
            return "advanced"  # Standard width
        else:
            style = "advanced"  # Full features for wide terminals
            
        logger.debug("progress_style_optimization_completed", 
                     recommended_style=style, 
                     reasoning=f"tty={self.is_tty}, ci={self.is_ci}, ssh={self.is_ssh}, width={self.terminal_width}")
        return style
            
    def get_optimal_update_frequency(self) -> str:
        """Determine optimal update frequency.
        
        Returns:
            Recommended update frequency
        """
        logger.debug("update_frequency_optimization_started", 
                     is_ci=self.is_ci, 
                     is_ssh=self.is_ssh, 
                     is_container=self.is_container)
        
        if self.is_ci:
            frequency = "slow"  # Minimal updates for CI
        elif self.is_ssh:
            return "normal"  # Moderate updates for SSH
        elif self.is_container:
            return "normal"  # Balanced for containers
        else:
            frequency = "adaptive"  # Dynamic adjustment for local use
            
        logger.debug("update_frequency_optimization_completed", 
                     recommended_frequency=frequency, 
                     reasoning=f"ci={self.is_ci}, ssh={self.is_ssh}, container={self.is_container}")
        return frequency
            
    def get_recommended_config(self) -> Dict[str, Any]:
        """Get environment-optimized configuration.
        
        Returns:
            Configuration dictionary optimized for current environment
        """
        logger.info("environment_config_generation_started")
        
        config = {
            "progress": {
                "style": self.get_optimal_progress_style(),
                "show_eta": True,
                "show_speed": not self.is_ci,
                "show_metrics": not self.is_ci and self.terminal_width >= 100,
                "update_frequency": self.get_optimal_update_frequency(),
                "use_adaptive_eta": not self.is_ci,
                "use_throttling": not self.is_ci
            },
            "colors": {
                "progress_bar": "cyan" if self.supports_color else "white",
                "success": "green" if self.supports_color else "white",
                "error": "red" if self.supports_color else "white",
                "warning": "yellow" if self.supports_color else "white",
                "info": "blue" if self.supports_color else "white",
                "accent": "magenta" if self.supports_color else "white"
            },
            "display": {
                "max_table_rows": 20 if self.terminal_height < 30 else 50,
                "truncate_columns": self.terminal_width < 120,
                "show_timestamps": not self.is_ci,
                "time_format": "relative" if not self.is_ci else "absolute",
                "auto_width": True,
                "use_icons": self.supports_unicode and not self.is_ci
            },
            "behavior": {
                "confirm_operations": not self.is_ci,
                "auto_retry": True,
                "max_retries": 3,
                "default_batch_size": self.recommended_workers,
                "save_history": not self.is_container,
                "cleanup_on_exit": True
            }
        }
        
        logger.info("environment_config_generation_completed", 
                    config_sections=list(config.keys()),
                    progress_style=config["progress"]["style"],
                    supports_color=self.supports_color,
                    use_icons=config["display"]["use_icons"])
        return config
        
    def _get_terminal_width(self) -> int:
        """Get terminal width with fallback."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80  # Safe default
            
    def _get_terminal_height(self) -> int:
        """Get terminal height with fallback."""
        try:
            return shutil.get_terminal_size().lines
        except:
            return 24  # Safe default
            
    def _detect_color_support(self) -> bool:
        """Detect if terminal supports color output."""
        if not self.is_tty:
            return False
        if os.environ.get('NO_COLOR'):
            return False
        if os.environ.get('TERM') == 'dumb':
            return False
        if self.is_windows:
            # Windows 10+ with ANSI support
            return (
                os.environ.get('ANSICON') is not None or
                'ANSI_COLORS_DISABLED' not in os.environ
            )
        return True
        
    def _detect_unicode_support(self) -> bool:
        """Detect if terminal supports Unicode characters."""
        if not self.is_tty:
            return False
        
        # Check encoding
        encoding = getattr(sys.stdout, 'encoding', 'ascii').lower()
        if 'utf' in encoding:
            return True
            
        # Check locale
        locale_env = os.environ.get('LC_ALL') or os.environ.get('LANG', '')
        if 'utf' in locale_env.lower():
            return True
            
        # Conservative default
        return not self.is_windows
        
    def _detect_ci_environment(self) -> bool:
        """Detect if running in CI/CD environment."""
        ci_indicators = [
            'CI', 'CONTINUOUS_INTEGRATION', 'JENKINS_URL', 'TRAVIS',
            'CIRCLECI', 'APPVEYOR', 'GITLAB_CI', 'BUILDKITE', 'DRONE',
            'GITHUB_ACTIONS', 'TEAMCITY_VERSION', 'TF_BUILD'
        ]
        return any(var in os.environ for var in ci_indicators)
        
    def _detect_ssh_session(self) -> bool:
        """Detect if running in SSH session."""
        return (
            'SSH_CLIENT' in os.environ or
            'SSH_TTY' in os.environ or
            'SSH_CONNECTION' in os.environ
        )
        
    def _detect_container_environment(self) -> bool:
        """Detect if running in container."""
        # Check for Docker
        if os.path.exists('/.dockerenv'):
            return True
            
        # Check for Kubernetes
        if 'KUBERNETES_SERVICE_HOST' in os.environ:
            return True
            
        # Check for other container indicators
        container_indicators = [
            'DOCKER_CONTAINER', 'CONTAINER_ID', 'PODMAN_CONTAINER'
        ]
        if any(var in os.environ for var in container_indicators):
            return True
            
        # Check cgroup for container runtime
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    return True
        except:
            pass
            
        return False
        
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of environment characteristics.
        
        Returns:
            Dictionary with environment information
        """
        return {
            'platform': self.platform,
            'is_tty': self.is_tty,
            'terminal_size': f"{self.terminal_width}x{self.terminal_height}",
            'supports_color': self.supports_color,
            'supports_unicode': self.supports_unicode,
            'is_ci': self.is_ci,
            'is_ssh': self.is_ssh,
            'is_container': self.is_container,
            'is_windows': self.is_windows,
            'cpu_cores': self.cpu_cores,
            'recommended_workers': self.recommended_workers,
            'optimal_progress_style': self.get_optimal_progress_style(),
            'optimal_update_frequency': self.get_optimal_update_frequency()
        }


class ConfigManager:
    """Manage CLI configuration with environment adaptation and user preferences.
    
    Handles loading, saving, and merging configuration from multiple sources:
    1. Default configuration
    2. Environment-optimized configuration  
    3. User configuration file (~/.hdi/config.yaml)
    4. Environment variables
    """
    
    CONFIG_FILE_NAME = "config.yaml"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files (default: ~/.hdi)
        """
        logger.info("config_manager_init_started", config_dir=str(config_dir) if config_dir else None)
        
        self.config_dir = config_dir or Path.home() / ".hdi"
        self.config_file = self.config_dir / self.CONFIG_FILE_NAME
        self.environment = EnvironmentAdapter()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        logger.debug("config_directory_created", config_dir=str(self.config_dir))
        
        # Load configuration
        self._config = self._load_configuration()
        
        logger.info("config_manager_init_completed", 
                    config_dir=str(self.config_dir),
                    config_file=str(self.config_file),
                    config_file_exists=self.config_file.exists())
        
    def _get_default_config(self) -> CLIConfig:
        """Get default configuration.
        
        Returns:
            Default CLI configuration
        """
        return CLIConfig(
            progress=ProgressConfig(),
            colors=ColorsConfig(),
            display=DisplayConfig(),
            behavior=BehaviorConfig()
        )
        
    def _load_configuration(self) -> CLIConfig:
        """Load configuration from all sources.
        
        Returns:
            Merged configuration from all sources
        """
        logger.info("config_loading_started")
        
        # Start with defaults
        config_dict = asdict(self._get_default_config())
        logger.debug("default_config_loaded")
        
        # Apply environment optimizations
        env_config = self.environment.get_recommended_config()
        config_dict = self._deep_merge(config_dict, env_config)
        logger.debug("environment_config_applied", env_optimizations=list(env_config.keys()))
        
        # Load user configuration if it exists
        if self.config_file.exists():
            logger.debug("loading_user_config_file", config_file=str(self.config_file))
            try:
                with open(self.config_file, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                    
                # Extract CLI section if present
                if 'cli' in user_config:
                    user_config = user_config['cli']
                    
                config_dict = self._deep_merge(config_dict, user_config)
                logger.info("user_config_loaded", config_sections=list(user_config.keys()))
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
                logger.warning("user_config_load_failed", 
                               config_file=str(self.config_file), 
                               error=str(e), 
                               error_type=type(e).__name__)
        else:
            logger.debug("user_config_file_not_found", config_file=str(self.config_file))
                
        # Apply environment variable overrides
        env_overrides = self._load_env_overrides()
        config_dict = self._deep_merge(config_dict, env_overrides)
        if env_overrides:
            logger.debug("env_overrides_applied", overrides=list(env_overrides.keys()))
        
        logger.info("config_loading_completed", 
                    final_sections=list(config_dict.keys()),
                    has_user_config=self.config_file.exists(),
                    has_env_overrides=bool(env_overrides))
        
        return CLIConfig(**config_dict)
        
    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables.
        
        Returns:
            Configuration overrides from environment
        """
        overrides = {}
        
        # Progress settings
        if 'HDI_PROGRESS_STYLE' in os.environ:
            overrides.setdefault('progress', {})['style'] = os.environ['HDI_PROGRESS_STYLE']
        if 'HDI_SHOW_ETA' in os.environ:
            overrides.setdefault('progress', {})['show_eta'] = os.environ['HDI_SHOW_ETA'].lower() == 'true'
        if 'HDI_SHOW_SPEED' in os.environ:
            overrides.setdefault('progress', {})['show_speed'] = os.environ['HDI_SHOW_SPEED'].lower() == 'true'
        if 'HDI_UPDATE_FREQUENCY' in os.environ:
            overrides.setdefault('progress', {})['update_frequency'] = os.environ['HDI_UPDATE_FREQUENCY']
            
        # Color settings
        if 'HDI_COLORS' in os.environ:
            use_colors = os.environ['HDI_COLORS'].lower() == 'true'
            if not use_colors:
                overrides.setdefault('colors', {}).update({
                    'progress_bar': 'white',
                    'success': 'white', 
                    'error': 'white',
                    'warning': 'white',
                    'info': 'white',
                    'accent': 'white'
                })
                
        # Behavior settings
        if 'HDI_CONFIRM_OPERATIONS' in os.environ:
            overrides.setdefault('behavior', {})['confirm_operations'] = os.environ['HDI_CONFIRM_OPERATIONS'].lower() == 'true'
        if 'HDI_AUTO_RETRY' in os.environ:
            overrides.setdefault('behavior', {})['auto_retry'] = os.environ['HDI_AUTO_RETRY'].lower() == 'true'
        if 'HDI_MAX_RETRIES' in os.environ:
            try:
                overrides.setdefault('behavior', {})['max_retries'] = int(os.environ['HDI_MAX_RETRIES'])
            except ValueError:
                pass
        if 'HDI_BATCH_SIZE' in os.environ:
            try:
                overrides.setdefault('behavior', {})['default_batch_size'] = int(os.environ['HDI_BATCH_SIZE'])
            except ValueError:
                pass
                
        return overrides
        
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            overlay: Configuration to overlay
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def get_config(self) -> CLIConfig:
        """Get current configuration.
        
        Returns:
            Current CLI configuration
        """
        return self._config
        
    def update_config(self, updates: Dict[str, Any], save: bool = True) -> None:
        """Update configuration.
        
        Args:
            updates: Configuration updates to apply
            save: Whether to save changes to file
        """
        logger.info("config_update_started", updates=list(updates.keys()), save=save)
        
        # Apply updates to current config
        current_dict = asdict(self._config)
        updated_dict = self._deep_merge(current_dict, updates)
        
        self._config = CLIConfig(**updated_dict)
        
        if save:
            self.save_config()
            
        logger.info("config_update_completed", 
                    updates_applied=list(updates.keys()), 
                    saved_to_file=save)
            
    def save_config(self) -> None:
        """Save current configuration to file."""
        logger.info("config_save_started", config_file=str(self.config_file))
        try:
            # Convert to dict and wrap in 'cli' section
            config_dict = {'cli': asdict(self._config)}
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info("config_save_completed", config_file=str(self.config_file))
                
        except Exception as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
            logger.error("config_save_failed", 
                         config_file=str(self.config_file), 
                         error=str(e), 
                         error_type=type(e).__name__)
            
    def reset_config(self, section: Optional[str] = None) -> None:
        """Reset configuration to defaults.
        
        Args:
            section: Specific section to reset, or None for all
        """
        logger.info("config_reset_started", section=section)
        
        if section:
            # Reset specific section
            default_config = self._get_default_config()
            env_config = self.environment.get_recommended_config()
            
            if hasattr(default_config, section):
                section_default = getattr(default_config, section)
                section_env = env_config.get(section, {})
                
                # Merge default with environment optimizations
                section_config = self._deep_merge(asdict(section_default), section_env)
                
                # Update current config
                current_dict = asdict(self._config)
                current_dict[section] = section_config
                self._config = CLIConfig(**current_dict)
        else:
            # Reset entire configuration
            self._config = self._load_configuration()
            
        self.save_config()
        
        logger.info("config_reset_completed", section=section or "all")
        
    def get_setting(self, path: str, default: Any = None) -> Any:
        """Get a specific configuration setting.
        
        Args:
            path: Dot-separated path to setting (e.g., "progress.style")
            default: Default value if setting not found
            
        Returns:
            Configuration value
        """
        try:
            config_dict = asdict(self._config)
            parts = path.split('.')
            
            current = config_dict
            for part in parts:
                current = current[part]
                
            return current
        except (KeyError, TypeError):
            return default
            
    def set_setting(self, path: str, value: Any, save: bool = True) -> None:
        """Set a specific configuration setting.
        
        Args:
            path: Dot-separated path to setting (e.g., "progress.style")
            value: Value to set
            save: Whether to save changes to file
        """
        logger.info("setting_update_started", path=path, value=value, save=save)
        
        parts = path.split('.')
        
        # Build nested update dictionary
        update = {}
        current = update
        
        for part in parts[:-1]:
            current[part] = {}
            current = current[part]
            
        current[parts[-1]] = value
        
        self.update_config(update, save)
        
        logger.info("setting_update_completed", path=path, value=value, saved=save)
        
    def list_settings(self, section: Optional[str] = None) -> Dict[str, Any]:
        """List all configuration settings.
        
        Args:
            section: Specific section to list, or None for all
            
        Returns:
            Configuration settings dictionary
        """
        config_dict = asdict(self._config)
        
        if section:
            return config_dict.get(section, {})
        else:
            return config_dict
            
    def validate_config(self) -> List[str]:
        """Validate current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        logger.info("config_validation_started")
        errors = []
        
        # Validate progress settings
        progress = self._config.progress
        valid_styles = [e.value for e in ProgressStyle]
        if progress.style not in valid_styles:
            errors.append(f"Invalid progress style: {progress.style}. Must be one of: {valid_styles}")
            
        valid_frequencies = [e.value for e in UpdateFrequency]
        if progress.update_frequency not in valid_frequencies:
            errors.append(f"Invalid update frequency: {progress.update_frequency}. Must be one of: {valid_frequencies}")
            
        # Validate display settings
        display = self._config.display
        if display.max_table_rows < 1:
            errors.append("max_table_rows must be at least 1")
            
        valid_time_formats = [e.value for e in TimeFormat]
        if display.time_format not in valid_time_formats:
            errors.append(f"Invalid time format: {display.time_format}. Must be one of: {valid_time_formats}")
            
        # Validate behavior settings
        behavior = self._config.behavior
        if behavior.max_retries < 0:
            errors.append("max_retries cannot be negative")
            
        if behavior.default_batch_size < 1:
            errors.append("default_batch_size must be at least 1")
        
        logger.info("config_validation_completed", 
                    is_valid=len(errors) == 0, 
                    error_count=len(errors),
                    errors=errors if errors else None)
            
        return errors
        
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information.
        
        Returns:
            Environment characteristics and recommendations
        """
        return self.environment.get_environment_summary()
        
    def apply_environment_optimizations(self, save: bool = True) -> None:
        """Apply environment-specific optimizations to configuration.
        
        Args:
            save: Whether to save changes to file
        """
        logger.info("environment_optimization_started", save=save)
        
        env_config = self.environment.get_recommended_config()
        self.update_config(env_config, save)
        
        logger.info("environment_optimization_completed", 
                    optimizations_applied=list(env_config.keys()), 
                    saved=save)
        
    def export_config(self, file_path: Path, format: str = "yaml") -> None:
        """Export configuration to file.
        
        Args:
            file_path: Path to export file
            format: Export format ("yaml" or "json")
        """
        logger.info("config_export_started", file_path=str(file_path), format=format)
        
        config_dict = {'cli': asdict(self._config)}
        
        try:
            if format.lower() == "yaml":
                with open(file_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif format.lower() == "json":
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info("config_export_completed", file_path=str(file_path), format=format)
                
        except Exception as e:
            console.print(f"[red]Error exporting configuration: {e}[/red]")
            logger.error("config_export_failed", 
                         file_path=str(file_path), 
                         format=format, 
                         error=str(e), 
                         error_type=type(e).__name__)
            
    def import_config(self, file_path: Path, merge: bool = True, save: bool = True) -> None:
        """Import configuration from file.
        
        Args:
            file_path: Path to import file
            merge: Whether to merge with existing config or replace
            save: Whether to save changes to file
        """
        logger.info("config_import_started", 
                    file_path=str(file_path), 
                    merge=merge, 
                    save=save)
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    imported_config = yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    imported_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
                    
            # Extract CLI section if present
            if 'cli' in imported_config:
                imported_config = imported_config['cli']
                
            if merge:
                self.update_config(imported_config, save)
                logger.info("config_import_completed", 
                            file_path=str(file_path), 
                            merge=True, 
                            sections_imported=list(imported_config.keys()))
            else:
                # Replace entire configuration
                self._config = CLIConfig(**imported_config)
                if save:
                    self.save_config()
                logger.info("config_import_completed", 
                            file_path=str(file_path), 
                            merge=False, 
                            config_replaced=True)
                    
        except Exception as e:
            console.print(f"[red]Error importing configuration: {e}[/red]")
            logger.error("config_import_failed", 
                         file_path=str(file_path), 
                         merge=merge, 
                         error=str(e), 
                         error_type=type(e).__name__)


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance.
    
    Returns:
        Global ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        logger.info("global_config_manager_created")
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> CLIConfig:
    """Get current CLI configuration.
    
    Returns:
        Current CLI configuration
    """
    return get_config_manager().get_config()


def update_config(updates: Dict[str, Any], save: bool = True) -> None:
    """Update CLI configuration.
    
    Args:
        updates: Configuration updates to apply
        save: Whether to save changes to file
    """
    get_config_manager().update_config(updates, save)


def get_setting(path: str, default: Any = None) -> Any:
    """Get a specific configuration setting.
    
    Args:
        path: Dot-separated path to setting
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    return get_config_manager().get_setting(path, default)


def set_setting(path: str, value: Any, save: bool = True) -> None:
    """Set a specific configuration setting.
    
    Args:
        path: Dot-separated path to setting
        value: Value to set
        save: Whether to save changes
    """
    get_config_manager().set_setting(path, value, save)