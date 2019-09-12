# Generated by Django 2.2.5 on 2019-09-12 14:23

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
                ('date', models.DateField()),
                ('document', models.CharField(max_length=100)),
                ('revoked', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
            ],
            options={
                'verbose_name': 'Repository',
                'verbose_name_plural': 'Repositories',
            },
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('date', models.DateField()),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Repository')),
            ],
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filesystem', models.CharField(max_length=260)),
                ('url', models.CharField(max_length=260)),
                ('search_path', models.CharField(max_length=200, null=True)),
                ('citation', models.CharField(max_length=100, null=True)),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Publication')),
            ],
        ),
        migrations.CreateModel(
            name='Hash',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=64, validators=[django.core.validators.MinLengthValidator(64)])),
                ('hash_type', models.CharField(choices=[('B', 'Bitstream'), ('R', 'Rendered')], default='B', max_length=1)),
                ('end_commit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hash_end_commit', to='olaaf_django.Commit')),
                ('path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Path')),
                ('start_commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hash_start_commit', to='olaaf_django.Commit')),
            ],
            options={
                'verbose_name': 'Hash',
                'verbose_name_plural': 'Hashes',
            },
        ),
        migrations.AddField(
            model_name='commit',
            name='publication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='olaaf_django.Publication'),
        ),
        migrations.AddIndex(
            model_name='publication',
            index=models.Index(fields=['repository', 'name'], name='olaaf_djang_reposit_6d391d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='publication',
            unique_together={('repository', 'name')},
        ),
        migrations.AddIndex(
            model_name='path',
            index=models.Index(fields=['filesystem', 'publication'], name='olaaf_djang_filesys_5024a7_idx'),
        ),
        migrations.AddIndex(
            model_name='path',
            index=models.Index(fields=['url', 'publication'], name='olaaf_djang_url_fb4d67_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='path',
            unique_together={('filesystem', 'publication')},
        ),
        migrations.AddIndex(
            model_name='hash',
            index=models.Index(fields=['path', 'value', 'hash_type'], name='olaaf_djang_path_id_181492_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='hash',
            unique_together={('path', 'value', 'hash_type')},
        ),
        migrations.AddIndex(
            model_name='commit',
            index=models.Index(fields=['publication', 'sha'], name='olaaf_djang_publica_2c60ae_idx'),
        ),
        migrations.AddIndex(
            model_name='commit',
            index=models.Index(fields=['date', 'id'], name='olaaf_djang_date_cf02d2_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='commit',
            unique_together={('publication', 'sha')},
        ),
    ]
