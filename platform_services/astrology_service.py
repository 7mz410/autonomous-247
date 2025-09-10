# src/platform_services/astrology_service.py

import os
import random
import requests
from config import PEXELS_API_KEY, DATA_PATH
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService

try:
    from pexels_api import API
except ImportError:
    API = None

class AstrologyService:
    """
    Service dedicated to creating daily astrology image posts.
    """
    def __init__(self, content_generator: 'ContentGeneratorService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_post_generator = image_post_generator
        self.temp_images_path = os.path.join(DATA_PATH, "temp_images")
        os.makedirs(self.temp_images_path, exist_ok=True)

        if not PEXELS_API_KEY or not API:
            self.pexels_api = None
            print("⚠️  Warning: Pexels API key not configured or pexels_api library not installed.")
        else:
            self.pexels_api = API(PEXELS_API_KEY)
            print("✅ Astrology Service initialized with Pexels API.")

    def _get_royalty_free_image(self, query: str, sign: str) -> str | None:
        if not self.pexels_api: return None
        try:
            print(f"   - 🔎 Searching Pexels for: '{query}'...")
            self.pexels_api.search(query, page=random.randint(1, 5), results_per_page=15)
            photos = self.pexels_api.get_entries()
            if not photos: return None
            
            response = requests.get(random.choice(photos).original, timeout=15)
            response.raise_for_status()
            
            temp_path = os.path.join(self.temp_images_path, f"temp_pexels_{sign}.jpg")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            return temp_path
        except Exception as e:
            print(f"   - ❌ Error fetching image from Pexels: {e}")
            return None

    def create_daily_astrology_post_for_all_signs(self):
        print("\n🔮 Starting AI-Powered Daily Astrology Post Generation 🔮")
        zodiac_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
        all_posts = []
        for sign in zodiac_signs:
            print(f"\n--- Generating post for {sign.upper()} ---")
            
            raw_data = self.content_generator.generate_astrology_data(sign)
            if not raw_data: continue
            
            caption = self.content_generator.create_astrology_caption(raw_data)
            
            image_query = f"mystical {raw_data.get('color', 'space')} abstract"
            base_image_path = self._get_royalty_free_image(image_query, sign)
            if not base_image_path: continue
            
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=base_image_path, 
                text=raw_data.get('description'), 
                title=sign.capitalize(),
                title_font_size=120,
                body_font_size=90
            )
            
            if final_post_url:
                all_posts.append({"sign": sign, "url": final_post_url, "caption": caption})
            
            # --- THIS IS THE FIX: Changed 'base_item_path' to 'base_image_path' ---
            if base_image_path and os.path.exists(base_image_path):
                os.remove(base_image_path)
        
        print(f"\n✨ --- Process Complete! Generated {len(all_posts)} posts. --- ✨")
        return all_posts