import signal
import time
from datetime import UTC, datetime

import feedparser
from django.core.management.base import BaseCommand
from django.utils import timezone

from feed.models import FeedItem, FeedSource


class Command(BaseCommand):
    help = "fetch feed items from feed sources"

    def handle_sigterm(self, _):
        self.stdout.write(self.style.WARNING("Shutdown requested by signal..."))
        self.shutdown = True

    def handle(self, *_args, **_options):
        self.stdout.write("feed item fetcher started.")
        self.shutdown = False
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        try:
            while not self.shutdown:
                cutoff = timezone.now() - timedelta(minutes=10)
                sources = FeedSource.objects.filter(
                    Q(last_fetched__isnull=True) |
                    Q(last_fetched__lt=cutoff)
                )
                for source in sources:
                    if self.shutdown:
                        break
                    self.fetch_feed(source)

                if self.shutdown:
                    break

                self.stdout.write("Sleeping for 10 minutes...")
                time.sleep(15)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )

    def fetch_feed(self, source):
        feed = feedparser.parse(source.url)
        if feed.bozo:
            return
        source.last_fetched = timezone.now()
        source.save(update_fields=["last_fetched"])

        for entry in feed.entries[:10]:
            published_parsed = entry.get("published_parse") or entry.get(
                "updated_parsed"
            )
            published_at = None
            if published_parsed:
                published_at = datetime(*published_parsed[:6], tzinfo=UTC)
            image_url = self.get_image_url(entry)

            content = ""
            if "content" in entry:
                content = entry.content[0].value
            elif "summary" in entry:
                content = entry.summary

            _, _ = FeedItem.objects.get_or_create(
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

    def get_image_url(self, entry):
        image_url = None
        if "media_content" in entry:
            for media in entry.media_content:
                if media.get("medium") == "image":
                    image_url = media.get("url")
        elif "enclosure" in entry and entry.enclosure.get("type", "").startswith(
            "image/"
        ):
            image_url = entry.enclosure.get("url")
        return image_url
