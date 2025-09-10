# src/platform_services/instagram_service.py

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.video_producer_service import VideoProducerService

class InstagramService:
    """
    Handles the generation of general-purpose Instagram posts based on user input.
    This service is responsible for creating the content package (caption and image).
    The actual publishing mechanism is a placeholder for future implementation due to API complexity.
    """
    def __init__(self, content_generator: 'ContentGeneratorService', image_generator: 'VideoProducerService'):
        self.content_generator = content_generator
        # We reuse the image generator from the VideoProducerService, same as LinkedInService
        self.image_generator = image_generator
        print("✅ General Instagram Service initialized.")

    def create_general_post(self, topic: str, niche: str):
        """
        Creates a complete package (caption, hashtags, image) for a general Instagram post.
        """
        print(f"\nINSTAGRAM: Generating post content for topic: '{topic}' in niche '{niche}'...")
        try:
            # Step 1: Generate the text content, hashtags, and an image prompt from the LLM
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="Instagram"
            )
            if not content_data:
                raise Exception("Failed to generate text content from AI.")

            # Step 2: Generate an image using the prompt from the previous step
            image_prompt = content_data.get("image_prompt")
            print(f"INSTAGRAM: Generating image with prompt: '{image_prompt[:60]}...'")
            
            # The _generate_images_with_stability returns a list of local paths
            image_paths = self.image_generator._generate_images_with_stability([image_prompt], aspect_ratio="1:1") # 1:1 is best for Instagram
            if not image_paths:
                raise Exception("Failed to generate an image.")

            local_image_path = image_paths[0]
            final_caption = f"{content_data.get('post_text')}\n\n{' '.join(content_data.get('hashtags', []))}"

            print("✅ Instagram content package generated successfully.")
            
            # Step 3: Publish the post (Placeholder for now)
            # self._publish_to_instagram_api(local_image_path, final_caption)

            return {
                "success": True, 
                "message": "Instagram post content generated successfully!",
                "path": local_image_path, # Return the local path for display in UI
                "caption": final_caption
            }

        except Exception as e:
            print(f"   - ❌ Error in create_general_post (Instagram): {e}")
            return {"success": False, "message": str(e)}

    def _publish_to_instagram_api(self, image_path: str, caption: str):
        """
        --- Placeholder for future implementation ---
        The official Instagram Content Publishing API is complex and requires
        Business verification, Facebook App reviews, and specific permissions.
        This function would contain the logic to upload the image and post it.
        """
        print("\n--- Publishing to Instagram (Not Implemented) ---")
        print(f"   - Image Path: {image_path}")
        print(f"   - Caption: {caption}")
        print("-------------------------------------------------")
        # In a real implementation, you would use requests to call the Instagram Graph API endpoints.
        pass