from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator
from goods.models import Goods, GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from order.models import OrderGoods
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


# /goods/goods_id
class GoodsDetailView(View):
    '''商品详情页'''
    def get(self, request, goods_id):
        '''显示用户点击的商品详情页'''
        # 获取商品种类信息
        types = GoodsType.objects.all()

        # 获取商品SKU
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品同类SPU的其他商品sku信息
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取新品信息
        new_goods = GoodsSKU.objects.filter(gtype=sku.gtype).order_by('-update_time')[:2]

        # 获取商品评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取用户购物车信息
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 如果用户已登录,获取用户购物车信息
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 保存最近浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            # 移除redis数据库中已存在的最近重复浏览的商品信息
            conn.lrem(history_key, 0, goods_id)
            # 从左插入用户最近浏览的商品信息
            conn.lpush(history_key, goods_id)
            # 只保存用户最近浏览的5条记录
            conn.ltrim(history_key, 0, 4)

        # 组织上下文
        context = {'types':types,
                   'sku':sku,
                   'same_spu_skus':same_spu_skus,
                   'new_goods':new_goods,
                   'sku_orders':sku_orders,
                   'cart_count':cart_count}

        # 使用模板
        return render(request, 'detail.html', context)

# /goods/(type)/(page)?sort=(['default', 'price', 'hot'])
class GoodsListView(View):
    '''商品列表页面'''
    def get(self, request, type_id, page):
        # 获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品的所有分类信息
        types = GoodsType.objects.all()

        # 获取排序信息
        # default:默认按id排序
        # price:按价格排序
        # hot:按人气(销量)排序
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(gtype=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(gtype=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(gtype=type).order_by('-id')
        # 对数据进行分页显示
        paginator = Paginator(skus, 3)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception:
            page = 1
        # 用户要求显示的页数不存在时,设置显示第1页
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        skus_page = paginator.page(page)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(gtype=type).order_by('-create_time')[:2]

        # 获取用户购物车信息
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'type':type,
                   'types':types,
                   'skus_page':skus_page,
                   'new_skus':new_skus,
                   'cart_count':cart_count,
                   'sort':sort}

        return render(request, 'list.html', context)
