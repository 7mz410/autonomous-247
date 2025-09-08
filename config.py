# src/config.py
# THIS FILE IS SAFE TO COMMIT TO GITHUB

import os
from dotenv import load_dotenv

# This line loads the variables from your .env file into the environment
load_dotenv()

# --- Core API Keys (read from environment) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_AI_API_KEY = os.getenv("STABILITY_AI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --- OAuth & Platform Credentials (read from environment) ---
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
# Note: Non-secret variables from the old file are removed for clarity
# as they were placeholders (e.g., INSTAGRAM_ACCESS_TOKEN)

# --- Asset & Path Configuration ---
DATA_PATH = os.getenv("DATA_PATH", ".")
ASSETS_PATH = "assets"
MUSIC_ASSETS_PATH = os.path.join(ASSETS_PATH, 'music')

# --- OAuth Redirect URI (read from environment) ---
# Defaults to localhost if not set in the environment
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8501")
