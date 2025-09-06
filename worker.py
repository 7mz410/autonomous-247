# worker.py

import time
import os
from dotenv import load_dotenv
from src.orchestration.main_orchestrator import MainOrchestrator

def main():
    """
    The main entry point for the background worker process.
    This worker's job is to initialize the system and then run the automation
    scheduler, keeping the process alive indefinitely to execute scheduled tasks.
    """
    # Load environment variables from .env file for local development
    load_dotenv()
    
    print("--- Starting the Autonomous 247 Worker ---")
    
    # Initialize the central orchestrator which sets up all services
    try:
        orchestrator = MainOrchestrator()
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize the Main Orchestrator: {e}")
        return # Exit if initialization fails

    # Start the automation scheduler (which runs in a background thread)
    orchestrator.start_automation()

    print("\n✅ Worker is running and listening for scheduled jobs.")
    print("   Press Ctrl+C to stop the worker.")

    # Keep the main thread alive to allow the scheduler's background thread to run
    try:
        while True:
            time.sleep(60) # Sleep for a minute and check for shutdown signals
    except KeyboardInterrupt:
        print("\n⏹️  Shutdown signal received. Stopping worker and scheduler...")
        orchestrator.stop_automation()
        print("--- Worker has been stopped gracefully. ---")

if __name__ == "__main__":
    main()
