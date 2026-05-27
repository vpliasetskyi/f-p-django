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

def search_by_type(query, media_type='movie', count=24):
    if not TMDB_API_KEY or not query:
        return []
    url = f"{TMDB_BASE_URL}/search/{media_type}"
    results = []
    for pg in range(1, 3):
        params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'en-US', 'page': pg, 'include_adult': 'false'}
        try:
            response = httpx.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            page_results = response.json().get('results', [])
            for item in page_results:
                item['contnt_type'] = media_type
            results.extend(page_results)
            if len(results) >= count:
                break
        except Exception as e:
            logger.error(f"Error searching {media_type}: {e}")
            break
    return results[:count]


def get_genres():
    if not TMDB_API_KEY:
        logger.warning("TMDB API Key is not set.")
        return {'movie': [], 'tv': []}

    genres = {}
    for media_type in ('movie', 'tv'):
        url = f"{TMDB_BASE_URL}/genre/{media_type}/list"
        try:
            response = httpx.get(url, params={'api_key': TMDB_API_KEY, 'language': 'en-US'}, timeout=5.0)
            response.raise_for_status()
            genres[media_type] = response.json().get('genres', [])
        except Exception as e:
            logger.error(f"Error fetching {media_type} genres: {e}")
            genres[media_type] = []
    return genres


def get_credits(tmdb_id, content_type='movie'):
    if not TMDB_API_KEY:
        logger.warning("TMDB API Key is not set.")
        return {'cast': [], 'crew': []}
    url = f"{TMDB_BASE_URL}/{content_type}/{tmdb_id}/credits"
    params = {'api_key': TMDB_API_KEY, 'language': 'en-US'}
    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching credits: {e}")
        return {'cast': [], 'crew': []}


def search_people(query):
    if not TMDB_API_KEY:
        return None
    url = f"{TMDB_BASE_URL}/search/person"
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'en-US', 'page': 1}
    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        results = response.json().get('results', [])
        return results[0]['id'] if results else None
    except Exception as e:
        logger.error(f"Error searching person: {e}")
        return None


def discover_media(media_type='movie', year=None, country=None, genre_id=None, min_rating=None, page=1, with_people=None, sort_by=None, count=24):
    if not TMDB_API_KEY:
        logger.warning("TMDB API Key is not set.")
        return []

    url = f"{TMDB_BASE_URL}/discover/{media_type}"
    actual_sort = sort_by or 'popularity.desc'
    if actual_sort == 'release_date.desc':
        actual_sort = 'primary_release_date.desc' if media_type == 'movie' else 'first_air_date.desc'

    base_params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'sort_by': actual_sort,
        'include_adult': 'false',
    }
    if year:
        key = 'primary_release_year' if media_type == 'movie' else 'first_air_date_year'
        base_params[key] = year
    if country:
        base_params['with_origin_country'] = country
    if genre_id:
        base_params['with_genres'] = genre_id
    if min_rating:
        base_params['vote_average.gte'] = min_rating
    if with_people:
        base_params['with_people'] = with_people

    results = []
    for pg in range(page, page + 2):
        try:
            response = httpx.get(url, params={**base_params, 'page': pg}, timeout=5.0)
            response.raise_for_status()
            page_results = response.json().get('results', [])
            for item in page_results:
                item['contnt_type'] = media_type
            results.extend(page_results)
            if len(results) >= count:
                break
        except Exception as e:
            logger.error(f"Error fetching discover results: {e}")
            break
    return results[:count]


def get_videos(tmdb_id, content_type='movie'):
    if not TMDB_API_KEY:
        return None
    url = f"{TMDB_BASE_URL}/{content_type}/{tmdb_id}/videos"
    try:
        response = httpx.get(url, params={'api_key': TMDB_API_KEY, 'language': 'en-US'}, timeout=5.0)
        response.raise_for_status()
        yt_results = [v for v in response.json().get('results', []) if v.get('site') == 'YouTube']
        for preferred in ('Trailer', 'Teaser', 'Clip', 'Featurette'):
            for video in yt_results:
                if video.get('type') == preferred:
                    return video.get('key')
        return yt_results[0].get('key') if yt_results else None
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return None


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
