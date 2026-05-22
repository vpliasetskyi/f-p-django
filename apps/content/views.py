from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from datetime import datetime
from .models import ContentItem
from . import tmdb

class HomeView(ListView):
    model = ContentItem
    template_name = "content/home.html"
    context_object_name = 'recent_items'
    
    def get_queryset(self):
        return ContentItem.objects.order_by('-created_at')[:12]

class ContentSearchView(ListView):
    template_name = "content/search_results.html"
    context_object_name = 'results'

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return []
        return tmdb.search_multi(query)
        
    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["components/search_dropdown.html"]
        return [self.template_name]

class ContentDetailView(DetailView):
    model = ContentItem
    template_name = "content/detail.html"
    context_object_name = 'item'

    def get_object(self, queryset=None):
        tmdb_id = self.kwargs.get('pk')
        content_type = self.request.GET.get('type', 'movie')
        
        # Try to get from local DB
        item = ContentItem.objects.filter(tmdb_id=tmdb_id).first()
        
        if not item:
            # Not in DB, fetch from TMDB and cache it locally
            data = tmdb.get_details(tmdb_id, content_type)
            if not data:
                raise Http404("Content not found on TMDB")
                
            # Parse release date securely
            release_date_str = data.get('release_date') or data.get('first_air_date')
            release_date = None
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Create local ContentItem
            item = ContentItem.objects.create(
                tmdb_id=data.get('id'),
                imdb_id=data.get('imdb_id'),
                title=data.get('title') or data.get('name', 'Unknown Title'),
                contnt_type=content_type,
                release_date=release_date,
                overview=data.get('overview', ''),
                poster_path=data.get('poster_path', '')
            )
            
        return item
