from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from datetime import datetime
from .models import ContentItem
from . import tmdb
from apps.lists.models import CustomListItem

class HomeView(ListView):
    model = ContentItem
    template_name = "content/home.html"
    context_object_name = 'recent_items'

    def get_queryset(self):
        return ContentItem.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['highest_rated'] = ContentItem.objects.order_by('-vote_average')[:12]

        # Slider: last 4 DB items with TMDB backdrops
        recent = list(ContentItem.objects.order_by('-created_at')[:4])
        slider_items = []
        for item in recent:
            details = tmdb.get_details(item.tmdb_id, item.contnt_type) or {}
            slider_items.append({
                'backdrop_path': details.get('backdrop_path', ''),
                'title': item.title,
                'overview': item.overview,
                'vote_average': item.vote_average,
                'release_year': item.release_date.year if item.release_date else '',
                'tmdb_id': item.tmdb_id,
                'contnt_type': item.contnt_type,
                'type_display': item.get_contnt_type_display(),
            })
        context['slider_items'] = slider_items

        # Recently Added: custom list items for logged-in, popular TMDB for guests
        if self.request.user.is_authenticated:
            seen = set()
            items = []
            for cli in CustomListItem.objects.filter(
                custom_list__user=self.request.user
            ).select_related('content_item').order_by('-id'):
                if cli.content_item_id not in seen:
                    seen.add(cli.content_item_id)
                    items.append(cli.content_item)
                    if len(items) >= 12:
                        break
            context['recent_items'] = items
        else:
            raw = tmdb.discover_media(media_type='movie')[:12]
            context['recent_items'] = [
                {
                    'poster_path': item.get('poster_path', ''),
                    'custom_poster': None,
                    'vote_average': item.get('vote_average'),
                    'title': item.get('title') or item.get('name', ''),
                    'tmdb_id': item.get('id'),
                    'contnt_type': item.get('contnt_type', 'movie'),
                }
                for item in raw
            ]

        return context


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

        item = ContentItem.objects.filter(tmdb_id=tmdb_id).first()

        if not item:
            data = tmdb.get_details(tmdb_id, content_type)
            if not data:
                raise Http404("Content not found on TMDB")

            release_date_str = data.get('release_date') or data.get('first_air_date')
            release_date = None
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

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
            self._tmdb_details = data
        else:
            data = tmdb.get_details(item.tmdb_id, item.contnt_type)
            self._tmdb_details = data
            if data:
                vote_average = data.get('vote_average')
                if vote_average is not None and vote_average != item.vote_average:
                    item.vote_average = vote_average
                    item.save(update_fields=['vote_average'])

        return item

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        details = getattr(self, '_tmdb_details', None)
        credits = tmdb.get_credits(item.tmdb_id, item.contnt_type)

        if details:
            context['genres'] = details.get('genres', [])
            context['backdrop_path'] = details.get('backdrop_path', '')
            context['tagline'] = details.get('tagline', '')
            context['vote_count'] = details.get('vote_count', 0)
            runtime = details.get('runtime') or (details.get('episode_run_time') or [None])[0]
            context['runtime'] = runtime
        else:
            context['genres'] = []
            context['backdrop_path'] = ''
            context['tagline'] = ''
            context['vote_count'] = 0
            context['runtime'] = None

        if credits:
            crew = credits.get('crew', [])
            directors = [c for c in crew if c.get('job') == 'Director']
            context['director'] = directors[0]['name'] if directors else ''
            context['cast'] = credits.get('cast', [])[:5]
        else:
            context['director'] = ''
            context['cast'] = []

        if self.request.user.is_authenticated:
            from apps.lists.models import WatchItem
            context['watch_item'] = WatchItem.objects.filter(
                user=self.request.user, contnt_item=item
            ).first()

        return context


class AdvancedSearchView(View):
    def get(self, request):
        genres_data = tmdb.get_genres()
        all_genres = {g['id']: g['name'] for g in genres_data.get('movie', []) + genres_data.get('tv', [])}
        unique_genres = [{'id': k, 'name': v} for k, v in sorted(all_genres.items(), key=lambda x: x[1])]

        media_type = request.GET.get('media_type', 'movie')
        year = request.GET.get('year') or None
        country = request.GET.get('country') or None
        genre_id = request.GET.get('genre_id') or None
        min_rating = request.GET.get('min_rating') or None
        sort_by = request.GET.get('sort_by') or None

        results = []
        if request.GET:
            results = tmdb.discover_media(
                media_type=media_type,
                year=year,
                country=country,
                genre_id=genre_id,
                min_rating=min_rating,
                sort_by=sort_by,
            )

        context = {
            'genres': unique_genres,
            'results': results,
            'selected_media_type': media_type,
            'selected_year': year or '',
            'selected_country': country or '',
            'selected_genre_id': genre_id or '',
            'selected_min_rating': min_rating or '',
        }
        return render(request, 'content/advanced_search.html', context)

    def post(self, request):
        media_type = request.POST.get('media_type', 'movie')
        year = request.POST.get('year') or None
        country = request.POST.get('country') or None
        genre_id = request.POST.get('genre_id') or None
        min_rating = request.POST.get('min_rating') or None
        sort_by = request.POST.get('sort_by') or None

        results = tmdb.discover_media(
            media_type=media_type,
            year=year,
            country=country,
            genre_id=genre_id,
            min_rating=min_rating,
            sort_by=sort_by,
        )
        return render(request, 'content/partials/discover_results.html', {'results': results})
