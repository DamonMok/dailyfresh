from django.urls import re_path
from apps.user import views

app_name = 'user'
urlpatterns = [
    re_path(r'^register', views.register, name='register'),

]
