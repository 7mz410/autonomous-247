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

        self.web_search_service = WebSearchService()
        self.video_producer = VideoProducerService(kill_switch=self.kill_switch)
        self.image_post_generator = ImagePostGeneratorService()
        self.content_generator = ContentGeneratorService(web_search_service=self.web_search_service)
        
        self.youtube_service = YouTubeService(
            content_generator=self.content_generator, video_producer=self.video_producer
        )
        # --- CHANGE: Pass the 'image_post_generator' to LinkedInService as well ---
        self.linkedin_service = LinkedInService(
            content_generator=self.content_generator, 
            image_generator=self.video_producer,
            image_post_generator=self.image_post_generator
        )
        self.astrology_service = AstrologyService(
            content_generator=self.content_generator, image_post_generator=self.image_post_generator
        )
        self.instagram_service = InstagramService(
            content_generator=self.content_generator, 
            image_generator=self.video_producer,
            image_post_generator=self.image_post_generator
        )
        
        self.scheduler = AutomationScheduler(youtube_service=self.youtube_service)
        print("✅ Main Orchestrator and all services initialized.")

    def generate_single_linkedin_post(self, topic: str, niche: str):
        self.reset_kill_switch()
        try:
            package = self.linkedin_service.generate_post_package(topic=topic, niche=niche)
            # --- CHANGE: Return the final public URL for display ---
            if package and package.get("url"):
                return {
                    "success": True,
                    "message": "LinkedIn post content generated successfully!",
                    "url": package.get("url"),
                    "caption": package.get("caption")
                }
            else:
                return {"success": False, "message": "Failed to generate LinkedIn content package."}
        except InterruptedException:
            return {"success": False, "message": "Operation Cancelled by User."}
        except Exception as e:
            print(f"ORCHESTRATOR: Critical error during LinkedIn post generation: {e}")
            return {"success": False, "message": "A critical internal error occurred."}
            
    # (The rest of the functions remain the same)
    def trigger_kill_switch(self): #...
    def reset_kill_switch(self): #...
    def generate_all_astrology_posts(self): #...
    def generate_single_instagram_post(self, topic, niche): #...
    def generate_single_youtube_video(self, topic, niche, upload, image_source, auto_search_context): #...
    def start_automation(self): #...
    def stop_automation(self): #...
    def get_automation_status(self): #...
    def update_automation_settings(self, new_settings): #...