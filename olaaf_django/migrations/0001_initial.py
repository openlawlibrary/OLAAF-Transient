# Generated by Django 2.2.3 on 2019-08-06 22:52

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sha', models.CharField(max_length=40)),
                ('date', models.DateTimeField()),
                ('revoked', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='Hash',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=64, validators=[django.core.validators.MinLengthValidator(64)])),
                ('path', models.CharField(max_length=200)),
                ('end_commit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hash_end_commit', to='olaaf_django.Commit')),
                ('start_commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hash_start_commit', to='olaaf_django.Commit')),
            ],
        ),
        migrations.CreateModel(
            name='Edition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=10)),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Repository')),
            ],
        ),
        migrations.AddField(
            model_name='commit',
            name='edition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Edition'),
        ),
    ]
