from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from user.models import User
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


# /user/user
class UserInfoView(LoginRequireMixin, View):
    '''用户中心'''
    def get(self, request):
        '''访问用户中心'''
        return render(request, 'user_center_info.html', {'page':'user'})


# /user/order
class UserOrderView(LoginRequireMixin, View):
    '''用户订单中心'''
    def get(self, request):
        '''访问用户订单中心'''
        return render(request, 'user_center_order.html', {'page':'order'})


# /user/user
class UserAddrView(LoginRequireMixin, View):
    '''用户收货地址'''
    def get(self, request):
        '''访问用户收货地址'''
        return render(request, 'user_center_site.html', {'page':'site'})