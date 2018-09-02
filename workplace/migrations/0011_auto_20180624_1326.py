# Generated by Django 2.0.2 on 2018-06-24 17:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workplace', '0010_address_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(verbose_name='Active')),
                ('timeslot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='workplace.TimeSlot', verbose_name='Time slot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.AddField(
            model_name='timeslot',
            name='users1',
            field=models.ManyToManyField(blank=True, related_name='time_slots1', through='workplace.Reservation', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
