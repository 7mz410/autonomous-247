# src/platform_services/instagram_service.py

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService
    # We need the video producer because it contains the image generation method
    from core_services.video_producer_service import VideoProducerService

class InstagramService:
    """
    Handles the generation of general-purpose Instagram posts using the professional two-step method:
    1. Generate a clean background image from Stability AI.
    2. Overlay clean, readable text using Python's Pillow library.
    """
    def __init__(self, content_generator: 'ContentGeneratorService', image_generator: 'VideoProducerService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_generator = image_generator # For generating the background
        self.image_post_generator = image_post_generator # For overlaying text
        print("✅ General Instagram Service initialized (Professional Method).")

    def create_general_post(self, topic: str, niche: str):
        """
        Creates a complete and high-quality Instagram post.
        """
        print(f"\nINSTAGRAM: Generating professional post for topic: '{topic}'...")
        try:
            # Step 1: Generate the text content (caption) AND a prompt for a background image from the LLM
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="Instagram"
            )
            if not content_data:
                raise Exception("Failed to generate text content from AI.")

            # --- THE CRITICAL CHANGE ---
            # Step 2: Modify the image prompt to ensure it's a clean background (no text)
            original_prompt = content_data.get("image_prompt")
            # We add keywords to guide the AI away from rendering text
            modified_prompt = f"{original_prompt}, clean modern background, minimalist, vibrant, no text, no words"
            print(f"INSTAGRAM: Generating clean background image with modified prompt: '{modified_prompt[:70]}...'")
            
            # Step 3: Generate the background image using the modified prompt
            image_paths = self.image_generator._generate_images_with_stability([modified_prompt], aspect_ratio="1:1")
            if not image_paths:
                raise Exception("Failed to generate a background image.")
            
            background_image_path = image_paths[0]
            post_text_content = content_data.get("post_text")
            final_caption = f"{post_text_content}\n\n{' '.join(content_data.get('hashtags', []))}"

            # Step 4: Use the ImagePostGeneratorService to overlay the clean text onto the background
            print("INSTAGRAM: Overlaying clean text onto the background image...")
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=background_image_path,
                text=post_text_content,
                title=topic.capitalize() # Use the topic as the main title
            )

            if not final_post_url:
                raise Exception("Failed to overlay text and create the final post image.")

            print("✅ Professional Instagram post generated successfully.")
            return {
                "success": True, 
                "message": "Instagram post generated successfully using the professional method!",
                "url": final_post_url, # The final URL from Spaces
                "caption": final_caption
            }

        except Exception as e:
            print(f"   - ❌ Error in create_general_post (Instagram): {e}")
            return {"success": False, "message": str(e)}