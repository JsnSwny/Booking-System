# Generated by Django 2.2 on 2019-11-28 18:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_auto_20191128_1810'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HistoricalBooking',
        ),
    ]