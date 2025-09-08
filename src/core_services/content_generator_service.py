# src/core_services/content_generator_service.py

import os
import json
import tempfile
from datetime import datetime
from openai import OpenAI
from src.config import OPENAI_API_KEY
from src.utils import storage_service

class ContentGeneratorService:
    def __init__(self, web_search_service):
        self.web_search_service = web_search_service
        
        if not OPENAI_API_KEY or "sk-proj-" not in OPENAI_API_KEY:
            self.client = None
            print("❌ Critical Error: OPENAI_API_KEY not found or is invalid.")
            return
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            print("✅ OpenAI client configured successfully.")
        except Exception as e:
            self.client = None
            print(f"❌ Critical Error configuring OpenAI client: {e}")

    def create_astrology_caption(self, astro_data: dict) -> str:
        # This function does not save files, so no changes are needed here.
        # ... (original code is fine)
        print("   - ✍️ Crafting an engaging astrology caption...")
        prompt = f"""
        You are an expert social media manager for an astrology brand. Your tone is mystical, positive, and insightful.
        You have received the following daily horoscope data for {astro_data.get('sign', 'a zodiac sign')}.
        DATA:
        - Description: {astro_data.get('description')}
        - Mood: {astro_data.get('mood')}
        - Lucky Number: {astro_data.get('lucky_number')}
        Your task is to transform this into a beautiful Instagram caption and provide relevant hashtags.
        The entire output MUST be a single, valid JSON object with two keys: "caption" and "hashtags".
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a creative astrology social media expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            raw_response = response.choices[0].message.content
            data = json.loads(raw_response)
            final_caption = data.get('caption', astro_data.get('description'))
            hashtags_str = " ".join(data.get('hashtags', []))
            return f"{final_caption}\n\n{hashtags_str}"
        except Exception as e:
            print(f"   - ❌ Error generating caption: {e}. Falling back to default.")
            return f"{astro_data.get('description')}\n\n#astrology #horoscope #{astro_data.get('sign')}"


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
            return None
        try:
            content_data = json.loads(json_string)
            
            # --- NEW: Save content to a temporary local file ---
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json", encoding='utf-8') as temp_file:
                json.dump(content_data, temp_file, ensure_ascii=False, indent=2)
                local_path = temp_file.name

            # --- NEW: Upload the content file to Spaces for archival ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"generated_content/youtube_content_{timestamp}.json"
            storage_service.upload_file(local_path, object_name)

            os.remove(local_path) # Clean up the temporary file

            print(f"✅ Deep content generated and archived to Spaces.")
            return content_data
        except json.JSONDecodeError as e:
            print(f"❌ CRITICAL ERROR: Failed to parse JSON from OpenAI. Error: {e}")
            return None

    def _generate_content_with_openai(self, prompt):
        if not self.client:
            return None
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert-level, world-class content creation assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Error during OpenAI API call: {e}")
            return None

    def generate_social_post_content(self, topic, niche, platform="LinkedIn"):
        # This is a placeholder and can be expanded.
        print(f"   - Generating placeholder content for {platform}...")
        return {
            "post_text": f"This is a post about {topic} in the {niche} field.",
            "hashtags": [f"#{niche.replace(' ', '')}", f"#{topic.replace(' ', '')}"],
            "image_prompt": f"An abstract image representing {topic}"
        }
