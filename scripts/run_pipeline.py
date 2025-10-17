#!/usr/bin/env python3
"""
StyleMe 6.0 Pipeline Runner
End-to-end pipeline execution script
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print("Error:", e.stderr)
        return False

def main():
    """Main pipeline execution"""
    print("🚀 StyleMe 6.0 - Personal Wardrobe AI Stylist")
    print("=" * 50)
    print("End-to-End Containerized Pipeline")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("docker-compose.yml").exists():
        print("❌ docker-compose.yml not found. Please run from project root.")
        sys.exit(1)
    
    # Create necessary directories
    print("\n🔧 Setting up directories...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("src/models/train/experiments", exist_ok=True)
    print("✅ Directories created")
    
    # Pipeline steps
    steps = [
        ("docker compose build", "Building all containers"),
        ("docker compose --profile pipeline up --build", "Running complete pipeline")
    ]
    
    # Execute pipeline
    for cmd, description in steps:
        success = run_command(cmd, description)
        if not success:
            print(f"\n❌ Pipeline failed at: {description}")
            sys.exit(1)
    
    print("\n🎉 Pipeline completed successfully!")
    print("📁 Check results in:")
    print("   - Data: ./data/")
    print("   - Experiments: ./src/models/train/experiments/")
    print("   - Logs: ./logs/")

if __name__ == "__main__":
    main()

