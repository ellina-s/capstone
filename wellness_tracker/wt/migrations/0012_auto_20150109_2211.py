# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0011_prequestion'),
    ]

    operations = [
        migrations.AddField(
            model_name='prequestion',
            name='activated',
            field=models.IntegerField(default=0, help_text=b'Is this gold selected?'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='prequestion',
            name='needsplanning',
            field=models.IntegerField(default=0, help_text=b'A flag for adding planning step to selected strategies'),
            preserve_default=True,
        ),
    ]
