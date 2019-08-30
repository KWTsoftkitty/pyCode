from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection
from django.core.paginator import Paginator
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from utils.mixin import LoginRequireMixin
from celery_tasks.tasks import send_reigster_active_mail
import re
# Create your views here.


# /user/register
class RegisterView(View):
    '''注册视图'''
    def get(self, request):
        '''请求注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''提交用户注册信息'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 验证数据
        # 1. 验证数据是否为空
        if not all([username, password, cpassword, email]):
            return render(request, 'register.html', {'errmsg': '注册信息不完整'})
        # 2. 验证再次密码是否一致
        if password != cpassword:
            return render(request, 'register.html', {'errmsg': '再次密码不一致'})
        # 3. 验证邮箱格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 4. 验证用户是否同意相关协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 5. 验证用户名是否已存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 提交数据
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 加密用户信息，生成token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info) # bytes
        token = token.decode()

        # 发送激活邮件
        send_reigster_active_mail.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


# /user/active
class ActiveView(View):
    '''用户激活视图'''
    def get(self, request, token):
        '''请求登录页面'''
        # 解密用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user = User.objects.get(id=info['confirm'])
            # 修改用户激活状态
            user.is_active = 1
            user.save()
            # 返回应答
            return redirect(reverse('user:login'))
        except SignatureExpired:
            return HttpResponse('用户激活链接已过期，请重新发送激活邮件')


# /user/login
class LoginView(View):
    '''用户登录视图'''
    def get(self, request):
        '''请求登录页面'''
        # 获取上次登录时记住的用户名信息
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录请求'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        user = authenticate(username=username, password=password)
        # 用户名密码是否正确
        if user is not None:
            # 用户是否激活
            if user.is_active:
                # 保存用户session到redis数据库中
                login(request, user)
                # 用户登录跳转
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                # 记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                # 返回应答
                return response
            else:
                return render(request, 'login.html', {'errmsg':'用户未激活'})
        else:
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


# /user/logout
class LogoutView(View):
    '''用户注销登录'''
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequireMixin, View):
    '''用户中心'''
    def get(self, request):
        '''访问用户中心'''
        # 显示用户基本信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户最近浏览记录
        # 存储在redis数据库，方式：history_userid: [goods_list]
        conn = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        sku_ids = conn.lrange(history_key, 0, 4)
        goods_list = list()
        # 遍历一次查询一次商品，以保证按照最近的浏览顺序显示最近浏览的商品
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_list.append(goods)

        context = {'page':'user', 'address':address, 'goods':goods_list}

        return render(request, 'user_center_info.html', context)


# /user/order/page
class UserOrderView(LoginRequireMixin, View):
    '''用户订单中心'''
    def get(self, request, page):
        '''访问用户订单中心'''
        # 接收数据
        user = request.user
        # 获取用户订单信息
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 遍历订单获取订单中的商品信息
        for order in orders:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            # 遍历订单中所有商品获取每个商品的信息
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态添加属性
                order_sku.amount = amount
            # 动态给订单对象增加属性，保存订单状态
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 2)
        # 获取用户请求的页数并校验
        try:
            page = int(page)
        except Exception:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的page对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        return render(request, 'user_center_order.html', context)


# /user/site
class UserAddrView(LoginRequireMixin, View):
    '''用户收货地址'''
    def get(self, request):
        '''访问用户收货地址'''
        # 获取用户的默认收货地址
        user = request.user
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page':'site', 'address':address})

    def post(self, request):
        '''添加用户的收货地址'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'地址信息不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机号码不合法'})

        # 验证是否存在默认地址
        user = request.user
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 提交数据
        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)

        # 返回应答
        return redirect(reverse('user:site'))
