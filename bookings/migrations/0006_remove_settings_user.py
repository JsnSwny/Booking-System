# Generated by Django 2.2 on 2019-11-28 19:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_auto_20191128_1906'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='settings',
            name='user',
        ),
    ]