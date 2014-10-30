import re
from datetime import datetime
from collections import defaultdict

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Max
from django.http import HttpResponse, Http404
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext

from preserialize.serialize import serialize

from wt.models import *


# Hack for homepage
def home(request):
    if is_physician(request.user):
        return patient_list(request)
    else:
        return graph(request)


def questions(request):
    if request.method == "POST":
        AnswerFormSet2 = modelformset_factory(Answer, form=AnswerForm)
        formset = AnswerFormSet2(request.POST)

        if formset.is_valid():
            formset.save()

    # Get questions list
    question_list = Question.objects.filter(patient=request.user)
    initial_data = [{'question': q, 'patient': request.user} for q in question_list]
    AnswerFormSet1 = modelformset_factory(Answer, form=AnswerForm, extra=len(initial_data))
    formset = AnswerFormSet1(queryset=Answer.objects.none(), initial=initial_data)

    return render(request, "questions.html", {"formset": formset})


@user_passes_test(is_physician)
def patient_list(request):
    patients = Patient.objects.filter(physicians=Physician.objects.get(user=request.user))
    return render(request, 'patient_list.html', {'patients': patients})


def graph(request, user_id=None):
    try:
        physician = Physician.objects.get(user=request.user)
    except Physician.DoesNotExist:
        physician = None

    # Get the right user for the graph
    # For a physician, this means checking that they are,
    # a physician for the patient they are requesting to view.
    if user_id and physician:
        user = get_object_or_404(User, pk=int(user_id))
        if not Patient.objects.get(user=user).physicians.filter(pk=physician.pk).exists():
            raise Http404
    else:
        user = request.user

    # Pull the questions for this user
    question_list = Question.objects.filter(patient=user)
    questions = Question.objects.filter(patient=user).get_real_instances(question_list)

    # Serialize the questions and answers
    serialized_questions = serialize(questions,
                                     exclude=['patient',
                                              'text',
                                              'question_ptr',
                                              'description',
                                              'polymorphic_ctype'])

    answers = Answer.objects.filter(question__in=questions).order_by('date')

    comments = defaultdict(list)
    for answer in answers:
        if answer.comment:
            comments[answer.date.date()].append(answer)

    """  GET MOST RECENT FOR EACH DAY
    # Get the most recent answer for each day
    latest_datetime = []
    Answer.objects.extra(
            select={'the_date': 'date(date)' }
        ).values_list('the_date').annotate(max_date=Max('date'))
    max_dates = [item[1] for item in latest_datetime]

    serialized_answers = serialize(Answer.objects.filter(question__in=questions).filter(date__in=max_dates).order_by('date'),
                                  fields=['date', 'value'])
    for i in serialized_answers:
        i['date'] = str(i['date'].date())

    serialized_answers = [serialized_answers]
    """
    serialized_answers = []
    for q in questions:
        serialized_answers.append(serialize(Answer.objects.filter(question=q).order_by('date'),
                                                  fields=['date', 'value']))

    for j in serialized_answers:
        for i in j:
            i['date'] = str(i['date'].date())

    print serialized_answers

    data = serialized_answers
    symptoms = serialized_questions

    return render(request, 'graph.html', {'symptoms': symptoms,
                                          'data': data,
                                          'answers' : answers,
                                          'comments' : dict(comments),
                                          'graph_user': user})


@user_passes_test(is_physician)
def new_question(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
            question_data[str(k)] = v.pop()

        if t == "[u'boolean']": # new question is boolean
            boolean = Boolean(title=question_data['title'],
                              text=question_data['text'],
                              description=question_data['description'],
                              target=int(question_data['goal']),
                              patient=patient)
            boolean.save()

        elif t == "[u'category']": # new question is categorical
            category_list = []

            i = 1
            while 'cat' + str(i) in question_data:
                category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                category_list.append(question_data['cat'+ str(i)].lower())
                i = i + 1

            categorical = Categorical(title=question_data['title'],
                                        text=question_data['text'],
                                        description=question_data['description'],
                                        categories=category_list,
                                        patient=patient)

            if question_data['goal'].lower() in category_list: # check for numerical or text goal
                categorical.target = category_list.index(question_data['goal'].lower())
            else:
                categorical.target = int(question_data['goal'])

            categorical.save()

        elif t == "[u'integer']": # new question is free form
            free_form = FreeForm(title=question_data['title'],
                                text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                units=question_data['units'])
            free_form.save()

        elif t == "[u'slider']": # new question is slider
            slider = Slider(title=question_data['title'],
                            text=question_data['text'],
                            description=question_data['description'],
                            target = int(question_data['goal']),
                            patient=patient,
                            max_value=question_data['max_value'],
                            min_value=question_data['min_value'],
                            increment=question_data['increment'])
            slider.save()

    return render(request, 'new_question.html', {'patient': patient})