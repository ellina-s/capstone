# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0003_auto_20141108_2327'),
    ]

    operations = [
        migrations.AddField(
            model_name='gasgoals',
            name='select',
            field=models.IntegerField(default=0, help_text=b'Is this gold selected?'),
            preserve_default=True,
        ),
    ]
