import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from feed.ai.providers import MockProvider, OpenAIProvider
from feed.ai.service import AIService
from feed.models import FeedItem


class Command(BaseCommand):
    help = "Add ai summary to article"
    ai_service = None

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
            if (
                self.ai_service is None
            ):  # this was implemented to allow tests to insert the necessary mock provider
                if settings.CURRENT_PROVIDER == "openai":
                    provider = OpenAIProvider()
                elif settings.CURRENT_PROVIDER == "mock":
                    provider = MockProvider()
                self.ai_service = AIService(provider)

            while not self.shutdown:
                items = self.get_pending_items(limit)

                if not items:
                    time.sleep(5)
                    continue

                for item in items:
                    self.stdout.write(f"Processing AI Summary: {item.title}")
                    self.process_ai_summary(item)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Worker shut down by keyboard interrupt.")
            )

    def process_ai_summary(self, item):
        # claim an article
        updated = FeedItem.objects.filter(
            pk=item.pk,
            ai_status="pending",
        ).update(ai_status="processing")

        if updated == 0:
            return

        # get ai metadata and summary
        try:
            result = self.ai_service.summarize_article(item)

        except Exception as e:
            self.stderr.write(f"Failed {item.id}: {e}")
            item.ai_status = "failed"
            item.save(update_fields=["ai_status"])
            return

        # update item and save
        item.ai_summary = result.summary
        item.ai_tags = result.tags
        item.ai_status = "complete"
        item.save(update_fields=["ai_summary", "ai_tags", "ai_status"])

    def get_pending_items(self, limit):
        return FeedItem.objects.filter(
            content_status="complete",
            ai_status="pending",
        )[:limit]
