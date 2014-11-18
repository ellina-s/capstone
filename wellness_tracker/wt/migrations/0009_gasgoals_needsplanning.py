# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0008_auto_20141117_0030'),
    ]

    operations = [
        migrations.AddField(
            model_name='gasgoals',
            name='needsplanning',
            field=models.IntegerField(default=0, help_text=b'A flag for adding planning step to selected strategies'),
            preserve_default=True,
        ),
    ]
