# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-18 15:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_siteconfiguration_frontend_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfiguration',
            name='frontend_url',
            field=models.URLField(help_text='Root URL of frontend app for specific site (e.g. https://journalapp.edx.org)', unique=True, verbose_name='Frontend app base url'),
        ),
    ]