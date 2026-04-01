from django import forms

from .models import FeedSource


class AddFeedForm(forms.ModelForm):
    class Meta:
        model = FeedSource
        fields = ["title", "url", "site_url"]
        widgets = {
            "url": forms.URLInput(
                attrs={"placeholder": "https://example.com/feed.xml"}
            ),
            "title": forms.TextInput(attrs={"placeholder": "Feed Title"}),
        }

    def clean_url(self):
        url = self.cleaned_data["url"]
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url
