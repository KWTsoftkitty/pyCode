from django.core.mail import send_mail
from django.conf import settings
from django.template import loader
from celery import Celery


# 导入django配置信息(worker上启动celery时用)
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()

from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# 创建一个celery实例
app = Celery('celery_tasks.tasks', broker='redis://192.168.0.103:6379/3')


# 定义任务函数
@app.task
def send_reigster_active_mail(to_email, username, token):
    '''发送激活邮件'''
    subject = '天天生鲜用户激活'
    message = ''
    sender = settings.EMAIL_FROM
    reciver = [to_email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)

    send_mail(subject, message, sender, reciver, html_message=html_message)


@app.task
def generate_static_index_html():
    '''使用celery生成首页静态html文件'''
    # 获取商品分类
    types = GoodsType.objects.all()

    # 获取首页商品轮播图展示
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页商品促销活动
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取商品分类展示
    for type in types:
        # 根据商品种类按商品标题查询对应商品升序排列
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        # 根据商品种类按商品图片查询对应商品升序排列
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 动态给type对象添加属性，分别是商品种类对应的商品标题和商品图片
        type.title_banners = title_banners
        type.image_banners = image_banners

    # 组织上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners}

    # 加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # 渲染模板
    static_index_html = temp.render(context)
    # 生成首页模板文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
