# Generated by Django 2.2.5 on 2020-10-22 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olaaf_django', '0010_remove_commit_document'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='commit',
            index=models.Index(fields=['publication', 'date'], name='olaaf_djang_publica_82f70a_idx'),
        ),
    ]
