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

    corp = get_object_or_404(corp_basic, entno = entno)

    # 해당 기업 키워드
    try:
        corp_keyword_object = corp_keyword.objects.get(corpname=corp.corpname)
        corp_keywords = eval(corp_keyword_object.keyword)
    except corp_keyword.DoesNotExist:
        corp_keywords = []

    # 해당 기업의 네이버 뉴스
    try:
        naver_news_objects = naver_news.objects.filter(corpname=corp.corpname)

        if len(naver_news_objects) > 5:
            naver_news_objects = naver_news_objects[:5]

    except naver_news.DoesNotExist:
        naver_news_objects = []

    return render(request, 'detail.html', {'corp' : corp, 'corp_keyword' : corp_keywords, 'naver_news': naver_news_objects})