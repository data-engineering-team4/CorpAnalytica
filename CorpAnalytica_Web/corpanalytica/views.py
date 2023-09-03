from django.shortcuts import render, get_object_or_404
from .models import *
from .utils import get_wordcloud, get_stock_graph, get_s3_image_url

def home_view(request):
    # S3에서 워드클라우드 가져오기
    corp_base_url = "https://de-4-3.s3.us-west-2.amazonaws.com/data/news_wordcloud/corp_wordcloud_"
    news_base_url = "https://de-4-3.s3.us-west-2.amazonaws.com/data/news_wordcloud/news_wordcloud_"

    # 최대 5일전까지 이미지를 가져온다
    corp_wordcloud_url = get_s3_image_url(corp_base_url)
    news_wordcloud_url = get_s3_image_url(news_base_url)

    context = {
        'corp_wordcloud_url': corp_wordcloud_url,
        'news_wordcloud_url': news_wordcloud_url
    }

    return render(request, 'home.html', context)

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

        context = {
            'searched': searched,
            'stock_corps_list' : stock_corps_list,
            'non_stock_corps_list' : non_stock_corps_list, 
            'searched_news_list' : searched_news_list, 
            'stock_corps_keywords': stock_corps_keywords
        }

        return render(request, 'search.html', context)
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

    # 해당 기업의 네이버 뉴스, 최신 날짜로 상위 5개 뉴스를 가져온다.

    news_keyword_map = {}
    try:
        naver_news_objects = naver_news.objects.filter(corpname=corp.corpname).order_by('-pubdate')[:5] # 그 기업의 뉴스 기준

        # # 해당 뉴스의 키워드 가져오기
        # for naver_news_object in naver_news_objects:
        #     try:
        #         news_keyword_map[naver_news_object.id] = eval(news_keyword.objects.get(id=naver_news_object.id).keyword)
        #     except news_keyword.DoesNotExist:
        #         news_keyword_map[naver_news_object.id] = []

    except naver_news.DoesNotExist:
        naver_news_objects = []

    # 해당 기업의 주식 그래프
    try:
        stock_graph_img = get_stock_graph(corp.code)
    except:
        print(f"종목 번호 {corp.code}의 주식 그래프 가져오기 오류")
        stock_graph_img = None

    # 해당 기업의 관련 기업 찾기
    try:
        related_corp_list = related_corp.objects.filter(corpname=corp.corpname)
        if len(related_corp_list) > 7:
            related_corp_list = related_corp_list[:7]

    except related_corp.DoesNotExist:
        related_corp_list = []


    context = {
        'corp' : corp,
        'corp_keyword' : corp_keywords,
        'naver_news': naver_news_objects,
        'wordcloud_img' : wordcloud_img,
        'stock_graph_img' : stock_graph_img,
        'related_corp_list' : related_corp_list,
        # 'news_keyword_map' : news_keyword_map,
    }

    return render(request, 'detail.html', context)