from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import time


@shared_task
def email_to_activate_user(username, user_id, email):
    # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/{用户id}
    # 用户id需要加密(使用itsdangerous)

    # 加密用户的身份信息，生成激活token
    serializer = Serializer(settings.SECRET_KEY, 3600)  # 秘钥、过期时间
    user_info = {'confirm': user_id}
    token = serializer.dumps(user_info).decode()  # 返回加密后的字符串

    # 发送激活邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [email]
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1><h1>请点击下面链接激活您的账户</h1><br /><a ' \
                   'href="http://%s:8888/user/active/%s">http://%s:8888/user/active/%s</a>' % \
                   (username, settings.redis_celery_minio_ip, token, settings.redis_celery_minio_ip, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)