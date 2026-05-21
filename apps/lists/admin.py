from django.contrib import admin
from .models import WatchItem

@admin.register(WatchItem)
class WatchItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'contnt_item', 'status', 'rating', 'updated_at')
    list_filter = ('status', 'rating')
    search_fields = ('user__username', 'contnt_item__title')
