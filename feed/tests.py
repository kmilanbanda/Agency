from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Entry, FeedSource
from .views import reader 
import feedparser

class EntryModelTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            title="Test Entry",
            slug="test-entry",
            content="This is test content.",
            pub_date=timezone.now()
        )

    def test_entry_str(self):
        self.assertEqual(str(self.entry), "Test Entry")

    def test_get_absolute_url(self):
        url = reverse('feed:entry_detail', kwargs={'slug': self.entry.slug})
        self.assertEqual(self.entry.get_absolute_url(), url)

class EntryDetailViewTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            title="Detail Test Entry",
            slug="detail-test-entry",
            content="This is the full content for testing the detail view.",
            pub_date=timezone.now()
        )

    def test_entry_detail_status_and_template(self):
        url = reverse('feed:entry_detail', kwargs={'slug': self.entry.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feed/entry_detail.html')

    def test_entry_detail_context_and_content(self):
        url = reverse('feed:entry_detail', kwargs={'slug': self.entry.slug})
        response = self.client.get(url)
        self.assertEqual(response.context['entry'], self.entry)
        self.assertContains(response, "Detail Test Entry")          # title
        self.assertContains(response, "This is the full content")   # content snippet
        self.assertContains(response, self.entry.pub_date.strftime("%B"))  # month in date

    def test_entry_detail_404_invalid_slug(self):
        url = reverse('feed:entry_detail', kwargs={'slug': 'non-existent-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

class FeedSourceModelTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test Feed",
            url="https://example.com/rss"
        )

    def test_feedsource_str(self):
        self.assertEqual(str(self.source), "Test Feed")

class RSSFeedTest(TestCase):
    def setUp(self):
        Entry.objects.create(
            title="Entry1", 
            slug="entry1", 
            content="Content1",
            pub_date=timezone.now()
        )

    def test_rss_feed_status(self):
        response = self.client.get(reverse('feed:rss_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<rss version="2.0"', response.content)
        self.assertIn(b'Entry1', response.content)
        self.assertIn(b'application/rss+xml', response['Content-Type'].encode())

class ReaderViewTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test Feed", 
            url="https://feeds.arstechnica.com/arstechnica/index"
        )

    def test_reader_view_status(self):
        response = self.client.get(reverse('feed:reader'))
        self.assertEqual(response.status_code, 200)

    def test_reader_fetches_entries(self):
        response = self.client.get(reverse('feed:reader'))
        self.assertContains(response, "Test Feed")
        self.assertContains(response, "<li")


