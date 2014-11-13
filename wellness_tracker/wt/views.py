import re
import json
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

from numpy import mean, std
from preserialize.serialize import serialize

from wt.models import *

from pprint import pformat as pprint

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
        else:
            print formset.errors

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

def create_patient(request):
    return render(request, 'create_patient.html')


#Goal Attainment Wizard Page ---------------------------
#    gas_step1
@user_passes_test(is_physician)
def gas_step1(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        gasgoals_data = {}
        for k, v in response.items():
            gasgoals_data[str(k)] = v.pop()

	print gasgoals_data
	if gasgoals_data['goal1'] == '':
	    print "There is no data"
	else:
            gas_goals = GASGoals(goal1=gasgoals_data['goal1'], 
			         environmentalassessment1=gasgoals_data['environmentalassessment1'], 
			         patient=patient)
            #gas_goals.save()
	if gasgoals_data['createanother'] == 'yes': 
            return render(request, 'gas_step1.html', {'patient': patient})
	else:
	    return render(request, 'gas_goal_selection_forward.html', {'patient': patient})
    else:

        return render(request, 'gas_step1.html', {'patient': patient})
    #gas_goal_selection
@user_passes_test(is_physician)
def gas_goal_selection(request, user_id=0):
    patient = get_object_or_404(User, pk=int(user_id))

    gas_goals_list = GASGoals.objects.filter(patient=patient)

    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        gas_goals_select = {}
        for k, v in response.items():
            gas_goals_select[str(k)] = v.pop()

        #print 'These are the id im looking for:' 
	#print gas_goals_select['goalselect']
	#print 'These are all the ids of each thing:'

	for tempGASGoals in gas_goals_list:
	    tempGASGoals.select = 0
	    tempGASGoals.save()
	    #print tempGASGoals.select
            if tempGASGoals.id == int(gas_goals_select['goalselect']):
	        selected_goal = tempGASGoals
	
	selected_goal.select = 1
	selected_goal.save()
	print 'Select Goal Page Selected Goal'
        print selected_goal.goal1
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient, 'selected_goal': selected_goal}
        return render(request, 'new_strategy_forward.html', context_dict)

    else:
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient}
        return render(request, 'gas_goal_selection.html', context_dict)

@user_passes_test(is_physician)
def gas_goal_selection_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
  
    return render(request, 'gas_goal_selection_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def new_strategy_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
  
    return render(request, 'new_strategy.html', {'patient': patient})
# ______________________________________________   Strategy ___________________________________________________________
@user_passes_test(is_physician)
def new_strategy(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.select == 1:
	    selected_goal = tempGASGoals
    print 'New Strategy Page Selected Goal'
    print selected_goal.goal1
    #Create dict
    context_dict = {'patient': patient, 'selected_goal': selected_goal}

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
            #boolean.save()

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

            #categorical.save()

        elif t == "[u'integer']": # new question is free form
            free_form = FreeForm(title=question_data['title'],
                                text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                units=question_data['units'])
            #free_form.save()

        elif t == "[u'slider']": # new question is slider
            slider = Slider(title=question_data['title'],
                            text=question_data['text'],
                            description=question_data['description'],
                            target = int(question_data['goal']),
                            patient=patient,
                            max_value=question_data['max_value'],
                            min_value=question_data['min_value'],
                            increment=question_data['increment'])
            #slider.save()
    
    return render(request, 'new_strategy.html', context_dict)


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

    latest_datetime = []
    latest_datetime = Answer.objects.extra(
            select={'the_date': 'date(date)' }
        ).values_list('the_date').annotate(max_date=Max('date'))
    max_dates = [item[1] for item in latest_datetime]

    answers = Answer.objects.filter(question__in=questions).filter(date__in=max_dates).order_by('date')

    grouped_answers = defaultdict(list)
    for ans in answers:
        grouped_answers[ans.question.title].append(ans)


    # Build nvd3 json
    data = []
    for k,v in grouped_answers.iteritems():
        point_list = []
        for datum in v:
            point_list.append(
                {'x': int(datum.date.strftime("%s") + "000"),
                 'y': datum.value,
                 'comment':datum.comment,
                })

        values = list(point['y'] for point in point_list)
        avg = mean(values)
        stdev = std(values)

        data.append(
                {'key':k,
                 'values': point_list,
                 'disabled': True,
                 'avg': avg,
                 'targ': v[0].question.target,
                 'std1': avg+stdev,
                 'std2': avg-stdev,
                 })

    return render(request, "graph.html",
            {"data_json": json.dumps(data),
             "data": data,
             "graph_user": user})


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
