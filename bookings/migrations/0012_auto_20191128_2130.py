# Generated by Django 2.2 on 2019-11-28 21:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0011_auto_20191128_2100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='usersettings', to=settings.AUTH_USER_MODEL),
        ),
    ]
