# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0007_auto_20141116_1715'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='target',
            field=models.IntegerField(default=0, help_text=b'The target of the strategy'),
        ),
    ]
