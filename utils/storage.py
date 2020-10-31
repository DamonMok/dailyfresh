from django.core.files.storage import Storage
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)


class MinioStorage(Storage):

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # 1.使用endpoint、access key和secret key来初始化minio_client对象。
        minio_client = Minio('192.168.8.118:9000',
                            access_key='minioadmin',
                            secret_key='minioadmin',
                            secure=False)

        etag = None

        try:
            # 2.调用make_bucket来创建一个存储桶。
            minio_client.make_bucket("images", location="cn-north-1")
        except BucketAlreadyOwnedByYou as err:
            print(err.message)
        except BucketAlreadyExists as err:
            print(err.message)
        except ResponseError as err:
            print(err)
        finally:
            try:
                # 3.上传文件
                etag = minio_client.put_object('images', content.name, content, content.size)
            except ResponseError as err:
                print(err)
        print(etag)
        return etag[0]

    def exists(self, name):
        return False

    def url(self, name):
        print(name)
        return "http://192.168.8.119:9000/%s" % name
