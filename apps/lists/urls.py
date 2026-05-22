from django.urls import path
from . import views

app_name = "lists"

urlpatterns = [
    path("my-list/", views.UserWatchListView.as_view(), name="my_list"),
    path("toggle/<int:content_id>/", views.WatchItemToggleView.as_view(), name="toggle"),
]
