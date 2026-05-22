from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from .models import WatchItem
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
