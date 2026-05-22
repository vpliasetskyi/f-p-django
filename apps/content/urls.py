from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.ContentSearchView.as_view(), name="search"),
    path("<int:pk>/", views.ContentDetailView.as_view(), name="detail"),
]
