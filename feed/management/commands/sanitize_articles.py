import bleach
from django.core.management.base import BaseCommand

from feed.models import FeedItem


class Command(BaseCommand):
    help = "Sanitize all completed articles"

    def handle(self):
        self.stdout.write("Sanitization worker started.")

        # Sanitize all completed articles
        try:
            items = FeedItem.objects.filter(content_status="complete")

            for item in items:
                self.stdout.write(f"Sanitizing: {item.title}")

                try:
                    article = item.content
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

                    item.content = clean_article
                    item.save()

                except Exception as e:
                    self.stderr.write(f"Failed {item.id}: {e}")

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )
