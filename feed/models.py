from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


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
    last_fetched = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feed = models.ForeignKey(FeedSource, on_delete=models.CASCADE)
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
