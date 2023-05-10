# Generated by Django 3.2.12 on 2023-05-10 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_customer_userid'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='user_name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]