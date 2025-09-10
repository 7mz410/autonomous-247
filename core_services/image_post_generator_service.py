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

    def create_post_image(
        self, 
        base_image_path: str, 
        text: str, 
        title: str, 
        title_font_size: int = 110, 
        body_font_size: int = 75
    ) -> str | None:
        try:
            # --- NEW: Smart Cropping & Resizing Logic (The Magic Happens Here) ---
            target_width, target_height = 1080, 1350
            target_aspect = target_width / target_height

            with Image.open(base_image_path) as img:
                original_width, original_height = img.size
                original_aspect = original_width / original_height

                # Determine the crop box
                if original_aspect > target_aspect:
                    # Original image is wider than target: Crop the sides
                    new_height = target_height
                    new_width = int(original_aspect * new_height)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    left = (new_width - target_width) / 2
                    top = 0
                    right = left + target_width
                    bottom = new_height
                    img = resized_img.crop((left, top, right, bottom))
                else:
                    # Original image is taller than target (or same aspect): Crop the top/bottom
                    new_width = target_width
                    new_height = int(new_width / original_aspect)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    left = 0
                    top = (new_height - target_height) / 2
                    right = new_width
                    bottom = top + target_height
                    img = resized_img.crop((left, top, right, bottom))

                # --- End of New Logic ---

                # Now 'img' is a perfect 1080x1350 image. The rest of the code proceeds as before.
                img = img.convert("RGBA")
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 150))
                img = Image.alpha_composite(img, overlay)
                draw = ImageDraw.Draw(img)

                try:
                    font_path = os.path.join(ASSETS_PATH, "Fonts", "Arial.ttf")
                    title_font = ImageFont.truetype(font_path, size=title_font_size)
                    body_font = ImageFont.truetype(font_path, size=body_font_size)
                except IOError:
                    print("   - ⚠️ Warning: Custom font not found. Using default font.")
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()

                # Centered drawing logic
                title_bbox = draw.textbbox((0,0), title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_height = title_bbox[3] - title_bbox[1]
                title_x = (img.width - title_width) / 2
                title_y = (img.height / 2) - title_height - 100 
                draw.text((title_x, title_y), title, font=title_font, fill="white")

                wrapped_body = textwrap.fill(text, width=30)
                body_bbox = draw.textbbox((0,0), wrapped_body, font=body_font, align="center", spacing=10)
                body_width = body_bbox[2] - body_bbox[0]
                body_x = (img.width - body_width) / 2
                body_y = title_y + title_height + 40
                draw.multiline_text((body_x, body_y), wrapped_body, font=body_font, fill="white", align="center", spacing=15)
                
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