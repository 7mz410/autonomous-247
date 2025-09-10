# src/core_services/content_generator_service.py

import os
import json
import tempfile
from datetime import datetime
from typing import TYPE_CHECKING
from utils import storage_service
from config import OPENAI_API_KEY

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# This allows for type hinting without causing circular import errors.
if TYPE_CHECKING:
    from core_services.web_search_service import WebSearchService

class ContentGeneratorService:
    """
    Handles all interactions with AI models for content creation.
    MERGED: Now includes AI-powered astrology generation and general content creation.
    """
    
    # --- FIX: The constructor now takes web_search_service again AND initializes OpenAI client ---
    def __init__(self, web_search_service: 'WebSearchService'):
        self.web_search_service = web_search_service
        
        if not OPENAI_API_KEY or not OpenAI:
            self.client = None
            print("❌ Critical Error: OPENAI_API_KEY not found or openai library not installed.")
        else:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ OpenAI client configured successfully.")
            except Exception as e:
                self.client = None
                print(f"❌ Critical Error configuring OpenAI client: {e}")

    def _generate_content_with_openai(self, prompt: str, system_message: str = "You are a helpful assistant.") -> str | None:
        """A centralized private method to interact with the OpenAI API."""
        if not self.client:
            print("   - ❌ OpenAI client not available. Cannot generate content.")
            return None
        
        print(f"   - 🤖 Calling LLM with prompt: '{prompt[:60]}...'")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Error during OpenAI API call: {e}")
            return None

    # --- NEW: AI-powered astrology data generation ---
    def generate_astrology_data(self, zodiac_sign: str) -> dict | None:
        print(f"   - 🔮 Generating AI astrological data for {zodiac_sign}...")
        prompt = f"""
        Generate a fictional but believable daily horoscope for the zodiac sign: {zodiac_sign.capitalize()}.
        The output MUST be a single, valid JSON object with these exact keys:
        - "description": A 1-2 sentence inspiring horoscope.
        - "mood": A single word describing the primary mood.
        - "lucky_number": A random number between 1 and 100.
        - "color": A lucky color for the day.
        """
        system_msg = "You are a creative, insightful, and positive astrologer."
        json_string = self._generate_content_with_openai(prompt, system_message=system_msg)
        if not json_string: return None
        try:
            data = json.loads(json_string)
            data['sign'] = zodiac_sign
            return data
        except Exception as e:
            print(f"   - ❌ Failed to parse astrology data for {zodiac_sign}: {e}")
            return None

    # --- UPDATED: AI-powered astrology caption generation ---
    def create_astrology_caption(self, astro_data: dict) -> str:
        print("   - ✍️ Crafting an engaging astrology caption...")
        prompt = f"""
        You have this data for {astro_data.get('sign', 'a zodiac sign')}:
        - Vibe: {astro_data.get('description')}
        - Mood: {astro_data.get('mood')}
        - Lucky Color: {astro_data.get('color')}
        Transform this into a short, beautiful Instagram caption and provide hashtags.
        The entire output MUST be a single, valid JSON object with keys "caption" and "hashtags".
        """
        system_msg = "You are a mystical and positive social media manager."
        json_string = self._generate_content_with_openai(prompt, system_message=system_msg)
        if not json_string:
            return f"{astro_data.get('description')}\n\n#astrology #horoscope #{astro_data.get('sign')}"
        try:
            data = json.loads(json_string)
            final_caption = data.get('caption', astro_data.get('description'))
            hashtags_str = " ".join(data.get('hashtags', []))
            return f"{final_caption}\n\n{hashtags_str}"
        except Exception as e:
            print(f"   - ❌ Error generating caption: {e}. Falling back to default.")
            return f"{astro_data.get('description')}\n\n#astrology #horoscope #{astro_data.get('sign')}"

    # --- RE-ADDED: Method for YouTube videos ---
    def generate_complete_video_content(self, topic, niche="Technology", auto_search_context=False):
        context = None
        if auto_search_context and self.web_search_service:
            context = self.web_search_service.search_and_extract_context(topic)
            if not context:
                print("   - ⚠️ Proceeding without web context. Quality may be lower.")

        prompt = f"You are a YouTube scriptwriter for a '{niche}' channel. Generate a content package for a video on: '{topic}'."
        if context:
            prompt += f"\n\nCONTEXT:\n---\n{context[:4000]}\n---"
        prompt += '\nThe final output MUST be a single, valid JSON object with keys: "title", "description", "tags", "script", "image_prompts".'
        
        json_string = self._generate_content_with_openai(prompt, "You are an expert-level YouTube content creator.")
        if not json_string: raise Exception("AI service returned an empty response.")
        
        try:
            content_data = json.loads(json_string)
            return content_data
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from AI. Error: {e}")

    # --- RE-ADDED: Method for LinkedIn/Instagram posts ---
    def generate_social_post_content(self, topic: str, niche: str, platform: str) -> dict | None:
        prompt = f"You are a social media expert for the '{niche}' niche. Generate a content package for a {platform} post on: '{topic}'. The final output MUST be a single, valid JSON object with keys: 'post_text', 'hashtags', 'image_prompt'."
        
        json_string = self._generate_content_with_openai(prompt, f"You are a social media expert for {platform}.")
        if json_string:
            try:
                return json.loads(json_string)
            except json.JSONDecodeError:
                return None
        return None```
