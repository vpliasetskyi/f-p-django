import httpx
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

TMDB_API_KEY = getattr(settings, 'TMDB_API_KEY', '')

def search_multi(query):
    if not TMDB_API_KEY:
        logger.warning("TMDB API Key is not set.")
        return []
    
    url = f"{TMDB_BASE_URL}/search/multi"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'en-US',
        'page': 1,
        'include_adult': 'false'
    }
    
    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('results', []):
            if item.get('contnt_type') in ['movie', 'tv']:
                results.append(item)
        return results
    except Exception as e:
        logger.error(f"Error fetching from TMDB: {e}")
        return []
