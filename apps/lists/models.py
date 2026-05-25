from django.db import models
from django.conf import settings
from apps.content.models import ContentItem


class CustomList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_lists')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    items = models.ManyToManyField('content.ContentItem', through='CustomListItem', related_name='in_lists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class CustomListItem(models.Model):
    custom_list = models.ForeignKey(CustomList, on_delete=models.CASCADE, related_name='list_items')
    content_item = models.ForeignKey('content.ContentItem', on_delete=models.CASCADE, related_name='custom_list_entries')
    custom_poster = models.ImageField(upload_to='custom_posters/', null=True, blank=True)
    custom_title = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('custom_list', 'content_item')
        ordering = ['order', 'added_at']

    def __str__(self):
        return f"{self.custom_list.name} — {self.content_item.title}"

class WatchItemQuerySet(models.QuerySet):
    def clone_list_to_user(self, source_user, target_user):
        """
        Specialized QuerySet method to fork public tracking records from another 
        profile securely into the target user's database schema.
        """
        source_items = self.filter(user=source_user)
        cloned_items = []
        for item in source_items:
            # Check if target user already has this item to avoid duplicates
            if not self.filter(user=target_user, contnt_item=item.contnt_item).exists():
                cloned_item = WatchItem(
                    user=target_user,
                    contnt_item=item.contnt_item,
                    status=item.status,
                    rating=item.rating,
                    review=item.review
                )
                cloned_items.append(cloned_item)
        
        return self.bulk_create(cloned_items)

class WatchItem(models.Model):
    STATUS_CHOICES = (
        ('plan_to_watch', 'Plan to Watch'),
        ('watching', 'Watching'),
        ('completed', 'Completed'),
    )

    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_items')
    # PROTECT ensures that if a film is scrubbed from the global catalog cache, 
    # existing user reviews and personalized metrics remain intact (or rather, 
    # it prevents deleting the ContentItem if users have it in their lists).
    contnt_item = models.ForeignKey(ContentItem, on_delete=models.PROTECT, related_name='tracked_by')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='plan_to_watch')
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    review = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WatchItemQuerySet.as_manager()

    class Meta:
        unique_together = ('user', 'contnt_item')

    def __str__(self):
        return f"{self.user.username} - {self.contnt_item.title} ({self.get_status_display()})"
