from django.urls import path
from . import views
from . import feeds

app_name = 'feed'

urlpatterns = [
    path('', views.home, name='home'),
    path('rss/', feeds.LatestEntriesFeed(), name='rss_feed'),
    path('reader/', views.reader, name='reader'),
    path('<slug:slug>/', views.entry_detail, name='entry_detail'),
]
