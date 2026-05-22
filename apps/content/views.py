from django.views.generic import ListView
from .models import ContentItem

class HomeView(ListView):
    model = ContentItem
    template_name = "content/home.html"
    context_object_name = 'recent_items'
    
    def get_queryset(self):
        return ContentItem.objects.order_by('-created_at')[:12]
