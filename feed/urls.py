from django.contrib.auth import views as auth_views
from django.urls import path

from . import feeds, views

app_name = "feed"

urlpatterns = [
    path("", views.home, name="home"),
    path("rss/", feeds.LatestEntriesFeed(), name="rss_feed"),
    path("reader/", views.reader, name="reader"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="feed/login.html", next_page="feed:reader"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="feed:home"),
        name="logout",
    ),
    path("register/", views.register, name="register"),
    path("<slug:slug>/", views.entry_detail, name="entry_detail"),
]
