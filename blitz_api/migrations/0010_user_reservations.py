# Generated by Django 2.0.2 on 2018-06-17 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blitz_api', '0009_user_membership'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reservations',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Reservations'),
        ),
    ]
