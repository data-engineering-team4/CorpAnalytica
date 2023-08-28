from django.shortcuts import render, get_object_or_404
from .models import *

def home_view(request):
    return render(request,'home.html')

def search_view(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        corps = corp_basic.objects.filter(corpname__contains=searched)
        return render(request, 'search.html', {'searched': searched, 'corps' : corps})
    else:
        return render(request, 'search.html', {})

def detail_view(request,entno):
    return render(request, 'detail.html', {'entno' : entno})