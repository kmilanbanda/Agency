from collections import defaultdict

import defusedxml.ElementTree as ET
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
    categories_with_sources = []
    if request.user.is_authenticated:
        categories_with_sources = get_categories_with_sources(request)
    query = request.GET.get("q", "").strip()

    # Still need to address possibility of no user
    all_entries = UserFeedItem.objects.all()
    if request.user.is_authenticated:
        all_entries = all_entries.filter(user=request.user).select_related(
            "item", "item__source"
        )

        category_slug = request.GET.get("category")
        if category_slug:
            all_entries = all_entries.filter(
                item__source__subscriptions__category__slug=category_slug,
            )

    feed_slug = request.GET.get("feed")
    if feed_slug:
        all_entries = all_entries.filter(item__source__slug=feed_slug)

    if query:
        all_entries = all_entries.filter(
            Q(item__title__icontains=query) | Q(item__description__icontains=query)
        )

    all_entries = all_entries.distinct()
    all_entries = all_entries.order_by("-item__published_at")
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

    uncategorized_sources = (
        FeedSource.objects.filter(
            subscriptions__user=request.user,
            subscriptions__category=None,
        )
    ).annotate(
        unread_count=Count(
            "items__user_items",
            filter=Q(
                items__user_items__user=request.user,
                items__user_items__is_read=False,
            ),
        )
    )

    categories_with_sources.append((None, uncategorized_sources))
    return categories_with_sources


def filter_entries(entries, query):
    return list(
        filter(
            lambda e: (
                query.lower() in e.title.lower()
                or query.lower() in e.description.lower()
            ),
            entries,
        )
    )


@login_required
def saved(request):
    items = UserFeedItem.objects.filter(user=request.user, is_saved=True)

    categories_with_sources = get_categories_with_sources(request)

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
        "feed/reader.html",
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
            feed_source, _ = FeedSource.objects.get_or_create(
                url=form.cleaned_data["url"],
                defaults={
                    "title": form.cleaned_data["title"],
                    "site_url": form.cleaned_data["site_url"],
                },
            )

            _, created = Subscription.objects.get_or_create(
                user=request.user, feed=feed_source
            )

            if created:
                messages.success(
                    request, f'Successfully subscribed to "{feed_source.title}"!'
                )
            else:
                messages.error(request, f'Failed to subscribe to "{feed_source.title}"')
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
    for sub in uncategorized:
        feed = sub.feed
        opml_content += f'   <outline text="{sub.title or feed.title}" '
        opml_content += f'type="rss" xmlUrl="{feed.url}" '
        if feed.site_url:
            opml_content += f'htmlUrl="{feed.site_url}" '
        opml_content += "/>\n"
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
