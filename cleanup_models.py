
#!/usr/bin/env python3
"""
Model Cleanup Script for HER Framework
Manually stop and cleanup models when needed
"""

import os
import sys
import gc
import psutil
import signal
import time

def cleanup_models():
    """Force cleanup of all models and free memory"""
    print("🧹 CLEANING UP MODELS AND MEMORY")
    print("=" * 40)
    
    # Get current memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"📊 Initial memory: {initial_memory:.1f} MB")
    
    # Force garbage collection
    print("🗑️  Running garbage collection...")
    collected = gc.collect()
    print(f"   Collected {collected} objects")
    
    # Clear Python cache
    print("🧽 Clearing Python cache...")
    if hasattr(sys, '_clear_type_cache'):
        sys._clear_type_cache()
    
    # Final memory check
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    freed_memory = initial_memory - final_memory
    
    print(f"📊 Final memory: {final_memory:.1f} MB")
    print(f"💾 Memory freed: {freed_memory:.1f} MB")
    
    return freed_memory

def stop_all_processes():
    """Stop all Python processes (nuclear option)"""
    print("⚠️  STOPPING ALL PYTHON PROCESSES")
    print("=" * 40)
    
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and proc.info['pid'] != current_pid:
                print(f"🛑 Stopping process {proc.info['pid']}")
                proc.terminate()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    
    print("✅ All Python processes stopped")

def signal_handler(signum, frame):
    """Handle cleanup signals"""
    print(f"\n🛑 Received signal {signum}, cleaning up...")
    cleanup_models()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🧹 HER Model Cleanup Script")
    print("=" * 30)
    print("1. Cleanup models and memory")
    print("2. Stop all Python processes")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        cleanup_models()
    elif choice == "2":
        stop_all_processes()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
