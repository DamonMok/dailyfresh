from django.urls import re_path
from .views import OrderPlaceView

app_name = 'order'
urlpatterns = [
    re_path(r'^place$', OrderPlaceView.as_view(), name='place')  # 订单页面显示
]
