# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wt', '0010_auto_20141117_2028'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'One word title to descript your question', max_length=32)),
                ('importance', models.IntegerField(default=0, help_text=b'Importance of Strategy (1-4) 4=extremely important')),
                ('difficulty', models.IntegerField(default=0, help_text=b'Importance of Strategy (1-4) 4=extremely important')),
                ('gasgoal', models.ForeignKey(blank=True, to='wt.GASGoals', help_text=b'The GASGoal this strategy belongs to.', null=True)),
                ('patient', models.ForeignKey(help_text=b'The user this question is intended for.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
