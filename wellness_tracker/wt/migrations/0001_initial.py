# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import polymorphic.showfields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.IntegerField(help_text=b'Answer to the question.')),
                ('date', models.DateTimeField(help_text=b'When this answer was submitted.', auto_now_add=True)),
                ('comment', models.CharField(help_text=b'An additional comment regarding your answer.', max_length=128, null=True, blank=True)),
                ('patient', models.ForeignKey(help_text=b'Which user submitted this answer.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
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
            name='GASGoals',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('goal1', models.CharField(max_length=128)),
                ('environmentalassessment1', models.CharField(max_length=512, blank=True)),
                ('patient', models.ForeignKey(help_text=b'The user this question is intended for.', to=settings.AUTH_USER_MODEL)),
                ('polymorphic_ctype', models.ForeignKey(related_name=b'polymorphic_wt.gasgoals_set', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Physician',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'One word title to descript your question', max_length=32)),
                ('text', models.CharField(help_text=b'The questions your would like to ask.', max_length=128)),
                ('description', models.CharField(help_text=b'A brief description of the question instructions.', max_length=512, blank=True)),
                ('target', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(polymorphic.showfields.ShowFieldType, models.Model),
        ),
        migrations.CreateModel(
            name='FreeForm',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Question')),
                ('units', models.CharField(help_text=b'The units this quetsion is measured in.', max_length=32)),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.question',),
        ),
        migrations.CreateModel(
            name='Categorical',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Question')),
                ('categories', models.ManyToManyField(help_text=b'Categories in this question.', to='wt.Category')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.question',),
        ),
        migrations.CreateModel(
            name='Boolean',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Question')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.question',),
        ),
        migrations.CreateModel(
            name='Slider',
            fields=[
                ('question_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wt.Question')),
                ('min_value', models.IntegerField(default=0, help_text=b'Minimum value for the slider.')),
                ('max_value', models.IntegerField(default=100, help_text=b'Maximum value for the slider.')),
                ('increment', models.IntegerField(default=1, help_text=b'The step (granularity) of the slider.')),
            ],
            options={
                'abstract': False,
            },
            bases=('wt.question',),
        ),
        migrations.AddField(
            model_name='question',
            name='patient',
            field=models.ForeignKey(help_text=b'The user this question is intended for.', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name=b'polymorphic_wt.question_set', editable=False, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='patient',
            name='physicians',
            field=models.ManyToManyField(to='wt.Physician'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='patient',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(help_text=b'The question that this is the answer to.', to='wt.Question'),
            preserve_default=True,
        ),
    ]
