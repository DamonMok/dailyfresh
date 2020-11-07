from django.contrib import admin
from apps.goods.models import GoodsType, Goods, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexPromotionBanner, \
    IndexTypeGoodsBanner


class BaseAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        """ 新增或者修改模型 """
        super().save_model(request, obj, form, change)

        # celery生成首页静态页面
        from .tasks import generate_static_index
        generate_static_index.delay()


class GoodsTypeAdmin(BaseAdmin):
    pass


class IndexGoodsBannerAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)

admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)

admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
