from django.urls import path
from . import views

urlpatterns = [
    path('',views.home_view, name='home'),
    path('search/',views.search_view, name='search'),
    path('corp_detail/',views.corp_detail_view, name='corp_detail'),
]