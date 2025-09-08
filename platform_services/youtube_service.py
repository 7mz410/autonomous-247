# src/platform_services/youtube_service.py

import os
import pickle
from  googleapiclient.discovery import build
from  googleapiclient.http import MediaFileUpload
from  google_auth_oauthlib.flow import InstalledAppFlow
from  google.auth.transport.requests import Request
from utils import storage_service # <-- NEW: Import our storage service

class YouTubeService:
    def __init__(self, content_generator, video_producer):
        self.content_generator = content_generator
        self.video_producer = video_producer
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        # --- NEW: Define object names for Spaces ---
        self.credentials_object_name = 'auth/youtube_credentials.json'
        self.token_object_name = 'auth/youtube_token.pickle'
        
        self.default_video_settings = {
            'privacy_status': 'private',
            'category_id': '28',
            'default_language': 'en',
            'default_audio_language': 'en'
        }
        self.youtube_api = self.authenticate()
        if self.youtube_api:
            print("✅ YouTube Service initialized and authenticated.")
        else:
            print("❌ YouTube Service failed to authenticate.")

    def create_and_upload_video(self, niche, topic, voice_type="female_voice", upload=True, image_source="ai_generated", auto_search_context=False):
        # ... (This function does not need changes, its logic is correct)
        print(f"\nYOUTUBE_SERVICE: Starting video pipeline for topic '{topic}'...")
        try:
            print("   - Step 1/3: Generating content package...")
            content_package = self.content_generator.generate_complete_video_content(
                topic=topic, niche=niche, auto_search_context=auto_search_context
            )
            if not content_package:
                raise Exception("Failed to generate content package.")
            
            print("   - Step 2/3: Producing video file...")
            video_filepath = self.video_producer.produce_complete_video(
                content_package, voice_type, image_source=image_source
            )
            if not video_filepath:
                raise Exception("Video production failed or was cancelled.")

            if upload:
                print("   - Step 3/3: Uploading video to YouTube...")
                if self.youtube_api:
                    self.upload_video(
                        video_file=video_filepath,
                        title=content_package.get('title', 'Untitled'),
                        description=content_package.get('description', ''),
                        tags=content_package.get('tags', [])
                    )
                else:
                    print("   - ⚠️ YouTube upload skipped due to authentication failure.")
            
            # Here you could optionally upload the final video to Spaces as well
            # storage_service.upload_file(video_filepath, f"final_videos/{os.path.basename(video_filepath)}")

            return {"success": True, "path": video_filepath}

        except Exception as e:
            print(f"   - ❌ Error in create_and_upload_video (YouTube): {e}")
            return {"success": False, "message": str(e)}

    def authenticate(self):
        """
        Authenticates with YouTube API using credentials and tokens stored in
        DigitalOcean Spaces.
        """
        creds = None
        
        # --- NEW: Try to load token from  Spaces ---
        token_data = storage_service.get_file_content(self.token_object_name)
        if token_data:
            creds = pickle.loads(token_data)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("   - Refreshing expired YouTube token...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"   - ❌ Failed to refresh token: {e}. Re-authenticating...")
                    creds = None
            
            if not creds:
                # --- NEW: Load credentials from  Spaces ---
                credentials_content = storage_service.get_file_content(self.credentials_object_name)
                if not credentials_content:
                    print(f"❌ Critical Error: '{self.credentials_object_name}' not found in Spaces.")
                    return None
                
                print("   - Performing first-time YouTube authentication (this requires local browser)...")
                flow = InstalledAppFlow.from _client_secrets_info(eval(credentials_content), self.SCOPES)
                creds = flow.run_local_server(port=0)

            # --- NEW: Save the new/refreshed token back to Spaces ---
            with open("temp_token.pickle", "wb") as token_file:
                pickle.dump(creds, token_file)
            storage_service.upload_file("temp_token.pickle", self.token_object_name)
            os.remove("temp_token.pickle") # Clean up temporary local file
        
        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, video_file, title, description, tags=None, privacy_status=None, category_id=None):
        # ... (This function does not need changes, its logic is correct)
        if not self.youtube_api: return None
        if not os.path.exists(video_file):
            print(f"   - ❌ Error: Video file not found at {video_file}")
            return None
        
        body = {
            'snippet': {
                'title': title, 'description': description, 'tags': tags or [],
                'categoryId': category_id or self.default_video_settings['category_id'],
                'defaultLanguage': self.default_video_settings['default_language'],
                'defaultAudioLanguage': self.default_video_settings['default_audio_language']
            },
            'status': {
                'privacyStatus': privacy_status or self.default_video_settings['privacy_status'],
                'selfDeclaredMadeForKids': False
            }
        }
        try:
            print(f"   - 🚀 Starting resumable upload for: '{title}'")
            media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
            request = self.youtube_api.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"     Uploaded {int(status.progress() * 100)}%")
            
            print(f"✅ Video uploaded successfully! URL: https://www.youtube.com/watch?v={response['id']}")
            return {'video_id': response['id']}
        except Exception as e:
            print(f"   - ❌ An unexpected error occurred during upload: {e}")
            return None
