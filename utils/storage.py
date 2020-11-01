from django.core.files.storage import Storage
from django.conf import settings
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
from datetime import timedelta
import json

# 存储桶的名称
bucket_name = 'images'

# 存储端Minio的基本路径
base_url = settings.MINIO_BASE_URL

# minio存储桶策略(读写权限)
# 权限必须可读可写，才能通过路径访问所上传的文件
policy_read_write = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:GetBucketLocation"],
                "Sid": "",
                "Resource": ["arn:aws:s3:::%s" % bucket_name],
                "Effect": "Allow",
                "Principal": {"AWS": "*"}
            },
            {
                "Action": ["s3:ListBucket"],
                "Sid": "",
                "Resource": ["arn:aws:s3:::%s" % bucket_name],
                "Effect": "Allow",
                "Principal": {"AWS": "*"}
            },
            {
                "Action": ["s3:ListBucketMultipartUploads"],
                "Sid": "",
                "Resource": ["arn:aws:s3:::%s" % bucket_name],
                "Effect": "Allow",
                "Principal": {"AWS": "*"}
            },
            {
                "Action": ["s3:ListMultipartUploadParts",
                           "s3:GetObject",
                           "s3:AbortMultipartUpload",
                           "s3:DeleteObject",
                           "s3:PutObject"],
                "Sid": "",
                "Resource": ["arn:aws:s3:::%s/*" % bucket_name],
                "Effect": "Allow",
                "Principal": {"AWS": "*"}
            }
        ]
    }


class MinioStorage(Storage):
    """自定义存储类，覆盖Django自带的存储操作"""

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # 点击保存的时候，会调用这个方法

        # 1.使用endpoint、access key和secret key来初始化minio_client对象。
        minio_client = Minio(base_url,
                            access_key='minioadmin',
                            secret_key='minioadmin',
                            secure=False)

        try:
            # 2.调用make_bucket来创建一个存储桶。
            minio_client.make_bucket(bucket_name, location="cn-north-1")

            # 3.修改存储桶策略为可读可写
            minio_client.set_bucket_policy(bucket_name, json.dumps(policy_read_write))
        except BucketAlreadyOwnedByYou as err:
            print(err.message)
        except BucketAlreadyExists as err:
            print(err.message)
        except ResponseError as err:
            print(err)
        finally:
            try:
                # 4.上传文件
                # 需要设置content_type为图片，不然通过路径读取图片的时候，会直接下载到本地，不会显示在网页上
                minio_client.put_object(bucket_name, content.name, content, content.size, content_type='image/jpeg')
            except ResponseError as err:
                print(err)
            else:
                # 5.获取文件在Minio的路径(不包括ip和端口)
                file_path = '%s/%s' % (bucket_name, content.name)

        return file_path

    def exists(self, name):
        return False

    def url(self, name):
        # image = models.ImageField(upload_to='type', verbose_name='商品类型图片')
        # image.url就可以获取到完整的路径
        full_path = 'http://%s/%s' % (settings.MINIO_BASE_URL, name)
        return full_path
