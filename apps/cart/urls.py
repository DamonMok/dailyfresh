from django.urls import re_path
from .views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = 'cart'
urlpatterns = [
    re_path('^add/$', CartAddView.as_view(), name='add'),  # 添加购物车
    re_path('^$', CartInfoView.as_view(), name='show'),  # 购物车页面
    re_path('^update', CartUpdateView.as_view(), name='update'),  # 更新购物车记录
    re_path('^delete', CartDeleteView.as_view(), name='delete'),  # 删除购物车记录
]
