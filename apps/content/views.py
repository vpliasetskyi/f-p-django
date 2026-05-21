from django.shortcuts import render
from .models import ContentItem

def home_view(request):
    # Fetch the 12 most recently added content items
    recent_items = ContentItem.objects.order_by('-created_at')[:12]
    
    context = {
        'recent_items': recent_items,
    }
    return render(request, "content/home.html", context)
