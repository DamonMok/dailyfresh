from django.contrib import admin
from apps.goods.models import GoodsType, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexPromotionBanner, \
    IndexTypeGoodsBanner

admin.site.register([GoodsType, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexPromotionBanner,
                    IndexTypeGoodsBanner])
