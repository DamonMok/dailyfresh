from django.urls import re_path
from apps.user import views

app_name = 'user'
urlpatterns = [
    re_path(r'^register$', views.register, name='register'),  # 注册页面
    re_path(r'^register_handle$', views.register_handle, name='register_handle')  # 注册处理
]
