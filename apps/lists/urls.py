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
    path("custom/<int:pk>/search/", views.CustomListTMDBSearchView.as_view(), name="custom_list_search"),
    path("custom/<int:pk>/add-item/", views.CustomListAddItemView.as_view(), name="custom_list_add_item"),
    path("custom/<int:pk>/remove-item/<int:item_pk>/", views.CustomListRemoveItemView.as_view(), name="custom_list_remove_item"),
    path("custom/<int:pk>/edit-item/<int:item_pk>/", views.CustomListItemEditView.as_view(), name="custom_list_item_edit"),
    path("add-to-list/<int:content_id>/", views.AddToListView.as_view(), name="add_to_list"),
    path("default/<str:status>/", views.DefaultListDetailView.as_view(), name="default_list_detail"),
    path("default/<str:status>/edit-item/<int:item_pk>/", views.DefaultListItemEditView.as_view(), name="default_list_item_edit"),
    path("default/<str:status>/remove-item/<int:item_pk>/", views.DefaultListRemoveItemView.as_view(), name="default_list_remove_item"),
]
