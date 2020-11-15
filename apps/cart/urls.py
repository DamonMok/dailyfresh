from django.urls import re_path
from .views import CartAddView, CartInfoView

app_name = 'cart'
urlpatterns = [
    re_path('^add/$', CartAddView.as_view(), name='add'),  # 添加购物车
    re_path('^$', CartInfoView.as_view(), name='show'),  # 购物车页面
]
