#!/usr/bin/env python3
"""
Demo script to showcase the enhanced metrics display functionality.

This script demonstrates Phase 1.3 of the CLI User Experience Enhancement
with real-time system metrics, operation metrics, and error tracking.
"""

import time
import random
import threading
from rich.console import Console

from cli.progress_utils import MetricsDisplay, ProgressWithMetrics

console = Console()


def demo_standalone_metrics():
    """Demonstrate standalone metrics display."""
    
    console.print("\n[bold cyan]📊 Standalone Metrics Display Demo[/bold cyan]")
    console.print("This shows the MetricsDisplay component with live system monitoring.\n")
    
    with MetricsDisplay(
        title="Data Ingestion Metrics",
        show_system_metrics=True,
        show_operation_metrics=True
    ).live_display() as metrics:
        
        # Simulate a data ingestion operation
        records_total = 50000
        records_processed = 0
        chunks_processed = 0
        errors = 0
        
        for i in range(50):  # 50 updates over ~10 seconds
            # Simulate processing
            batch_size = random.randint(800, 1200)
            records_processed += batch_size
            
            if i % 5 == 0:  # Every 5th batch is a new chunk
                chunks_processed += 1
                
            # Simulate occasional errors
            if random.random() < 0.1:
                errors += random.randint(1, 5)
                
            # Update metrics
            metrics.update(
                records_processed=records_processed,
                records_total=records_total,
                chunks_processed=chunks_processed,
                errors=errors,
                api_calls=i + 1,
                cache_hits=int(i * 0.7),
                completion_percent=round((records_processed / records_total) * 100, 1)
            )
            
            # Add error message occasionally
            if errors > 0 and random.random() < 0.3:
                metrics.update(last_error="ValidationError: Invalid timestamp format")
                
            time.sleep(0.2)
            
    console.print("\n✅ Metrics display demo completed!")
    console.print(f"Final stats: {records_processed:,} records processed with {errors} errors")


def demo_progress_with_metrics():
    """Demonstrate combined progress and metrics display."""
    
    console.print("\n[bold cyan]🚀 Progress + Metrics Combined Demo[/bold cyan]")
    console.print("This shows progress bar with live metrics panel above.\n")
    
    total_records = 100000
    
    with ProgressWithMetrics(
        "Processing financial data",
        show_metrics=True,
        metrics_position="above"
    ) as progress_metrics:
        
        records_done = 0
        errors = 0
        warnings = 0
        api_calls = 0
        
        # Simulate processing in batches
        while records_done < total_records:
            batch_size = random.randint(1000, 3000)
            
            # Update progress
            progress_metrics.update_progress(
                completed=records_done,
                total=total_records,
                operation_type="databento_ohlcv"
            )
            
            # Simulate API call
            if records_done % 10000 == 0:
                api_calls += 1
                progress_metrics.log(f"Making API call #{api_calls}...", style="blue")
                time.sleep(0.5)
                
            # Simulate processing with occasional issues
            if random.random() < 0.05:
                errors += 1
            if random.random() < 0.1:
                warnings += 1
                
            # Update metrics
            progress_metrics.update_metrics(
                records_processed=records_done,
                api_calls=api_calls,
                errors=errors,
                warnings=warnings,
                active_connections=random.randint(3, 8),
                queue_depth=random.randint(100, 500)
            )
            
            records_done += batch_size
            if records_done > total_records:
                records_done = total_records
                
            time.sleep(0.1)
            
        # Final update
        progress_metrics.update_progress(
            completed=total_records,
            total=total_records,
            description="Processing complete!"
        )
        
        time.sleep(1)
        
    console.print("\n✅ Combined display demo completed!")


def demo_side_by_side_layout():
    """Demonstrate side-by-side layout option."""
    
    console.print("\n[bold cyan]📐 Side-by-Side Layout Demo[/bold cyan]")
    console.print("Progress bar and metrics displayed side-by-side.\n")
    
    with ProgressWithMetrics(
        "Downloading market data",
        show_metrics=True,
        metrics_position="side"
    ) as progress_metrics:
        
        total_mb = 500
        downloaded_mb = 0
        
        while downloaded_mb < total_mb:
            # Simulate download
            chunk = random.uniform(5, 15)
            downloaded_mb += chunk
            if downloaded_mb > total_mb:
                downloaded_mb = total_mb
                
            # Update progress
            progress_metrics.update_progress(
                completed=int(downloaded_mb),
                total=total_mb,
                description=f"Downloading: {downloaded_mb:.1f}/{total_mb} MB"
            )
            
            # Update metrics with download stats
            progress_metrics.update_metrics(
                download_speed_mbps=random.uniform(8, 12),
                files_completed=int(downloaded_mb / 50),
                files_total=10,
                compression_ratio=random.uniform(2.5, 3.5),
                estimated_savings_mb=int(downloaded_mb * 0.65)
            )
            
            time.sleep(0.2)
            
    console.print("\n✅ Side-by-side layout demo completed!")


def demo_system_stress_monitoring():
    """Demonstrate system metrics under simulated load."""
    
    console.print("\n[bold cyan]💻 System Stress Monitoring Demo[/bold cyan]")
    console.print("Watch system metrics change under simulated load.\n")
    
    with MetricsDisplay(
        title="System Load Simulation",
        show_system_metrics=True,
        show_operation_metrics=False
    ).live_display() as metrics:
        
        console.print("[yellow]Simulating CPU-intensive operation...[/yellow]")
        
        # Create some CPU load
        def cpu_load():
            end_time = time.time() + 3
            while time.time() < end_time:
                sum(i**2 for i in range(1000))
                
        # Start threads to create load
        threads = []
        for i in range(3):
            t = threading.Thread(target=cpu_load)
            t.start()
            threads.append(t)
            time.sleep(0.5)
            
        # Monitor for 5 seconds
        for i in range(25):
            metrics.update(status=f"Monitoring... {i+1}/25")
            time.sleep(0.2)
            
        # Wait for threads
        for t in threads:
            t.join()
            
        console.print("[green]Load simulation completed.[/green]")
        time.sleep(1)
        
    console.print("\n✅ System monitoring demo completed!")


def main():
    """Run all demos."""
    
    console.print("[bold]═" * 60 + "[/bold]")
    console.print("[bold cyan]Historical Data Ingestor - Enhanced Metrics Display Demo[/bold cyan]")
    console.print("[bold]═" * 60 + "[/bold]")
    
    demos = [
        demo_standalone_metrics,
        demo_progress_with_metrics,
        demo_side_by_side_layout,
        demo_system_stress_monitoring
    ]
    
    for demo in demos:
        demo()
        console.print("\n" + "─" * 60 + "\n")
        
    console.print("[bold green]All demos completed! 🎉[/bold green]")
    console.print("\n[dim]The enhanced metrics display provides:")
    console.print("• Real-time system metrics (CPU, memory, network)")
    console.print("• Operation metrics with automatic formatting")
    console.print("• Error and warning tracking")
    console.print("• Flexible layout options")
    console.print("• Live throughput calculations[/dim]")


if __name__ == "__main__":
    main()