# Generated by Django 5.0 on 2024-01-05 13:52

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_importorder_supplier_importorderdetail_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='SaleOrder',
            fields=[
                ('sale_orderID', models.AutoField(primary_key=True, serialize=False)),
                ('sale_date', models.DateField(default=django.utils.timezone.now)),
                ('total_revenue', models.FloatField(default=0)),
                ('total_interest', models.FloatField(default=0)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.customer')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.employee')),
            ],
        ),
        migrations.CreateModel(
            name='SaleOrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.FloatField()),
                ('sale_price', models.FloatField()),
                ('revenue', models.FloatField()),
                ('interest', models.FloatField()),
                ('note', models.CharField(default='', max_length=50)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.product')),
                ('sale_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.saleorder')),
            ],
        ),
    ]
