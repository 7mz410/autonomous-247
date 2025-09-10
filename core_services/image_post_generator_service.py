# src/core_services/image_post_generator_service.py

import os
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import ASSETS_PATH
from utils import storage_service

class ImagePostGeneratorService:
    def __init__(self):
        print("✅ Image Post Generator Service initialized.")

    def _wrap_text_by_pixels(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        """Wraps text to fit a specific pixel width."""
        lines = []
        words = text.split()
        if not words: return ""
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return "\n".join(lines)

    def create_post_image(
        self, 
        base_image_path: str, 
        text: str, 
        title: str, 
        title_font_size: int = 120, 
        body_font_size: int = 80
    ) -> str | None:
        try:
            target_width, target_height = 1080, 1350
            target_aspect = target_width / target_height

            with Image.open(base_image_path) as img:
                # (Smart Cropping logic remains the same)
                original_width, original_height = img.size
                original_aspect = original_width / original_height
                if original_aspect > target_aspect:
                    new_height = target_height
                    new_width = int(original_aspect * new_height)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    left = (new_width - target_width) / 2
                    right = left + target_width
                    img = resized_img.crop((left, 0, right, new_height))
                else:
                    new_width = target_width
                    new_height = int(new_width / original_aspect)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    top = (new_height - target_height) / 2
                    bottom = top + target_height
                    img = resized_img.crop((0, top, new_width, bottom))

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

                # --- CORRECTED: Professional Text Centering & Padding Logic ---
                side_padding = 100
                max_text_width = img.width - (2 * side_padding)
                
                wrapped_title = self._wrap_text_by_pixels(title, title_font, max_text_width, draw)
                wrapped_body = self._wrap_text_by_pixels(text, body_font, max_text_width, draw)
                
                title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font, align="center", spacing=15)
                title_height = title_bbox[3] - title_bbox[1]
                
                body_bbox = draw.multiline_textbbox((0, 0), wrapped_body, font=body_font, align="center", spacing=15)
                body_height = body_bbox[3] - body_bbox[1]
                
                spacing_between = 50
                total_block_height = title_height + spacing_between + body_height
                
                start_y = (img.height - total_block_height) / 2
                
                # --- THIS IS THE FIX: Manually calculate X for true centering ---
                title_width = title_bbox[2] - title_bbox[0]
                title_x = (img.width - title_width) / 2
                title_y = start_y
                
                body_width = body_bbox[2] - body_bbox[0]
                body_x = (img.width - body_width) / 2
                body_y = start_y + title_height + spacing_between
                
                # --- THE FIX: Removed the unsupported 'anchor' argument ---
                draw.multiline_text((title_x, title_y), wrapped_title, font=title_font, fill="white", align="center", spacing=15)
                draw.multiline_text((body_x, body_y), wrapped_body, font=body_font, fill="white", align="center", spacing=15)
                # --- End of Corrected Logic ---

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