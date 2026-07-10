from collections import defaultdict
from datetime import UTC, datetime

import defusedxml.ElementTree as ET
import feedparser
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AddFeedForm, CategorizeForm
from .models import Category, Entry, FeedItem, FeedSource, Subscription, UserFeedItem


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


def item_detail(request, slug):
    item = get_object_or_404(FeedItem, slug=slug)
    context = {
        "item": item,
        "title": item.title,
    }

    if request.user.is_authenticated:
        user_item = get_object_or_404(UserFeedItem, user=request.user, item=item)
        user_item.is_read = True
        user_item.viewed_at = timezone.now()
        user_item.save()

    if request.method == "GET":
        return render(request, "feed/item_detail.html", context)
    elif request.method == "POST":
        user_item.is_saved = not user_item.is_saved
        user_item.save()

    return redirect(request.path)


def reader(request):
    sources = FeedSource.objects.all()

    if request.user.is_authenticated:
        subscriptions = (
            Subscription.objects.filter(user=request.user)
            .select_related("category")
            .annotate(
                unread_count=Count(
                    "feed__items__user_items",
                    filter=Q(
                        feed__items__user_items__user=request.user,
                        feed__items__user_items__is_read=False,
                    ),
                )
            )
        )
        subscription_lookup = {sub.feed.id: sub for sub in subscriptions}

    categories_with_sources = []
    if request.user.is_authenticated:
        categories_with_sources, sources = get_categories_with_sources(request)

    all_entries = []
    source_limit = 10
    query = request.GET.get("q", "").strip()

    for source in sources:
        feed = feedparser.parse(source.url)
        if feed.bozo:
            continue

        for entry in feed.entries[:source_limit]:
            published_parsed = entry.get("published_parse") or entry.get(
                "updated_parsed"
            )
            published_at = None
            if published_parsed:
                published_at = datetime(*published_parsed[:6], tzinfo=UTC)
            image_url = get_image_url(entry)

            content = ""
            if "content" in entry:
                content = entry.content[0].value
            elif "summary" in entry:
                content = entry.summary

            item, _ = FeedItem.objects.get_or_create(
                url=entry.get("link", "#"),
                defaults={
                    "source": source,
                    "title": entry.title,
                    "published_at": published_at,
                    "author": entry.get("author", "Unknown"),
                    "description": entry.get("summary", "No description"),
                    "image_url": image_url or None,
                    "content": content,
                },
            )
            if request.user.is_authenticated:
                item.category = subscription_lookup[source.id].category

            if request.user.is_authenticated:
                _, _ = UserFeedItem.objects.get_or_create(
                    user=request.user,
                    item=item,
                )
            all_entries.append(item)

    if query != "":
        all_entries = filter_entries(all_entries, query)
    all_entries.sort(key=lambda e: e.published_at, reverse=True)
    paginator = Paginator(all_entries, per_page=10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "entries": page_obj.object_list,
        "categories": categories_with_sources,
    }

    return render(
        request,
        "feed/reader.html",
        context,
    )


@login_required
def get_categories_with_sources(request):
    categories_with_sources = []
    category_slug = request.GET.get("category")
    feed_slug = request.GET.get("feed")
    if category_slug:
        sources = FeedSource.objects.filter(
            subscriptions__user=request.user,
            subscriptions__category__slug=category_slug,
        )

    elif feed_slug:
        sources = FeedSource.objects.filter(
            subscriptions__user=request.user,
            subscriptions__feed__slug=feed_slug,
        )

    else:
        sources = FeedSource.objects.filter(subscriptions__user=request.user)

    categories_list = Category.objects.filter(user=request.user).annotate(
        unread_count=Count(
            "subscriptions__feed__items__user_items",
            filter=Q(
                subscriptions__feed__items__user_items__user=request.user,
                subscriptions__feed__items__user_items__is_read=False,
            ),
        )
    )
    for category in categories_list:
        category_sources = (
            FeedSource.objects.filter(
                subscriptions__user=request.user,
                subscriptions__category=category,
            )
            .distinct()
            .annotate(
                unread_count=Count(
                    "items__user_items",
                    filter=Q(
                        items__user_items__user=request.user,
                        items__user_items__is_read=False,
                    ),
                )
            )
        )

        categories_with_sources.append((category, category_sources))

    return (categories_with_sources, sources)


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


@login_required
def saved(request):
    saved_user_items = UserFeedItem.objects.filter(user=request.user).filter(
        is_saved=True
    )
    items = FeedItem.objects.filter(user_items__in=saved_user_items)

    categories_with_sources, _ = get_categories_with_sources(request)

    paginator = Paginator(items, per_page=10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "entries": page_obj.object_list,
        "categories": categories_with_sources,
    }

    return render(
        request,
        "feed/saved_items.html",
        context,
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
        "category"
    )
    categorized_subs = defaultdict(list)

    for sub in subscriptions:
        if sub.category:
            categorized_subs[sub.category.title].append(sub)
        else:
            categorized_subs["Uncategorized"].append(sub)

    user_categories = Category.objects.filter(user=request.user)

    context = {
        "form": form,
        "subscriptions": subscriptions,
        "user_categories": user_categories,
        "categorized_subs": categorized_subs,
        "categorized_items": categorized_subs.items(),
    }

    return render(request, "feed/feeds.html", context)


@login_required
def opml(request):
    if request.method == "GET":
        return export_opml(request)
    elif request.method == "POST":
        return import_opml(request)
    else:
        messages.warning(request, "Improper HTTP request")
        return redirect("feed:feeds")


def import_opml(request):
    if request.FILES.get("opml_file"):
        opml_file = request.FILES["opml_file"]

        try:
            tree = ET.parse(opml_file)
            root = tree.getroot()

            imported_count = 0
            skipped_count = 0

            for outline in root.findall(".//body/outline"):
                title = outline.get("text") or outline.get("title")

                if len(outline):
                    category, _ = Category.objects.get_or_create(
                        user=request.user, title=title
                    )

                    for feed_outline in outline.findall("outline"):
                        feed_url = feed_outline.get("xmlUrl")
                        feed_title = feed_outline.get("text") or feed_outline.get(
                            "title"
                        )

                        if feed_url:
                            feed_source, _ = FeedSource.objects.get_or_create(
                                url=feed_url,
                                defaults={"title": feed_title or "Untitled Feed"},
                            )

                            _, sub_created = Subscription.objects.get_or_create(
                                user=request.user,
                                feed=feed_source,
                                defaults={"category": category},
                            )

                            if sub_created:
                                imported_count += 1
                            else:
                                skipped_count += 1
                else:
                    feed_url = outline.get("xmlUrl")
                    if feed_url:
                        feed_source, _ = FeedSource.objects.get_or_create(
                            url=feed_url,
                            defaults={"title": title or "Untitled Feed"},
                        )

                        _, sub_created = Subscription.objects.get_or_create(
                            user=request.user, feed=feed_source
                        )

                        if sub_created:
                            imported_count += 1
                        else:
                            skipped_count += 1

            messages.success(
                request,
                f"Successfully imported {imported_count} feeds!   "
                f"Skipped {skipped_count} duplicates.",
            )
            return redirect("feed:feeds")

        except Exception as e:
            messages.error(request, f"Failed to import OPML: {e!s}")
            return redirect("feed:feeds")

    messages.error(request, "No opml_file in request")
    return redirect("feed:feeds")


def export_opml(request):
    categories = Category.objects.filter(user=request.user).prefetch_related(
        "subscriptions"
    )
    subscriptions = Subscription.objects.filter(user=request.user).select_related(
        "feed", "category"
    )

    opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Agency - My Feeds</title>
    <dateCreated>{}</dateCreated>
  </head>
  <body>
""".format(timezone.now().strftime("%a, %d %b %Y %H:%M:%S GMT"))

    for category in categories:
        opml_content += (
            f'      <outline text="{category.title}" title="{category.title}">\n'
        )

        for sub in category.subscriptions.all():
            feed = sub.feed
            opml_content += f'      <outline text="{sub.title or feed.title}" '
            opml_content += f'type="rss" xmlUrl="{feed.url}" '
            if feed.site_url:
                opml_content += f'htmlUrl="{feed.site_url}" '
            opml_content += "/>\n"

        opml_content += "   </outline>\n"

    uncategorized = subscriptions.filter(category__isnull=True)
    if uncategorized.exists():
        opml_content += '   <outline text="Uncategorized">\n'
        for sub in uncategorized:
            feed = sub.feed
            opml_content += f'      <outline text="{sub.title or feed.title}" '
            opml_content += f'type="rss" xmlUrl="{feed.url}" '
            if feed.site_url:
                opml_content += f'htmlUrl="{feed.site_url}" '
            opml_content += "/>\n"
        opml_content += "   </outline>\n"

    opml_content += "   </body>\n</opml>"

    response = HttpResponse(opml_content, content_type="text/xml")
    response["Content-Disposition"] = 'attachment; filename="my-feeds.opml"'
    return response


@login_required
def categorize_subscription(request, subscription_id):
    subscription = get_object_or_404(
        Subscription, id=subscription_id, user=request.user
    )

    if request.method == "POST":
        form = CategorizeForm(request.POST, user=request.user)
        if form.is_valid():
            category_choice = form.cleaned_data["category_choice"]

            if category_choice == "new":
                category_name = form.cleaned_data["new_category_name"]
                category, _ = Category.objects.get_or_create(
                    user=request.user, title=category_name
                )
                category.save()
            else:
                category = form.cleaned_data["category"]

            subscription.category = category
            subscription.save()

            messages.success(request, f'Feed categorized under "{category.title}"')
    else:
        messages.error(request, "Invalid category selection")

    return redirect("feed:feeds")


@login_required
def toggle_item_is_saved(request, item_id):
    user_item = get_object_or_404(UserFeedItem, user=request.user, item=item_id)

    if request.method == "POST":
        user_item.is_saved = not user_item.is_saved

    return
