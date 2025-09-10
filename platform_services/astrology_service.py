# src/platform_services/instagram_service.py

import os
import random
import requests
from config import PEXELS_API_KEY, DATA_PATH

# --- CHANGE: The ContentGeneratorService now needs to be imported for type hinting ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService

try:
    from pexels_api import API
except ImportError:
    API = None

class InstagramService:
    """
    A service dedicated to creating daily astrology posts. It uses the 
    ContentGeneratorService to create unique astrological data and captions,
    fetches a background image from Pexels, and combines them into a final post.
    """
    def __init__(self, content_generator: 'ContentGeneratorService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_post_generator = image_post_generator
        
        # This path is for temporary source images downloaded from Pexels
        self.temp_images_path = os.path.join(DATA_PATH, "temp_images")
        os.makedirs(self.temp_images_path, exist_ok=True)

        if not PEXELS_API_KEY or "YOUR_PEXELS_API_KEY" in PEXELS_API_KEY or not API:
            self.pexels_api = None
            print("⚠️  Warning: Pexels API key not configured or pexels_api library not installed.")
        else:
            self.pexels_api = API(PEXELS_API_KEY)
            print("✅ Instagram Service initialized with Pexels API.")

    # --- CHANGE: The external astrology API call is no longer needed and has been removed. ---

    def _get_royalty_free_image(self, query: str, sign: str) -> str | None:
        """Searches and downloads a royalty-free image from Pexels."""
        if not self.pexels_api:
            print("   - ❗ Pexels API not configured. Skipping image search.")
            return None
        try:
            print(f"   - 🔎 Searching Pexels for: '{query}'...")
            self.pexels_api.search(query, page=random.randint(1, 5), results_per_page=15)
            photos = self.pexels_api.get_entries()
            
            if not photos:
                print(f"   - ❗ No photos found on Pexels for '{query}'.")
                return None
            
            photo_url = random.choice(photos).original
            response = requests.get(photo_url, timeout=15)
            response.raise_for_status()
            
            # Save to a temporary path
            temp_path = os.path.join(self.temp_images_path, f"temp_pexels_{sign}.jpg")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            print(f"   - ✅ Image downloaded successfully from Pexels to {temp_path}.")
            return temp_path
        except Exception as e:
            print(f"   - ❌ Error fetching image from Pexels: {e}")
            return None

    def create_daily_astrology_post_for_all_signs(self):
        """The main automation loop that generates a post for every zodiac sign using AI."""
        print("\n🔮 Starting Daily Astrology Post Generation for ALL SIGNS (AI-Powered) 🔮")
        zodiac_signs = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo", 
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
        
        all_posts = []
        for sign in zodiac_signs:
            print(f"\n--- Generating post for {sign.upper()} ---")
            
            # --- CHANGE: Step 1 now uses the ContentGeneratorService to create the data ---
            raw_data = self.content_generator.generate_astrology_data(sign)
            if not raw_data:
                print(f"   - ❗ Failed to generate AI astrology data for {sign}. Skipping.")
                continue
            
            # Step 2: Use the ContentGeneratorService to create a beautiful caption from the AI data
            caption = self.content_generator.create_astrology_caption(raw_data)
            
            # Step 3: Get a background image based on the AI-generated color
            image_query = f"mystical {raw_data.get('color', 'space')} abstract"
            base_image_path = self._get_royalty_free_image(image_query, sign)
            if not base_image_path:
                continue
            
            # Step 4: Combine text and image into a final post
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=base_image_path,
                text=raw_data.get('description'),
                title=sign.capitalize()
            )
            
            if final_post_url:
                print(f"✅ Successfully created post for {sign}!")
                all_posts.append({
                    "sign": sign,
                    "url": final_post_url,
                    "caption": caption
                })
            
            # Clean up the temporary downloaded image
            if os.path.exists(base_image_path):
                os.remove(base_image_path)
        
        print(f"\n✨ --- Process Complete! Generated {len(all_posts)} posts. --- ✨")
        return all_posts