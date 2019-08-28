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
        skus = conn.hgetall(cart_key)

        # 获取用户购物车中商品的单价和数量

        # 计算用户购物车中商品的总数量和总价

        return render(request, 'cart.html')


# 使用的ajax请求，不能使用LoginRequireMixin类校验登录，会将后台请求跳转到登录页面，前台看不到
class CartAddView(View):
    '''添加购物车'''
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res':0, 'errmsg':'请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res':1, 'errmsg':'数据不完整'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':2, 'errmsg':'商品不存在'})
        # 校验商品数量是否合法，是否大于库存数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res':3, 'errmsg':'商品数量不合法'})
        if count > sku.stock:
            return JsonResponse({'res':4, 'errmsg':'数量大于库存数量'})

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

        return JsonResponse({'res':5, 'total_count':total_count, 'message':'添加成功'})

