# Generated by Django 3.1 on 2020-11-01 04:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_auto_20201031_1434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodstype',
            name='image',
            field=models.ImageField(upload_to='type', verbose_name='商品类型图片'),
        ),
    ]
