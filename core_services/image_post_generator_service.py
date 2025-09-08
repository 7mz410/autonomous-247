# src/core_services/image_post_generator_service.py

import os
import textwrap
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
fromconfig import ASSETS_PATH
fromutils import storage_service

class ImagePostGeneratorService:
    def __init__(self):
        # No longer needs to manage local paths, it's now cloud-native.
        print("✅ Image Post Generator Service initialized.")

    def create_post_image(self, base_image_path: str, text: str, title: str) -> str | None:
        """
        Overlays text onto a base image, saves the result to a temporary file,
        uploads it to Spaces, and returns the public URL.
        """
        try:
            with Image.open(base_image_path) as img:
                img = img.convert("RGBA")
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 128))
                img = Image.alpha_composite(img, overlay)
                draw = ImageDraw.Draw(img)

                try:
                    font_path = os.path.join(ASSETS_PATH, "fonts", "Arial.ttf")
                    title_font = ImageFont.truetype(font_path, size=90)
                    body_font = ImageFont.truetype(font_path, size=60)
                except IOError:
                    print("   - ⚠️ Warning: Font not found. Using default font.")
                    title_font = ImageFont.load_default(size=90)
                    body_font = ImageFont.load_default(size=60)

                margin = 60
                wrapped_text = textwrap.fill(text, width=25)
                
                title_bbox = draw.textbbox((0, 0), title, font=title_font)
                body_bbox = draw.textbbox((0, 0), wrapped_text, font=body_font, spacing=15)
                title_width = title_bbox[2] - title_bbox[0]
                title_height = title_bbox[3] - title_bbox[1]
                body_height = body_bbox[3] - body_bbox[1]
                
                total_height = title_height + 20 + body_height
                start_y = (img.height - total_height) / 2
                title_x = (img.width - title_width) / 2
                
                draw.text((title_x, start_y), title, font=title_font, fill="white")
                body_start_y = start_y + title_height + 40
                draw.text((margin, body_start_y), wrapped_text, font=body_font, fill="white", spacing=15)
                
                # --- NEW: Save to a temporary local file ---
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    img.save(temp_file.name, "PNG")
                    local_path = temp_file.name

                # --- NEW: Upload to Spaces and get the URL ---
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_name = f"generated_posts/post_{title.replace(' ','_')}_{timestamp}.png"
                spaces_url = storage_service.upload_file(local_path, object_name)

                os.remove(local_path) # Clean up the temporary file

                if spaces_url:
                    print(f"✅ Post image created and uploaded to Spaces.")
                    return spaces_url
                else:
                    raise Exception("File upload to Spaces failed.")
        
        except Exception as e:
            print(f"❌ Error creating post image: {e}")
            return None
