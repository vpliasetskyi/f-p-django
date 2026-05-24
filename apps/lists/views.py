from django.views.generic import ListView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .models import WatchItem, CustomList
from apps.content.models import ContentItem

class UserWatchListView(LoginRequiredMixin, ListView):
    model = WatchItem
    template_name = "lists/my_list.html"
    context_object_name = "watch_items"
    
    def get_queryset(self):
        return WatchItem.objects.filter(user=self.request.user).select_related('contnt_item').order_by('-updated_at')

class WatchItemToggleView(LoginRequiredMixin, View):
    def post(self, request, content_id):
        content_item = get_object_or_404(ContentItem, id=content_id)
        status = request.POST.get('status')
        
        if status in dict(WatchItem.STATUS_CHOICES):
            watch_item, created = WatchItem.objects.update_or_create(
                user=request.user,
                contnt_item=content_item,
                defaults={'status': status}
            )
        else:
            WatchItem.objects.filter(user=request.user, contnt_item=content_item).delete()
            watch_item = None

        context = {
            'item': content_item,
            'watch_item': watch_item,
        }
        return render(request, "lists/partials/track_button.html", context)

class CloneWatchListView(LoginRequiredMixin, View):
    def post(self, request, username):
        target_user = get_object_or_404(get_user_model(), username=username)

        if not target_user.profile.is_public:
            return redirect('profile', username=username)

        WatchItem.objects.clone_list_to_user(target_user, request.user)
        return redirect('lists:my_list')


class CustomListCreateView(LoginRequiredMixin, CreateView):
    model = CustomList
    fields = ['name', 'description']
    template_name = 'lists/custom_list_form.html'
    success_url = reverse_lazy('lists:my_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CustomListUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomList
    fields = ['name', 'description']
    template_name = 'lists/custom_list_form.html'
    success_url = reverse_lazy('lists:my_list')

    def get_queryset(self):
        return CustomList.objects.filter(user=self.request.user)


class CustomListDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomList
    success_url = reverse_lazy('lists:my_list')

    def get_queryset(self):
        return CustomList.objects.filter(user=self.request.user)


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

        custom_list.items.add(content_item)
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
