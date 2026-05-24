from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, render
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
                poster_path=data.get('poster_path', ''),
                vote_average=data.get('vote_average'),
            )
        else:
            # Refresh vote_average from TMDB if stale
            vote_average = data.get('vote_average') if (data := tmdb.get_details(item.tmdb_id, item.contnt_type)) else None
            if vote_average is not None and vote_average != item.vote_average:
                item.vote_average = vote_average
                item.save(update_fields=['vote_average'])
            
        return item
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            from apps.lists.models import WatchItem
            context['watch_item'] = WatchItem.objects.filter(user=self.request.user, contnt_item=self.object).first()
        return context


class AdvancedSearchView(View):
    def get(self, request):
        genres_data = tmdb.get_genres()
        all_genres = {g['id']: g['name'] for g in genres_data.get('movie', []) + genres_data.get('tv', [])}
        unique_genres = [{'id': k, 'name': v} for k, v in sorted(all_genres.items(), key=lambda x: x[1])]
        context = {'genres': unique_genres, 'results': []}
        return render(request, 'content/advanced_search.html', context)

    def post(self, request):
        media_type = request.POST.get('media_type', 'movie')
        year = request.POST.get('year') or None
        country = request.POST.get('country') or None
        genre_id = request.POST.get('genre_id') or None
        min_rating = request.POST.get('min_rating') or None

        results = tmdb.discover_media(
            media_type=media_type,
            year=year,
            country=country,
            genre_id=genre_id,
            min_rating=min_rating,
        )
        return render(request, 'content/partials/discover_results.html', {'results': results})
