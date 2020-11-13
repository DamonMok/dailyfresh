from haystack import indexes
from .models import GoodsSKU


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)  # 使用数据模板来构建搜索引擎将索引的文档

    def get_model(self):
        return GoodsSKU  # 返回要检索的模型类

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
