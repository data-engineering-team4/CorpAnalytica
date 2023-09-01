from django.shortcuts import render, get_object_or_404
from .models import *
from .utils import get_wordcloud

def home_view(request):
    return render(request,'home.html')

def search_view(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        corps = corp_basic.objects.filter(corpname__contains=searched)

        # 검색어가 포함된 기업
        searched_corps_list = corp_total_info.objects.filter(corpname__contains=searched)
        
        # 상장기업과 비상장기업 나누기
        stock_corps_list = []
        stock_corps_keywords = {}
        non_stock_corps_list = []
        for searched_corp in searched_corps_list:

            if searched_corp.entno: 
                stock_corps_list.append(searched_corp)

                # 상장기업의 키워드 삽입
                # 키워드가 문자열 형태의 리스트이므로 eval 필요
                if searched_corp.keyword:
                    stock_corps_keywords[searched_corp.entno] = eval(searched_corp.keyword)
                    
                    if len(stock_corps_keywords[searched_corp.entno]) > 7:
                        stock_corps_keywords[searched_corp.entno] = stock_corps_keywords[searched_corp.entno][:7]

            else: 
                non_stock_corps_list.append(searched_corp)

        # 검색어가 포함된 뉴스(제목)
        searched_news_list = naver_news.objects.filter(title__contains=searched)
        if searched_news_list:
            if len(searched_news_list) > 5:
                searched_news_list = searched_news_list[:5]

        return render(request, 'search.html', {'searched': searched, 'stock_corps_list' : stock_corps_list, 'non_stock_corps_list' : non_stock_corps_list, 'searched_news_list' : searched_news_list, 'stock_corps_keywords': stock_corps_keywords })
    else:
        return render(request, 'search.html', {})

def detail_view(request,entno):

    corp = get_object_or_404(corp_basic, entno = entno)

    # 해당 기업 키워드
    try:
        corp_keyword_object = corp_keyword.objects.get(corpname=corp.corpname)
        corp_keywords = eval(corp_keyword_object.keyword)

        wordcloud_img = get_wordcloud(corp_keywords)
    except corp_keyword.DoesNotExist:
        corp_keywords = []

    # 해당 기업의 네이버 뉴스
    try:
        naver_news_objects = naver_news.objects.filter(corpname=corp.corpname)

        if len(naver_news_objects) > 5:
            naver_news_objects = naver_news_objects[:5]

    except naver_news.DoesNotExist:
        naver_news_objects = []


    return render(request, 'detail.html', {'corp' : corp, 'corp_keyword' : corp_keywords, 'naver_news': naver_news_objects, 'wordcloud_img' : wordcloud_img})