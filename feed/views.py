import feedparser
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AddFeedForm
from .models import Entry, FeedSource, Subscription


def home(request):
    recent_entries = Entry.objects.order_by("-pub_date")[:5]
    return render(request, "feed/home.html", {"recent_entries": recent_entries})


def entry_detail(request, slug):
    entry = get_object_or_404(Entry, slug=slug)
    context = {
        "entry": entry,
        "title": entry.title,
    }
    return render(request, "feed/entry_detail.html", context)


def reader(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "feed/reader.html",
        )
    sources = FeedSource.objects.filter(subscription__user=request.user)
    all_entries = []
    source_limit = 10
    query = request.GET.get("q", "").strip()

    for source in sources:
        feed = feedparser.parse(source.url)
        if feed.bozo:
            continue

        for entry in feed.entries[:source_limit]:
            pub_date_parsed = entry.get("published_parsed") or entry.get(
                "updated_parsed"
            )
            pub_date_str = entry.get("published") or entry.get("updated") or "Unknown"
            image_url = get_image_url(entry)

            if pub_date_parsed is None:
                pub_date_parsed = timezone.now().timetuple()
                pub_date_str = f"Fetched {timezone.now().strftime('%Y-%m-%d %H:%M')}"

            all_entries.append(
                {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", "#"),
                    "image_url": image_url,
                    "published": pub_date_str,
                    "published_parsed": pub_date_parsed,
                    "description": entry.get("description", entry.get("summary", "")),
                    "source": source.title,
                }
            )

    if query != "":
        all_entries = filter_entries(all_entries, query)
    all_entries.sort(key=lambda e: e["published_parsed"], reverse=True)
    paginator = Paginator(all_entries, per_page=10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "feed/reader.html",
        {
            "page_obj": page_obj,
            "entries": page_obj.object_list,
        },
    )


def get_image_url(entry):
    image_url = None
    if "media_content" in entry:
        for media in entry.media_content:
            if media.get("medium") == "image":
                image_url = media.get("url")
    elif "enclosure" in entry and entry.enclosure.get("type", "").startswith("image/"):
        image_url = entry.enclosure.get("url")
    return image_url


def filter_entries(entries, query):
    return list(
        filter(
            lambda e: (
                query.lower() in e["title"].lower()
                or query.lower() in e["description"].lower()
            ),
            entries,
        )
    )


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, f"Welcome, {user.username}! Your account has been created."
            )
            return redirect("feed:reader")
    else:
        form = UserCreationForm()

    return render(request, "feed/register.html", {"form": form})


def feeds(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "feed/feeds.html",
        )

    if request.method == "POST":
        if "delete_feed" in request.POST:
            feed_id = request.POST.get("feed_id")
            Subscription.objects.filter(id=feed_id, user=request.user).delete()
            messages.success(request, "Feed removed from your subscriptions.")
            return redirect("feed:feeds")

        form = AddFeedForm(request.POST)
        if form.is_valid():
            feed_source = form.save(commit=False)

            existing = FeedSource.objects.filter(url=feed_source.url).first()

            if not existing:
                feed_source.save()

            Subscription.objects.get_or_create(user=request.user, feed=feed_source)

            messages.success(request, f'Feed "{feed_source.title}" added successfully!')
            return redirect("feed:feeds")
    else:
        form = AddFeedForm()

    subscriptions = Subscription.objects.filter(user=request.user).select_related(
        "feed"
    )

    context = {
        "form": form,
        "subscriptions": subscriptions,
    }

    return render(request, "feed/feeds.html", context)
