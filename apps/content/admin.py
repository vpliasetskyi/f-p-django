from django.contrib import admin
from .models import ContentItem

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'contnt_type', 'release_date', 'tmdb_id', 'imdb_id')
    list_filter = ('contnt_type',)
    search_fields = ('title', 'tmdb_id', 'imdb_id')
