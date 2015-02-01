# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import polymorphic.showfields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('wt', '0014_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Survey title.', max_length=32)),
                ('spatients', models.ManyToManyField(to='wt.Patient')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Squestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'One word title to descript your question', max_length=32)),
                ('text', models.CharField(help_text=b'The questions your would like to ask.', max_length=128)),
                ('description', models.CharField(help_text=b'A brief description of the question instructions.', max_length=512, blank=True)),
                ('target', models.IntegerField(default=0, help_text=b'The target of the strategy')),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_wt.squestion_set', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(polymorphic.showfields.ShowFieldType, models.Model),
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Survey title.', max_length=32)),
                ('spatients', models.ManyToManyField(to='wt.Patient')),
                ('squestions', models.ManyToManyField(to='wt.Squestion')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
