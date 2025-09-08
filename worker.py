# worker.py
# app.py
import os
import sys
# --- THE GOLDEN FIX: Force the project root into the Python path ---
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from orchestration.main_orchestrator import MainOrchestrator

import time
from dotenv import load_dotenv
from autonomous247.orchestration.main_orchestrator import MainOrchestrator

def main():
    load_dotenv()
    print("--- Starting the Autonomous 247 Worker ---")
    try:
        orchestrator = MainOrchestrator()
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize the Main Orchestrator: {e}")
        return
    orchestrator.start_automation()
    print("\n✅ Worker is running and listening for scheduled jobs.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹️  Shutdown signal received. Stopping worker...")
        orchestrator.stop_automation()
        print("--- Worker has been stopped gracefully. ---")

if __name__ == "__main__":
    main()
