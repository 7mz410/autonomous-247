# src/platform_services/youtube_service.py

import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.config import DATA_PATH

class YouTubeService:
    """
    Handles all interactions with the YouTube API, from authentication
    to video uploading.
    """
    def __init__(self, content_generator, video_producer):
        self.content_generator = content_generator
        self.video_producer = video_producer
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        # Paths for credential and token files must be in the persistent data directory
        self.credentials_file = os.path.join(DATA_PATH, 'youtube_credentials.json')
        self.token_file = os.path.join(DATA_PATH, 'youtube_token.pickle')
        
        self.default_video_settings = {
            'privacy_status': 'private', # Default to private to allow for review
            'category_id': '28', # Science & Technology
            'default_language': 'en',
            'default_audio_language': 'en'
        }
        self.youtube_api = self.authenticate()

    def create_and_upload_video(self, niche, topic, voice_type="female_voice", upload=True, image_source="ai_generated", auto_search_context=False):
        """
        Orchestrates the entire pipeline for creating and optionally uploading a YouTube video.
        """
        print(f"\nYOUTUBE_SERVICE: Starting video pipeline for topic '{topic}'...")
        try:
            print("   - Step 1/3: Generating video content package...")
            content_package = self.content_generator.generate_complete_video_content(
                topic=topic, niche=niche, auto_search_context=auto_search_context
            )
            if not content_package:
                raise Exception("Failed to generate content package.")
            
            print("   - Step 2/3: Producing video from content package...")
            video_info = self.video_producer.produce_complete_video(
                content_package, voice_type, image_source=image_source
            )
            if not video_info or 'filename' not in video_info:
                raise Exception("Video production failed or was cancelled.")

            if upload:
                print("   - Step 3/3: Uploading video to YouTube...")
                if self.youtube_api:
                    self.upload_video(
                        video_file=video_info['filename'],
                        title=content_package.get('title', 'Untitled'),
                        description=content_package.get('description', ''),
                        tags=content_package.get('tags', [])
                    )
                else:
                    print("   - ⚠️ YouTube upload skipped due to authentication failure.")
            
            return {"success": True, "path": video_info.get('filename')}

        except Exception as e:
            print(f"   - ❌ Error in create_and_upload_video (YouTube): {e}")
            return {"success": False, "message": str(e)}

    def authenticate(self):
        """
        Authenticates with the YouTube API using OAuth 2.0 credentials.
        Handles token loading, validation, and refreshing.
        """
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("   - Refreshing expired YouTube token...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"   - ❌ Failed to refresh token: {e}. Manual authentication may be required.")
                    creds = None # Force re-authentication
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Error: Credentials file '{self.credentials_file}' not found. Cannot authenticate.")
                    return None
                print("   - Performing first-time YouTube authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                # Note: run_local_server will only work in a local environment.
                # For production, a pre-generated token file must be provided.
                creds = flow.run_local_server(port=0)

            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        print("✅ YouTube API service is ready.")
        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, video_file, title, description, tags=None, privacy_status=None, category_id=None):
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
        except HttpError as e:
            print(f"   - ❌ An HTTP error occurred during upload: {e.resp.status} {e.content}")
            return None
        except Exception as e:
            print(f"   - ❌ An unexpected error occurred during upload: {e}")
            return None
