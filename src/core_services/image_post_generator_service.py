# src/core_services/image_post_generator_service.py

import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from src.config import DATA_PATH, ASSETS_PATH

class ImagePostGeneratorService:
    """
    A service dedicated to creating text-based image posts by overlaying
    stylized text onto a base image.
    """
    def __init__(self):
        self.posts_path = os.path.join(DATA_PATH, "generated_posts")
        os.makedirs(self.posts_path, exist_ok=True)
        print("✅ Image Post Generator Service initialized.")

    def create_post_image(self, base_image_path: str, text: str, title: str) -> str | None:
        """
        Overlays a title and body text onto a base image to create a final post.
        Returns the path to the generated image, or None on failure.
        """
        try:
            with Image.open(base_image_path) as img:
                # Ensure image is in a format that supports alpha blending
                img = img.convert("RGBA")

                # Create a semi-transparent overlay
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 128))
                img = Image.alpha_composite(img, overlay)

                draw = ImageDraw.Draw(img)

                try:
                    # Use a centrally managed path for assets
                    font_path = os.path.join(ASSETS_PATH, "fonts", "Arial.ttf")
                    title_font = ImageFont.truetype(font_path, size=90)
                    body_font = ImageFont.truetype(font_path, size=60)
                except IOError:
                    print("   - ⚠️ Warning: Font not found in assets. Using default font.")
                    title_font = ImageFont.load_default(size=90)
                    body_font = ImageFont.load_default(size=60)

                margin = 60
                wrapped_text = textwrap.fill(text, width=25)

                # Calculate positions for centering text
                title_bbox = draw.textbbox((0, 0), title, font=title_font)
                body_bbox = draw.textbbox((0, 0), wrapped_text, font=body_font, spacing=15)

                title_width = title_bbox[2] - title_bbox[0]
                body_height = body_bbox[3] - body_bbox[1]
                title_height = title_bbox[3] - title_bbox[1]

                total_height = title_height + 20 + body_height
                start_y = (img.height - total_height) / 2
                
                title_x = (img.width - title_width) / 2
                draw.text((title_x, start_y), title, font=title_font, fill="white")

                body_start_y = start_y + title_height + 40
                draw.text((margin, body_start_y), wrapped_text, font=body_font, fill="white", spacing=15)

                # Save the final image to the correct data path
                filename = f"post_{title.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_filepath = os.path.join(self.posts_path, filename)
                img.save(output_filepath, "PNG")

                print(f"✅ Post image created and saved to: {output_filepath}")
                return output_filepath

        except FileNotFoundError:
            print(f"   - ❌ Error: Base image not found at '{base_image_path}'")
            return None
        except Exception as e:
            print(f"   - ❌ An unexpected error occurred in create_post_image: {e}")
            return None
