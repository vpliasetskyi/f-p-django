from django.db import models

class ContentItem(models.Model):
    MEDIA_TYPES = (
        ('movie', 'Movie'),
        ('tv', 'TV Show'),
    )

    tmdb_id = models.IntegerField(null=True, blank=True, unique=True, help_text="TMDB ID for external references")
    imdb_id = models.CharField(max_length=50, null=True, blank=True, help_text="IMDb ID for external links")
    title = models.CharField(max_length=255)
    contnt_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='movie')
    release_date = models.DateField(null=True, blank=True)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True, help_text="CDN path for TMDB poster or custom path")
    custom_poster = models.ImageField(upload_to='custom_posters/', null=True, blank=True, help_text="Uploaded custom poster if not using TMDB")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        year = self.release_date.year if self.release_date else "Unknown"
        return f"{self.title} ({year}) - {self.get_contnt_type_display()}"
