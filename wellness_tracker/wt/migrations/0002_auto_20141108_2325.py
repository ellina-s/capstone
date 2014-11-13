# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gasgoals',
            name='polymorphic_ctype',
        ),
        migrations.AlterField(
            model_name='gasgoals',
            name='environmentalassessment1',
            field=models.CharField(help_text=b'Describe the Environment', max_length=512),
        ),
        migrations.AlterField(
            model_name='gasgoals',
            name='goal1',
            field=models.CharField(help_text=b'Decription of the Goal', max_length=128),
        ),
        migrations.AlterField(
            model_name='gasgoals',
            name='patient',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, help_text=b'The user these goals are intended for.', unique=True),
        ),
    ]
