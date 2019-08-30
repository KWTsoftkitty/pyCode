from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from utils.mixin import LoginRequireMixin
from goods.models import GoodsSKU
# Create your views here.


# /cart/show
class CartInfoView(LoginRequireMixin, View):
    '''显示购物车页面'''
    def get(self, request):
        # 获取用户购物车中商品的信息
        user = request.user
        # 用户购物车中的信息保存在redis数据库，格式：cart_user.id: {goods.id: 商品数量}
        cart_key = 'cart_%d' % user.id
        # 创建redis数据库连接
        conn = get_redis_connection('default')
        cart_goods = conn.hgetall(cart_key)

        # 获取用户购物车中商品的单价和数量
        skus = list()
        total_count = 0
        total_price = 0
        for sku_id, count in cart_goods.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # 单个商品的总价
            amount = sku.price*int(count)
            # 给商品对象添加属性
            sku.amount = amount
            sku.count = count
            # 商品列表
            skus.append(sku)
            # 商品总数目和总价钱
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {'total_count': total_count,
                   'total_price': total_price,
                   'skus': skus}

        # 使用模板
        return render(request, 'cart.html', context)



        # 计算用户购物车中商品的总数量和总价

        return render(request, 'cart.html')


# /cart/add
# 使用ajax请求，不能使用LoginRequireMixin类校验登录，会将后台请求跳转到登录页面，前台看不到
class CartAddView(View):
    '''添加购物车'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg':'请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})
        # 校验商品数量是否合法，是否大于库存数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 3, 'errmsg': '商品数量不合法'})
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '数量大于库存数量'})

        # 业务处理：添加购物车记录
        # 先从redis数据库中查看是否已有对应商品的购物车记录，如果有：更新，没有：添加
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车中商品的条目数
        total_count = conn.hlen(cart_key)

        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '添加成功'})


# /cart/update
# 使用ajax请求
class CartUpdateView(View):
    '''更新用户购物车信息'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})
        # 校验商品数量是否合法，是否大于库存数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 3, 'errmsg': '商品数量不合法'})
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '数量大于库存数量'})

        # 业务处理：添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hset(cart_key, sku_id, count)
        # 更新购物车中商品的总数目, conn.hvals(cart_key) -> [商品1的数量，商品2的数量，...]
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '更新成功'})


# /cart/delete
# 使用ajax请求
class CartDeleteView(View):
    '''删除用户购物车记录'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')

        # 校验数据
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})

        # 业务处理：删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hdel(cart_key, sku_id)
        # 更新购物车中商品的总数目, conn.hvals(cart_key) -> [商品1的数量，商品2的数量，...]
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 2, 'total_count': total_count, 'message': '删除成功'})
