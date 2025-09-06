# src/platform_services/instagram_service.py

import os
import random
import requests
from src.config import PEXELS_API_KEY, DATA_PATH

try:
    from pexels_api import API
except ImportError:
    API = None

class InstagramService:
    """
    A service dedicated to creating daily astrology posts. It fetches data,
    gets a background image, generates a caption, and combines them into a final image post.
    """
    def __init__(self, content_generator, image_post_generator):
        self.content_generator = content_generator
        self.image_post_generator = image_post_generator
        
        # This path is for temporary source images downloaded from Pexels
        self.temp_images_path = os.path.join(DATA_PATH, "generated_images")
        os.makedirs(self.temp_images_path, exist_ok=True)

        if not PEXELS_API_KEY or "YOUR_PEXELS_API_KEY" in PEXELS_API_KEY or not API:
            self.pexels_api = None
            print("⚠️  Warning: Pexels API key not configured or pexels_api library not installed.")
        else:
            self.pexels_api = API(PEXELS_API_KEY)
            print("✅ Instagram Service initialized with Pexels API.")

    def _get_daily_astrology_data(self, sign: str) -> dict | None:
        """Fetches daily horoscope data from a free, public astrology API."""
        print(f"   - Fetching daily data for {sign}...")
        try:
            response = requests.post(f'https://aztro.sameerkumar.website/?sign={sign}&day=today', timeout=10)
            response.raise_for_status()
            data = response.json()
            data['sign'] = sign
            return data
        except requests.RequestException as e:
            print(f"   - ❌ Could not fetch astrology data for {sign}: {e}")
            return None

    def _get_royalty_free_image(self, query: str, sign: str) -> str | None:
        """Searches and downloads a royalty-free image from Pexels."""
        if not self.pexels_api:
            print("   - ❗ Pexels API not configured. Skipping image search.")
            return None
        try:
            print(f"   - 🔎 Searching Pexels for: '{query}'...")
            self.pexels_api.search(query, page=1, results_per_page=15)
            photos = self.pexels_api.get_entries()
            
            if not photos:
                print(f"   - ❗ No photos found on Pexels for '{query}'.")
                return None
            
            photo_url = random.choice(photos).original
            response = requests.get(photo_url, timeout=15)
            response.raise_for_status()
            
            # Save to the persistent data path
            temp_path = os.path.join(self.temp_images_path, f"temp_pexels_{sign}.jpg")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            print(f"   - ✅ Image downloaded successfully from Pexels to {temp_path}.")
            return temp_path
        except Exception as e:
            print(f"   - ❌ Error fetching image from Pexels: {e}")
            return None

    def create_daily_astrology_post_for_all_signs(self):
        """The main automation loop that generates a post for every zodiac sign."""
        print("\n🔮 Starting Daily Astrology Post Generation for ALL SIGNS 🔮")
        zodiac_signs = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo", 
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
        
        all_posts = []
        for sign in zodiac_signs:
            print(f"\n--- Generating post for {sign.upper()} ---")
            
            # Step 1: Get raw daily data for the sign
            raw_data = self._get_daily_astrology_data(sign)
            if not raw_data:
                continue
            
            # Step 2: Use GPT-4o to create a beautiful caption
            caption = self.content_generator.create_astrology_caption(raw_data)
            
            # Step 3: Get a background image
            image_query = f"mystical {raw_data.get('color', 'space')} abstract"
            base_image_path = self._get_royalty_free_image(image_query, sign)
            if not base_image_path:
                continue
            
            # Step 4: Combine text and image into a final post
            # The image_post_generator service will save the final result in its own directory
            final_post_path = self.image_post_generator.create_post_image(
                base_image_path=base_image_path,
                text=raw_data.get('description'),
                title=sign.capitalize()
            )
            
            if final_post_path:
                print(f"✅ Successfully created post for {sign}!")
                all_posts.append({
                    "sign": sign,
                    "path": final_post_path,
                    "caption": caption
                })
            
            # Clean up the temporary downloaded image
            if os.path.exists(base_image_path):
                os.remove(base_image_path)
        
        print(f"\n✨ --- Process Complete! Generated {len(all_posts)} posts. --- ✨")
        return all_posts
