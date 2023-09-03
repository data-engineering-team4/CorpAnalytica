from django.contrib import admin

# Register your models here.
from .models import *

model_list = [
    corp_basic,
    corp_detail,
    corp_keyword,
    naver_news,
    news_article,
    news_keyword,
    corp_total_info,
    related_corp,
]

admin.site.register(model_list)