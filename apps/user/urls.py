from django.urls import re_path
from apps.user.views import RegisterView, ActiveView, LoginView

app_name = 'user'
urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 用户激活
    re_path(r'^login$', LoginView.as_view(), name='login')  # 用户登录
]
