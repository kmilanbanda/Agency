import feedparser
from django.shortcuts import render, get_object_or_404
from .models import Entry, FeedSource
from django.utils import timezone
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

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
            image_url = getImageURL(entry)

            if pub_date_parsed is None:
                pub_date_parsed = timezone.now().timetuple()
                pub_date_str = f"Fetched {timezone.now().strftime('%Y-%m-%d %H:%M')}"

            all_entries.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'image_url': image_url,
                'published': pub_date_str,
                'published_parsed': pub_date_parsed,
                'description': entry.get('description', entry.get('summary', '')),
                'source': source.title,
            })

    all_entries.sort(key=lambda e: e['published_parsed'], reverse=True)
    paginator = Paginator(all_entries, per_page=10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'feed/reader.html', {
        'page_obj': page_obj,
        'entries': page_obj.object_list,
    })

def getImageURL(entry):
    image_url = None
    if 'media_content' in entry:
        for media in entry.media_content:
            if media.get('medium') == 'image':
                image_url = media.get('url')
    elif 'enclosure' in entry and entry.enclosure.get('type', '').startswith('image/'):
        image_url = entry.enclosure.get('url')
    return image_url
