from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, OrderCommentView

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'), # 用户订单页面显示
    url(r'^commit$', OrderCommitView.as_view(), name='commit'), # 用户提单订单
    url(r'^pay$', OrderPayView.as_view(), name='pay'), # 用户支付订单
    url(r'^check$', CheckPayView.as_view(), name='check'), # 查询用户支付是否成功
    url(r'^comment/(?P<order_id>.+)$', OrderCommentView.as_view(), name='comment'),  # 订单评论

]
