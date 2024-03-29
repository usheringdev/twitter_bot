# Generated by Django 5.0.2 on 2024-02-20 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APOD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('title', models.CharField(max_length=255)),
                ('explanation', models.TextField()),
                ('url', models.CharField(max_length=255)),
                ('media_type', models.CharField(max_length=32)),
                ('service_version', models.CharField(max_length=8)),
                ('twitter_media_id', models.CharField(blank=True, max_length=128, null=True)),
                ('twitter_post_id', models.CharField(blank=True, max_length=128, null=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='apod',
            constraint=models.UniqueConstraint(fields=('date', 'title'), name='unique_date_title'),
        ),
    ]
