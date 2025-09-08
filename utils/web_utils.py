# src/utils/web_utils.py

import requests
from  bs4 import BeautifulSoup

def browse_url(url: str) -> str | None:
    """
    Takes a URL, fetches its content using requests, parses it with
    BeautifulSoup to extract clean text, and returns the text.
    Returns None if any error occurs.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        return clean_text

    except requests.RequestException as e:
        print(f"   - ❗ Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"   - ❗ An unexpected error occurred during browsing: {e}")
        return None
