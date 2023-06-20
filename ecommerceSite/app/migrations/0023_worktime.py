# Generated by Django 5.0 on 2024-01-15 04:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_rename_full_name_customer_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_date', models.DateField()),
                ('work_time', models.FloatField(blank=True, default=0, null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.employee')),
            ],
        ),
    ]