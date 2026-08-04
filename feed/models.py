from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Entry(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Auto-generated from title for clean URLs",
    )
    content = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pub_date"]  # Newest first
        verbose_name_plural = "entries"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # We'll use this for RSS links and future detail pages
        return reverse("feed:entry_detail", kwargs={"slug": self.slug})


class FeedSource(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    site_url = models.URLField(blank=True)  # optional main site link
    slug = models.SlugField(blank=True, null=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "sources"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class FeedItem(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Auto-generated from title",
    )
    description = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    author = models.CharField(max_length=200)
    published_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)
    source = models.ForeignKey(
        FeedSource, on_delete=models.CASCADE, related_name="items"
    )
    url = models.URLField(unique=True)
    image_url = models.URLField(blank=True, null=True)
    content_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("complete", "Complete"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 2

            while FeedItem.objects.filter(slug=slug).exists():
                slug = f"({base_slug}-{count}"
                count += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("feed:item_detail", kwargs={"slug": self.slug})


class UserFeedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_items")
    item = models.ForeignKey(
        FeedItem, on_delete=models.CASCADE, related_name="user_items"
    )

    is_read = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"],
                name="unique_user_item",
            )
        ]

    def __str__(self):
        return (
            self.user.username + "'s " + self.item.title
            or "Error fetching UserFeedItem title"
        )


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "title", "parent"],
                name="unique_user_title_parent_category",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Category {self.id}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    feed = models.ForeignKey(
        FeedSource, on_delete=models.CASCADE, related_name="subscriptions"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    title = models.CharField(max_length=200, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} to {self.feed}"

    class Meta:
        verbose_name_plural = "subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feed"], name="unique_user_feed_subscription"
            )
        ]
