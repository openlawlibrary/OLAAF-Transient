# Generated by Django 2.2.5 on 2020-10-22 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olaaf_django', '0008_auto_20200625_1859'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='commit',
            index=models.Index(fields=['publication', 'date'], name='olaaf_djang_publica_82f70a_idx'),
        ),
    ]