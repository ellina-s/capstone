# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wt', '0004_gasgoals_select'),
    ]

    operations = [
        migrations.AddField(
            model_name='gasgoals',
            name='baseline',
            field=models.IntegerField(default=0, help_text=b'Baseline for the goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='indicator',
            field=models.CharField(help_text=b'How will we know if the gold has been reached', max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='scoreneg1',
            field=models.IntegerField(default=0, help_text=b'Gas score -1'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='scoreneg2',
            field=models.IntegerField(default=0, help_text=b'Gas score -2'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='scorepos1',
            field=models.IntegerField(default=0, help_text=b'Gas score +1'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='scorepos2',
            field=models.IntegerField(default=0, help_text=b'Gas score +2'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='target',
            field=models.IntegerField(default=0, help_text=b'Target for the goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gasgoals',
            name='timeline',
            field=models.IntegerField(default=0, help_text=b'Timeline (days) to achieve the goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='action',
            field=models.CharField(help_text=b'The questions your would like to ask.', max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='baseline',
            field=models.IntegerField(default=0, help_text=b'Baseline for the goal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='difficulty',
            field=models.IntegerField(default=0, help_text=b'Importance of Strategy (1-4) 4=extremely important'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='gasgoal',
            field=models.ForeignKey(blank=True, to='wt.GASGoals', help_text=b'The GASGoal this strategy belongs to.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='importance',
            field=models.IntegerField(default=0, help_text=b'Importance of Strategy (1-4) 4=extremely important'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='indicator',
            field=models.CharField(help_text=b'How will we know if the strategy is working', max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='scoreneg1',
            field=models.IntegerField(default=0, help_text=b'Gas score -1'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='scoreneg2',
            field=models.IntegerField(default=0, help_text=b'Gas score -2'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='scorepos1',
            field=models.IntegerField(default=0, help_text=b'Gas score +1'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='scorepos2',
            field=models.IntegerField(default=0, help_text=b'Gas score +2'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='question',
            name='timeline',
            field=models.IntegerField(default=0, help_text=b'Timeline (days) to achieve the strategy'),
            preserve_default=True,
        ),
    ]
