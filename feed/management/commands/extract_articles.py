import time

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

    def handle(self, *_, **options):
        self.stdout.write("Content extraction worker started.")

        try:
            limit = options["limit"]
            while True:
                items = FeedItem.objects.filter(content_status="pending")[:limit]

                if not items:
                    time.sleep(5)
                    continue

                for item in items:
                    self.stdout.write(f"Processing: {item.title}")

                    # Download the content
                    # Extract the content
                    # Save the content
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )
