# src/core_services/content_generator_service.py

# ... (the rest of the file is the same above this function)

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
    
    # --- THIS IS THE CRITICAL FIX ---
    if not json_string:
        # Instead of returning None, we now raise a specific error.
        raise Exception("OpenAI service returned an empty response.")
    
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
        # Instead of returning None, we now raise a specific error with context.
        print(f"   - RAW RESPONSE FROM OPENAI: {json_string}")
        raise Exception(f"Failed to parse JSON from OpenAI. Error: {e}")

# ... (the rest of the file is the same below this function)
