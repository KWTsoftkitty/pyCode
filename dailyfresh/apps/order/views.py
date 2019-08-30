from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from utils.mixin import LoginRequireMixin
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from datetime import datetime
from alipay import AliPay
import os
# Create your views here.


# /order/place
class OrderPlaceView(LoginRequireMixin, View):
    '''订单页面显示'''
    def post(self, request):
        '''显示用户订单页'''
        # 获取数据
        user = request.user
        sku_ids = request.POST.getlist('sku_ids')

        # 数据校验
        if not sku_ids:
            return redirect(reverse('cart:show'))

        # 创建redis数据库连接
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 用户要购买的商品,商品总数和总价
        skus = list()
        total_count = 0
        total_price = 0
        # 遍历sku_ids获取用户要购买的商品信息
        for sku_id in sku_ids:
            # 获取商品对象
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户购买的商品数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price*int(count)
            # 动态给商品添加属性
            sku.count = count
            sku.amount = amount
            # 更新用户要购买商品的总数和总价
            total_count += int(count)
            total_price += amount
            # 记录用户要购买的商品
            skus.append(sku)

        # 运费
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price,
                   'total_pay': total_pay,
                   'transit_price': transit_price,
                   'addrs': addrs,
                   'sku_ids': sku_ids}

        # 使用模板
        return render(request, 'place_order.html', context)


# /order/commit
class OrderCommitView(View):
    '''用户提交订单'''
    @transaction.atomic
    def post(self, request):
        '''用户以ajax post方式提交订单'''
        # 获取数据
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')

        # 校验数据
        # 参数完整性
        if not all([sku_ids, addr_id, pay_method]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        # 支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式不合法'})
        # 用户地址
        try:
            address = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '收货地址不存在'})

        # todo: 核心业务->创建订单，使用乐观锁解决高并发问题
        # 生成订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10
        # 商品总数和总价
        total_count = 0
        total_price = 0
        # 设置事务保存点
        save_id = transaction.savepoint()

        try:
            # todo: 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=address,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # todo: 用户订单中有几个商品，就需要向df_order_goods表中添加几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    # 获取商品信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                    # 从redis数据库中获取用户要购买的商品的数量
                    count = conn.hget(cart_key, sku_id)

                    # todo: 判断商品的库存
                    if int(count) > sku.stock:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 5, 'errmsg': '商品库存不足'})

                    # todo: 更新商品的库存和销量
                    # 获取更新前的商品库存，用乐观锁更新商品库存时使用
                    origin_stock = sku.stock
                    new_stock = origin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # todo: 乐观锁更新商品库存的方式：
                    # update df_goods_sku set stock=new_stock, sales=new_sales where id=sku_id and stock = orgin_stock
                    # sql语句条件中加入判断当前商品库存是否和更新前一致，如不一致，跳出当前循环，进入下一次循环，重新获取商品库存：origin_stock = sku.stock
                    # 如循环3次后依然不一致，则回滚事务，并响应请求结果
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试3次后回滚事务，响应下单失败
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 6, 'errmsg': '下单失败'})
                        continue

                    # todo: 向df_order_goods表中添加对应商品的记录
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # todo: 累加计算订单商品的总数和总价
                    amount = sku.price*int(count)
                    total_count += int(count)
                    total_price += amount

                    # 跳出循环
                    break

            # todo: 更新df_order_info订单信息表中的商品总数和总价
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 以上操作期间出现任何异常都回滚事务，响应失败
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': str(e)})

        # todo: 提单事务保存点之后的所有事务
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中对应的商品记录，可以清除多个商品：拆包的方式
        conn.hdel(cart_key, *sku_ids)

        # 响应下单成功
        return JsonResponse({'res': 8, 'message': '下单成功'})


# /order/pay
class OrderPayView(View):
    '''用户支付'''
    def post(self, request):
        '''用户对订单进行支付'''
        # 验证用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 获取请求参数并校验
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist as e:
            return JsonResponse({'res': 2, 'errmsg': str(e)})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2016101400685608",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# /order/check
class CheckPayView(View):
    '''查询支付结果'''
    def post(self, request):
        '''
        用户支付后自动发起ajax请求，让网站访问支付宝平台，查询支付结果并返回
        如有公网IP，则不需要此步，可设置用户支付后，支付宝平台的回调地址，返回结果给用户
        '''
        # 验证用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 获取请求参数并校验
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2016101400685608",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #         "code": "10000", # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS", # 支付结果
            #         "total_amount": "20.00"
            # }

            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(3)
                continue
            else:
                # 支付出错
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


# /order/comment
class OrderCommentView(LoginRequireMixin, View):
    '''用户评论'''
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
