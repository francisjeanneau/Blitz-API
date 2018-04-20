# Generated by Django 2.0.2 on 2018-04-18 00:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authtoken', '0002_auto_20160226_1747'),
        ('blitz_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryToken',
            fields=[
                ('token_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='authtoken.Token')),
                ('expires', models.DateTimeField(blank=True, verbose_name='Expiration date')),
            ],
            bases=('authtoken.token',),
        ),
    ]