from datetime import datetime
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.http import JsonResponse
from django.db import transaction
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from apps.order.models import OrderInfo, OrderGoods


# Create your views here.
# /order/place
class OrderPlaceView(View):
    """ 提交订单页面显示 """
    def post(self, request):
        """ 提交订单页面显示 """
        # 获取登录的用户
        user = request.user

        # sku_id被绑定在表单的复选框按钮中，只有选中的才会被提交
        sku_ids = request.POST.getlist('sku_ids')  # [2, 4, ...]

        con = get_redis_connection('default')

        # 获取商品sku
        skus = []
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)

            # 获取商品数量
            cart_key = 'cart_%s' % user.id
            count = con.hget(cart_key, sku_id)

            # 计算商品小计
            sku.amount = sku.price * int(count)
            sku.count = int(count)
            skus.append(sku)

            total_count += sku.count  # 总件数
            total_price += sku.amount  # 总金额

        transition_price = 10  # 运费
        final_price = total_price + transition_price  # 实付款

        # 收货地址
        addrs = Address.objects.filter(user=user)

        # 订单的商品id
        sku_ids = ','.join(sku_ids)

        # 组织参数
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transition_price': transition_price,
            'final_price': final_price,
            'sku_ids': sku_ids
        }

        return render(request, 'place_order.html', context)


# /order/commit
# 通过悲观锁解决并发引起的资源竞争
class OrderCommitView2(View):
    """ 订单创建 """
    @transaction.atomic
    def post(self, request):
        """ 订单创建 """
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 验证支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式不合法'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist as e:
            return JsonResponse({'res': 3, 'errmsg': '地址不存在'})

        # ************** 向【订单信息表】df_order_info 插入一条数据 **************
        # 组织参数
        # 订单id：20201116163728+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transition_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务还原点
        sid = transaction.savepoint()
        try:
            # 插入数据库
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transition_price)

            # ************** 向【订单商品表】df_order_goods 插入N条数据 **************
            # 订单中有多少件商品，就插入多少条
            sku_ids = sku_ids.split(',')
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            for sku_id in sku_ids:
                # 遍历订单中的商品，进行插入
                # 获取商品信息
                try:
                    # 悲观锁，查询时加锁
                    # 哪个用户先获得锁，谁就先执行；没获得锁的就等待
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    # sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist as e:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                import time
                print(user.username, sku.stock)
                time.sleep(10)

                # 获取商品的数量
                count = con.hget(cart_key, sku_id)

                if int(count) > sku.stock:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 6, 'errmsg': '库存不足'})

                # 更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # 插入数据库
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # 计算订单商品的总数量和总价格
                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

            # ************** 更新 【订单信息表】的商品总数量和总金额 **************
            order.total_price = total_price
            order.total_count = total_count
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
        transaction.savepoint_commit(sid)
        # ************** 清除购物车的记录 **************
        # sku_ids = [2, 4, 5]
        # hdel(name, *keys)  keys是一个位置参数，不能直接把数组传进去。
        # 需要在前面加*号进行对数组拆包[2, 4, 5]--->2, 4, 5
        con.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})

# 通过乐观锁解决并发引起的资源竞争
class OrderCommitView(View):
    """ 订单创建 """
    @transaction.atomic
    def post(self, request):
        """ 订单创建 """
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 验证支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式不合法'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist as e:
            return JsonResponse({'res': 3, 'errmsg': '地址不存在'})

        # ************** 向【订单信息表】df_order_info 插入一条数据 **************
        # 组织参数
        # 订单id：20201116163728+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transition_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务还原点
        sid = transaction.savepoint()
        try:
            # 插入数据库
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transition_price)

            # ************** 向【订单商品表】df_order_goods 插入N条数据 **************
            # 订单中有多少件商品，就插入多少条
            sku_ids = sku_ids.split(',')
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            for sku_id in sku_ids:
                # 遍历订单中的商品，进行插入

                for i in range(3):
                    # 循环3次，通过乐观锁解决资源竞争
                    # 获取商品信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist as e:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 获取商品的数量
                    count = con.hget(cart_key, sku_id)

                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 6, 'errmsg': '库存不足'})

                    # 更新商品的库存和销量
                    # sku.stock -= int(count)
                    # sku.sales += int(count)
                    # sku.save()

                    # 乐观锁:在更改的时候加锁
                    # 更改前，通过判断【库存】是否和查询的时候一致，去执行后续的操作。
                    # 如果一致，直接更改。
                    # 如果不一致，则产生了资源竞争。重复3次下单操作，避免资源竞争。
                    origin_stock = sku.stock  # 记录一开始查询的库存
                    new_stock = sku.stock - int(count)  # 要更改的库存
                    new_sales = sku.sales + int(count)  # 要更改的销量

                    # res代表受影响的行数，>0代表成功
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales=new_sales)
                    if res == 0:
                        if i == 2:
                            transaction.savepoint_rollback(sid)  # 回滚
                            return JsonResponse({'res': 8, 'errmsg': '下单失败'})
                        continue

                    # 插入数据库
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # 计算订单商品的总数量和总价格
                    amount = sku.price * int(count)
                    total_count += int(count)
                    total_price += amount

                    break

            # ************** 更新 【订单信息表】的商品总数量和总金额 **************
            order.total_price = total_price
            order.total_count = total_count
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
        transaction.savepoint_commit(sid)
        # ************** 清除购物车的记录 **************
        # sku_ids = [2, 4, 5]
        # hdel(name, *keys)  keys是一个位置参数，不能直接把数组传进去。
        # 需要在前面加*号进行对数组拆包[2, 4, 5]--->2, 4, 5
        con.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})









