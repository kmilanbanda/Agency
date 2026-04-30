from django.contrib import admin

from .models import Category, Entry, FeedItem, FeedSource, Subscription

admin.site.register(FeedSource)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("title", "pub_date", "updated")
    list_filter = ("pub_date",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "pub_date"


@admin.register(Subscription)
class UserFeedAdmin(admin.ModelAdmin):
    list_display = ("user", "feed", "subscribed_at", "category")
    list_filter = ("subscribed_at",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    list_filter = ("created_at",)


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "published_at")
    list_filter = ("published_at",)
