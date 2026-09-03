import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, FeedItem, FeedSource, Subscription
from .views import get_categories_with_sources


@override_settings(SECURE_SSL_REDIRECT=False)
class FeedItemModelTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test FeedSource",
            url="www.example.com",
        )

        self.entry = FeedItem.objects.create(
            title="Test FeedItem",
            slug="test-entry",
            content="This is test content.",
            published_at=timezone.now(),
            source=self.source,
        )

    def test_entry_str(self):
        self.assertEqual(str(self.entry), "Test FeedItem")

    def test_get_absolute_url(self):
        url = reverse("feed:item_detail", kwargs={"slug": self.entry.slug})
        self.assertEqual(self.entry.get_absolute_url(), url)


@override_settings(SECURE_SSL_REDIRECT=False)
class FeedItemDetailViewTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test FeedSource",
            url="www.example.com",
        )

        self.entry = FeedItem.objects.create(
            title="Detail Test FeedItem",
            slug="detail-test-item",
            content="This is the full content for testing the detail view.",
            published_at=timezone.now(),
            source=self.source,
        )

    def test_item_detail_status_and_template(self):
        url = reverse("feed:item_detail", kwargs={"slug": self.entry.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feed/item_detail.html")

    def test_item_detail_context_and_content(self):
        url = reverse("feed:item_detail", kwargs={"slug": self.entry.slug})
        response = self.client.get(url)
        self.assertEqual(response.context["item"], self.entry)
        self.assertContains(response, "Detail Test FeedItem")  # title
        self.assertContains(response, "This is the full content")  # content snippet
        self.assertContains(
            response, self.entry.published_at.strftime("%B")
        )  # month in date

    def test_item_detail_404_invalid_slug(self):
        url = reverse("feed:item_detail", kwargs={"slug": "non-existent-slug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@override_settings(SECURE_SSL_REDIRECT=False)
class BrokenFeedTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Broken", url="https://example.com/rss"
        )

        self.mock_feed = Mock()
        self.mock_feed.bozo = 1
        self.mock_feed.bozo_exception = None
        self.mock_feed.entries = []

    def test_broken_feed_status(self):
        with patch("feed.views.feedparser.parse", return_value=self.mock_feed):
            response = self.client.get(reverse("feed:reader"))
            self.assertEqual(response.status_code, 200)


@override_settings(SECURE_SSL_REDIRECT=False)
class FeedSourceModelTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test Feed", url="https://example.com/rss"
        )

    def test_feedsource_str(self):
        self.assertEqual(str(self.source), "Test Feed")


@override_settings(SECURE_SSL_REDIRECT=False)
class ReaderViewTest(TestCase):
    def setUp(self):
        self.source = FeedSource.objects.create(
            title="Test Feed", url="https://feeds.arstechnica.com/arstechnica/index"
        )

    def test_reader_view_status(self):
        response = self.client.get(reverse("feed:reader"))
        self.assertEqual(response.status_code, 200)

    def test_reader_fetches_entries(self):
        response = self.client.get(reverse("feed:reader"))
        self.assertContains(response, "Test Feed")
        self.assertContains(response, "<li")


@override_settings(SECURE_SSL_REDIRECT=False)
class UserTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )

        self.client.login(username="testuser", password="testpassword123")

    def test_authenticated_user(self):
        response = self.client.get("/feeds/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Feed Subscriptions")
        self.assertContains(response, "add-feed")


@override_settings(SECURE_SSL_REDIRECT=False)
class RegisterTest(TestCase):
    def setUp(self):
        self.form_data = {
            "username": "testuser",
            "password1": "testpassword123",
            "password2": "testpassword123",
        }

    def test_register_post(self):
        response = self.client.post(reverse("feed:register"), self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_get(self):
        response = self.client.get(reverse("feed:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feed/register.html")


@override_settings(SECURE_SSL_REDIRECT=False)
class AddDeleteFeedTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )

        self.client.login(username="testuser", password="testpassword123")

    def test_add_feed(self):
        form_data = {"title": "New Test Feed", "url": "https://example.com/feed.xml"}

        self.client.login(username="testuser", password="testpassword123")

        response = self.client.post(reverse("feed:feeds"), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            FeedSource.objects.filter(url="https://example.com/feed.xml").exists()
        )
        feed = FeedSource.objects.get(url="https://example.com/feed.xml")
        self.assertTrue(Subscription.objects.filter(user=self.user, feed=feed).exists())

    def test_delete_feed(self):
        feed_source = FeedSource.objects.create(
            title="Test Feed to Delete", url="https://example.com/delete-test.xml"
        )

        subscription = Subscription.objects.create(user=self.user, feed=feed_source)

        response = self.client.post(
            reverse("feed:feeds"), {"delete_feed": "1", "feed_id": subscription.id}
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("feed:feeds"))
        self.assertFalse(Subscription.objects.filter(id=subscription.id).exists())
        self.assertTrue(FeedSource.objects.filter(id=feed_source.id).exists())

    def test_feeds_while_logged_out(self):
        self.client.logout()

        response = self.client.get(reverse("feed:feeds"))
        self.assertEqual(response.status_code, 200)


@override_settings(SECURE_SSL_REDIRECT=False)
class OPMLTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password")
        self.client.login(username="username", password="password")

    def test_import_opml_file(self):
        opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test Feeds</title></head>
  <body>
    <outline text="News">
      <outline text="BBC News" xmlUrl="https://feeds.bbci.co.uk/news/rss.xml"/>
      <outline text="CNN" xmlUrl="https://rss.cnn.com/rss/cnn_topstories.rss"/>
    </outline>
    <outline text="Tech">
      <outline text="Hacker News" xmlUrl="https://news.ycombinator.com/rss"/>
    </outline>
  </body>
</opml>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".opml", delete=False) as tmp:
            tmp.write(opml_content)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            response = self.client.post(
                reverse("feed:opml"), {"opml_file": f}, format="multipart"
            )

        import os

        os.unlink(tmp_path)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            FeedSource.objects.filter(url="https://news.ycombinator.com/rss").exists()
        )

    def test_export_opml_file(self):
        feed = FeedSource.objects.create(
            title="Test Feed", url="https://example.com/test.xml"
        )
        Subscription.objects.create(user=self.user, feed=feed)

        response = self.client.get(reverse("feed:opml"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/xml")
        self.assertTrue("attachment" in response["Content-Disposition"])
        self.assertTrue("my-feeds.opml" in response["Content-Disposition"])

        content = response.content.decode("utf-8")
        self.assertIn('<opml version="2.0">', content)
        self.assertIn("Test Feed", content)
        self.assertIn("https://example.com/test.xml", content)


@override_settings(SECURE_SSL_REDIRECT=False)
class CategorizationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password")
        self.client.login(username="username", password="password")
        feed = FeedSource.objects.create(
            title="Test Feed", url="https://example.com/test.xml"
        )
        self.subscription = Subscription.objects.create(user=self.user, feed=feed)

    def test_categorize_subscription(self):
        category = Category.objects.create(user=self.user, title="Test")

        form_data = {"category_choice": "existing", "category": category.id}

        url = reverse(
            "feed:categorize_subscription",
            kwargs={"subscription_id": self.subscription.id},
        )
        response = self.client.post(url, form_data)

        updated_subscription = Subscription.objects.select_related("category").get(
            id=self.subscription.id
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(updated_subscription.category.title, category.title)

    def test_new_category(self):
        category_choice = "new"
        new_category_name = "New Test Category"

        form_data = {
            "category_choice": category_choice,
            "new_category_name": new_category_name,
        }

        url = reverse(
            "feed:categorize_subscription",
            kwargs={"subscription_id": self.subscription.id},
        )
        response = self.client.post(url, form_data)

        updated_subscription = Subscription.objects.select_related("category").get(
            id=self.subscription.id
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(updated_subscription.category.title, new_category_name)


class GetCategoriesWithSourcesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(username="username", password="password")
        self.client.login(username="username", password="password")
        feed1 = FeedSource.objects.create(
            title="Test Feed 1", url="https://example1.com/test.xml"
        )
        feed2 = FeedSource.objects.create(
            title="Test Feed 2", url="https://example2.com/test.xml"
        )
        feed3 = FeedSource.objects.create(
            title="Test Feed 3", url="https://example3.com/test.xml"
        )
        feed4 = FeedSource.objects.create(
            title="Uncategorized Test Feed", url="https://example4.com/test.xml"
        )

        self.category1 = Category.objects.create(user=self.user, title="category1")
        self.category2 = Category.objects.create(user=self.user, title="category2")

        self.subscription1 = Subscription.objects.create(
            user=self.user, feed=feed1, category=self.category1
        )
        self.subscription2 = Subscription.objects.create(
            user=self.user, feed=feed2, category=self.category1
        )
        self.subscription3 = Subscription.objects.create(
            user=self.user, feed=feed3, category=self.category2
        )
        self.subscription4 = Subscription.objects.create(user=self.user, feed=feed4)

    def test_get_categories_with_sources(self):
        request = self.factory.get("/")

        request.user = self.user

        categories_with_sources, sources = get_categories_with_sources(request)

        test_sources_object = FeedSource.objects.filter(
            subscriptions__user=request.user
        )
        test_categories_with_sources_object = []
        test_categories_with_sources_object.append(
            (
                self.category1,
                FeedSource.objects.filter(
                    subscriptions__user=request.user,
                    subscriptions__category=self.category1,
                ),
            )
        )
        test_categories_with_sources_object.append(
            (
                self.category2,
                FeedSource.objects.filter(
                    subscriptions__user=request.user,
                    subscriptions__category=self.category2,
                ),
            )
        )
        test_categories_with_sources_object.append(
            (
                None,
                FeedSource.objects.filter(
                    subscriptions__user=request.user, subscriptions__category=None
                ),
            )
        )

        self.assertCountEqual(
            list(test_sources_object.values_list("id", flat=True)),
            list(sources.values_list("id", flat=True)),
        )

        def normalize_categories_with_sources_object(obj):
            return [
                (
                    category.id if category else None,
                    list(feed_ids.values_list("id", flat=True)),
                )
                for category, feed_ids in obj
            ]

        self.assertCountEqual(
            normalize_categories_with_sources_object(
                test_categories_with_sources_object
            ),
            normalize_categories_with_sources_object(categories_with_sources),
        )
