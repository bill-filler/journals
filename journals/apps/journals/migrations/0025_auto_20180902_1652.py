# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-02 16:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0024_journalpage_display_last_published_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='transcript_url',
            field=models.URLField(max_length=255, null=True),
        ),
    ]
