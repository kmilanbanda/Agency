from django import forms

from .models import Category


class AddFeedForm(forms.Form):
    title = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Feed Title"}),
    )

    url = forms.URLField(
        widget=forms.URLInput(attrs={"placeholder": "https://example.com/rss"})
    )

    site_url = forms.URLField(required=False)

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
