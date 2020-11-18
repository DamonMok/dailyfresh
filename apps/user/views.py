from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
import re
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
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

                # 是否记住用户名
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
    def get(self, request, page):
        # 显示

        # 获取订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user)

        # 遍历获取订单中商品的信息
        for order in orders:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)  # 每个订单中的商品集合

            # 遍历商品集合，获取每个商品的小计
            for order_sku in order_skus:
                order_sku.amount = order_sku.count * order_sku.price  # 动态绑定小计到商品模型上

            order.order_skus = order_skus  # 每个订单对应的商品集合

            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的Page实例对象
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        order_page = paginator.page(page)

        # 自定义页码控制，最多显示5个页码(分页器的paginator.page_range显示的是所有的页码)
        # 1.如果总页数少于5，显示所有页码
        # 2.如果是前3页，显示1-5页
        # 3.如果是后3页，显示后5页
        # 4.其他情况，显示当前页前2页、当前页、当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page < 3:
            pages = range(1, 6)
        elif page >= num_pages - 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        current_page = 'order'

        # 组织参数
        context = {
            'order_page': order_page,
            'pages': pages,
            'current_page': current_page
        }

        return render(request, 'user_center_order.html', context)


# /user/address
class UserAddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        """ 收货地址显示 """
        current_page = 'address'

        user = request.user

        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'current_page': current_page, 'address': address})

    # TODO 插入表情有问题
    def post(self, request):
        """ 新增收货地址 """
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

