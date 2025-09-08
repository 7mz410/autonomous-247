# src/core_services/video_producer_service.py

import os
import random
import io
import re
import requests
import tempfile
from datetime import datetime
from PIL import Image
from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop

from src.config import STABILITY_AI_API_KEY, ASSETS_PATH, MUSIC_ASSETS_PATH
from src.utils.exceptions import InterruptedException
from src.utils import storage_service

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

class VideoProducerService:
    def __init__(self, kill_switch):
        self.kill_switch = kill_switch
        self.fps = 24

        # --- No longer creating local directories, using temp files instead ---

        self.stability_api_key = STABILITY_AI_API_KEY
        self.stability_api_url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
        if not self.stability_api_key or "sk-" not in self.stability_api_key:
            print("⚠️  Warning: STABILITY_AI_API_KEY not found or invalid.")
        else:
            print("✅ Stability AI client configured.")

        if gTTS:
            print("✅ gTTS (fallback TTS) is available.")
        else:
            print("❌ Critical Error: gTTS library not installed. Audio generation will fail.")

        print("✅ Video Producer Service initialized.")

    def _generate_images_with_stability(self, prompts, aspect_ratio="16:9"):
        if not self.stability_api_key:
            print("ℹ️ AI generation skipped: API key not configured.")
            return []

        local_image_paths = []
        print(f"🤖 Generating {len(prompts)} image(s) from Stability AI...")
        for i, prompt in enumerate(prompts):
            if self.kill_switch.is_set(): raise InterruptedException("AI Image generation cancelled.")
            
            full_prompt = f"concept art for a youtube video, {prompt}, cinematic, ultra realistic, 8k"
            print(f"   - Prompting: '{prompt[:50]}...'")
            try:
                headers = {"authorization": f"Bearer {self.stability_api_key}", "accept": "image/*"}
                files = {"prompt": (None, full_prompt), "output_format": (None, "png"), "aspect_ratio": (None, aspect_ratio)}
                response = requests.post(self.stability_api_url, headers=headers, files=files, timeout=30)
                response.raise_for_status()

                # --- NEW: Save to a temporary local file ---
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    temp_file.write(response.content)
                    local_path = temp_file.name
                
                # --- NEW: Upload the temporary file to Spaces ---
                object_name = f"generated_images/image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
                storage_service.upload_file(local_path, object_name)
                
                local_image_paths.append(local_path)
                print(f"   🖼️  Image generated, saved locally to {local_path}, and uploaded to Spaces.")

            except Exception as e:
                print(f"   - ❌ Error generating image: {e}")
        return local_image_paths

    def produce_complete_video(self, content, voice_type="female_voice", aspect_ratio="16:9", image_source="ai_generated"):
        local_temp_files = [] # Keep track of all local files to clean up
        try:
            if self.kill_switch.is_set(): raise InterruptedException("Operation cancelled before start.")
            
            print(f"\n🎬 Starting video production...")
            target_resolution = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
            
            script_data = content.get('script')
            if not script_data: raise ValueError("Critical Error: Script is empty.")
            script_for_audio = "\n".join(str(v) for v in script_data.values()) if isinstance(script_data, dict) else str(script_data)
            
            audio_file_path = self.generate_script_audio(script_for_audio, voice_type)
            if not audio_file_path: raise ValueError("Audio generation failed.")
            local_temp_files.append(audio_file_path)
            
            main_audio = AudioFileClip(audio_file_path)
            
            image_prompts = content.get('image_prompts', [])
            image_paths = self._generate_images_with_stability(image_prompts, aspect_ratio)
            local_temp_files.extend(image_paths)

            intro = self._create_intro_clip(duration=3, resolution=target_resolution)
            content_clips = self._create_content_clips_from_images(image_paths, main_audio.duration, resolution=target_resolution)
            outro = self._create_outro_clip(duration=5, resolution=target_resolution)

            final_content_video = concatenate_videoclips(content_clips, method="compose").set_audio(main_audio)
            final_video = concatenate_videoclips([intro, final_content_video, outro])
            final_video_with_music = self._add_background_music(final_video)
            
            # --- NEW: Save final video to a temporary local file ---
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                output_filepath = temp_file.name

            print(f"💾 Rendering final video to temporary path: {output_filepath}")
            final_video_with_music.write_videofile(output_filepath, fps=self.fps, codec='libx264', audio_codec='aac', threads=4)
            
            # --- NEW: Upload the final video to Spaces ---
            object_name = f"generated_videos/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            storage_service.upload_file(output_filepath, object_name)

            return output_filepath # Return the local path for YouTubeService to use
        
        except Exception as e:
            import traceback
            print(f"❌ CATASTROPHIC ERROR during video production: {e}")
            traceback.print_exc()
            return None
        finally:
            # --- NEW: Clean up all temporary local files ---
            print("   - Cleaning up temporary local files...")
            for f in local_temp_files:
                if os.path.exists(f):
                    os.remove(f)

    def generate_script_audio(self, script_text, voice_type="male_voice"):
        cleaned_script = "".join(str(v) for v in script_text.values()) if isinstance(script_text, dict) else str(script_text)
        if not cleaned_script: return None
        
        try:
            if gTTS:
                tts = gTTS(text=cleaned_script, lang='en', slow=False)
                # --- NEW: Save to a temporary local file ---
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    filepath = temp_file.name
                    tts.save(filepath)

                # --- NEW: Upload the audio file to Spaces ---
                object_name = f"generated_audio/audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                storage_service.upload_file(filepath, object_name)

                print(f"   🔊 Audio generated, saved locally to {filepath}, and uploaded to Spaces.")
                return filepath
            else:
                print("   - ❌ No TTS client available.")
                return None
        except Exception as e:
            print(f"   - ❌ Error during gTTS audio synthesis: {e}")
            return None
            
    # --- Helper methods (no changes needed) ---
    def _create_intro_clip(self, duration, resolution):
        logo_path = os.path.join(ASSETS_PATH, "visual_identity/intro_logo.png")
        background = ColorClip(size=resolution, color=(13, 17, 23), duration=duration)
        if os.path.exists(logo_path):
            logo = ImageClip(logo_path).set_duration(duration).resize(height=int(resolution[1] * 0.2)).set_position('center')
            return CompositeVideoClip([background, logo])
        return background

    def _create_outro_clip(self, duration, resolution):
        outro_path = os.path.join(ASSETS_PATH, "visual_identity/outro_card.png")
        if os.path.exists(outro_path):
            return ImageClip(outro_path).set_duration(duration).resize(resolution)
        return ColorClip(size=resolution, color=(13, 17, 23), duration=duration)

    def _create_content_clips_from_images(self, images, audio_duration, resolution):
        if not images:
            return [ColorClip(size=resolution, color=(0, 0, 0), duration=audio_duration)]
        clips = []
        segment_duration = audio_duration / len(images)
        for image_path in images:
            try:
                clip = ImageClip(image_path).set_duration(segment_duration)
                final_clip = clip.resize(height=resolution[1]).set_position(('center', 'center'))
                clips.append(CompositeVideoClip([final_clip], size=resolution))
            except Exception as e:
                print(f"   - ⚠️ Warning: Could not process image {image_path}: {e}")
        return clips

    def _add_background_music(self, video_clip, music_volume=0.1):
        try:
            music_files = [os.path.join(MUSIC_ASSETS_PATH, f) for f in os.listdir(MUSIC_ASSETS_PATH) if f.lower().endswith(('.mp3', '.wav'))]
            if not music_files: return video_clip
            music_path = random.choice(music_files)
            music = AudioFileClip(music_path).volumex(music_volume)
            if music.duration > video_clip.duration:
                music = music.subclip(0, video_clip.duration)
            else:
                music = audio_loop(music, duration=video_clip.duration)
            return video_clip.set_audio(CompositeAudioClip([video_clip.audio, music]))
        except Exception as e:
            print(f"   - ⚠️ Warning: Could not add background music: {e}")
            return video_clip
