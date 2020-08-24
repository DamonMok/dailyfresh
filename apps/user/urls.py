from django.urls import re_path
from apps.user.views import RegisterView

app_name = 'user'
urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),  # 注册
]
