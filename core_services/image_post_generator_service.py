# src/core_services/image_post_generator_service.py

import os
import textwrap
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import ASSETS_PATH
from utils import storage_service

class ImagePostGeneratorService:
    def __init__(self):
        print("✅ Image Post Generator Service initialized.")

    def create_post_image(self, base_image_path: str, text: str, title: str) -> str | None:
        """
        Overlays text onto a base image, saves it to a temporary file,
        uploads it to Spaces, and cleans up.
        """
        try:
            with Image.open(base_image_path) as img:
                img = img.convert("RGBA")
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 128))
                img = Image.alpha_composite(img, overlay)
                draw = ImageDraw.Draw(img)

                try:
                    # The code will try to find the font at this exact path
                    font_path = os.path.join(ASSETS_PATH, "Fonts", "Arial.ttf")
                    title_font = ImageFont.truetype(font_path, size=90)
                    body_font = ImageFont.truetype(font_path, size=60)
                except IOError:
                    print("   - ⚠️ Warning: Custom font not found. Using default font.")
                    # --- THIS IS THE FIX: load_default() does not take a 'size' argument ---
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()

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
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    img.save(temp_file.name, "PNG")
                    local_path = temp_file.name

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_name = f"generated_posts/post_{title.replace(' ','_')}_{timestamp}.png"
                spaces_url = storage_service.upload_file(local_path, object_name)

                os.remove(local_path) 

                if spaces_url:
                    print(f"✅ Post image created and uploaded to Spaces.")
                    return spaces_url
                else:
                    raise Exception("File upload to Spaces failed.")
        
        except Exception as e:
            print(f"❌ Error creating post image: {e}")
            return None