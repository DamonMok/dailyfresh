from django.contrib import admin
from django.core.cache import cache
from apps.goods.models import GoodsType, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexPromotionBanner, \
    IndexTypeGoodsBanner


class BaseAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        """ 新增或者修改模型 """
        super().save_model(request, obj, form, change)

        # celery生成首页静态页面
        from .tasks import generate_static_index
        generate_static_index.delay()

        # 清除首页数据的缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """ 删除模型 """
        super().delete_model(request, obj)

        # celery生成首页静态页面
        from .tasks import generate_static_index
        generate_static_index.delay()

        # 清除首页数据的缓存
        cache.delete('index_page_data')


class GoodsTypeAdmin(BaseAdmin):
    pass


class IndexGoodsBannerAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)

admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)

admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)

admin.site.register(Goods, GoodsAdmin)

admin.site.register(GoodsSKU, GoodsSKUAdmin)




