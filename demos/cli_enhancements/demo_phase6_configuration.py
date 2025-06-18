#!/usr/bin/env python3
"""
Phase 6 Configuration System Demo

Demonstrates the comprehensive configuration management and environment 
adaptation features implemented in Phase 6 of the CLI User Experience 
Enhancement project.

This script showcases:
1. Environment detection and optimization
2. Configuration management (get/set/reset/validate)
3. User preferences and customization
4. Progress bar adaptation based on configuration
5. Export/import functionality
6. Environment variable overrides

Run: python demo_phase6_configuration.py
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Confirm, Prompt

from cli.config_manager import ConfigManager, EnvironmentAdapter, get_config_manager
from cli.progress_utils import create_configured_progress, EnhancedProgress, MetricsDisplay

console = Console()


def print_section_header(title: str, description: str = ""):
    """Print a formatted section header."""
    console.print()
    console.print(Panel(
        f"[bold cyan]{title}[/bold cyan]" + (f"\n[dim]{description}[/dim]" if description else ""),
        border_style="blue",
        padding=(1, 2)
    ))


def demo_environment_detection():
    """Demonstrate environment detection capabilities."""
    print_section_header(
        "🌍 Environment Detection",
        "Analyzing current environment and recommending optimal settings"
    )
    
    # Create environment adapter
    env_adapter = EnvironmentAdapter()
    env_info = env_adapter.get_environment_summary()
    
    # Display environment information
    table = Table(title="Environment Analysis", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green")
    table.add_column("Impact", style="yellow")
    
    # Basic environment info
    table.add_row(
        "Platform", 
        env_info['platform'].title(),
        "Determines OS-specific optimizations"
    )
    
    table.add_row(
        "Terminal", 
        f"{env_info['terminal_size']} ({'TTY' if env_info['is_tty'] else 'Non-TTY'})",
        "Affects progress display layout"
    )
    
    table.add_row(
        "Color Support", 
        "Yes" if env_info['supports_color'] else "No",
        "Enables/disables color themes"
    )
    
    table.add_row(
        "Unicode Support", 
        "Yes" if env_info['supports_unicode'] else "No",
        "Affects icon and symbol display"
    )
    
    table.add_row(
        "CPU Cores", 
        str(env_info['cpu_cores']),
        "Determines default batch sizes"
    )
    
    console.print(table)
    
    # Environment context
    console.print("\n🔍 [bold cyan]Environment Context[/bold cyan]")
    contexts = []
    if env_info['is_ci']:
        contexts.append("CI/CD Environment - Optimized for automation")
    if env_info['is_ssh']:
        contexts.append("SSH Session - Reduced update frequency")
    if env_info['is_container']:
        contexts.append("Container Environment - Minimal resource usage")
    if env_info['is_windows']:
        contexts.append("Windows Platform - ANSI color adjustments")
        
    if contexts:
        for context in contexts:
            console.print(f"  🏷️  [yellow]{context}[/yellow]")
    else:
        console.print("  🖥️  [green]Local Interactive Environment - Full features enabled[/green]")
        
    # Recommendations
    console.print("\n💡 [bold cyan]Environment-Optimized Recommendations[/bold cyan]")
    console.print(f"  📊 Progress Style: [green]{env_info['optimal_progress_style']}[/green]")
    console.print(f"  ⚡ Update Frequency: [green]{env_info['optimal_update_frequency']}[/green]")
    console.print(f"  👥 Recommended Workers: [green]{env_info['recommended_workers']}[/green]")
    
    time.sleep(2)


def demo_configuration_management():
    """Demonstrate configuration management features."""
    print_section_header(
        "⚙️ Configuration Management",
        "Creating, modifying, and managing CLI configuration settings"
    )
    
    # Create temporary config manager for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / ".hdi_demo"
        config_manager = ConfigManager(config_dir)
        
        console.print("📝 [cyan]Initial Configuration (Environment-Optimized)[/cyan]")
        
        # Show current configuration
        current_config = config_manager.list_settings()
        
        # Display key settings in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Description", style="dim")
        
        key_settings = [
            ("progress.style", "Progress bar style"),
            ("progress.show_eta", "Show estimated time remaining"),
            ("progress.use_adaptive_eta", "Use machine learning for ETA"),
            ("colors.progress_bar", "Progress bar color theme"),
            ("display.max_table_rows", "Maximum rows in result tables"),
            ("behavior.auto_retry", "Automatic retry on failures")
        ]
        
        for setting, description in key_settings:
            value = config_manager.get_setting(setting)
            table.add_row(setting, str(value), description)
            
        console.print(table)
        
        # Demonstrate setting modification
        console.print("\n🔧 [cyan]Modifying Configuration Settings[/cyan]")
        
        # Change progress style
        console.print("  Setting progress style to 'compact'...")
        config_manager.set_setting('progress.style', 'compact')
        
        # Change colors for dark theme
        console.print("  Applying dark theme colors...")
        config_manager.update_config({
            'colors': {
                'progress_bar': 'bright_cyan',
                'success': 'bright_green',
                'warning': 'bright_yellow',
                'error': 'bright_red'
            }
        })
        
        # Change display preferences
        console.print("  Updating display preferences...")
        config_manager.update_config({
            'display': {
                'max_table_rows': 25,
                'time_format': 'absolute',
                'use_icons': True
            }
        })
        
        console.print("\n✅ [green]Configuration updated successfully![/green]")
        
        # Show validation
        console.print("\n🔍 [cyan]Validating Configuration[/cyan]")
        errors = config_manager.validate_config()
        if errors:
            console.print("❌ [red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  • [red]{error}[/red]")
        else:
            console.print("✅ [green]Configuration is valid[/green]")
            
        # Demonstrate export
        console.print("\n📤 [cyan]Exporting Configuration[/cyan]")
        export_file = Path(temp_dir) / "demo_config.yaml"
        config_manager.export_config(export_file)
        console.print(f"  Configuration exported to: [green]{export_file}[/green]")
        
        # Show exported content
        console.print("\n📄 [cyan]Exported Configuration Preview[/cyan]")
        with open(export_file, 'r') as f:
            content = f.read()
            console.print(Panel(content[:500] + "..." if len(content) > 500 else content, 
                              title="config.yaml", border_style="green"))
    
    time.sleep(2)


def demo_progress_adaptation():
    """Demonstrate progress bar adaptation based on configuration."""
    print_section_header(
        "📊 Progress Bar Adaptation",
        "Showing how progress bars adapt to different configuration styles"
    )
    
    styles = ['simple', 'compact', 'advanced', 'minimal']
    
    for style in styles:
        console.print(f"\n🎨 [cyan]Demonstrating '{style}' Progress Style[/cyan]")
        
        # Create progress bar with specific style
        progress = create_configured_progress(
            f"Processing data ({style} style)",
            progress_style=style
        )
        
        with progress as p:
            p.update_main(total=100)
            
            for i in range(0, 101, 10):
                p.update_main(
                    completed=i,
                    description=f"Processing data ({style} style) - {i}% complete",
                    speed=1000 + (i * 10),  # Simulate increasing speed
                    operation_type=f"demo_{style}"
                )
                time.sleep(0.3)
                
        console.print(f"  ✅ [green]{style.title()} style demonstration complete[/green]")
    
    time.sleep(1)


def demo_color_themes():
    """Demonstrate different color themes and their effects."""
    print_section_header(
        "🎨 Color Theme Adaptation",
        "Showing how color themes affect progress displays and output"
    )
    
    themes = [
        {
            'name': 'Default Theme',
            'colors': {
                'progress_bar': 'cyan',
                'success': 'green',
                'warning': 'yellow',
                'error': 'red',
                'info': 'blue'
            }
        },
        {
            'name': 'High Contrast',
            'colors': {
                'progress_bar': 'bright_white',
                'success': 'bright_green',
                'warning': 'bright_yellow',
                'error': 'bright_red',
                'info': 'bright_blue'
            }
        },
        {
            'name': 'Monochrome',
            'colors': {
                'progress_bar': 'white',
                'success': 'white',
                'warning': 'white',
                'error': 'white',
                'info': 'white'
            }
        }
    ]
    
    for theme in themes:
        console.print(f"\n🎨 [cyan]Theme: {theme['name']}[/cyan]")
        
        # Temporarily modify configuration
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".hdi_demo"
            config_manager = ConfigManager(config_dir)
            config_manager.update_config({'colors': theme['colors']}, save=False)
            
            # Create progress with theme
            progress = EnhancedProgress(
                f"Demo progress with {theme['name']}",
                show_speed=True,
                show_eta=True,
                show_records=True
            )
            
            with progress as p:
                p.update_main(total=50)
                for i in range(0, 51, 5):
                    p.update_main(
                        completed=i,
                        speed=500 + i * 20,
                        operation_type="color_demo"
                    )
                    time.sleep(0.2)
                    
        # Show color samples
        colors = theme['colors']
        console.print(f"  📊 Progress: [{colors['progress_bar']}]████████████[/{colors['progress_bar']}]")
        console.print(f"  ✅ Success: [{colors['success']}]Operation completed successfully[/{colors['success']}]")
        console.print(f"  ⚠️  Warning: [{colors['warning']}]Resource usage is high[/{colors['warning']}]")
        console.print(f"  ❌ Error: [{colors['error']}]Connection failed, retrying...[/{colors['error']}]")
        console.print(f"  ℹ️  Info: [{colors['info']}]Processing 1,250 records[/{colors['info']}]")
    
    time.sleep(2)


def demo_environment_variables():
    """Demonstrate environment variable overrides."""
    print_section_header(
        "🌍 Environment Variable Overrides",
        "Showing how environment variables can override configuration settings"
    )
    
    # Show current environment
    console.print("📋 [cyan]Current Environment Variables (HDI_* only)[/cyan]")
    
    hdi_vars = {k: v for k, v in os.environ.items() if k.startswith('HDI_')}
    if hdi_vars:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="green")
        
        for var, value in hdi_vars.items():
            table.add_row(var, value)
        console.print(table)
    else:
        console.print("  [dim]No HDI_* environment variables set[/dim]")
    
    # Demonstrate setting environment variables
    console.print("\n🔧 [cyan]Setting Demo Environment Variables[/cyan]")
    
    # Set demo environment variables
    demo_env_vars = {
        'HDI_PROGRESS_STYLE': 'minimal',
        'HDI_SHOW_ETA': 'false',
        'HDI_COLORS': 'false',
        'HDI_MAX_RETRIES': '5',
        'HDI_BATCH_SIZE': '20'
    }
    
    for var, value in demo_env_vars.items():
        os.environ[var] = value
        console.print(f"  Setting {var} = {value}")
    
    # Create new config manager to pick up environment variables
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / ".hdi_demo"
        config_manager = ConfigManager(config_dir)
        
        console.print("\n📊 [cyan]Configuration with Environment Overrides[/cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")
        
        # Show how environment variables override settings
        env_overrides = [
            ('progress.style', 'HDI_PROGRESS_STYLE'),
            ('progress.show_eta', 'HDI_SHOW_ETA'),
            ('colors.progress_bar', 'HDI_COLORS'),
            ('behavior.max_retries', 'HDI_MAX_RETRIES'),
            ('behavior.default_batch_size', 'HDI_BATCH_SIZE')
        ]
        
        for setting, env_var in env_overrides:
            value = config_manager.get_setting(setting)
            source = f"Environment ({env_var})" if env_var in os.environ else "Configuration File"
            table.add_row(setting, str(value), source)
            
        console.print(table)
        
        # Demonstrate progress with environment settings
        console.print("\n🚀 [cyan]Progress Bar with Environment Settings[/cyan]")
        
        progress = create_configured_progress("Environment-configured progress")
        
        with progress as p:
            p.update_main(total=30)
            for i in range(0, 31, 3):
                p.update_main(completed=i, operation_type="env_demo")
                time.sleep(0.2)
    
    # Clean up environment variables
    for var in demo_env_vars:
        os.environ.pop(var, None)
    
    time.sleep(2)


def demo_metrics_with_configuration():
    """Demonstrate metrics display with configuration integration."""
    print_section_header(
        "📈 Metrics Display Integration",
        "Showing how metrics displays adapt to configuration settings"
    )
    
    console.print("🚀 [cyan]Starting Metrics Display Demo[/cyan]")
    
    # Create metrics display
    metrics = MetricsDisplay(
        title="Configuration-Aware Metrics",
        show_system_metrics=True,
        show_operation_metrics=True
    )
    
    console.print("📊 [dim]Live metrics display running for 10 seconds...[/dim]")
    
    with metrics.live_display() as m:
        start_time = time.time()
        records_processed = 0
        
        while time.time() - start_time < 10:
            # Simulate processing
            records_processed += 100
            
            # Update metrics
            m.update(
                records_processed=records_processed,
                throughput=records_processed / (time.time() - start_time),
                api_calls=records_processed // 100,
                chunks_completed=records_processed // 500,
                errors=max(0, records_processed // 1000 - 1),
                memory_usage=127 + (records_processed // 100)
            )
            
            time.sleep(0.5)
    
    console.print("✅ [green]Metrics display demo completed[/green]")
    time.sleep(1)


def demo_interactive_features():
    """Demonstrate interactive configuration features."""
    print_section_header(
        "🤖 Interactive Configuration",
        "Interactive features for configuration management"
    )
    
    if not sys.stdin.isatty():
        console.print("  ⏭️  [dim]Skipping interactive demo (non-TTY environment)[/dim]")
        return
    
    if not Confirm.ask("Would you like to try interactive configuration?"):
        console.print("  ⏭️  [dim]Skipping interactive demo[/dim]")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / ".hdi_demo"
        config_manager = ConfigManager(config_dir)
        
        console.print("\n🎯 [cyan]Interactive Configuration Wizard[/cyan]")
        
        # Progress style selection
        style_options = ['simple', 'compact', 'advanced', 'minimal']
        console.print("\n📊 Progress Style Options:")
        for i, style in enumerate(style_options, 1):
            console.print(f"  {i}. {style.title()}")
        
        try:
            style_choice = int(Prompt.ask("Select progress style (1-4)", default="3"))
            selected_style = style_options[style_choice - 1]
            config_manager.set_setting('progress.style', selected_style, save=False)
            console.print(f"  ✅ Set progress style to: [green]{selected_style}[/green]")
        except (ValueError, IndexError):
            console.print("  ⚠️  Invalid choice, using default")
        
        # Color theme selection
        if Confirm.ask("\nWould you like to enable high contrast colors?"):
            config_manager.update_config({
                'colors': {
                    'progress_bar': 'bright_cyan',
                    'success': 'bright_green',
                    'warning': 'bright_yellow',
                    'error': 'bright_red'
                }
            }, save=False)
            console.print("  ✅ [green]High contrast colors enabled[/green]")
        
        # Show configured progress
        console.print("\n🚀 [cyan]Your Configured Progress Bar[/cyan]")
        
        progress = create_configured_progress("Your custom configuration")
        
        with progress as p:
            p.update_main(total=25)
            for i in range(0, 26, 5):
                p.update_main(
                    completed=i,
                    speed=800 + i * 30,
                    operation_type="interactive_demo"
                )
                time.sleep(0.4)
        
        console.print("✅ [green]Interactive demo completed![/green]")
    
    time.sleep(1)


def main():
    """Run the complete Phase 6 configuration demo."""
    console.print(Panel(
        "[bold cyan]Phase 6: CLI Configuration System Demo[/bold cyan]\n"
        "[dim]Comprehensive demonstration of configuration management and environment adaptation[/dim]",
        title="🚀 Historical Data Ingestor",
        subtitle="CLI User Experience Enhancement - Phase 6",
        border_style="bright_blue",
        padding=(1, 2)
    ))
    
    console.print("\n[bold yellow]This demo showcases the Phase 6 configuration features:[/bold yellow]")
    console.print("  📊 Environment detection and optimization")
    console.print("  ⚙️  Configuration management (YAML-based)")
    console.print("  🎨 Color theme and style adaptation") 
    console.print("  🌍 Environment variable overrides")
    console.print("  📈 Integrated metrics and progress displays")
    console.print("  🤖 Interactive configuration management")
    
    # Skip interactive confirmation for non-TTY environments
    if sys.stdin.isatty():
        if not Confirm.ask("\nReady to start the demo?", default=True):
            console.print("Demo cancelled.")
            return
    else:
        console.print("\n[yellow]Running in non-interactive mode - starting demo automatically[/yellow]")
    
    try:
        # Run demo sections
        demo_environment_detection()
        demo_configuration_management()
        demo_progress_adaptation()
        demo_color_themes()
        demo_environment_variables()
        demo_metrics_with_configuration()
        demo_interactive_features()
        
        # Final summary
        print_section_header(
            "🎉 Demo Complete!",
            "Phase 6 configuration system successfully demonstrated"
        )
        
        console.print("✅ [bold green]All Phase 6 features demonstrated successfully![/bold green]\n")
        
        console.print("📋 [cyan]Summary of demonstrated features:[/cyan]")
        features = [
            "🌍 Environment detection and automatic optimization",
            "⚙️  YAML-based configuration management with validation",
            "🎨 Customizable color themes and progress styles",
            "🔧 Environment variable overrides for deployment scenarios",
            "📊 Adaptive progress bars that respond to configuration",
            "📈 Configuration-aware metrics displays",
            "📤 Configuration export/import in YAML and JSON formats",
            "🤖 Interactive configuration wizards",
            "✅ Comprehensive validation and error handling",
            "🔄 Automatic environment optimizations"
        ]
        
        for feature in features:
            console.print(f"  {feature}")
        
        console.print(f"\n💡 [yellow]Try these CLI commands to explore further:[/yellow]")
        console.print(f"  [cyan]python main.py config environment[/cyan]  # Show environment info")
        console.print(f"  [cyan]python main.py config list[/cyan]          # List all settings")
        console.print(f"  [cyan]python main.py config set progress.style compact[/cyan]  # Change progress style")
        console.print(f"  [cyan]python main.py config export --file my-config.yaml[/cyan] # Export config")
        
    except KeyboardInterrupt:
        console.print("\n\n⏹️  [yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n\n❌ [red]Demo error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()