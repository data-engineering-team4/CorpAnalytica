from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register([corp_basic,corp_detail,corp_keyword,test_table])
