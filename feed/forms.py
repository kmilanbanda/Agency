from django import forms

from .models import Category, FeedSource


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


class CategorizeForm(forms.Form):
    category_choice = forms.ChoiceField(
        choices=[
            ("existing", "Add to existing category"),
            ("new", "Create new category"),
        ],
        widget=forms.RadioSelect,
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="-- Select a category --",
    )

    new_category_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "New category name"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
