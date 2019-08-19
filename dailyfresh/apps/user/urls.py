from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, UserAddrView, LogoutView

urlpatterns = [
    url(r'^register/', RegisterView.as_view(), name='register'), # 注册页面
    # url(r'^register_handle/', RegisterView.as_view, name='register_handle'), # 注册提交
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'), # 用户激活
    url(r'^login/', LoginView.as_view(), name='login'), # 登录页面
    url(r'^logout/', LogoutView.as_view(  ), name='logout'), # 注销登录
    url(r'^order/', UserOrderView.as_view(), name='order'), # 用户全部订单
    url(r'^site/', UserAddrView.as_view(), name='site'),  # 用户全部收货地址
    url(r'^$', UserInfoView.as_view(), name='user'), # 用户中心

]
