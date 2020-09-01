from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
import re
from apps.user.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired


# /user/register
class RegisterView(View):
    """注册"""
    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
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
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4.激活用户
        self.email_to_activate_user(username, user, email)

        # 5.返回应答
        return redirect(reverse('goods:index'))

    @staticmethod
    def email_to_activate_user(username, user, email):
        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/{用户id}
        # 用户id需要加密(使用itsdangerous)

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)  # 秘钥、过期时间
        user_info = {'confirm': user.id}
        token = serializer.dumps(user_info).decode()  # 返回加密后的字符串

        # 发送激活邮件
        subject = '天天生鲜欢迎信息'
        message = ''
        sender = settings.EMAIL_FROM
        receiver = [email]
        html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1><h1>请点击下面链接激活您的账户</h1><br /><a ' \
                       'href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % \
                       (username, token, token)
        send_mail(subject, message, sender, receiver, html_message=html_message)


class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        """进行用户激活"""
        # 1.对token进行解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            user_info = serializer.loads(token)
            user_id = user_info['confirm']
            print(user_info)
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 激活完成后，跳转到登录页面
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 激活时间超时
            return HttpResponse('激活链接已过期！')


# user/login
class LoginView(View):
    """登录"""
    def get(self, request):
        """显示登录页面"""
        return render(request, 'login.html')
