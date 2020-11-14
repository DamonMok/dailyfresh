from django.urls import re_path
from .views import CartAddView

app_name = 'cart'
urlpatterns = [
    re_path('^add/$', CartAddView.as_view(), name='add'),  # 添加购物车
]
