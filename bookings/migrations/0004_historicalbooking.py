# Generated by Django 2.2 on 2019-11-28 19:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0003_delete_historicalbooking'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalBooking',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('time', models.TimeField()),
                ('name', models.CharField(max_length=100)),
                ('people', models.IntegerField()),
                ('info', models.TextField()),
                ('tel', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('initials', models.CharField(max_length=20)),
                ('assign', models.CharField(default='', max_length=100)),
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('arrived', models.BooleanField(default=False)),
                ('cleared', models.BooleanField(default=False)),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('table', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='bookings.TableItem')),
            ],
            options={
                'verbose_name': 'historical booking',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
