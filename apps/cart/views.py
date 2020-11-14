from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection

# Create your views here.
class CartAddView(View):
    """ 购物车记录添加 """
    def get(self, request):
        """ 购物车记录添加"""
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 数据接收
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验

        # 校验数据完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加购物车记录
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 查找redis数据库中是否已经有该记录
        # 已存在则更新，不存在就添加
        cart_count = con.hget(cart_key, sku_id)
        if cart_key:
            # 已存在，累加购物车商品的数目
            count += cart_count

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 设置redis-hash中对应的值
        # 如果sku_id已存在，则更新；没有，则添加
        con.hset(cart_key, sku_id, count)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '添加成功'})





