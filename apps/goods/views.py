from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.core.cache import cache
from django.core.paginator import Paginator
from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods
from django_redis import get_redis_connection


# /index
class IndexView(View):
    """首页"""
    def get(self, request):
        """首页显示"""

        # 各用户相同的数据

        context = cache.get('index_page_data')  # 从缓存中获取

        if context is None:
            print('首页数据:数据库')
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
        else:
            print('首页数据:缓存')

        # 各用户不同的数据
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            # 已经登录

            # 购物车:使用redis的hash存储
            # hashName[key:value]---->cart_userID[skuID:cartCount]
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        context.update(cart_count=cart_count)

        return render(request, 'index.html', context=context)


# /goods/1
class DetailView(View):
    """详情页"""
    def get(self, request, goods_id):

        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 同类商品(SPU)的其他规格(SKU)
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取商品的评论信息
        sku_order = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取商品的新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 购物车
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            # 已经登录

            # 购物车:使用redis的hash存储
            # hashName[key:value]---->cart_userID[skuID:cartCount]
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

            # 历史浏览记录:history_user.id : [h1, h2, h3, ...]
            history_key = 'history_%d' % user.id
            con.lrem(history_key, 0, goods_id)  # 删除历史记录数组内已经存在的商品
            con.lpush(history_key, goods_id)  # 把当前浏览的商品，加入到历史浏览记录数组里面
            con.ltrim(history_key, 0, 4)  # 只保存5个商品记录

        context = {
            "sku": sku,
            "same_spu_skus": same_spu_skus,
            "types": types,
            "sku_order": sku_order,
            "new_skus": new_skus,
            "cart_count": cart_count
        }

        return render(request, 'detail.html', context)


# list/种类id/页码?sort=排序方式
class ListView(View):
    """ 列表页 """
    def get(self, request, type_id, page):
        # 显示列表页
        try:
            goods_type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的新品信息
        new_skus = GoodsSKU.objects.filter(type=goods_type).order_by('-create_time')[:2]

        # 获取排序方式：
        # default:默认按照id降序排列
        # price:按照价格升序
        # hot:按照人气降序
        sort = request.GET.get('sort')

        # 按排序方式获取全部商品
        if sort == "price":
            skus = GoodsSKU.objects.filter(type=goods_type).order_by('price')
        elif sort == "hot":
            skus = GoodsSKU.objects.filter(type=goods_type).order_by('-sales')
        else:
            sort = "default"
            skus = GoodsSKU.objects.filter(type=goods_type).order_by('-id')

        # 生成分页器
        paginator = Paginator(skus, 1)  # 每页显示一条

        # 获取第page页的Page实例对象
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        skus_page = paginator.page(page)

        # 购物车
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            # 已经登录

            # 购物车:使用redis的hash存储
            # hashName[key:value]---->cart_userID[skuID:cartCount]
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        context = {
            "page": page,
            "sort": sort,
            "goods_type": goods_type,
            "types": types,
            "new_skus": new_skus,
            "skus_page": skus_page,
            "cart_count": cart_count,
        }

        return render(request, 'list.html', context)













