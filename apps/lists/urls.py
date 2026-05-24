from django.urls import path
from . import views

app_name = "lists"

urlpatterns = [
    path("my-list/", views.UserWatchListView.as_view(), name="my_list"),
    path("toggle/<int:content_id>/", views.WatchItemToggleView.as_view(), name="toggle"),
    path("clone/<str:username>/", views.CloneWatchListView.as_view(), name="clone"),
    path("custom/create/", views.CustomListCreateView.as_view(), name="custom_list_create"),
    path("custom/<int:pk>/edit/", views.CustomListUpdateView.as_view(), name="custom_list_update"),
    path("custom/<int:pk>/delete/", views.CustomListDeleteView.as_view(), name="custom_list_delete"),
    path("add-to-list/<int:content_id>/", views.AddToListView.as_view(), name="add_to_list"),
]
