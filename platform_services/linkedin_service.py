# src/platform_services/linkedin_service.py

import requests
from  urllib.parse import urlencode
from config import LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI

class LinkedInService:
    """
    Handles the entire workflow for LinkedIn, including OAuth2 authentication
    and content publishing.
    """
    def __init__(self, content_generator, image_generator):
        self.content_generator = content_generator
        self.image_generator = image_generator
        
        # --- Critical Configuration ---
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.redirect_uri = LINKEDIN_REDIRECT_URI # Dynamically set for dev vs. prod

        # --- LinkedIn API Endpoints ---
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base_url = "https://api.linkedin.com/v2"
        
        # --- State Variables ---
        self.access_token = None
        self.user_urn = None

        if not self.client_id or not self.client_secret:
            print("⚠️  Warning: LinkedIn credentials not found in config.py.")
        else:
            print("✅ LinkedIn Service initialized.")

    def generate_post_package(self, niche, topic):
        """
        Creates a complete package (text, hashtags, image) for a LinkedIn post.
        Delegates generation to core services.
        """
        print(f"LINKEDIN: Generating content for topic: '{topic}'...")
        try:
            content_data = self.content_generator.generate_social_post_content(
                topic=topic, niche=niche, platform="LinkedIn"
            )
            if not content_data:
                raise Exception("Failed to generate text content.")

            image_prompt = content_data.get("image_prompt")
            print("LINKEDIN: Generating image for the post...")
            # Note: The image generator now returns a list, we take the first one.
            image_paths = self.image_generator._generate_images_with_stability([image_prompt])
            if not image_paths:
                raise Exception("Failed to generate an image.")
            
            return {
                "post_text": f"{content_data.get('post_text')}\n\n{' '.join(content_data.get('hashtags', []))}",
                "image_path": image_paths[0]
            }
        except Exception as e:
            print(f"   - ❌ Error in generate_post_package (LinkedIn): {e}")
            return None

    def generate_auth_url(self):
        """Generates the authorization URL for the user to click."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': 'a_random_state_string_for_security', # Should be dynamically generated per user
            'scope': 'openid profile w_member_social'
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code):
        """Exchanges the authorization code from  the redirect for an access token."""
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
        # ... (This part of the code is complex and seems correct, no changes needed to the logic)
        # It correctly uses the image_path provided to it.
        # The following is the original code, confirmed to be okay.
        if not self.access_token or not self.user_urn:
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
