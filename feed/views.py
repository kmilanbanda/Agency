import feedparser
from django.shortcuts import render, get_object_or_404
from .models import Entry, FeedSource

def home(request):
    recent_entries = Entry.objects.order_by('-pub_date')[:5]
    return render(request, 'feed/home.html', {'recent_entries': recent_entries})

def entry_detail(request, slug):
   entry = get_object_or_404(Entry, slug=slug)
   context = {
       'entry': entry,
       'title': entry.title,
   }
   return render(request, 'feed/entry_detail.html', context)

def reader(request):
    sources = FeedSource.objects.all()
    all_entries = []

    for source in sources:
        feed = feedparser.parse(source.url)
        if feed.bozo: #skip broken feeds
            continue

        for entry in feed.entries[:10]: # limit per feed
            all_entries.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'published': entry.get('published', 'Unknown date'),
                'description': entry.get('description', entry.get('summary', '')),
                'source': source.title,
            })

    all_entries.sort(key=lambda e: e['published'], reverse=True)
    return render(request, 'feed/reader.html', {'entries': all_entries[:20]})

