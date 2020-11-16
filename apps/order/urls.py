from django.urls import re_path
from .views import OrderPlaceView, OrderCommitView

app_name = 'order'
urlpatterns = [
    re_path(r'^place$', OrderPlaceView.as_view(), name='place'),  # 订单页面显示
    re_path(r'^commit$', OrderCommitView.as_view(), name='commit'),  # 订单页面显示
]
