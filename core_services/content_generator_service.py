# src/core_services/content_generator_service.py

import json
import os
import tempfile
from datetime import datetime
from typing import TYPE_CHECKING
from utils import storage_service

# This block allows for type hinting without causing circular import errors.
# It's a best practice for complex applications like this.
if TYPE_CHECKING:
    from core_services.web_search_service import WebSearchService

# NOTE: You would have an OpenAI client import here, for example:
# from openai import OpenAI

class ContentGeneratorService:
    """
    Handles all interactions with AI models for content creation,
    including video scripts, social media posts, and captions.
    """
    
    # --- FIX: Added the __init__ constructor which was missing. ---
    def __init__(self, web_search_service: 'WebSearchService'):
        self.web_search_service = web_search_service
        # --- The OpenAI client would be initialized here ---
        # self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Content Generator Service initialized.")

    def _generate_content_with_openai(self, prompt: str) -> str | None:
        """
        A private helper method to interact with the OpenAI API.
        This is a placeholder for your actual OpenAI API call logic.
        """
        print(f"   - 🤖 Calling LLM with prompt: '{prompt[:60]}...'")
        try:
            # --- THIS IS WHERE YOUR API CALL WOULD GO ---
            # response = self.client.chat.completions.create(
            #     model="gpt-4o",
            #     messages=[{"role": "system", "content": prompt}],
            #     response_format={"type": "json_object"}
            # )
            # return response.choices[0].message.content
            
            # --- Returning a dummy response for now ---
            dummy_response = {
                "title": "This is a placeholder title",
                "description": "This is a placeholder description.",
                "tags": ["tag1", "placeholder"],
                "script": {"Part 1": "Hello from the placeholder script."},
                "image_prompts": ["a placeholder image prompt"],
                "post_text": "This is placeholder text for a social media post.",
                "hashtags": ["#placeholder", "#example"],
                "image_prompt": "A single placeholder image prompt."
            }
            return json.dumps(dummy_response)

        except Exception as e:
            print(f"   - ❌ An error occurred with the OpenAI API call: {e}")
            return None

    def generate_complete_video_content(self, topic, niche="Technology", auto_search_context=False):
        context = None
        if auto_search_context:
            context = self.web_search_service.search_and_extract_context(topic)
            if not context:
                print("   - ⚠️ Proceeding with generation without web context. Quality may be lower.")

        print(f"📝 Generating video content for topic: {topic}...")
        prompt = f"You are an expert-level YouTube scriptwriter for a '{niche}' channel. Generate a complete content package for a video on: '{topic}'."
        if context:
            prompt += f"\n\n*** CRITICAL INSTRUCTION ***\nYou MUST base your script, title, and image prompts on the following context. Use this text as your single source of truth.\n\nCONTEXT:\n---\n{context[:4000]}\n---"
        prompt += '\nThe final output MUST be a single, valid JSON object with these exact keys: "title", "description", "tags", "script", "image_prompts".'

        json_string = self._generate_content_with_openai(prompt)
        
        if not json_string:
            raise Exception("AI service returned an empty response.")
        
        try:
            content_data = json.loads(json_string)
            
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json", encoding='utf-8') as temp_file:
                json.dump(content_data, temp_file, ensure_ascii=False, indent=2)
                local_path = temp_file.name

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"generated_content/youtube_content_{timestamp}.json"
            storage_service.upload_file(local_path, object_name)
            os.remove(local_path)

            print(f"✅ Deep content generated and archived to Spaces.")
            return content_data
        except json.JSONDecodeError as e:
            print(f"   - RAW RESPONSE from AI: {json_string}")
            raise Exception(f"Failed to parse JSON from AI. Error: {e}")

    # --- FIX: Added the missing method used by InstagramService ---
    def create_astrology_caption(self, raw_data: dict) -> str:
        """Generates a creative caption based on raw astrology data."""
        sign = raw_data.get('sign', 'the stars')
        description = raw_data.get('description', 'a mysterious message')
        mood = raw_data.get('mood', 'cosmic')
        
        prompt = f"You are a mystical astrologer. Write a short, engaging, and slightly poetic Instagram caption for {sign}. The horoscope says: '{description}'. The mood is '{mood}'. The caption should be 2-3 sentences and end with relevant hashtags."
        
        # NOTE: This uses the same generic OpenAI call. You could customize it further.
        response_text = self._generate_content_with_openai(prompt)
        # For a simple text response, we might need to parse it differently
        # For now, let's just return a placeholder.
        return f"A caption for {sign}: {description} #astrology #{sign}"

    # --- FIX: Added the missing method used by LinkedInService ---
    def generate_social_post_content(self, topic: str, niche: str, platform: str) -> dict | None:
        """Generates a complete content package for a social media post."""
        prompt = f"You are a social media expert for the '{niche}' niche. Generate a content package for a {platform} post on: '{topic}'. The final output MUST be a single, valid JSON object with these exact keys: 'post_text', 'hashtags', 'image_prompt'."
        
        json_string = self._generate_content_with_openai(prompt)
        if json_string:
            try:
                return json.loads(json_string)
            except json.JSONDecodeError:
                return None
        return None