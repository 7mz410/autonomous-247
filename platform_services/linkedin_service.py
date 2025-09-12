# src/platform_services/linkedin_service.py

import requests
from urllib.parse import urlencode
from config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI
from typing import TYPE_CHECKING

# --- CHANGE: Added dependencies needed for the professional method ---
if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService
    from core_services.video_producer_service import VideoProducerService

class LinkedInService:
    # --- CHANGE: The service now requires the image_post_generator ---
    def __init__(self, content_generator: 'ContentGeneratorService', image_generator: 'VideoProducerService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_generator = image_generator
        self.image_post_generator = image_post_generator
        
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.redirect_uri = LINKEDIN_REDIRECT_URI

        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base_url = "https://api.linkedin.com/v2"
        
        self.access_token = None
        self.user_urn = None

        if not self.client_id or not self.client_secret:
            print("⚠️  Warning: LinkedIn credentials not found.")
        else:
            print("✅ LinkedIn Service initialized (Professional Method).")

    def is_authenticated(self) -> bool:
        return self.access_token is not None

    # --- CHANGE: This function now uses the professional two-step image generation ---
    def generate_post_package(self, niche, topic):
        print(f"LINKEDIN: Generating professional post for topic: '{topic}'...")
        try:
            # 1. Generate text and a clean background prompt
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="LinkedIn"
            )
            if not content_data:
                raise Exception("Failed to generate text content from AI.")

            # 2. Use the correct key for the background prompt
            background_prompt = content_data.get("background_image_prompt", f"A professional, clean background for a post about {niche}")
            print(f"LINKEDIN: Generating clean background image with prompt: '{background_prompt}'")
            
            # 3. Generate the background image (LinkedIn posts are often 1.91:1 or 1:1, we'll use 1:1 for consistency)
            image_paths = self.image_generator._generate_images_with_stability([background_prompt], aspect_ratio="1:1")
            if not image_paths:
                raise Exception("Failed to generate a background image.")
            
            background_image_path = image_paths[0]
            post_text_content = content_data.get("post_text")
            final_caption_for_upload = f"{post_text_content}\n\n{' '.join(content_data.get('hashtags', []))}"
            
            # 4. Use the ImagePostGenerator to overlay clean text
            print("LINKEDIN: Overlaying clean text onto the background image...")
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=background_image_path,
                text=post_text_content,
                title=topic.capitalize()
            )

            if not final_post_url:
                raise Exception("Failed to create the final post image.")
            
            return {
                "url": final_post_url,
                "caption": final_caption_for_upload
            }
        except Exception as e:
            print(f"   - ❌ Error in generate_post_package (LinkedIn): {e}")
            return None

    # (The rest of the file: auth, user info, publishing methods remain the same)
    def generate_auth_url(self):
        # ...
    def exchange_code_for_token(self, auth_code):
        # ...
    def fetch_user_info(self):
        # ...
    def publish_post(self, post_data):
        # ...