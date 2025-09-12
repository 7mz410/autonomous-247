# src/platform_services/linkedin_service.py

import requests
from urllib.parse import urlencode
from config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI

class LinkedInService:
    def __init__(self, content_generator, image_generator):
        self.content_generator = content_generator
        self.image_generator = image_generator
        
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.redirect_uri = LINKEDIN_REDIRECT_URI

        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base_url = "https://api.linkedin.com/v2"
        
        self.access_token = None
        self.user_urn = None

        if not self.client_id or not self.client_secret:
            print("⚠️  Warning: LinkedIn credentials not found in config.py.")
        else:
            print("✅ LinkedIn Service initialized.")

    # --- NEW: A single source of truth for authentication status ---
    def is_authenticated(self) -> bool:
        """Returns True if the service has a valid access token."""
        return self.access_token is not None

    def generate_post_package(self, niche, topic):
        # (This function remains unchanged)
        print(f"LINKEDIN: Generating content for topic: '{topic}'...")
        try:
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="LinkedIn"
            )
            if not content_data: raise Exception("Failed to generate text content.")
            image_prompt = content_data.get("image_prompt")
            print("LINKEDIN: Generating image for the post...")
            image_paths = self.image_generator._generate_images_with_stability([image_prompt])
            if not image_paths: raise Exception("Failed to generate an image.")
            return {
                "post_text": f"{content_data.get('post_text')}\n\n{' '.join(content_data.get('hashtags', []))}",
                "image_path": image_paths[0]
            }
        except Exception as e:
            print(f"   - ❌ Error in generate_post_package (LinkedIn): {e}")
            return None

    def generate_auth_url(self):
        # (This function remains unchanged)
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': 'a_random_state_string_for_security',
            'scope': 'openid profile w_member_social'
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code):
        # (This function remains unchanged)
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()
            self.access_token = response.json().get('access_token')
            if self.access_token:
                return {"success": True}
            return {"success": False, "message": "Access token not found in response."}
        except requests.RequestException as e:
            error_details = e.response.json() if e.response else str(e)
            print(f"   - ❌ LinkedIn token exchange failed: {error_details}")
            return {"success": False, "message": f"API Error: {error_details}"}

    def fetch_user_info(self):
        # (This function remains unchanged)
        if not self.access_token: return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.api_base_url}/userinfo", headers=headers, timeout=10)
            response.raise_for_status()
            user_data = response.json()
            self.user_urn = f"urn:li:person:{user_data['sub']}"
            print(f"✅ Fetched LinkedIn user URN: {self.user_urn}")
            return True
        except Exception as e:
            print(f"   - ❌ Error fetching LinkedIn user info: {e}")
            return False

    def publish_post(self, post_data):
        # (This function and its helpers remain unchanged)
        if not self.is_authenticated() or not self.user_urn:
            return {"success": False, "message": "Authentication required. Cannot publish post."}
        # ... rest of the function