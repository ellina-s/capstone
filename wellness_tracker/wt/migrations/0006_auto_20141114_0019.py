# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0005_auto_20141114_0015'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gasgoals',
            old_name='select',
            new_name='activiated',
        ),
        migrations.AddField(
            model_name='question',
            name='activiated',
            field=models.IntegerField(default=0, help_text=b'Is this gold selected?'),
            preserve_default=True,
        ),
    ]
