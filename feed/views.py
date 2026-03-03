from django.shortcuts import render, get_object_or_404
from .models import Entry

def home(request):
    return render(request, 'feed/home.html', {})

def entry_detail(request, slug):
   entry = get_object_or_404(Entry, slug=slug)
   context = {
       'entry': entry,
       'title': entry.title,
   }
   return render(request, 'feed/entry_detail.html', context)

