from django.shortcuts import render
from .models import Entry

def home(request):
    return render(request, 'feed/home.html', {})

def entry_detail(request, slug):
    try:
        entry = Entry.objects.get(slug=slug)
        return HttpResponse(f"<h1>{entry.title}</h1><p>{entry.content[:200]}...</p>")
    except Entry.DoesNotExist:
        return HttpResponse("Entry not found", status=404)
