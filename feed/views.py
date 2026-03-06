import feedparser
from django.shortcuts import render, get_object_or_404
from .models import Entry, FeedSource
from django.utils import timezone

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
    source_limit = 10

    for source in sources:
        feed = feedparser.parse(source.url)
        if feed.bozo: 
            continue

        for entry in feed.entries[:source_limit]:
            pub_date_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
            pub_date_str = entry.get('published') or entry.get('updated') or 'Unknown'

            if pub_date_parsed is None:
                pub_date_parsed = timezone.now().timetuple()
                pub_date_str = f"Fetched {timezone.now().strftime('%Y-%m-%d %H:%M')}"

            all_entries.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'published': pub_date_str,
                'published_parsed': pub_date_parsed,
                'description': entry.get('description', entry.get('summary', '')),
                'source': source.title,
            })

    all_entries.sort(key=lambda e: e['published_parsed'], reverse=True)
    return render(request, 'feed/reader.html', {'entries': all_entries[:20]})

