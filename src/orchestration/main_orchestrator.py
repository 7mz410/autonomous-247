# src/orchestration/main_orchestrator.py

import threading
from src.utils.exceptions import InterruptedException
from src.core_services.content_generator_service import ContentGeneratorService
from src.core_services.video_producer_service import VideoProducerService
from src.core_services.web_search_service import WebSearchService
from src.core_services.image_post_generator_service import ImagePostGeneratorService
from src.platform_services.youtube_service import YouTubeService
from src.platform_services.linkedin_service import LinkedInService
from src.platform_services.instagram_service import InstagramService
from src.orchestration.automation_scheduler import AutomationScheduler

class MainOrchestrator:
    """
    The central coordinator of the entire application. It initializes all
    services and provides high-level methods for the UI and background workers
    to call, decoupling them from the underlying service implementations.
    """
    def __init__(self):
        print("Initializing the Main Orchestrator...")
        
        # A threading event to signal cancellation to long-running services
        self.kill_switch = threading.Event()

        # --- Initialize Core Services ---
        self.web_search_service = WebSearchService()
        self.video_producer = VideoProducerService(kill_switch=self.kill_switch)
        self.image_post_generator = ImagePostGeneratorService()
        self.content_generator = ContentGeneratorService(web_search_service=self.web_search_service)
        
        # --- Initialize Platform Services (injecting core services as dependencies) ---
        self.youtube_service = YouTubeService(
            content_generator=self.content_generator, 
            video_producer=self.video_producer
        )
        self.linkedin_service = LinkedInService(
            content_generator=self.content_generator, 
            image_generator=self.video_producer # LinkedIn can use the video producer for single images
        )
        self.instagram_service = InstagramService(
            content_generator=self.content_generator,
            image_post_generator=self.image_post_generator
        )
        
        # --- Initialize the Automation Scheduler ---
        self.scheduler = AutomationScheduler(youtube_service=self.youtube_service)
        print("✅ Main Orchestrator and all services initialized.")

    # --- Kill Switch Management for Graceful Shutdown ---
    def trigger_kill_switch(self):
        """Signals all services to stop their current long-running task."""
        print("ORCHESTRATOR: Kill switch triggered!")
        self.kill_switch.set()

    def reset_kill_switch(self):
        """Resets the kill switch for the next operation."""
        self.kill_switch.clear()

    # --- High-Level API for UI / Workers ---
    def generate_all_astrology_posts(self):
        self.reset_kill_switch()
        try:
            return self.instagram_service.create_daily_astrology_post_for_all_signs()
        except InterruptedException:
            print("ORCHESTRATOR: Astrology post generation was cancelled by user.")
            return [] # Return an empty list on cancellation
        except Exception as e:
            print(f"ORCHESTRATOR: A critical error occurred during astrology post generation: {e}")
            return None

    def generate_single_youtube_video(self, topic, niche, upload=True, image_source="ai_generated", auto_search_context=False):
        self.reset_kill_switch()
        try:
            return self.youtube_service.create_and_upload_video(
                topic=topic, 
                niche=niche, 
                upload=upload, 
                image_source=image_source, 
                auto_search_context=auto_search_context
            )
        except InterruptedException as e:
            return {"success": False, "message": f"Operation Cancelled by User."}
        except Exception as e:
            print(f"ORCHESTRATOR: A critical error occurred during YouTube video generation: {e}")
            return {"success": False, "message": "A critical internal error occurred."}
    
    # --- Automation Control ---
    def start_automation(self):
        self.scheduler.start()

    def stop_automation(self):
        self.scheduler.stop()

    def get_automation_status(self):
        return self.scheduler.get_status()

    def update_automation_settings(self, new_settings):
        self.scheduler.update_settings(new_settings)
