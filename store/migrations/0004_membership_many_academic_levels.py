# Generated by Django 2.0.2 on 2018-07-14 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blitz_api', '0012_auto_20180624_1321'),
        ('store', '0003_product_available'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membership',
            name='academic_level',
        ),
        migrations.AddField(
            model_name='membership',
            name='academic_levels',
            field=models.ManyToManyField(blank=True, related_name='memberships', to='blitz_api.AcademicLevel', verbose_name='Academic levels'),
        ),
    ]
