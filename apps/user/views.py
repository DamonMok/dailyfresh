from django.shortcuts import render, redirect
from django.urls import reverse
import re
from apps.user.models import User


# /user/register
def register(request):
    """显示注册页面"""
    return render(request, 'register.html')


# /user/register_handle
def register_handle(request):
    """注册处理"""
    # 1.获取数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    cpassword = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 2.数据校验
    if not all([username, password, cpassword, email]):
        return render(request, 'register.html', {'err_msg': '数据不完整！'})

    if password != cpassword:
        return render(request, 'register.html', {'err_msg': '两次输入的密码不一致！'})

    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'err_msg': '邮箱格式不正确！'})

    if allow != 'on':
        return render(request, 'register.html', {'err_msg': '请同意用户协议！'})

    # 校验用户是否已存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    
    if user:
        # 用户已存在
        return render(request, 'register.html', {'err_msg': '用户已存在！'})

    # 3.业务处理
    user = User.objects.create_user(user_name, email, password)
    user.is_active = 0
    user.save()

    # 4.返回应答
    return redirect(reverse('goods:index'))
