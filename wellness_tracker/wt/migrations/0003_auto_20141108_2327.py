# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0002_auto_20141108_2325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gasgoals',
            name='patient',
            field=models.ForeignKey(help_text=b'The user these goals are intended for.', to=settings.AUTH_USER_MODEL),
        ),
    ]
