from __future__ import absolute_import, unicode_literals
import os
from django.conf import settings
from django.template import loader, RequestContext
from celery import shared_task
from .models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


@shared_task
def generate_static_index():

    # 商品类型
    goods_type = GoodsType.objects.all()

    # 首页轮播商品
    goods_banner = IndexGoodsBanner.objects.all().order_by('index')

    # 首页促销活动
    promotion_banner = IndexPromotionBanner.objects.all()

    # 首页分类商品
    for kind in goods_type:
        # titles
        kind.title_goods = IndexTypeGoodsBanner.objects.filter(type=kind, display_type=0).order_by('index')

        # details
        kind.detail_goods = IndexTypeGoodsBanner.objects.filter(type=kind, display_type=1).order_by('index')

    # 购物车
    cart_count = 0

    context = {
        "goods_type": goods_type,
        "goods_banner": goods_banner,
        "promotion_banner": promotion_banner,
        "cart_count": cart_count
    }

    # 生成静态html
    template = loader.get_template('static_index.html')  # 生成模板

    static_index_html = template.render(context)  # 根据上下文，渲染模板生成html

    # 保存静态页面文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
