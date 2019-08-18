from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from user.models import User
import re
# Create your views here.


# 注册页面
def register(request):
    return render(request, 'register.html')


# 注册处理
def register_handle(request):
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    cpassword = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 验证数据
    # 1. 验证数据是否为空
    if not all([username,password,cpassword,email]):
        return render(request, 'register.html', {'errmsg':'注册信息不完整'})
    # 2. 验证再次密码是否一致
    if password != cpassword:
        return render(request, 'register.html', {'errmsg':'再次密码不一致'})
    # 3. 验证邮箱格式
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg':'邮箱格式不正确'})
    # 4. 验证用户是否同意相关协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg':'请同意协议'})
    # 5. 验证用户名是否已存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None

    if user:
        return render(request, 'register.html', {'errmsg':'用户名已存在'})

    # 提交数据
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    # 返回应答
    return redirect(reverse('goods:index'))
