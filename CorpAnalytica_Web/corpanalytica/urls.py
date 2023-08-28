from django.urls import path
from . import views

urlpatterns = [
    path('',views.home_view, name='home'),
    path('search/',views.search_view, name='search'),
    path('detail/',views.detail_view, name='detail'),
    path('detail/<str:entno>',views.detail_view, name='detail'),
]