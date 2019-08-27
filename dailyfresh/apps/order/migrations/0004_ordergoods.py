# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_auto_20190822_1554'),
        ('order', '0003_auto_20190822_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('count', models.IntegerField(verbose_name='商品数目', default=1)),
                ('price', models.DecimalField(verbose_name='商品价格', max_digits=10, decimal_places=2)),
                ('comment', models.CharField(verbose_name='商品评论', max_length=256, default='')),
                ('order', models.ForeignKey(verbose_name='订单', to='order.OrderInfo')),
                ('sku', models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU')),
            ],
            options={
                'verbose_name': '订单商品',
                'verbose_name_plural': '订单商品',
                'db_table': 'df_order_goods',
            },
        ),
    ]
