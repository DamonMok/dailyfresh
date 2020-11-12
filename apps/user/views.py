from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
import re
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from apps.user.tasks import email_to_activate_user
# from utils.mixin import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection


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
        email_to_activate_user.delay(username, user.id, email)

        # 5.返回应答
        return redirect(reverse('goods:index'))


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
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        # 1.获取数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 2.数据校验
        if not all([username, password]):
            return render(request, 'login.html', {'err_msg': '数据不完整!'})

        # 3.业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名、密码正确
            if user.is_active:
                # 用户已激活
                login(request, user)  # 记录用户的登录状态

                # 获取登录成功需要跳转的页面
                # 有next就跳转到next页面，没有next就跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)

                # 是否记住密码
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'err_msg': '用户未激活!'})
        else:
            # 用户名、密码错误
            return render(request, 'login.html', {'err_msg': '用户名或密码错误!'})


# user/logout
class LogoutView(View):
    """退出登录"""
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        # 显示
        current_page = 'info'

        # 基本信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 最近浏览:使用redis的list存储
        # listName[item, item, ....]----->history_userID[skuID1, skuID2, ...]
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)  # ->[2, 4, 1]

        # 从数据库中查询商品的具体信息
        goods_list = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            goods_list.append(goods)

        context = {
            'current_page': current_page,
            'address': address,
            'goods_list': goods_list
        }

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request):
        # 显示
        current_page = 'order'
        return render(request, 'user_center_order.html', {'current_page': current_page})


# /user/address
class UserAddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        # 显示
        current_page = 'address'

        user = request.user

        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'current_page': current_page, 'address': address})

    def post(self, request):
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            # 校验数据完整性
            return render(request, 'user_center_site.html', {'err_msg': '数据不完整!'})

        if not re.match(r'^1[3|4|5|7|8|][0-9]{9}$', phone):
            # 验证手机号
            return render(request, 'user_center_site.html', {'err_msg': '手机格式不正确!'})

        # 业务处理：地址添加
        # 如果用户已存在默认收货地址，添加的地址不作为默认地址；否则作为默认收货地址
        user = request.user

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答
        return redirect(reverse('user:address'))

