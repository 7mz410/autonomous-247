# src/core_services/web_search_service.py

import requests
import json
from src.config import SERPER_API_KEY
from src.utils.web_utils import browse_url

class WebSearchService:
    """
    A service responsible for performing web searches using the Serper API
    and extracting content from the most relevant URL.
    """
    def __init__(self):
        if not SERPER_API_KEY or "YOUR_SERPER_API_KEY" in SERPER_API_KEY:
            print("❌ Critical Error: SERPER_API_KEY not found or is a placeholder.")
            self.is_configured = False
        else:
            self.is_configured = True
            print("✅ Web Search Service initialized with Serper API.")

    def search_and_extract_context(self, topic: str) -> str | None:
        """
        Searches a topic, finds the best URL from the results, and browses it
        to extract clean text content.
        """
        if not self.is_configured:
            print("   - ❗ Web Search is not configured. Skipping context search.")
            return None

        print(f"🧠 Conducting autonomous research for: '{topic}'...")
        try:
            payload = json.dumps({"q": topic})
            headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
            response = requests.post("https://google.serper.dev/search", headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            search_results = response.json()

            if not search_results.get("organic"):
                print("   - ❗ Serper API returned no organic search results.")
                return None

            best_link = search_results["organic"][0]["link"]
            print(f"   - ✅ Found most promising URL: {best_link}")

            print(f"   - 📖 Reading and extracting content from URL...")
            context_text = browse_url(best_link)

            if context_text:
                print(f"   - ✅ Successfully extracted context! (Length: {len(context_text)} chars)")
                return context_text
            else:
                print(f"   - ❗ Failed to extract usable content from the URL.")
                return None
        except requests.RequestException as e:
            print(f"   - ❌ An error occurred during the Serper API call: {e}")
            return None
        except Exception as e:
            print(f"   - ❌ An unexpected error occurred during autonomous research: {e}")
            return None
