from django.shortcuts import render


# /user/register
def register(request):
    """显示注册页面"""
    return render(request, 'register.html')
