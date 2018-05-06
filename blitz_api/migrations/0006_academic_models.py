# Generated by Django 2.0.2 on 2018-05-06 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blitz_api', '0005_user_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Academic field',
                'verbose_name_plural': 'Academic fields',
            },
        ),
        migrations.CreateModel(
            name='AcademicLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Academic level',
                'verbose_name_plural': 'Academic levels',
            },
        ),
    ]
