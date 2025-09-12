# src/platform_services/linkedin_service.py

import requests
from urllib.parse import urlencode
from config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core_services.content_generator_service import ContentGeneratorService
    from core_services.image_post_generator_service import ImagePostGeneratorService
    from core_services.video_producer_service import VideoProducerService

class LinkedInService:
    def __init__(self, content_generator: 'ContentGeneratorService', image_generator: 'VideoProducerService', image_post_generator: 'ImagePostGeneratorService'):
        self.content_generator = content_generator
        self.image_generator = image_generator
        self.image_post_generator = image_post_generator
        
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.redirect_uri = LINKEDIN_REDIRECT_URI

        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base_url = "https://api.linkedin.com/v2"
        
        self.access_token = None
        self.user_urn = None

        if not self.client_id or not self.client_secret:
            print("⚠️  Warning: LinkedIn credentials not found.")
        else:
            print("✅ LinkedIn Service initialized (Professional Method).")

    def is_authenticated(self) -> bool:
        return self.access_token is not None

    def generate_post_package(self, niche, topic):
        print(f"LINKEDIN: Generating professional post for topic: '{topic}'...")
        try:
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="LinkedIn"
            )
            if not content_data:
                raise Exception("Failed to generate text content from AI.")

            background_prompt = content_data.get("background_image_prompt", f"A professional, clean background for a post about {niche}")
            print(f"LINKEDIN: Generating clean background image with prompt: '{background_prompt}'")
            
            image_paths = self.image_generator._generate_images_with_stability([background_prompt], aspect_ratio="1:1")
            if not image_paths:
                raise Exception("Failed to generate a background image.")
            
            background_image_path = image_paths[0]
            post_text_content = content_data.get("post_text")
            final_caption_for_upload = f"{post_text_content}\n\n{' '.join(content_data.get('hashtags', []))}"
            
            print("LINKEDIN: Overlaying clean text onto the background image...")
            final_post_url = self.image_post_generator.create_post_image(
                base_image_path=background_image_path,
                text=post_text_content,
                title=topic.capitalize()
            )

            if not final_post_url:
                raise Exception("Failed to create the final post image.")
            
            return {
                "url": final_post_url,
                "caption": final_caption_for_upload
            }
        except Exception as e:
            print(f"   - ❌ Error in generate_post_package (LinkedIn): {e}")
            return None

    # --- FULL, UNABBREVIATED AUTHENTICATION FUNCTIONS ---

    def generate_auth_url(self):
        """Generates the authorization URL for the user to click."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': 'a_random_state_string_for_security',
            'scope': 'openid profile w_member_social'
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code):
        """Exchanges the authorization code from the redirect for an access token."""
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
        """Fetches the authenticated user's URN ('sub' field), required for posting."""
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
        """Publishes the given post data (text and image) to LinkedIn."""
        if not self.is_authenticated() or not self.user_urn:
            return {"success": False, "message": "Authentication required. Cannot publish post."}
        post_text = post_data.get("post_text")
        image_path = post_data.get("image_path")
        if not all([post_text, image_path]):
            return {"success": False, "message": "Post data is incomplete."}

        print("LINKEDIN: Step 1/3 - Registering image...")
        upload_url, asset_id = self._register_image()
        if not upload_url: return {"success": False, "message": "Failed to register image."}

        print("LINKEDIN: Step 2/3 - Uploading image file...")
        if not self._upload_image(upload_url, image_path): return {"success": False, "message": "Failed to upload image."}

        print("LINKEDIN: Step 3/3 - Creating the final post...")
        return self._create_ugc_post(post_text, asset_id)

    def _register_image(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        body = {"registerUploadRequest": {"recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],"owner": self.user_urn,"serviceRelationships": [{"relationshipType": "OWNER","identifier": "urn:li:userGeneratedContent"}]}}
        try:
            response = requests.post(f"{self.api_base_url}/assets?action=registerUpload", headers=headers, json=body)
            response.raise_for_status()
            data = response.json()['value']
            return data['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl'], data['asset']
        except Exception as e:
            print(f"   - ❌ LinkedIn Error (Registering Image): {e}")
            return None, None

    def _upload_image(self, upload_url, image_path):
        try:
            with open(image_path, 'rb') as f:
                response = requests.put(upload_url, data=f, headers={"Authorization": f"Bearer {self.access_token}"})
            response.raise_for_status()
            return response.status_code == 201
        except Exception as e:
            print(f"   - ❌ LinkedIn Error (Uploading Image): {e}")
            return False

    def _create_ugc_post(self, post_text, asset_id):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        post_body = {"author": self.user_urn,"lifecycleState": "PUBLISHED","specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": post_text},"shareMediaCategory": "IMAGE","media": [{"status": "READY", "media": asset_id}]}},"visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}
        try:
            response = requests.post(f"{self.api_base_url}/ugcPosts", headers=headers, json=post_body)
            response.raise_for_status()
            print("✅ Post published successfully to LinkedIn!")
            return {"success": True, "data": response.json()}
        except Exception as e:
            print(f"   - ❌ LinkedIn Error (Creating Post): {e}")
            return {"success": False, "message": "Failed to create the final post."}