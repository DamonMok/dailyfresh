from django.shortcuts import render
from django.views.generic import View
from django.core.cache import cache
from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection


# 127.0.0.1:8000
class IndexView(View):
    """首页"""
    def get(self, request):
        """首页显示"""

        # 各用户相同的数据

        context = cache.get('index_page_data')  # 从缓存中获取

        if context is None:

            # 缓存为空，从数据库中查询数据，并设置缓存
            # 商品类型
            goods_type = GoodsType.objects.all()

            # 首页轮播商品
            goods_banner = IndexGoodsBanner.objects.all().order_by('index')

            # 首页促销活动
            promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

            # 首页分类商品
            for kind in goods_type:
                # titles
                kind.title_goods = IndexTypeGoodsBanner.objects.filter(type=kind, display_type=0).order_by('index')

                # details
                kind.detail_goods = IndexTypeGoodsBanner.objects.filter(type=kind, display_type=1).order_by('index')

            context = {
                "goods_type": goods_type,
                "goods_banner": goods_banner,
                "promotion_banner": promotion_banner,
            }

            # 把各用户相同的数据存入缓存
            # set(key, value, time_out) value可以是任意python对象
            cache.set('index_page_data', context, 3600)

        # 各用户不同的数据
        # 购物车:使用redis的hash存储
        # hashName[key:value]---->cart_userID[skuID:cartCount]
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            # 已经登录
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        context.update(cart_count=cart_count)

        return render(request, 'index.html', context=context)
