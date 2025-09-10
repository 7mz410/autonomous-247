# src/platform_services/instagram_service.py

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService
    from core_services.video_producer_service import VideoProducerService

class InstagramService:
    """
    Handles generation of general Instagram posts using the professional two-step method.
    """
    def __init__(self, content_generator: 'ContentGeneratorService', image_generator: 'VideoProducerService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_generator = image_generator 
        self.image_post_generator = image_post_generator
        print("✅ General Instagram Service initialized (Professional Method v2).")

    def create_general_post(self, topic: str, niche: str):
        print(f"\nINSTAGRAM: Generating professional post for topic: '{topic}'...")
        try:
            # Step 1: Generate text content and a SEPARATE, VISUAL-ONLY prompt for the background.
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="Instagram"
            )
            if not content_data:
                raise Exception("Failed to generate text content from AI.")

            # --- THE CRITICAL CHANGE ---
            # Step 2: Use the new, clean "background_image_prompt" directly.
            background_prompt = content_data.get("background_image_prompt", f"A clean, minimalist background related to {niche}")
            print(f"INSTAGRAM: Generating clean background image with prompt: '{background_prompt}'")
            
            # Step 3: Generate the background image.
            image_paths = self.image_generator._generate_images_with_stability([background_prompt], aspect_ratio="1:1")
            if not image_paths:
                raise Exception("Failed to generate a background image.")
            
            background_image_path = image_paths[0]
            post_text_content = content_data.get("post_text")
            final_caption_for_upload = f"{post_text_content}\n\n{' '.join(content_data.get('hashtags', []))}"

            # Step 4: Use the ImagePostGeneratorService to overlay the clean text onto the background.
            print("INSTAGRAM: Overlaying clean text onto the background image...")
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=background_image_path,
                text=post_text_content, # This is the text written ON the image
                title=topic.capitalize()
            )

            if not final_post_url:
                raise Exception("Failed to overlay text and create the final post image.")

            print("✅ Professional Instagram post generated successfully.")
            return {
                "success": True, 
                "message": "Instagram post generated successfully using the professional method!",
                "url": final_post_url,
                "caption": final_caption_for_upload # This is the caption for the post upload
            }

        except Exception as e:
            print(f"   - ❌ Error in create_general_post (Instagram): {e}")
            return {"success": False, "message": str(e)}