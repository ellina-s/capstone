# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0016_sboolean_scategorical_scategory_sfreeform_sslider'),
    ]

    operations = [
        migrations.AddField(
            model_name='presurvey',
            name='squestions',
            field=models.ManyToManyField(to='wt.Squestion'),
            preserve_default=True,
        ),
    ]
