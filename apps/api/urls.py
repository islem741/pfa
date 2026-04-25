from django.urls import path
from apps.api.views import QueryView, SessionListView

urlpatterns = [
    path("query/",    QueryView.as_view(),       name="query"),
    path("sessions/", SessionListView.as_view(), name="sessions"),
]
