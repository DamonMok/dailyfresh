from django.urls import re_path
from apps.goods.views import IndexView, DetailView

app_name = 'goods'
urlpatterns = [
    re_path(r'^index/$', IndexView.as_view(), name='index'),  # 首页
    re_path(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail')  # 商品详情页
]
