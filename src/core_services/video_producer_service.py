# src/core_services/video_producer_service.py

import os
import random
import io
import re
import requests
from datetime import datetime
from urllib.parse import quote_plus
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop

from src.config import STABILITY_AI_API_KEY, DATA_PATH, ASSETS_PATH, MUSIC_ASSETS_PATH
from src.utils.exceptions import InterruptedException

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

# Note: Google Cloud TTS is removed for now to simplify dependencies.
# It can be re-added later if gTTS is insufficient.

class VideoProducerService:
    """
    Handles the entire video creation pipeline: generating/fetching images,
    synthesizing audio, and combining them into a final video file.
    """
    def __init__(self, kill_switch):
        self.kill_switch = kill_switch
        self.fps = 24

        # Define dynamic paths based on the DATA_PATH environment variable
        self.images_path = os.path.join(DATA_PATH, "generated_images")
        self.audio_path = os.path.join(DATA_PATH, "generated_audio")
        self.videos_path = os.path.join(DATA_PATH, "generated_videos")
        os.makedirs(self.images_path, exist_ok=True)
        os.makedirs(self.audio_path, exist_ok=True)
        os.makedirs(self.videos_path, exist_ok=True)

        # Stability AI configuration
        self.stability_api_key = STABILITY_AI_API_KEY
        self.stability_api_url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
        if not self.stability_api_key or "sk-" not in self.stability_api_key:
            print("⚠️  Warning: STABILITY_AI_API_KEY not found or invalid.")
        else:
            print("✅ Stability AI client configured.")

        # Fallback TTS configuration
        if gTTS:
            print("✅ gTTS (fallback TTS) is available.")
        else:
            print("❌ Critical Error: gTTS library not installed. Audio generation will fail.")

        print("✅ Video Producer Service initialized.")


    def _search_and_download_images(self, search_queries):
        image_paths = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        print(f"🔎 Starting web search for {len(search_queries)} image(s)...")
        for i, query in enumerate(search_queries):
            if self.kill_switch.is_set(): raise InterruptedException("Image download cancelled.")
            try:
                print(f"   - Searching for: '{query}'")
                search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()
                image_urls = re.findall(r'src="(https://[^"]+)"', response.text)
                
                for img_url in image_urls:
                    if img_url.endswith(('.jpg', '.png', '.jpeg')):
                        try:
                            img_response = requests.get(img_url, headers=headers, timeout=5)
                            if img_response.status_code == 200:
                                img = Image.open(io.BytesIO(img_response.content)).convert('RGB')
                                filename = f"web_image_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                filepath = os.path.join(self.images_path, filename)
                                img.save(filepath)
                                image_paths.append(filepath)
                                print(f"   ✓ Image downloaded and saved to: {filepath}")
                                break 
                        except Exception:
                            continue
            except Exception as e:
                print(f"   - ❌ Error during web search for '{query}': {e}")
        return image_paths

    def _generate_images_with_stability(self, prompts, aspect_ratio="16:9"):
        if not self.stability_api_key:
            print("ℹ️ AI generation skipped: API key not configured. Trying web search as fallback...")
            return self._search_and_download_images(prompts)

        image_paths = []
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

                img = Image.open(io.BytesIO(response.content))
                filename = f"ai_image_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join(self.images_path, filename)
                img.save(filepath)
                image_paths.append(filepath)
                print(f"   🖼️  Image saved successfully: {filepath}")
            except Exception as e:
                print(f"   - ❌ Error generating image: {e}")
        return image_paths

    def produce_complete_video(self, content, voice_type="female_voice", aspect_ratio="16:9", image_source="ai_generated"):
        try:
            if self.kill_switch.is_set(): raise InterruptedException("Operation cancelled before start.")
            
            print(f"\n🎬 Starting video production (Aspect: {aspect_ratio}, Images: {image_source})...")
            target_resolution = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
            
            script_data = content.get('script')
            if not script_data: raise ValueError("Critical Error: Script is empty or missing.")
            script_for_audio = "\n".join(str(v) for v in script_data.values()) if isinstance(script_data, dict) else str(script_data)
            
            audio_file = self.generate_script_audio(script_for_audio, voice_type)
            if not audio_file: raise ValueError("Audio generation failed.")
            if self.kill_switch.is_set(): raise InterruptedException("Operation cancelled after audio generation.")
            
            main_audio = AudioFileClip(audio_file)
            print(f"⏱️  Audio duration: {main_audio.duration:.2f} seconds")
            
            image_prompts = content.get('image_prompts', [])
            image_paths = self._generate_images_with_stability(image_prompts, aspect_ratio) if image_source == "ai_generated" else self._search_and_download_images(image_prompts)
            if self.kill_switch.is_set(): raise InterruptedException("Operation cancelled after image generation.")

            intro = self._create_intro_clip(duration=3, resolution=target_resolution)
            content_clips = self._create_content_clips_from_images(image_paths, main_audio.duration, resolution=target_resolution)
            outro = self._create_outro_clip(duration=5, resolution=target_resolution)

            final_content_video = concatenate_videoclips(content_clips, method="compose").set_audio(main_audio)
            final_video = concatenate_videoclips([intro, final_content_video, outro])
            final_video_with_music = self._add_background_music(final_video)
            
            output_filename = os.path.join(self.videos_path, f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            
            if self.kill_switch.is_set(): raise InterruptedException("Operation cancelled before final render.")
            
            print(f"💾 Rendering final video to: {output_filename}")
            final_video_with_music.write_videofile(output_filename, fps=self.fps, codec='libx264', audio_codec='aac', threads=4)
            
            return {"filename": output_filename, "content": content}
        
        except InterruptedException as e:
            print(f"   - 🛑 VideoProducer acknowledging kill signal: {e}")
            raise e
        except Exception as e:
            import traceback
            print(f"❌ CATASTROPHIC ERROR during video production: {e}")
            traceback.print_exc()
            return None

    def _clean_script_text(self, script_text):
        if isinstance(script_text, list): script_text = "\n".join(script_text)
        lines = script_text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip() and not (line.startswith('#') or line.startswith('**'))]
        return ' '.join(cleaned_lines)

    def generate_script_audio(self, script_text, voice_type="male_voice"):
        if self.kill_switch.is_set(): raise InterruptedException("Audio generation cancelled.")
        cleaned_script = self._clean_script_text(script_text)
        if not cleaned_script: return None
        
        filename = f"script_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(self.audio_path, filename)
        
        print(f"🗣️ Generating audio using gTTS fallback...")
        try:
            if gTTS:
                tts = gTTS(text=cleaned_script, lang='en', slow=False)
                tts.save(filepath)
                print(f"   🔊 Audio file generated with gTTS: {filepath}")
                return filepath
            else:
                print("   - ❌ No TTS client available (gTTS not installed).")
                return None
        except Exception as e:
            print(f"   - ❌ Error during gTTS audio synthesis: {e}")
            return None

    def _create_intro_clip(self, duration, resolution):
        logo_path = os.path.join(ASSETS_PATH, "visual_identity/intro_logo.png")
        background = ColorClip(size=resolution, color=(13, 17, 23), duration=duration)
        if os.path.exists(logo_path):
            logo_height = int(resolution[1] * 0.2)
            logo = ImageClip(logo_path).set_duration(duration).resize(height=logo_height).set_position('center')
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
            if self.kill_switch.is_set(): raise InterruptedException("Video clip assembly cancelled.")
            try:
                clip = ImageClip(image_path).set_duration(segment_duration).set_position('center')
                # Simple scale and crop to fit target resolution
                clip_resized = clip.resize(height=resolution[1]) if clip.size[1] < resolution[1] else clip.resize(width=resolution[0])
                final_clip = CompositeVideoClip([clip_resized.set_position('center')], size=resolution)
                clips.append(final_clip)
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

            final_audio = CompositeAudioClip([video_clip.audio, music])
            return video_clip.set_audio(final_audio)
        except Exception as e:
            print(f"   - ⚠️ Warning: Could not add background music: {e}")
            return video_clip
