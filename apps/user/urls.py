from django.urls import re_path
from django.contrib.auth.decorators import login_required
from apps.user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, UserAddressView, LogoutView

app_name = 'user'
urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 用户激活
    re_path(r'^login$', LoginView.as_view(), name='login'),  # 用户登录
    re_path(r'^logout$', LogoutView.as_view(), name='logout'),  # 用户退出

    # re_path(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心-信息页
    # re_path(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户中心-订单页
    # re_path(r'^address$', login_required(UserAddressView.as_view()), name='address'),  # 用户中心-地址页

    re_path(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    re_path(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    re_path(r'^address$', UserAddressView.as_view(), name='address'),  # 用户中心-地址页
]
