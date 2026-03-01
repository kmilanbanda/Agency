from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Entry

class LatestEntriesFeed(Feed):
    title = "Agency Updates"
    link = "/"
    description = "Latest updates for the RSS feed."

    def items(self):
        return Entry.objects.order_by('-pub_date')[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.pub_date

    def item_updateddate(self, item):
        return item.updated
