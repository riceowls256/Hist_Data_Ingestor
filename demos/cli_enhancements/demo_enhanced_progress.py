#!/usr/bin/env python3
"""
Demo script to showcase the enhanced progress tracking functionality.

This script simulates a data ingestion pipeline with the new progress features
implemented in Phase 1.1 of the CLI User Experience Enhancement.
"""

import sys
import os
import time
import random
from typing import List, Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cli.progress_utils import EnhancedProgress
from rich.console import Console

console = Console()


def simulate_data_chunk(size: int) -> List[Dict[str, Any]]:
    """Generate a fake data chunk for demo purposes."""
    return [
        {
            'id': i,
            'symbol': random.choice(['ES.c.0', 'NQ.c.0', 'CL.c.0']),
            'price': round(random.uniform(100, 200), 2),
            'volume': random.randint(100, 10000)
        }
        for i in range(size)
    ]


def demo_enhanced_progress():
    """Demonstrate the enhanced progress tracking features."""
    
    console.print("\n[bold cyan]🚀 Enhanced Progress Tracking Demo[/bold cyan]")
    console.print("This demo simulates a data ingestion pipeline with multiple stages.\n")
    
    # Simulate job configuration
    total_records = 10000
    chunk_size = 1000
    num_chunks = total_records // chunk_size
    
    job_description = "Ingesting DATABENTO OHLCV data for ES.c.0, NQ.c.0, CL.c.0"
    
    with EnhancedProgress(
        job_description,
        show_speed=True,
        show_eta=True,
        show_records=True
    ) as progress:
        
        # Stage 1: Data Extraction
        progress.log("Stage: Data Extraction - Connecting to Databento API...", style="yellow")
        time.sleep(1)
        
        progress.log("Stage: Data Extraction - Fetching historical data...", style="yellow")
        time.sleep(0.5)
        
        # Initialize progress bar with total
        progress.update_main(
            description=f"Processing {total_records:,} records",
            total=total_records,
            completed=0
        )
        
        # Simulate chunk processing
        records_processed = 0
        records_stored = 0
        records_quarantined = 0
        
        for chunk_idx in range(num_chunks):
            # Update main progress
            progress.update_main(
                completed=records_processed,
                total=total_records,
                description=f"Processing chunk {chunk_idx + 1}/{num_chunks}"
            )
            
            # Stage 2: Transformation
            progress.log(f"Stage: Transformation - Transforming chunk {chunk_idx + 1}", style="blue")
            chunk_data = simulate_data_chunk(chunk_size)
            time.sleep(0.2)  # Simulate processing time
            
            # Stage 3: Validation
            progress.log(f"Stage: Validation - Validating chunk {chunk_idx + 1}", style="green")
            
            # Simulate some records being quarantined
            quarantined = random.randint(0, 5)
            valid_records = chunk_size - quarantined
            records_quarantined += quarantined
            
            time.sleep(0.1)
            
            # Stage 4: Storage
            progress.log(f"Stage: Storage - Storing {valid_records} records to TimescaleDB", style="magenta")
            
            # Simulate database write
            time.sleep(0.3)
            
            records_processed += chunk_size
            records_stored += valid_records
            
            # Log metrics
            if chunk_idx % 2 == 0:  # Show metrics every 2 chunks
                progress.log(f"Metrics: Stored={records_stored:,} Quarantined={records_quarantined} Throughput={records_processed / ((chunk_idx + 1) * 0.6):.0f} rec/s", style="dim")
            
            # Simulate occasional warnings
            if random.random() < 0.2:
                progress.log(f"Warning: High latency detected for chunk {chunk_idx + 1}", style="yellow")
                time.sleep(0.5)
        
        # Final update
        progress.update_main(
            completed=total_records,
            total=total_records,
            description="Pipeline completed successfully"
        )
        
        progress.log("Stage: Complete - Finalizing pipeline statistics...", style="bold green")
        time.sleep(0.5)
    
    # Display final statistics
    console.print("\n[bold green]✅ Pipeline Completed Successfully![/bold green]")
    console.print("\n[bold cyan]📊 Final Statistics:[/bold cyan]")
    console.print(f"  • Total Records Processed: [green]{records_processed:,}[/green]")
    console.print(f"  • Records Stored: [green]{records_stored:,}[/green]")
    console.print(f"  • Records Quarantined: [yellow]{records_quarantined}[/yellow]")
    console.print(f"  • Success Rate: [green]{(records_stored/records_processed)*100:.1f}%[/green]")
    
    console.print("\n[dim]This was a simulation. In production, these would be real data operations.[/dim]")


def demo_progress_with_error():
    """Demonstrate error handling in progress tracking."""
    
    console.print("\n[bold yellow]⚠️  Error Handling Demo[/bold yellow]")
    console.print("This demo shows how errors are displayed in the progress tracker.\n")
    
    with EnhancedProgress(
        "Processing data with potential errors",
        show_speed=True,
        show_eta=True
    ) as progress:
        
        # Process some data successfully
        for i in range(5):
            progress.update_main(
                completed=i * 100,
                total=1000,
                description=f"Processing batch {i + 1}/10"
            )
            time.sleep(0.5)
        
        # Simulate an error
        progress.log("Error: Connection timeout to database", style="red")
        time.sleep(2)
        
        # Show recovery
        progress.log("Retrying connection...", style="yellow")
        time.sleep(1)
        
        progress.log("Connection restored, resuming...", style="green")
        
        # Continue processing
        for i in range(5, 10):
            progress.update_main(
                completed=i * 100,
                total=1000,
                description=f"Processing batch {i + 1}/10"
            )
            time.sleep(0.3)
    
    console.print("\n[green]✅ Completed with error recovery[/green]")


def main():
    """Run all demos."""
    
    console.print("[bold]═" * 60 + "[/bold]")
    console.print("[bold cyan]Historical Data Ingestor - Enhanced Progress Demo[/bold cyan]")
    console.print("[bold]═" * 60 + "[/bold]")
    
    # Run main demo
    demo_enhanced_progress()
    
    console.print("\n" + "─" * 60 + "\n")
    
    # Run error handling demo
    demo_progress_with_error()
    
    console.print("\n[bold cyan]Demo completed! 🎉[/bold cyan]")
    console.print("\n[dim]To use in production: python src/main.py ingest --api databento --job ohlcv_1d[/dim]")


if __name__ == "__main__":
    main()