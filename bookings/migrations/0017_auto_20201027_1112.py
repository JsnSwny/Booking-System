# Generated by Django 2.2 on 2020-10-27 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0016_auto_20201024_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(blank=True, choices=[('M', 'Meal'), ('D', 'Drinks'), ('HT', 'High Tea'), ('AT', 'Afternoon Tea')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbooking',
            name='booking_type',
            field=models.CharField(blank=True, choices=[('M', 'Meal'), ('D', 'Drinks'), ('HT', 'High Tea'), ('AT', 'Afternoon Tea')], max_length=1, null=True),
        ),
    ]
