import signal
import time

from django.core.management.base import BaseCommand

from feed.ai.service import AIService
from feed.models import FeedItem


class Command(BaseCommand):
    help = "Add ai summary to article"

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
        self.stdout.write("AI embedder worker started.")
        self.shutdown = False
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        try:
            limit = options["limit"]
            self.ai_service = AIService()
            while not self.shutdown:
                items = FeedItem.objects.filter(ai_status="pending")[:limit]

                if not items:
                    time.sleep(5)
                    continue

                for item in items:
                    self.stdout.write(f"Processing AI Summary: {item.title}")
                    try:
                        self.process_ai_summary(item)

                    except Exception as e:
                        self.stderr.write(f"Failed {item.id}: {e}")
                        item.ai_status = "failed"
                        item.save()

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )

    def process_ai_summary(self, item):
        # claim an article
        item.ai_status = "processing"
        item.save()

        # get ai metadata and summary
        result = self.ai_service.summarize_article(item)

        # update item and save
        item.ai_summary = result["summary"]
        item.ai_tags = result["tags"]
        item.ai_status = "complete"
        item.save()
