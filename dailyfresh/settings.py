"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
import sys


redis_celery_minio_ip = '192.168.1.21'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y3!ggq+pak3$v#%5re-oa-5gd*tl-olabbd(w=nkqnp2$3alfw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',  # 富文本
    'haystack',  # 全文检索框架
    'apps.user',  # 用户模块
    'apps.goods',  # 商品模块
    'apps.cart',  # 购物车模块
    'apps.order'  # 订单模块
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'USER': 'root',
        'PASSWORD': 'damonmok',
        'HOST': 'localhost',
        'PORT': 3306
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTH_USER_MODEL = 'user.User'


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = '/var/www/dailyfresh/static'  # 指定收集静态资源的路径


# 富文本编辑器配置
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'silver',
    'width': 600,
    'height': 400,
}


# 163发送邮件配置
# 发送Email配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 发邮件的smtp服务器地址
EMAIL_HOST = 'smtp.163.com'  # 可以查看你使用那个服务，就是对应的哪个服务器地址
EMAIL_PORT = 25  # 端口号固定

# 发送邮件的邮箱
EMAIL_HOST_USER = 'damonmok1216@163.com'  # 你的邮箱名字
# 邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'DOHEJSTCYXQTPUUK'  # 授权码
# 收件人看到的发件人
EMAIL_FROM = '天天生鲜<damonmok1216@163.com>'


# Celery
CELERY_BROKER_URL = 'redis://%s:6379/0' % redis_celery_minio_ip
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'redis://%s:6379/0' % redis_celery_minio_ip
CELERY_TASK_SERIALIZER = 'json'


# 配置redis作为缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:6379/1" % redis_celery_minio_ip,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# 把session存储在redis中
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# 若当前未登录，去访问要登录才能访问的页面时，会跳转到以下地址。
# 跳转后会在地址栏带上?next=xxx参数。xxx为跳转前的页面地址
LOGIN_URL = "/user/login"


# 自定义文件上传(Minio)
# 指定点击保存的时候，由哪个类去处理
DEFAULT_FILE_STORAGE = "utils.storage.MinioStorage"

# Minio服务器的url
MINIO_BASE_URL = "%s:9000" % redis_celery_minio_ip


# 全文检索(haystack)引擎配置,使用Whoosh搜索引擎
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    },
}

# 当数据模型增删改时，会自动更新索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# 配置Haystack搜索结果每页多少条数据
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 1





