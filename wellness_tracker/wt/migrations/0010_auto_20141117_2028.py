# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0009_gasgoals_needsplanning'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gasgoals',
            name='needsplanning',
        ),
        migrations.AddField(
            model_name='question',
            name='needsplanning',
            field=models.IntegerField(default=0, help_text=b'A flag for adding planning step to selected strategies'),
            preserve_default=True,
        ),
    ]
