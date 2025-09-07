# src/orchestration/automation_scheduler.py

import os
# ... other imports
import logging
from src.config import DATA_PATH

LOG_FILE = os.path.join(DATA_PATH, 'automation.log')

# --- THIS IS THE ROBUST FIX ---
# First, ensure the directory (/data) exists.
# The exist_ok=True flag prevents an error if the directory already exists.
os.makedirs(DATA_PATH, exist_ok=True)
# Then, ensure the log file itself exists.
open(LOG_FILE, 'a').close()

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AutomationScheduler:
    """
    Manages the background scheduling of automated tasks. It maintains its state
    (settings and stats) in JSON files within the persistent data directory.
    """
    def __init__(self, youtube_service):
        self.youtube_service = youtube_service
        
        # State files are stored in the persistent data directory
        self.settings_file = os.path.join(DATA_PATH, 'automation_settings.json')
        self.stats_file = os.path.join(DATA_PATH, 'automation_stats.json')
        
        self.settings = self._load_json(self.settings_file, self._get_default_settings())
        self.stats = self._load_json(self.stats_file, self._get_default_stats())
        
        self.is_running = False
        self.scheduler_thread = None
        
        print("✅ Automation Scheduler initialized.")

    def run_single_automation_cycle(self):
        """Executes one full cycle of the automated task."""
        logging.info("🚀 Starting new automation cycle...")
        niche = self.settings.get('automation_niche', 'Artificial Intelligence')
        voice = self.settings.get('voice_type', 'female_voice')
        logging.info(f"   - Niche: {niche}, Voice: {voice}")

        try:
            # Delegate the task to the appropriate service
            result = self.youtube_service.create_and_upload_video(
                niche=niche,
                topic=None, # Topic should be decided by the service for automation
                voice_type=voice,
                upload=True,
                auto_search_context=True # Automation should always research
            )

            if not result or not result.get("success"):
                raise Exception(result.get("message", "YouTube service reported a failure."))

            self.stats['videos_generated'] += 1
            self.stats['videos_uploaded'] += 1
            logging.info("✅ Automation cycle completed successfully.")

        except Exception as e:
            self.stats['errors'] += 1
            logging.error(f"❌ Error in automation cycle: {e}")
        finally:
            self.stats['last_run'] = datetime.now().isoformat()
            self._save_json(self.stats_file, self.stats)

    def start(self):
        """Starts the scheduler in a background thread."""
        if self.is_running:
            print("   - Scheduler is already running.")
            return
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_pending_jobs, daemon=True)
        self.scheduler_thread.start()
        print("▶️  Automation scheduler started.")

    def stop(self):
        """Stops the background scheduler thread."""
        if not self.is_running:
            print("   - Scheduler is not running.")
            return
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2)
        schedule.clear()
        print("⏹️  Automation scheduler stopped.")

    def _run_pending_jobs(self):
        self._setup_schedule()
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def _setup_schedule(self):
        """Configures the job schedule based on current settings."""
        schedule.clear()
        upload_time = self.settings.get('upload_time', '19:00')
        upload_days = self.settings.get('upload_days', [])
        
        for day in upload_days:
            day_attr = day.lower().strip()
            if hasattr(schedule.every(), day_attr):
                getattr(schedule.every(), day_attr).at(upload_time).do(self.run_single_automation_cycle)
        
        job_count = len(schedule.jobs)
        print(f"🗓️   Schedule configured. {job_count} job(s) scheduled.")
        if job_count > 0 and schedule.next_run:
            next_run_dt = schedule.next_run
            print(f"   - Next run is scheduled for: {next_run_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    def update_settings(self, new_settings):
        """Updates the settings, saves them, and reconfigures the schedule."""
        self.settings.update(new_settings)
        self._save_json(self.settings_file, self.settings)
        if self.is_running:
            self._setup_schedule()

    def get_status(self):
        """Returns the current status and stats of the scheduler."""
        next_run_time = "No jobs scheduled"
        if schedule.jobs and schedule.next_run:
            next_run_time = schedule.next_run.strftime('%Y-%m-%d %H:%M:%S')
            
        return {
            "is_running": self.is_running,
            "stats": self.stats,
            "scheduled_jobs": len(schedule.jobs),
            "next_run": next_run_time
        }

    def _load_json(self, file_path, default_data):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"   - ⚠️ Could not load JSON from {file_path}: {e}. Using default.")
        return default_data

    def _save_json(self, file_path, data):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"   - ❌ Could not save JSON to {file_path}: {e}")

    def _get_default_settings(self):
        return {
            "upload_days": ["tuesday", "thursday", "saturday"],
            "upload_time": "19:00",
            "voice_type": "female_voice",
            "automation_niche": "Artificial Intelligence"
        }

    def _get_default_stats(self):
        return {"videos_generated": 0, "videos_uploaded": 0, "errors": 0, "last_run": None}
