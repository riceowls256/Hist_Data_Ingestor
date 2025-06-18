#!/usr/bin/env python3
"""
Demo script for Phase 5: ThrottledProgressUpdater and StreamingProgressTracker

This script demonstrates the throttling and streaming capabilities for
high-frequency progress updates and memory-efficient tracking.
"""

import time
import random
import threading
from pathlib import Path

from cli.progress_utils import (
    EnhancedProgress, 
    ThrottledProgressUpdater,
    StreamingProgressTracker,
    ProgressWithMetrics
)
from rich.console import Console

console = Console()


def demo_throttled_progress():
    """Demonstrate throttled progress updates."""
    console.print("\n🚀 [bold cyan]Demo: Throttled Progress Updates[/bold cyan]\n")
    
    console.print("Comparing normal vs throttled progress with high-frequency updates...\n")
    
    # Demo 1: Normal progress (can be overwhelming with rapid updates)
    console.print("📊 [yellow]Normal Progress (no throttling):[/yellow]")
    with EnhancedProgress("Processing without throttling", use_throttling=False) as progress:
        progress.update_main(total=1000)
        
        for i in range(1000):
            progress.update_main(completed=i + 1, operation_type="demo_normal")
            time.sleep(0.001)  # Very rapid updates
            
    console.print("✅ Normal progress completed\n")
    
    # Demo 2: Throttled progress (smooth updates)
    console.print("🎛️  [green]Throttled Progress (adaptive throttling):[/green]")
    with EnhancedProgress(
        "Processing with throttling", 
        use_throttling=True,
        throttle_min_interval=0.05,
        throttle_max_interval=0.2
    ) as progress:
        progress.update_main(total=1000)
        
        for i in range(1000):
            progress.update_main(completed=i + 1, operation_type="demo_throttled")
            time.sleep(0.001)  # Same rapid updates, but throttled display
            
    console.print("✅ Throttled progress completed\n")


def demo_adaptive_throttling():
    """Demonstrate adaptive throttling behavior."""
    console.print("🧠 [bold cyan]Demo: Adaptive Throttling[/bold cyan]\n")
    
    console.print("Showing how throttling adapts to different update frequencies...\n")
    
    with EnhancedProgress(
        "Adaptive throttling demo",
        use_throttling=True,
        throttle_min_interval=0.02,
        throttle_max_interval=0.5
    ) as progress:
        progress.update_main(total=300)
        
        # Phase 1: Slow updates
        console.print("Phase 1: Slow updates (should use min interval)")
        for i in range(100):
            progress.update_main(
                completed=i + 1, 
                description="Slow phase",
                operation_type="slow_demo"
            )
            time.sleep(0.1)  # Slow updates
            
        # Phase 2: Very rapid updates  
        console.print("Phase 2: Rapid updates (should increase interval)")
        for i in range(100, 200):
            progress.update_main(
                completed=i + 1,
                description="Rapid phase", 
                operation_type="rapid_demo"
            )
            time.sleep(0.001)  # Very rapid updates
            
        # Phase 3: Return to normal
        console.print("Phase 3: Normal updates (should stabilize)")
        for i in range(200, 300):
            progress.update_main(
                completed=i + 1,
                description="Normal phase",
                operation_type="normal_demo"
            )
            time.sleep(0.02)  # Normal updates
            
        # Show throttling stats
        if progress.throttler:
            stats = progress.throttler.get_stats()
            console.print(f"\n📈 Final throttling stats: {stats}")


def demo_streaming_tracker():
    """Demonstrate StreamingProgressTracker for memory efficiency."""
    console.print("\n💾 [bold cyan]Demo: Streaming Progress Tracker[/bold cyan]\n")
    
    console.print("Tracking large amounts of metrics with memory efficiency...\n")
    
    # Create tracker with limited memory
    tracker = StreamingProgressTracker(
        max_history=1000,  # Only keep 1000 recent metrics
        checkpoint_interval=250  # Checkpoint every 250 metrics
    )
    
    console.print("Recording 5000 metrics with automatic checkpointing...")
    
    # Simulate recording lots of metrics
    start_time = time.time()
    for i in range(5000):
        # Simulate varying throughput
        throughput = 1000 + random.randint(-200, 300)
        tracker.record_metric("throughput", throughput, metadata={"batch": i // 100})
        
        # Simulate occasional errors
        if random.random() < 0.02:  # 2% error rate
            tracker.record_metric("error_rate", 1.0)
            
        # Simulate processing metric
        tracker.total_processed = i + 1
        
        if i % 1000 == 0:
            console.print(f"  Recorded {i + 1} metrics...")
            
    elapsed = time.time() - start_time
    console.print(f"✅ Recorded 5000 metrics in {elapsed:.2f} seconds")
    
    # Show current stats
    current_stats = tracker.get_current_metrics()
    console.print(f"\n📊 Current metrics:")
    for key, value in current_stats.items():
        if isinstance(value, float):
            console.print(f"  {key}: {value:.2f}")
        else:
            console.print(f"  {key}: {value}")
            
    # Show streaming stats for different windows
    console.print(f"\n🔍 Streaming statistics:")
    for window in [30, 60, 120]:
        window_stats = tracker.get_streaming_stats(window_seconds=window)
        console.print(f"  Last {window}s: {window_stats['metrics_count']} metrics")
        
    # Show checkpoints
    console.print(f"\n🏁 Checkpoints created: {len(tracker.checkpoints)}")
    for name, checkpoint in list(tracker.checkpoints.items())[-3:]:  # Show last 3
        console.print(f"  {name}: {checkpoint['total_processed']} processed")
        
    # Export metrics
    export_path = Path("demo_metrics_export.json")
    tracker.export_metrics(export_path, format="json")
    console.print(f"\n💾 Exported metrics to {export_path}")
    
    # Test memory clearing
    original_count = len(tracker.metrics_buffer)
    tracker.clear_history(keep_recent_seconds=60)
    new_count = len(tracker.metrics_buffer)
    console.print(f"🧹 Cleared old metrics: {original_count} → {new_count}")


def demo_combined_throttling_streaming():
    """Demonstrate combined throttling and streaming."""
    console.print("\n🔄 [bold cyan]Demo: Combined Throttling + Streaming[/bold cyan]\n")
    
    console.print("Using both throttling and streaming for ultimate efficiency...\n")
    
    # Create streaming tracker
    tracker = StreamingProgressTracker(max_history=500, checkpoint_interval=100)
    
    # Function to record metrics in background
    def record_metrics():
        for i in range(2000):
            tracker.record_metric("background_throughput", 800 + random.randint(-100, 200))
            tracker.total_processed = i + 1
            time.sleep(0.001)
            
    # Start background metric recording
    metrics_thread = threading.Thread(target=record_metrics, daemon=True)
    metrics_thread.start()
    
    # Show progress with throttling
    with ProgressWithMetrics(
        "Combined demo with streaming metrics",
        show_metrics=True,
        metrics_position="above",
        use_throttling=True,
        throttle_min_interval=0.05
    ) as pm:
        pm.update_progress(total=1000)
        
        for i in range(1000):
            # Update main progress (throttled)
            pm.update_progress(
                completed=i + 1,
                operation_type="combined_demo"
            )
            
            # Update metrics display with streaming data
            current_metrics = tracker.get_current_metrics()
            pm.update_metrics(
                background_processing=tracker.total_processed,
                memory_usage_mb=tracker._estimate_memory_usage(),
                metrics_recorded=len(tracker.metrics_buffer),
                checkpoints=len(tracker.checkpoints)
            )
            
            time.sleep(0.002)  # Rapid updates
            
    # Wait for background thread
    metrics_thread.join(timeout=1.0)
    
    console.print("✅ Combined demo completed")
    console.print(f"📊 Final metrics recorded: {len(tracker.metrics_buffer)}")
    console.print(f"🏁 Checkpoints created: {len(tracker.checkpoints)}")
    console.print(f"💾 Memory usage: {tracker._estimate_memory_usage():.2f} MB")


def demo_throttling_performance():
    """Demonstrate performance benefits of throttling."""
    console.print("\n⚡ [bold cyan]Demo: Throttling Performance Benefits[/bold cyan]\n")
    
    update_counts = []
    
    def count_updates():
        """Count actual UI updates (simulated)."""
        return len(update_counts)
    
    # Test without throttling
    console.print("🔥 Testing without throttling (5000 rapid updates)...")
    start_time = time.time()
    
    # Simulate progress updates without throttling
    for i in range(5000):
        update_counts.append(i)  # Simulate each update hitting the UI
        time.sleep(0.0001)  # Micro delay to simulate UI overhead
        
    no_throttle_time = time.time() - start_time
    no_throttle_updates = len(update_counts)
    
    console.print(f"  Time: {no_throttle_time:.2f}s, Updates: {no_throttle_updates}")
    
    # Test with throttling
    console.print("\n🎛️  Testing with throttling (same 5000 updates)...")
    update_counts.clear()
    
    throttler = ThrottledProgressUpdater(min_interval=0.01, max_interval=0.1)
    mock_progress = type('MockProgress', (), {
        '_direct_update_main': lambda **kwargs: update_counts.append(len(update_counts))
    })()
    
    throttler.set_target(mock_progress)
    
    start_time = time.time()
    with throttler:
        for i in range(5000):
            throttler.update("main", completed=i + 1, total=5000)
            time.sleep(0.0001)  # Same micro delay
            
        # Give throttler time to finish
        time.sleep(0.2)
        
    throttled_time = time.time() - start_time  
    throttled_updates = len(update_counts)
    
    console.print(f"  Time: {throttled_time:.2f}s, Updates: {throttled_updates}")
    
    # Show benefits
    time_saved = no_throttle_time - throttled_time
    updates_saved = no_throttle_updates - throttled_updates
    
    console.print(f"\n✨ [green]Performance Benefits:[/green]")
    console.print(f"  ⏱️  Time saved: {time_saved:.2f}s ({time_saved/no_throttle_time*100:.1f}%)")
    console.print(f"  🎯 Updates reduced: {updates_saved} ({updates_saved/no_throttle_updates*100:.1f}%)")
    console.print(f"  🚀 Efficiency gain: {no_throttle_time/throttled_time:.1f}x faster")


def main():
    """Run all demos."""
    console.print("🎭 [bold magenta]Phase 5 Progress Enhancement Demos[/bold magenta]")
    console.print("=" * 60)
    
    try:
        # Run individual demos
        demo_throttled_progress()
        demo_adaptive_throttling()
        demo_streaming_tracker()
        demo_combined_throttling_streaming()
        demo_throttling_performance()
        
        console.print("\n🎉 [bold green]All demos completed successfully![/bold green]")
        console.print("\nKey benefits demonstrated:")
        console.print("  🎛️  Throttled updates prevent UI freezing")
        console.print("  🧠 Adaptive intervals optimize performance")
        console.print("  💾 Streaming tracker enables memory efficiency")
        console.print("  ⚡ Combined approach maximizes both responsiveness and efficiency")
        
    except KeyboardInterrupt:
        console.print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}")
        raise
    finally:
        # Cleanup
        export_file = Path("demo_metrics_export.json")
        if export_file.exists():
            export_file.unlink()
            

if __name__ == "__main__":
    main()