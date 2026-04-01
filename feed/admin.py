from django.contrib import admin

from .models import Entry, FeedSource, Subscription

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
    list_display = ("user", "feed", "subscribed_at")
    list_filter = ("subscribed_at",)
