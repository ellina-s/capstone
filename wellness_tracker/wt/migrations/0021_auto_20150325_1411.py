# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0020_auto_20150309_1604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gasgoals',
            name='goal1',
            field=models.CharField(help_text=b'Decription of the Goal', max_length=32),
            preserve_default=True,
        ),
    ]
