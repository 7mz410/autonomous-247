# orchestration/main_orchestrator.py
import threading
from utils.exceptions import InterruptedException

from core_services.content_generator_service import ContentGeneratorService
from core_services.video_producer_service import VideoProducerService
from core_services.web_search_service import WebSearchService
from core_services.image_post_generator_service import ImagePostGeneratorService
from platform_services.youtube_service import YouTubeService
from platform_services.linkedin_service import LinkedInService
from platform_services.astrology_service import AstrologyService
from platform_services.instagram_service import InstagramService
from orchestration.automation_scheduler import AutomationScheduler

class MainOrchestrator:
    def __init__(self):
        print("Initializing the Main Orchestrator...")
        
        self.kill_switch = threading.Event()

        # --- Initialize Core Services ---
        self.web_search_service = WebSearchService()
        self.video_producer = VideoProducerService(kill_switch=self.kill_switch)
        self.image_post_generator = ImagePostGeneratorService()
        # --- FIX: Pass the web_search_service to the ContentGeneratorService constructor ---
        self.content_generator = ContentGeneratorService(web_search_service=self.web_search_service)
        
        # --- Initialize Platform Services ---
        self.youtube_service = YouTubeService(
            content_generator=self.content_generator, video_producer=self.video_producer
        )
        self.linkedin_service = LinkedInService(
            content_generator=self.content_generator, image_generator=self.video_producer
        )
        self.astrology_service = AstrologyService(
            content_generator=self.content_generator, image_post_generator=self.image_post_generator
        )
        self.instagram_service = InstagramService(
            content_generator=self.content_generator, image_generator=self.video_producer
        )
        
        # --- Initialize the Automation Scheduler ---
        self.scheduler = AutomationScheduler(youtube_service=self.youtube_service)
        print("✅ Main Orchestrator and all services initialized.")

    def trigger_kill_switch(self):
        self.kill_switch.set()

    def reset_kill_switch(self):
        self.kill_switch.clear()

    def generate_all_astrology_posts(self):
        self.reset_kill_switch()
        try:
            return self.astrology_service.create_daily_astrology_post_for_all_signs()
        except InterruptedException:
            return []
        except Exception as e:
            print(f"ORCHESTRATOR: Critical error during astrology generation: {e}")
            return None

    def generate_single_instagram_post(self, topic: str, niche: str):
        self.reset_kill_switch()
        try:
            return self.instagram_service.create_general_post(topic=topic, niche=niche)
        except InterruptedException:
            return {"success": False, "message": "Operation Cancelled by User."}
        except Exception as e:
            print(f"ORCHESTRATOR: Critical error during Instagram post generation: {e}")
            return {"success": False, "message": "A critical internal error occurred."}

    def generate_single_youtube_video(self, topic, niche, upload=True, image_source="ai_generated", auto_search_context=False):
        self.reset_kill_switch()
        try:
            return self.youtube_service.create_and_upload_video(
                topic=topic, niche=niche, upload=upload, 
                image_source=image_source, auto_search_context=auto_search_context
            )
        except InterruptedException:
            return {"success": False, "message": "Operation Cancelled by User."}
        except Exception as e:
            print(f"ORCHESTRATOR: Critical error during YouTube video generation: {e}")
            return {"success": False, "message": "A critical internal error occurred."}
    
    def start_automation(self):
        self.scheduler.start()

    def stop_automation(self):
        self.scheduler.stop()

    def get_automation_status(self):
        return self.scheduler.get_status()

    def update_automation_settings(self, new_settings):
        self.scheduler.update_settings(new_settings)