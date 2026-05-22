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
            if item.get('media_type') in ['movie', 'tv']:
                # Standardize to contnt_type to match our models
                item['contnt_type'] = item['media_type']
                results.append(item)
        return results
    except Exception as e:
        logger.error(f"Error fetching from TMDB: {e}")
        return []

def get_details(tmdb_id, content_type='movie'):
    if not TMDB_API_KEY:
        logger.warning("TMDB API Key is not set.")
        return None
        
    url = f"{TMDB_BASE_URL}/{content_type}/{tmdb_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
    }
    
    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        data['contnt_type'] = content_type
        return data
    except Exception as e:
        logger.error(f"Error fetching details from TMDB: {e}")
        return None
