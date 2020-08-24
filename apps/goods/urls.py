from django.urls import re_path
from apps.goods.views import IndexView

app_name = 'goods'
urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name='index')  # 首页
]
