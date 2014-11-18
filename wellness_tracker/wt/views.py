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

#Creating a new patient
@user_passes_test(is_physician)
def create_patient(request):
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        new_patient_data = {}
        for k, v in response.items():
            new_patient_data[str(k)] = v.pop()
	
	#Create a new user object
	tempuser = User.objects.create_user(new_patient_data['userid'],
					    new_patient_data['useremail'],
					    new_patient_data['password'])
	# At this point, tempuser is a User object that has already been saved
	# to the database. You can continue to change its attributes
	# if you want to change other fields.

	#get physician object(s)
	currentdoctors = Physician.objects.get(user=request.user)
	#create Patient
	newpatient = Patient(user = tempuser)
	#save Patient
	newpatient.save()
	#add physicians
	#Note: the corresponding Patient object has to be created and saved by this point
	newpatient.physicians.add(currentdoctors)
	#update Patient
	newpatient.save()        

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
            gas_goals.save()
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
	    tempGASGoals.activated = 0
	    tempGASGoals.save()
	    #print tempGASGoals.select
            if tempGASGoals.id == int(gas_goals_select['goalselect']):
	        selected_goal = tempGASGoals
	
	selected_goal.activated = 1
	selected_goal.save()
	print 'Select Goal Page Selected Goal'
        print selected_goal.goal1
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient, 'selected_goal': selected_goal}
        #return render(request, 'planning.html', context_dict)
	return render(request, 'planning_forward.html', context_dict)

    else:
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient}
        return render(request, 'gas_goal_selection.html', context_dict)

@user_passes_test(is_physician)
def gas_goal_selection_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
  
    return render(request, 'gas_goal_selection_forward.html', {'patient': patient})

# ______________________________________________   Goal Planning ___________________________________________________________
@user_passes_test(is_physician)
def planning_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'planning_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def planning(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to planning information
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
    #print 'Goal Planning Page Selected Goal'
    #print selected_goal.goal1
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
	
	if question_data['baseline'] == '':
	    print 'No goal planning data in the form'
	else:
	    selected_goal.baseline = question_data['baseline']
	    selected_goal.target = question_data['target']
	    selected_goal.timeline = question_data['timeline']
	    selected_goal.indicator = question_data['indicator']
	    selected_goal.scorepos2 = question_data['scorepos2']
	    selected_goal.scorepos1 = question_data['scorepos1']
	    selected_goal.scoreneg1 = question_data['scoreneg1']
	    selected_goal.scoreneg2 = question_data['scoreneg2']
	
	    selected_goal.save()

        return render(request, 'goal_summary_forward.html', context_dict)

    return render(request, 'planning.html', context_dict)

# ______________________________________________   Goal Summary ___________________________________________________________
@user_passes_test(is_physician)
def goal_summary_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'goal_summary_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def goal_summary(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    context_dict = {'patient': patient, 'selected_goal': selected_goal}
    return render(request, 'goal_summary.html', context_dict)



# ______________________________________________   Strategy ___________________________________________________________
@user_passes_test(is_physician)
def new_strategy_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'new_strategy_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def new_strategy(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

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
	#Check for blank title, if so dont save strategy
	if question_data['title'] == '':
	    print 'There is no strategy data'
	else:
	    newstrategy = Question(title=question_data['title'], 
			         importance=question_data['importance'],
			         difficulty=question_data['difficulty'],
			         gasgoal=selected_goal, 
			         patient=patient)
            newstrategy.save()
	#Check if user would like to create another strategy or move to next step
	if question_data['createanotherstrategy'] == 'yes':
	    return render(request, 'new_strategy.html', context_dict)
	else:
	    return render(request, 'new_strategy_selection_forward.html', context_dict)
    else:

        return render(request, 'new_strategy.html', context_dict)

def new_strategy_selection_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'new_strategy_selection_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def new_strategy_selection(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    strategy_list = Question.objects.filter(gasgoal=selected_goal)
    print 'All strategies created:'
    for tempstrategy in strategy_list:
	print tempstrategy.title

    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
            question_data[str(k)] = v.pop()

	
	#print question_data
	#print 'Strategies you selected:'
	#for stratcheck in strategy_list:
	    #if question_data['stratcheck.id'] == 'selected':
	    #print stratcheck.id
	    #print question_data['char(stratcheck.id)']

	myvar = str(3)
	print myvar
	#print question_data[myvar]

    
    #Create dict
    context_dict = {'gas_goal_strategies' : strategy_list, 'patient': patient, 'selected_goal': selected_goal}
    return render(request, 'new_strategy_selection.html', context_dict)


@user_passes_test(is_physician)
def new_strategy_planning(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
    #print 'New Strategy Page Selected Goal'
    #print selected_goal.goal1
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
        if question_data['createanother'] == 'yes': 
            return render(request, 'new_strategy_forward.html', context_dict)
	else:
	    return render(request, 'gas_step1.html', context_dict)
    
    return render(request, 'new_strategy.html', context_dict)


def strategies(request):
    return render(request, 'strategies.html')

def strategy_planning(request):
    return render(request, 'strategy_planning.html')

def appendix_va(request):
    return render(request, 'appendix_va.html')

def appendix_vb(request):
    return render(request, 'appendix_vb.html')

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
