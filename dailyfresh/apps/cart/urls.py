from django.conf.urls import url
from cart.views import CartInfoView, CartAddView

urlpatterns = [
    url(r'^show$', CartInfoView.as_view(), name='show'), # 购物车页面显示
    url(r'^add$', CartAddView.as_view(), name='add'), # 购物车添加

]
