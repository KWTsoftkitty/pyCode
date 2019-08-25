from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
# Create your views here.


# /---首页
class IndexView(View):
    '''首页视图'''
    def get(self, request):
        # 先从redis缓存中获取主页信息
        context = cache.get('index_redis_cache')

        if context is None:
            # 获取商品分类
            types = GoodsType.objects.all()

            # 获取首页商品轮播图展示
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页商品促销活动
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取商品分类展示
            for type in types:
                # 根据商品种类按商品标题查询对应商品升序排列
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                # 根据商品种类按商品图片查询对应商品升序排列
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 动态给type对象添加属性，分别是商品种类对应的商品标题和商品图片
                type.title_banners = title_banners
                type.image_banners = image_banners

            # 组织上下文
            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置首页redis缓存
            cache.set('index_redis_cache', context, 3600)

        # 获取用户购物车中商品个数
        # 如果用户已登录，则获取购物车中的商品个数，如果未登录显示0.
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            # 已登录
            # 创建redis数据库连接
            conn = get_redis_connection('default')
            # 设置redis数据库以hash方式存储的购物车记录的键
            cart_key = 'cart_%d' % user.id
            # hlen方法获取键值对的个数
            cart_count = conn.hlen(cart_key)

        # 更新上下文中购物车信息
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


