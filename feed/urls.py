from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    # home, rss and rss reader
    path("", views.home, name="home"),
    path("reader/", views.reader, name="reader"),
    path("reader/saved-items/", views.saved, name="saved"),
    # user login/logout/register
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
    # feeds modify/opml page
    path("feeds/", views.feeds, name="feeds"),
    path("feeds/opml", views.opml, name="opml"),
    path(
        "feeds/<int:subscription_id>/categories/",
        views.categorize_subscription,
        name="categorize_subscription",
    ),
    # entries
    path("<slug:slug>/", views.item_detail, name="item_detail"),
]
