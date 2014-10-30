from datetime import datetime

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from django.forms.models import BaseModelFormSet
from django.template.loader import render_to_string

from polymorphic import PolymorphicModel, ShowFieldType


class Physician(models.Model):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

class Patient(models.Model):
    user = models.OneToOneField(User)
    physicians = models.ManyToManyField(Physician, blank=False)

    def __unicode__(self):
        return self.user.username


class Question(ShowFieldType, PolymorphicModel):
    title = models.CharField(max_length=32,
                             null=False,
                             blank=False,
                             help_text='One word title to descript your question')

    text = models.CharField(max_length=128,
                            null=False,
                            blank=False,
                            help_text='The questions your would like to ask.')

    description = models.CharField(max_length=512,
                                   blank=True,
                                   help_text='A brief description of the question instructions.')

    patient = models.ForeignKey(User,
                                null=False,
                                blank=False,
                                help_text='The user this question is intended for.')

    target = models.IntegerField()

    def __unicode__(self):
        return self.text


class Boolean(Question):
    def __unicode__(self):
        return self.text


class Category(models.Model):
    name = models.CharField(max_length=32,
                            null=False,
                            blank=False,
                            help_text='Category name.')

    value = models.IntegerField(null=False,
                                blank=False,
                                help_text='Value for this category.')

    def __unicode__(self):
        return self.name

class Categorical(Question):
    categories = models.ManyToManyField(Category,
                                        null=False,
                                        blank=False,
                                        help_text='Categories in this question.')
    _categories = []

    def __init__(self, *args, **kwargs):
        self._categories = kwargs.pop('categories', None)
        super(Categorical, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.text

    def save(self, *args, **kwargs):
        # Save the categorical question first, then
        # save and add the categories to it.
        super(Categorical, self).save(*args, **kwargs)
        if self._categories:
            for value, category in enumerate(self._categories):
                cat = Category(name=category, value=value)
                cat.save()
                self.categories.add(cat)

    def get_query_set(self):
        # Always pull the categories when pulling the question
        return super(Categorical, self).get_query_set().select_related('category')

class Slider(Question):
    min_value = models.IntegerField(default=0,
                                    null=False,
                                    blank=False,
                                    help_text='Minimum value for the slider.')

    max_value = models.IntegerField(default=100,
                                    null=False,
                                    blank=False,
                                    help_text='Maximum value for the slider.')

    increment = models.IntegerField(default=1,
                                    null=False,
                                    blank=False,
                                    help_text='The step (granularity) of the slider.')

    def __unicode__(self):
        return self.text

class FreeForm(Question):
    units = models.CharField(max_length=32,
                             null=False,
                             blank=False,
                             help_text='The units this quetsion is measured in.')
    def __unicode__(self):
        return self.text

class Answer(models.Model):
    value = models.IntegerField(null=False,
                                blank=False,
                                help_text='Answer to the question.') 

    date = models.DateTimeField(auto_now_add=True,
                            null=False,
                            blank=False,
                            help_text='When this answer was submitted.')

    patient = models.ForeignKey(User,
                                null=False,
                                blank=False,
                                help_text='Which user submitted this answer.')

    question = models.ForeignKey(Question,
                                 null=False,
                                 blank=False,
                                 help_text="The question that this is the answer to.")

    comment = models.CharField(max_length=128,
                            null=True,
                            blank=True,
                            help_text='An additional comment regarding your answer.')

    def __unicode__(self):
        return u"{question}".format(question='')

    def clean(self, *args, **kwargs):
        question_type = self.question.__class__.__name__.lower()

        if question_type == 'boolean':
            if self.value not in [0,1]:
                raise ValidationError('Boolean answer must be 0 or 1')

        elif question_type == 'slider':
            self.value = int(self.question.increment * round(float(self.value)/self.question.increment))
            if self.value not in range(self.question.min_value, self.question.max_value):
                raise ValidationError('Slider value {value} is not in range {low} to {high}'.format(
                    value=self.value,
                    low=self.question.min_value,
                    high=self.question.max_value))

        elif question_type == 'categorical':
            if self.value not in range(0,len(self.question.categories.all())):
                raise ValidationError('Categorical question only has {} categories.'.format(len(self.question.categories.all())))

        super(Answer, self).clean(*args, **kwargs)

class AnswerForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        #print self.instance.question.text

    def as_wt(self):
        "Returns this form rendered as a WellnessTracker Element."
        return render_to_string("question_form.html",
                {'question': self.initial['question'],
                'prefix': self.prefix,
                'patient': self.initial['patient'],
                'id': self.auto_id % self.prefix})

    class Meta:
        model = Answer
        fields = ['value', 'patient', 'question', 'comment']

def is_physician(user):
    if user.is_authenticated():
        if user.is_superuser:
            return True
        try:
            physician = Physician.objects.get(user=user)
            return True
        except Physician.DoesNotExist:
            return False
    return False