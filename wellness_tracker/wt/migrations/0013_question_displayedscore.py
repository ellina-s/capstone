# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0012_auto_20150109_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='displayedscore',
            field=models.CharField(help_text=b'Displayed score on graph (+2, ', max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
    ]
