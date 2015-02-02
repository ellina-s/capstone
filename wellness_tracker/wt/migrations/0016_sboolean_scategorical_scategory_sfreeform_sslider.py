# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0015_presurvey_squestion_survey'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sboolean',
            fields=[
                ('squestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Squestion')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.squestion',),
        ),
        migrations.CreateModel(
            name='Scategorical',
            fields=[
                ('squestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Squestion')),
                ('categories', models.ManyToManyField(help_text=b'Categories in this question.', to='wt.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.squestion',),
        ),
        migrations.CreateModel(
            name='Scategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Category name.', max_length=32)),
                ('value', models.IntegerField(help_text=b'Value for this category.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SfreeForm',
            fields=[
                ('squestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Squestion')),
                ('units', models.CharField(help_text=b'The units this quetsion is measured in.', max_length=32)),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.squestion',),
        ),
        migrations.CreateModel(
            name='Sslider',
            fields=[
                ('squestion_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Squestion')),
                ('min_value', models.IntegerField(default=0, help_text=b'Minimum value for the slider.')),
                ('max_value', models.IntegerField(default=100, help_text=b'Maximum value for the slider.')),
                ('increment', models.IntegerField(default=1, help_text=b'The step (granularity) of the slider.')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.squestion',),
        ),
    ]
