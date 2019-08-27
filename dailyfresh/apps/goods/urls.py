from django.conf.urls import url
from goods.views import IndexView, GoodsDetailView, GoodsListView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'), # 首页
    url(r'^goods/(?P<goods_id>\d+)$', GoodsDetailView.as_view(), name='detail'), # 商品详情页
    url(r'^goods/(?P<type_id>\d+)/(?P<page>\d+)$', GoodsListView.as_view(), name='list'), # 商品分类列表页

]
