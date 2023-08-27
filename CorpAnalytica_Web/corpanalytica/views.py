from django.shortcuts import render
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

def corp_detail_view(request):
    return render(request,'corp_detail.html')