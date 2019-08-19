from django.core.mail import send_mail
from django.conf import settings
from celery import Celery


# 导入django配置信息(worker上启动celery时用)
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()


# 创建一个celery实例
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/3')


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


