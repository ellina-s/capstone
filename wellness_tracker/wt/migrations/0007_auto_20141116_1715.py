# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0006_auto_20141114_0019'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gasgoals',
            old_name='activiated',
            new_name='activated',
        ),
        migrations.RenameField(
            model_name='question',
            old_name='activiated',
            new_name='activated',
        ),
    ]
