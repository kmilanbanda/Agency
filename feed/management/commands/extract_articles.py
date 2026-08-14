import signal
import time

import bleach
import requests
import trafilatura
from django.core.management.base import BaseCommand

from feed.models import FeedItem


class Command(BaseCommand):
    help = "Extract full article content"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
        )

    def handle_sigterm(self, _):  # (self, signum, frame)
        self.stdout.write(self.style.WARNING("Shutdown requested by signal..."))
        self.shutdown = True

    def handle(self, *_, **options):
        self.stdout.write("Content extraction worker started.")
        self.shutdown = False
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        try:
            limit = options["limit"]
            while not self.shutdown:
                items = FeedItem.objects.filter(content_status="pending")[:limit]

                if not items:
                    time.sleep(5)
                    continue

                for item in items:
                    item.content_status = "processing"
                    item.save()

                    self.stdout.write(f"Processing: {item.title}")

                    try:
                        self.process_article(item)

                    except Exception as e:
                        self.stderr.write(f"Failed {item.id}: {e}")
                        item.content_status = "failed"
                        item.save()

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )

    def process_article(self, item):
        pass
        # Download the content
        headers = {"User-Agent": "AgencyRSSReader"}

        try:
            response = requests.get(item.url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(e)
            item.content_status = "failed"
            item.save()
            return

        # Verify content encoding

        if "text/html" not in response.headers["Content-Type"]:
            print("Response error occured. Skipping article.")
            item.content_status = "failed"
            item.save()
            return

        if response.encoding is None or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding
        html = response.text

        # Extract the content
        article = trafilatura.extract(
            html,
            output_format="html",
            include_links=True,
            include_images=True,
            favor_precision=True,
        )
        if article is None:
            print("Article extraction error occured. Skipping article.")
            item.content_status = "failed"
            item.save()
            return

        # Sanitize the content
        tags = [
            "p",
            "h1",
            "h2",
            "h3",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "blockquote",
            "a",
            "img",
        ]
        attributes = {
            "a": ["href", "title"],
            "img": ["src", "alt"],
        }

        clean_article = bleach.clean(
            article, tags=tags, attributes=attributes, strip=True
        )

        # Save the content
        item.content = clean_article
        item.content_status = "complete"
        item.save()
