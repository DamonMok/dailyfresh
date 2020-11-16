from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address


# Create your views here.
# /order/place
class OrderPlaceView(View):
    """ 提交订单页面显示 """
    def post(self, request):
        """ 提交订单页面显示 """
        # 获取登录的用户
        user = request.user

        # sku_id被绑定在表单的复选框按钮中，只有选中的才会被提交
        sku_ids = request.POST.getlist('sku_ids')  # [2, 4, ...]

        con = get_redis_connection('default')

        # 获取商品sku
        skus = []
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)

            # 获取商品数量
            cart_key = 'cart_%s' % user.id
            count = con.hget(cart_key, sku_id)

            # 计算商品小计
            sku.amount = sku.price * int(count)
            sku.count = int(count)
            skus.append(sku)

            total_count += sku.count  # 总件数
            total_price += sku.amount  # 总金额

        transition_price = 10  # 运费
        final_price = total_price + transition_price  # 实付款

        # 收货地址
        addrs = Address.objects.filter(user=user)

        # 组织参数
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transition_price': transition_price,
            'final_price': final_price,
        }

        return render(request, 'place_order.html', context)







