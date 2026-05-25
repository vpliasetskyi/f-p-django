from django.views.generic import ListView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.http import HttpResponse
from datetime import datetime

from .models import WatchItem, CustomList, CustomListItem
from apps.content.models import ContentItem
from apps.content import tmdb


class UserWatchListView(LoginRequiredMixin, ListView):
    model = WatchItem
    template_name = "lists/my_list.html"
    context_object_name = "watch_items"

    def get_queryset(self):
        return WatchItem.objects.filter(user=self.request.user).select_related('contnt_item').order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['plan_to_watch_items'] = qs.filter(status='plan_to_watch')
        context['watching_items'] = qs.filter(status='watching')
        context['completed_items'] = qs.filter(status='completed')
        context['rated_items'] = qs.filter(rating__isnull=False)
        context['custom_lists'] = CustomList.objects.filter(
            user=self.request.user
        ).prefetch_related('list_items__content_item').order_by('-updated_at')
        return context


class WatchItemToggleView(LoginRequiredMixin, View):
    def post(self, request, content_id):
        content_item = get_object_or_404(ContentItem, id=content_id)
        status = request.POST.get('status')
        rating = request.POST.get('rating')

        if status in dict(WatchItem.STATUS_CHOICES):
            watch_item, _ = WatchItem.objects.update_or_create(
                user=request.user,
                contnt_item=content_item,
                defaults={'status': status},
            )
        elif rating:
            try:
                rating_val = int(rating)
                if 1 <= rating_val <= 10:
                    watch_item, _ = WatchItem.objects.update_or_create(
                        user=request.user,
                        contnt_item=content_item,
                        defaults={'rating': rating_val},
                    )
                else:
                    watch_item = WatchItem.objects.filter(
                        user=request.user, contnt_item=content_item
                    ).first()
            except ValueError:
                watch_item = WatchItem.objects.filter(
                    user=request.user, contnt_item=content_item
                ).first()
        else:
            WatchItem.objects.filter(user=request.user, contnt_item=content_item).delete()
            watch_item = None

        return render(request, "lists/partials/track_button.html", {
            'item': content_item,
            'watch_item': watch_item,
        })


class CloneWatchListView(LoginRequiredMixin, View):
    def post(self, request, username):
        source_user = get_object_or_404(get_user_model(), username=username)

        if not source_user.profile.is_public:
            return redirect('users:profile', username=username)

        custom_list = CustomList.objects.create(
            user=request.user,
            name=f"Imported from {source_user.username}",
        )
        source_items = WatchItem.objects.filter(user=source_user).select_related('contnt_item')
        CustomListItem.objects.bulk_create(
            [CustomListItem(custom_list=custom_list, content_item=wi.contnt_item) for wi in source_items],
            ignore_conflicts=True,
        )
        return redirect('lists:my_list')


class CustomListCreateView(LoginRequiredMixin, View):
    def get(self, request):
        custom_list = CustomList.objects.create(user=request.user, name='New List')
        return redirect('lists:custom_list_update', pk=custom_list.pk)


class CustomListUpdateView(LoginRequiredMixin, View):
    def _get_list(self, request, pk):
        return get_object_or_404(CustomList, pk=pk, user=request.user)

    def _watch_items_map(self, request, list_items):
        if not list_items:
            return {}
        return {
            wi.contnt_item_id: wi
            for wi in WatchItem.objects.filter(
                user=request.user,
                contnt_item__in=[li.content_item for li in list_items],
            )
        }

    def get(self, request, pk):
        custom_list = self._get_list(request, pk)
        list_items = list(custom_list.list_items.select_related('content_item').all())
        return render(request, 'lists/custom_list_form.html', {
            'custom_list': custom_list,
            'list_items': list_items,
            'watch_items_map': self._watch_items_map(request, list_items),
        })

    def post(self, request, pk):
        custom_list = self._get_list(request, pk)
        name = request.POST.get('name', '').strip()
        if name:
            custom_list.name = name
            custom_list.save(update_fields=['name'])
        return redirect('lists:my_list')


class CustomListDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomList
    success_url = reverse_lazy('lists:my_list')

    def get_queryset(self):
        return CustomList.objects.filter(user=self.request.user)


class CustomListTMDBSearchView(LoginRequiredMixin, View):
    def get(self, request, pk):
        custom_list = get_object_or_404(CustomList, pk=pk, user=request.user)
        query = request.GET.get('q', '').strip()
        year = request.GET.get('year') or None
        country = request.GET.get('country') or None
        min_rating = request.GET.get('min_rating') or None
        actor_name = request.GET.get('actor', '').strip() or None

        results = []
        if query or year or country or min_rating or actor_name:
            if actor_name:
                person_id = tmdb.search_people(actor_name)
                results = tmdb.discover_media(
                    year=year, country=country, min_rating=min_rating,
                    with_people=person_id,
                ) if person_id else []
            elif year or country or min_rating:
                results = tmdb.discover_media(year=year, country=country, min_rating=min_rating)
            elif query:
                results = tmdb.search_multi(query)

        existing_tmdb_ids = set(
            custom_list.list_items.values_list('content_item__tmdb_id', flat=True)
        )
        return render(request, 'lists/partials/cl_search_results.html', {
            'results': results,
            'existing_tmdb_ids': existing_tmdb_ids,
            'custom_list': custom_list,
        })


class CustomListAddItemView(LoginRequiredMixin, View):
    def post(self, request, pk):
        custom_list = get_object_or_404(CustomList, pk=pk, user=request.user)
        tmdb_id = request.POST.get('tmdb_id')
        content_type = request.POST.get('content_type', 'movie')

        if not tmdb_id:
            return HttpResponse(status=400)

        content_item = ContentItem.objects.filter(tmdb_id=tmdb_id).first()
        if not content_item:
            data = tmdb.get_details(tmdb_id, content_type)
            if not data:
                return HttpResponse(status=404)
            release_date_str = data.get('release_date') or data.get('first_air_date')
            release_date = None
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            content_item = ContentItem.objects.create(
                tmdb_id=data.get('id'),
                imdb_id=data.get('imdb_id', ''),
                title=data.get('title') or data.get('name', 'Unknown'),
                contnt_type=content_type,
                release_date=release_date,
                overview=data.get('overview', ''),
                poster_path=data.get('poster_path', ''),
                vote_average=data.get('vote_average'),
            )

        CustomListItem.objects.get_or_create(
            custom_list=custom_list,
            content_item=content_item,
        )
        return self._render_added_items(request, custom_list)

    def _render_added_items(self, request, custom_list):
        list_items = list(custom_list.list_items.select_related('content_item').all())
        watch_items_map = {
            wi.contnt_item_id: wi
            for wi in WatchItem.objects.filter(
                user=request.user,
                contnt_item__in=[li.content_item for li in list_items],
            )
        } if list_items else {}
        return render(request, 'lists/partials/cl_added_items.html', {
            'custom_list': custom_list,
            'list_items': list_items,
            'watch_items_map': watch_items_map,
        })


class CustomListRemoveItemView(LoginRequiredMixin, View):
    def post(self, request, pk, item_pk):
        custom_list = get_object_or_404(CustomList, pk=pk, user=request.user)
        CustomListItem.objects.filter(pk=item_pk, custom_list=custom_list).delete()
        list_items = list(custom_list.list_items.select_related('content_item').all())
        watch_items_map = {
            wi.contnt_item_id: wi
            for wi in WatchItem.objects.filter(
                user=request.user,
                contnt_item__in=[li.content_item for li in list_items],
            )
        } if list_items else {}
        return render(request, 'lists/partials/cl_added_items.html', {
            'custom_list': custom_list,
            'list_items': list_items,
            'watch_items_map': watch_items_map,
        })


class CustomListItemEditView(LoginRequiredMixin, View):
    def get(self, request, pk, item_pk):
        custom_list = get_object_or_404(CustomList, pk=pk, user=request.user)
        list_item = get_object_or_404(CustomListItem, pk=item_pk, custom_list=custom_list)
        watch_item = WatchItem.objects.filter(
            user=request.user, contnt_item=list_item.content_item
        ).first()
        return render(request, 'lists/partials/cl_item_edit_popup.html', {
            'custom_list': custom_list,
            'list_item': list_item,
            'watch_item': watch_item,
        })

    def post(self, request, pk, item_pk):
        custom_list = get_object_or_404(CustomList, pk=pk, user=request.user)
        list_item = get_object_or_404(CustomListItem, pk=item_pk, custom_list=custom_list)

        update_fields = []
        if 'custom_title' in request.POST:
            list_item.custom_title = request.POST.get('custom_title', '').strip()
            update_fields.append('custom_title')
        if 'custom_poster' in request.FILES:
            list_item.custom_poster = request.FILES['custom_poster']
            update_fields.append('custom_poster')
        if update_fields:
            list_item.save(update_fields=update_fields)

        rating_str = request.POST.get('rating', '').strip()
        if rating_str:
            try:
                rating_val = int(rating_str)
                if 1 <= rating_val <= 10:
                    WatchItem.objects.update_or_create(
                        user=request.user,
                        contnt_item=list_item.content_item,
                        defaults={'rating': rating_val},
                    )
            except ValueError:
                pass

        list_items = list(custom_list.list_items.select_related('content_item').all())
        watch_items_map = {
            wi.contnt_item_id: wi
            for wi in WatchItem.objects.filter(
                user=request.user,
                contnt_item__in=[li.content_item for li in list_items],
            )
        }
        return render(request, 'lists/partials/cl_added_items.html', {
            'custom_list': custom_list,
            'list_items': list_items,
            'watch_items_map': watch_items_map,
        })


class AddToListView(LoginRequiredMixin, View):
    def _get_content_item(self, tmdb_id):
        return get_object_or_404(ContentItem, tmdb_id=tmdb_id)

    def post(self, request, content_id):
        content_item = self._get_content_item(content_id)
        list_id = request.POST.get('list_id')
        list_name = request.POST.get('list_name', '').strip()

        if list_id:
            custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)
        elif list_name:
            custom_list, _ = CustomList.objects.get_or_create(user=request.user, name=list_name)
        else:
            return render(request, 'lists/partials/add_to_list_result.html', {'error': 'No list specified.'})

        CustomListItem.objects.get_or_create(custom_list=custom_list, content_item=content_item)
        user_lists = CustomList.objects.filter(user=request.user).order_by('name')
        return render(request, 'lists/partials/add_to_list_result.html', {
            'custom_list': custom_list,
            'content_item': content_item,
            'user_lists': user_lists,
        })

    def get(self, request, content_id):
        content_item = self._get_content_item(content_id)
        user_lists = CustomList.objects.filter(user=request.user).order_by('name')
        return render(request, 'lists/partials/add_to_list_panel.html', {
            'content_item': content_item,
            'user_lists': user_lists,
        })
