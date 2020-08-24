from django.shortcuts import render
from django.views.generic import View


# 127.0.0.1:8000
class IndexView(View):
    """首页"""
    def get(self, request):
        """首页显示"""
        return render(request, 'index.html')
