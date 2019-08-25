from django.contrib import admin
from django.core.cache import cache
from goods.models import Goods, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, GoodsType, IndexTypeGoodsBanner
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    '''模型管理后台类'''
    def save_model(self, request, obj, form, change):
        '''新增或更新表中数据时调用'''
        super().save_model(request, obj, form, change)
        # 发出任务让celery重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_redis_cache')

    def delete_model(self, request, obj):
        '''删除表中数据时调用'''
        super().delete_model(request, obj)
        # 发出任务让celery重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_redis_cache')


class GoodsAdmin(BaseModelAdmin):
    '''商品SPU后台管理类'''
    pass


class GoodsSKUAdmin(BaseModelAdmin):
    '''商品SKU后台管理类'''
    pass


class GoodsTypeAdmin(BaseModelAdmin):
    '''商品类型后台管理类'''
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    '''首页商品轮播图后台管理类'''
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    '''首页商品促销展示后台管理类'''
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    '''首页商品分类展示后台管理类'''
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
