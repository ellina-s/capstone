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
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.db import IntegrityError
from smtplib import SMTPException
# Import custom forms
from wt.forms import PasswordForm
from django import forms
# Import http redirect
from django.http import HttpResponseRedirect

from numpy import mean, std
from preserialize.serialize import serialize

from wt.models import *

from pprint import pformat as pprint

# Hack for homepage
def home(request):
    if is_physician(request.user):
        return patient_list(request)
    elif is_significant_other(request.user):
        return following_list(request)
    else:
        return graph(request)


def questions(request):
    #patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    #gas_goals_list = GASGoals.objects.filter(patient=patient)
    #for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        #if tempGASGoals.activated == 1:
	    #selected_goal = tempGASGoals

    if request.method == "POST":
        AnswerFormSet2 = modelformset_factory(Answer, form=AnswerForm)
        formset = AnswerFormSet2(request.POST)

        if formset.is_valid():
            formset.save()
	    return render(request, 'graphuser_forward.html')

        else:
            print formset.errors

    #Find patient
    patient=request.user

    #Find selected goal 
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    # Get questions list
    question_list = Question.objects.filter(patient=request.user, gasgoal=selected_goal)
    initial_data = [{'question': q, 'patient': request.user} for q in question_list]
    AnswerFormSet1 = modelformset_factory(Answer, form=AnswerForm, extra=len(initial_data))
    formset = AnswerFormSet1(queryset=Answer.objects.none(), initial=initial_data)

    return render(request, "questions.html", {"formset": formset})

# _________ Physician's list of patients _________
@user_passes_test(is_physician)
def patient_list(request):
    patients = Patient.objects.filter(physicians=Physician.objects.get(user=request.user))
    return render(request, 'patient_list.html', {'patients': patients})

# _________ Significant Other's list of patients _________
@user_passes_test(is_significant_other)
def following_list(request):
    # Retrieve patients associated with the given significant other
    patients = SignificantOther.objects.get(user=request.user).patients.all()
    return render(request, 'following.html', {'patients': patients})

#Creating a new patient
@user_passes_test(is_physician)
def create_patient(request):
    status={}
    status['duplicate_username'] = False # default
    status['smtp_error'] = False # default
    status['missing_info'] = False #default
    status['patient_created'] = False #default
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        new_patient_data = {}
        for k, v in response.items():
            new_patient_data[str(k)] = v.pop()
	
        # Check for empty stings in forms
        if new_patient_data['userid'] == "" or new_patient_data['useremail'] == "" or new_patient_data['password'] == "":
            #print ' * NO USERNAME OR EMAIL OR PASSWORD SET'
            status['missing_info'] = True
            return render(request, 'create_patient.html', {'status': status})
    
        #Create a new user object
        try:
            tempuser = User.objects.create_user(new_patient_data['userid'],
					    new_patient_data['useremail'],
					    new_patient_data['password'])
        except IntegrityError as e:
            #print ' * Detected an integrity error'
            print e
            status['duplicate_username'] = True
            return render(request, 'create_patient.html', {'status': status})
            
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

        status['patient_created'] = True #set the flag to True if SO is successfully created

        email_flag = True
        if (email_flag):
            # Send an email
            #email = EmailMessage('Django Subject', 'Body goes here', 'wtdev.testing@gmail.com', ['capstone59.wt@gmail.com'] )
            email = EmailMessage('Your Account on Welness Tracker',
                'Dear ' + new_patient_data['userid'] + '\n\nThis is a message from the Wellness Tracker. You have been signed up for the Wellness Tracker. Here are the details of you account:\n\nYour username: ' + new_patient_data['userid'] + '\nYour password: ' + new_patient_data['password'] + '\n\nSincerely,\nWellness Tracker Team',
                'wtdev.testing@gmail.com',
                [new_patient_data['useremail']] )
            try:
                email.send()
            except SMTPException as e:
                #print ' * Error when sending email'
                print e
                status['smtp_error'] = True
                return render(request, 'create_patient.html', {'status': status})
    
    if(status['patient_created']):
        #print ' * New Patient ID is'
        #print newpatient.user.id
        return render(request, 'start_gas.html', {'patient': newpatient, 'status': status})
    
    return render(request, 'create_patient.html', {'status': status})
    

# Upon successful creation of a patient, suggest to start the GAS process
@user_passes_test(is_physician)
def start_gas(request):
    return render(request, 'start_gas.html') 

#--------------------------------------------------Goal Attainment Wizard Page1 ---------------------------
#    gas_step1
@user_passes_test(is_physician)
def gas_step1(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    pageforward = 'unknown'
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        gasgoals_data = {}
        for k, v in response.items():
	    #checking for "Create Another Goal" button pressed
	    if str(v) == "[u'Create Another Goal']":
		pageforward = 'createanothergoal'
	    #Done - checking for "Create Another Goal" button pressed

	    #checking for "Next" button pressed
	    if str(v) == "[u'Next']":
		pageforward = 'next'
	    #Done - checking for "Create New Goal" button pressed

            gasgoals_data[str(k)] = v.pop()

	print gasgoals_data
	if gasgoals_data['goal1'] == '':
	    print "There is no data"
	else:
            gas_goals = GASGoals(goal1=gasgoals_data['goal1'], 
			         environmentalassessment1=gasgoals_data['environmentalassessment1'], 
			         patient=patient)
            gas_goals.save()

	if pageforward == 'createanothergoal':
	    return render(request, 'gas_step1.html', {'patient': patient})
	if pageforward == 'next':
	    return render(request, 'gas_goal_selection_forward.html', {'patient': patient})
	
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
	    #create a new strategy (question) with isgoalplanningdata flag = 1 (goal info, no a strategy)
	    if t == "[u'boolean']": # new question is boolean
                boolean = Boolean(title=question_data['title'],
				  text=question_data['text'],
                                  description=question_data['description'],
                                  target=int(question_data['goal']),
                                  patient=patient,
				  gasgoal=selected_goal,
				  baseline=question_data['baseline'],
				  timeline=question_data['timeline'],
				  indicator=question_data['indicator'],
				  scorepos2=question_data['scorepos2'],
				  scorepos1=question_data['scorepos1'],
				  scoreneg1=question_data['scoreneg1'],
				  scoreneg2=question_data['scoreneg2'],
				  activated=1,
				  needsplanning=0,
				  isgoalplanningdata = 1)
                boolean.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()


            elif t == "[u'category']": # new question is categorical
                category_list = []

                i = 1
                while 'cat' + str(i) in question_data:
                    category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                    category_list.append(question_data['cat'+ str(i)].lower())
                    i = i + 1

                categorical = Categorical(title=selected_strategy.title,
					    text=question_data['text'],
                                            description=question_data['description'],
                                            categories=category_list,
                                            patient=patient)

                if question_data['goal'].lower() in category_list: # check for numerical or text goal
                    categorical.target = category_list.index(question_data['goal'].lower())
                else:
                    categorical.target = int(question_data['goal'])

                categorical.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

            elif t == "[u'integer']": # new question is free form
		#selected_strategy.text = question_data['text']
		#selected_strategy.description = question_data['description']
		#selected_strategy.target = question_data['target']
		#selected_strategy.text = question_data['units']

                free_form = FreeForm(title=question_data['title'],
				     text=question_data['text'],
                                     description=question_data['description'],
                                     target = int(question_data['goal']),
                                     patient=patient,
                                     units=question_data['units'],
				     gasgoal=selected_goal,
				     baseline=question_data['baseline'],
				     timeline=question_data['timeline'],
				     indicator=question_data['indicator'],
				     scorepos2=question_data['scorepos2'],
				     scorepos1=question_data['scorepos1'],
				     scoreneg1=question_data['scoreneg1'],
				     scoreneg2=question_data['scoreneg2'],
				     activated=1,
				     needsplanning=0,
				     isgoalplanningdata = 1)
		#print 'Saved the freeform'
                free_form.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()
            elif t == "[u'slider']": # new question is slider
                slider = Slider(title=question_data['title'],
				text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                max_value=question_data['max_value'],
                                min_value=question_data['min_value'],
                                increment=question_data['increment'],
				gasgoal=selected_goal,
				baseline=question_data['baseline'],
				timeline=question_data['timeline'],
				indicator=question_data['indicator'],
				scorepos2=question_data['scorepos2'],
				scorepos1=question_data['scorepos1'],
				scoreneg1=question_data['scoreneg1'],
				scoreneg2=question_data['scoreneg2'],
				activated=1,
				needsplanning=0,
				isgoalplanningdata = 1)
                slider.save()


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

    #find Goal Question (isgoalplanningdata = 1)
    strategy_list = Question.objects.filter(gasgoal=selected_goal)
    for each_strategy in strategy_list:
	if each_strategy.isgoalplanningdata == 1:
	    selected_goal_question = each_strategy
    

    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_goal_question': selected_goal_question}
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
	    #checking for "Create Another Strategy" button pressed
	    if str(v) == "[u'Create Another Strategy']":
		pageforward = 'createanotherstrategy'
	    #Done - checking for "Create Another Strategy" button pressed

	    #checking for "Next" button pressed
	    if str(v) == "[u'Next']":
		pageforward = 'next'
	    #Done - checking for "Next" button pressed

            question_data[str(k)] = v.pop()
	#Check for blank title, if so dont save strategy
	if question_data['title'] == '':
	    print 'There is no strategy data'
	else:
	    #Save Question Title, Importance, and Difficulty to PreQuestion for further planning
	    newstrategy = PreQuestion(title=question_data['title'], 
			         importance=question_data['importance'],
			         difficulty=question_data['difficulty'],
			         gasgoal=selected_goal, 
			         patient=patient)
            newstrategy.save()

	context_dict = {'patient': patient, 'selected_goal': selected_goal}

	if pageforward == 'createanotherstrategy':
	    return render(request, 'new_strategy.html', {'patient': patient})
	if pageforward == 'next':
	    return render(request, 'new_strategy_selection_forward.html', {'patient': patient})

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
    #Find all strategies
    strategy_list = PreQuestion.objects.filter(gasgoal=selected_goal)
	
    #Reset needsplanning for all strategies because user will decide what strategies to use
    for tempstrat in strategy_list:
	tempstrat.needsplanning = 0
	tempstrat.save()

    #Find all new (non active) strategies
    non_active_strategy_list = PreQuestion.objects.filter(gasgoal=selected_goal, activated='0')

    #for chkneedsplanningstrat in strategy_list:
	#print tempGASGoals.select
        #if chkneedsplanningstrat.needsplanning == 0:
	    #needsplanning_strategy_list = chkneedsplanningstrat
    #print 'All strategies created that needs planning:'
    #for plzprint in needsplanning_strategy_list:
	#print plzprint.title
    
    no_selected_checkbox = False #default

    #Create dictionary
    context_dict = {'gas_goal_strategies' : non_active_strategy_list, 'patient': patient, 'selected_goal': selected_goal, 'status': no_selected_checkbox}

    #print request.POST
    if request.method == 'POST':
	#Reset flag (needsplanning) to 0 then update.
	#for stratcheck in strategy_list:
	    #stratcheck.needsplanning = 0
	    #stratcheck.activated = 0
	    #stratcheck.save()

        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')

	# Check if the list of items is empty
	if not response.items():
		#print 'Response list is empty'
		no_selected_checkbox = True
		# Update context dictionary
		context_dict = {'gas_goal_strategies' : non_active_strategy_list, 'patient': patient, 'selected_goal': selected_goal, 'status': no_selected_checkbox}
		return render(request, 'new_strategy_selection.html', context_dict)

	# If the list of items is not empty:
	if response.items():
        	for k, v in response.items():
	    		for stratcheck in strategy_list:
                		if str(k) == str(stratcheck.id): # if the ID specified in k is the same as the ID of the strategy
		    			if v.pop() == 'selected': # then, check if v.pop contains selected for that pair of k and v
	                			#print stratcheck.title
						stratcheck.needsplanning = 1 # and if it's true, then indicate that this strategy needs planning
						stratcheck.activated = 0
						stratcheck.save()

	return render(request, 'new_strategy_planning_forward.html', context_dict)

    else:
        return render(request, 'new_strategy_selection.html', context_dict)


def new_strategy_planning_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'new_strategy_planning_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def new_strategy_planning(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))

    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    #Find flagged (needsplanning) strategies and finish them 1 by 1
    strategy_list = PreQuestion.objects.filter(gasgoal=selected_goal)
    for tempstrategy in strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy

    #Create dict
    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_strategy': selected_strategy }

    #print request.POST
    if request.method == 'POST':
	#unflag needsplanning for strategy submitted.
	selected_strategy.needsplanning = 0
	selected_strategy.activated = 1
	selected_strategy.save()

        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
            question_data[str(k)] = v.pop()

	#print question_data
	if question_data['text'] == '':
		print 'These is no strategy planning data.'
	else:
            if t == "[u'boolean']": # new question is boolean
                boolean = Boolean(title=selected_strategy.title,
				  text=question_data['text'],
                                  description=question_data['description'],
                                  target=int(question_data['goal']),
                                  patient=patient,
				  gasgoal=selected_strategy.gasgoal,
				  importance=selected_strategy.importance,
				  difficulty=selected_strategy.difficulty,
				  baseline=question_data['baseline'],
				  action=question_data['action'],
				  timeline=question_data['timeline'],
				  indicator=question_data['indicator'],
				  scorepos2=question_data['scorepos2'],
				  scorepos1=question_data['scorepos1'],
				  scoreneg1=question_data['scoreneg1'],
				  scoreneg2=question_data['scoreneg2'],
				  activated=1,
				  needsplanning=0)
                boolean.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		selected_strategy.delete()


            elif t == "[u'category']": # new question is categorical
                category_list = []

                i = 1
                while 'cat' + str(i) in question_data:
                    category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                    category_list.append(question_data['cat'+ str(i)].lower())
                    i = i + 1

                categorical = Categorical(title=selected_strategy.title,
					    text=question_data['text'],
                                            description=question_data['description'],
                                            categories=category_list,
                                            patient=patient)

                if question_data['goal'].lower() in category_list: # check for numerical or text goal
                    categorical.target = category_list.index(question_data['goal'].lower())
                else:
                    categorical.target = int(question_data['goal'])

                categorical.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		selected_strategy.delete()

            elif t == "[u'integer']": # new question is free form
		#selected_strategy.text = question_data['text']
		#selected_strategy.description = question_data['description']
		#selected_strategy.target = question_data['target']
		#selected_strategy.text = question_data['units']

                free_form = FreeForm(title=selected_strategy.title,
				     text=question_data['text'],
                                     description=question_data['description'],
                                     target = int(question_data['goal']),
                                     patient=patient,
                                     units=question_data['units'],
				     gasgoal=selected_strategy.gasgoal,
				     importance=selected_strategy.importance,
				     difficulty=selected_strategy.difficulty,
				     baseline=question_data['baseline'],
				     action=question_data['action'],
				     timeline=question_data['timeline'],
				     indicator=question_data['indicator'],
				     scorepos2=question_data['scorepos2'],
				     scorepos1=question_data['scorepos1'],
				     scoreneg1=question_data['scoreneg1'],
				     scoreneg2=question_data['scoreneg2'],
				     activated=1,
				     needsplanning=0)
		print 'Saved the freeform'
                free_form.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()
            elif t == "[u'slider']": # new question is slider
                slider = Slider(title=selected_strategy.title,
				text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                max_value=question_data['max_value'],
                                min_value=question_data['min_value'],
                                increment=question_data['increment'],
				gasgoal=selected_strategy.gasgoal,
				importance=selected_strategy.importance,
				difficulty=selected_strategy.difficulty,
				baseline=question_data['baseline'],
				action=question_data['action'],
				timeline=question_data['timeline'],
				indicator=question_data['indicator'],
				scorepos2=question_data['scorepos2'],
				scorepos1=question_data['scorepos1'],
				scoreneg1=question_data['scoreneg1'],
				scoreneg2=question_data['scoreneg1'],
				activated=1,
				needsplanning=0)
                slider.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

	#check if anymore strategies need planning, if so repeat strategy planning page
	#if not, continue to overall summary page.
	for tempstrategy in strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'new_strategy_planning_forward.html', context_dict)
	else:
	    return render(request, 'overall_summary_forward.html', context_dict)
    
    return render(request, 'new_strategy_planning.html', context_dict)

# ______________________________________________   Overall Summary ___________________________________________________________
@user_passes_test(is_physician)
def overall_summary_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'overall_summary_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def overall_summary(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
	    print tempGASGoals.goal1

    #Find Goal Question
    strategy_list = Question.objects.filter(gasgoal=selected_goal)
    for each_strategy in strategy_list:
	if each_strategy.isgoalplanningdata == 1:
	    selected_goal_question = each_strategy

    #Find all active strategies
    active_strategy_list = Question.objects.filter(gasgoal=selected_goal, activated='1', isgoalplanningdata='0')
    for astrat in active_strategy_list:
	print astrat.title

    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_goal_question': selected_goal_question, 'active_strategy_list': active_strategy_list}
    return render(request, 'overall_summary.html', context_dict)

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
        #print ' * Is it a physician making request\?'
        physician = Physician.objects.get(user=request.user)
    except Physician.DoesNotExist:
        physician = None
        #print ' * No, it is not a physician'

    # Check if the user of the request is a significant other
    try:
        #print ' * Is it a SigOther making request\?'
        sig_other = SignificantOther.objects.get(user=request.user)
    except SignificantOther.DoesNotExist:
        sig_other = None
        #print ' * No, it is not a SigOther'

    # Get the right user for the graph
    # For a physician, this means checking that they are,
    # a physician for the patient they are requesting to view.
    if user_id and physician:
        user = get_object_or_404(User, pk=int(user_id))
        try:
            if not Patient.objects.get(user=user).physicians.filter(pk=physician.pk).exists():
                #print ' * This patient is not associated with this doctor'
                raise Http404
        except Patient.DoesNotExist as e:
            #print ' * Exception: Patient does not exists'
            #print e
            raise Http404
    elif user_id and sig_other:
        user = get_object_or_404(User, pk=int(user_id))
        try:
            patient_given_id = Patient.objects.get(user=user)
        except Patient.DoesNotExist as e:
            #print ' * Exception: Patient does not exists'
            #print e
            raise Http404
        if not sig_other.patients.filter(pk=patient_given_id.pk).exists():
            #print ' * This patient is not associated with this SO'
            raise Http404
    else:
        user = request.user

    patient = user
    at_least_1_goal = 'nogoal'
    selected_goal = '-1'
    #Pull selected goal for this patient
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	at_least_1_goal = 'goalpresent'
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    #print at_least_1_goal
    # Pull the questions for this user
    question_list = Question.objects.filter(patient=user, gasgoal=selected_goal, activated=1)
    questions = Question.objects.filter(patient=user, gasgoal=selected_goal, activated=1).get_real_instances(question_list)
    active_questions = Question.objects.filter(patient=user, gasgoal=selected_goal, activated=1)
	
    #testing
    order = []
    for index in question_list:
	if index.isgoalplanningdata == 1:
	    order.append(index)
    count = 1
    for index in question_list:
	if index.isgoalplanningdata == 0:
	    order.append(index)
	    count = count+1
    #print 'Is this reordered?'
    #print order
    questions = order
    question_list = order
    active_questions = order
    #print questions
    #END Testing

    #start of original
    #latest_datetime = []
    #latest_datetime = Answer.objects.extra(
    #        select={'the_date': 'date(date)' }
    #    ).values_list('the_date').annotate(max_date=Max('date'))
    #max_dates = [item[1] for item in latest_datetime]



    #literally ... but original answers = Answer.objects.filter(question__in=questions).filter(date__in=max_dates).order_by('date')
    #end of original
    answers = Answer.objects.filter(question__in=questions).order_by('date')


    #check most recent point and base gasscore on most recent point. Check for type fo question as well.
    #for tempanswer in answers:
	#most_recent_value=tempanswer.value
	#if most_recent_value >= tempanswer.question.question_ptr.scoreneg2:
	    #print most_recent_value
	    #print "GAS Score +2"
	    
	    #gasscore = '+2'
    #try again lol
    for question1 in question_list:
	for tempanswer in answers:
	    if tempanswer.question.question_ptr.id == question1.id:
		question1.displayedscore = tempanswer.value
		question1.save()
		#print question1.title
		#print question1.displayedscore
		#print '-------'
    #end check most recent

    #Logic for gasscore....
    for question in question_list:
	mostrecentscore = question.displayedscore
	if (question.scorepos2 - question.scoreneg2) <= 0:
	     #+2 - (-2) is negative, start +2 and add to get to -2
	    if mostrecentscore <= question.scorepos2:
		question.displayedscore = '+2'
	    elif mostrecentscore <= question.scorepos1:
		question.displayedscore = '+1'
	    elif mostrecentscore <= question.target:
		question.displayedscore = '0'
	    elif mostrecentscore <= question.scoreneg1:
		question.displayedscore = '-1'
	    else:
		question.displayedscore = '-2'
	else:
	    if mostrecentscore >= question.scorepos2:
		question.displayedscore = '+2'
	    elif mostrecentscore >= question.scorepos1:
		question.displayedscore = '+1'
	    elif mostrecentscore >= question.target:
		question.displayedscore = '0'
	    elif mostrecentscore >= question.scoreneg1:
		question.displayedscore = '-1'
	    else:
		question.displayedscore = '-2'
	question.save()     
    #end Logic for gasscore

    
    grouped_answers = defaultdict(list)
    new_grouped_answers = defaultdict(list)
    new_grouped_answers2 = defaultdict(list)
    ordered_grouped_answers = defaultdict(list)
    #old
    for ans in answers:
        grouped_answers[ans.question.title].append(ans)
    #end old
    #new
    for ans in answers:
	#print ans.question.isgoalplanningdata
	if ans.question.isgoalplanningdata == 1:
            new_grouped_answers[ans.question.title].append(ans)
    #print 'Should be all goal question data'
    #print new_grouped_answers
    for ans in answers:
	if ans.question.isgoalplanningdata == 0:
            new_grouped_answers2[ans.question.title].append(ans)
    #print 'Should be all just question data'
    #print new_grouped_answers2

    #print 'Unordered grouped answers'
    #print grouped_answers



    ordered_grouped_answers = grouped_answers
    #print 'Ordered Grouped Answers'
    #print ordered_grouped_answers
    #end new

    # A list to hold strategy questions (text fields)
    strategy_questions_list = []
    #counter for a list of strategy questions
    icount = 0
    print 'The order the Strategies read (issue with displaying on graph correcly? Try)'
    # Build nvd3 json
    data = []
    for k,v in new_grouped_answers.iteritems():
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

	print k
	#print values
	
	#find displayedscore of each question (compare title of question). Note: Bad way to do it since there could be another
	#question with the same name..... must find a better way.
	for eachquestion in question_list:
	    if k == eachquestion.title:
		displayedscoretemp = eachquestion.displayedscore
		isgoalplanningdata = eachquestion.isgoalplanningdata
		#populate a list with strategy questions
		sub_question = {}
		sub_question['key'] = "line-" + str(icount)
		sub_question['thequestion'] = eachquestion.text
		strategy_questions_list.append(sub_question)
		#print 'Current count: ' + str(icount)
		#count_str = "line-" + str(icount)
		#print count_str
		icount = icount + 1
	    
	#reorder data so goal question data is first???????????????????????????????????????????????????????????????????????
        data.append(
                {'key':k,
		 'displayedscore': displayedscoretemp,
		 'isgoalplanningdata': isgoalplanningdata,
                 'values': point_list,
                 'disabled': True,
                 'avg': avg,
                 'targ': v[0].question.target,
                 'std1': avg+stdev,
                 'std2': avg-stdev,
		 'datatag': sub_question['key'],
                 })

    #added another can delete probs
    for k,v in new_grouped_answers2.iteritems():
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

	print k
	#print values
	
	#find displayedscore of each question (compare title of question). Note: Bad way to do it since there could be another
	#question with the same name..... must find a better way.
	for eachquestion in question_list:
	    if k == eachquestion.title:
		displayedscoretemp = eachquestion.displayedscore
		isgoalplanningdata = eachquestion.isgoalplanningdata
		#populate a list with strategy questions
		sub_question = {}
		sub_question['key'] = "line-" + str(icount)
		sub_question['thequestion'] = eachquestion.text
		strategy_questions_list.append(sub_question)
		#print 'Current count: ' + str(icount)
		#count_str = "line-" + str(icount)
		#print count_str
		icount = icount + 1
	    
	#reorder data so goal question data is first???????????????????????????????????????????????????????????????????????
        data.append(
                {'key':k,
		 'displayedscore': displayedscoretemp,
		 'isgoalplanningdata': isgoalplanningdata,
                 'values': point_list,
                 'disabled': True,
                 'avg': avg,
                 'targ': v[0].question.target,
                 'std1': avg+stdev,
                 'std2': avg-stdev,
		 'datatag': sub_question['key'],
                 })
        #END added another can delete probs
    
    
    return render(request, "graph.html",
            {"data_json": json.dumps(data),
             "data": data,
             "graph_user": user,
	     "selected_goal": selected_goal,
	     "question_list": question_list,
	     "at_least_1_goal": at_least_1_goal,
	     "strategy_questions": strategy_questions_list,
	     "questions": active_questions})


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

## ______________________________________________   Follow Up Meeting Goaledit __________________________________________________
@user_passes_test(is_physician)
def followup_goaledit_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    return render(request, 'followup_goaledit_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_goaledit(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Jennifer Lawrence
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
	    
    #Find all banked goals
    banked_goals_list = GASGoals.objects.filter(patient=patient, activated='0')

    #Find Question for Goal (isgoalplannning = 1) .
    strategy_list = Question.objects.filter(gasgoal=selected_goal)
    for each_strategy in strategy_list:
	#print each_strategy.isgoalplanningdata
	if each_strategy.isgoalplanningdata == 1:
	    #print 'Goal Question '+each_strategy.text
	    selected_goal_question = each_strategy

    #Find all active strategies
    #active_strategy_list = Question.objects.filter(gasgoal=selected_goal, activated='1')
    #for astrat in active_strategy_list:
	#print astrat.title
    navselecterror = 'good'
    pageforward = 'unknown'
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
	navselecterror = 'error'
        for k, v in response.items():
	    
	    #Checking for "Edit and Activate" a new goal
	    if str(v) == "[u'Edit and Activate']":
	        for each_goal in gas_goals_list:
		    if str(k) == str(each_goal.id):
			#print 'deactivated' + selected_strategy.id
			print 'Edit and Activate pressed for:'+each_goal.goal1+'(id:' + str(each_goal.id)+')'
			#Deactivate all goals and activate edit/activate pressed
		        for tempGASGoals in gas_goals_list:
			    tempGASGoals.activated = 0
			    tempGASGoals.save()
			each_goal.activated = 1
			each_goal.save()
			#Find goal_question
			strategy_list = Question.objects.filter(gasgoal=each_goal)
			
    			for each_strategy in strategy_list:
			    if each_strategy.isgoalplanningdata == 1:
	    		        #print 'Goal Question '+each_strategy.text
	    			selected_goal_question = each_strategy
				selected_goal_question.needsplanning = '1'
	    			selected_goal_question.save()
			pageforward = 'followup_goal_planning_forward.html'
	    #Done - Checking for "edit and activate" a new goal

	    #checking for "Edit Strategies" button pressed
	    if str(v) == "[u'Edit Strategies']":
		pageforward = 'followup_strategyedit_forward.html'
	    #Done - checking for "finish" button pressed

	    #checking for "edit" button pressed (edit select goal)
	    if str(v) == "[u'Edit']":
		pageforward = 'followup_goal_planning_forward.html'
		for each_strategy in strategy_list:
		    if each_strategy.isgoalplanningdata == 1:
			each_strategy.needsplanning = '1'
	    		each_strategy.save()
	    #Done - checking for "edit" button pressed (edit select goal)

	    #checking for "Create New Goal" button pressed
	    if str(v) == "[u'Create New Goal']":
		pageforward = 'followup_goal_create_forward.html'
	    #Done - checking for "Create New Goal" button pressed

	    #checking for "Graph" button pressed
	    if str(v) == "[u'Graph']":
		pageforward = 'graph_forward.html'
	    #Done - checking for "Create New Goal" button pressed



            question_data[str(k)] = v.pop()
	    if k == 'navselect':
		navselecterror = 'good'

	context_dict = {'patient': patient, 'selected_goal': selected_goal, 'banked_goals_list': banked_goals_list, 'navselecterror' : navselecterror}

	#Next Page logic 
	if pageforward == 'followup_strategyedit_forward.html':
	    return render(request, 'followup_strategyedit_forward.html', context_dict)
	if pageforward == 'followup_goal_planning_forward.html':
	    return render(request, 'followup_goal_planning_forward.html', context_dict)
	if pageforward == 'followup_goal_create_forward.html':
	    return render(request, 'followup_goal_create_forward.html', context_dict)
	if pageforward == 'graph_forward.html':
	    return render(request, 'graph_forward.html', context_dict)
	#done Next Page Logic

	#If user didnt select option., Return to page with error notification
	if navselecterror == 'error':
	    return render(request, 'followup_goaledit.html', context_dict)

	if question_data['navselect'] == 'keep':
	    return render(request, 'followup_strategyedit_forward.html', context_dict)
	if question_data['navselect'] == 'edit':
	    return render(request, 'followup_goal_planning_forward.html', context_dict)
	if question_data['navselect'] == 'select':
	    return render(request, 'followup_goal_selection_forward.html', context_dict)
	if question_data['navselect'] == 'create':
	    return render(request, 'followup_goal_create_forward.html', context_dict)

    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'banked_goals_list': banked_goals_list, 'navselecterror' : navselecterror}
    return render(request, 'followup_goaledit.html', context_dict)

#__________________________________________________Follow Up Meeting Goal Create_________________________________________
@user_passes_test(is_physician)
def followup_goal_create_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    return render(request, 'followup_goal_create_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_goal_create(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        gasgoals_data = {}
        for k, v in response.items():
	    #checking for "Create Another Goal" button pressed
	    if str(v) == "[u'Create Another Goal']":
		pageforward = 'createanothergoal'
	    #Done - checking for "Create Another Goal" button pressed

	    #checking for "Save + Continue" button pressed
	    if str(v) == "[u'Save + Continue']":
		pageforward = 'savecontinue'
	    #Done - checking for "Create New Goal" button pressed

            gasgoals_data[str(k)] = v.pop()

	print gasgoals_data
	if gasgoals_data['goal1'] == '':
	    print "There is no data"
	else:
            gas_goals = GASGoals(goal1=gasgoals_data['goal1'], 
			         environmentalassessment1=gasgoals_data['environmentalassessment1'], 
			         patient=patient)
            gas_goals.save()
	
	#check what page to forward to
	if pageforward == 'createanothergoal':
	    return render(request, 'followup_goal_create.html', {'patient': patient})
	if pageforward == 'savecontinue':
	    return render(request, 'followup_goaledit_forward.html', {'patient': patient})

	if gasgoals_data['createanother'] == 'yes': 
            return render(request, 'gas_step1.html', {'patient': patient})
	else:
	    return render(request, 'followup_goal_selection_forward.html', {'patient': patient})
    else:

        return render(request, 'followup_goal_create.html', {'patient': patient})

## ______________________________________________   Follow Up Meeting Goal selection __________________________________
@user_passes_test(is_physician)
def followup_goal_selection(request, user_id=0):
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
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient, 'selected_goal': selected_goal}
        #return render(request, 'planning.html', context_dict)
	return render(request, 'followup_goal_planning_forward.html', context_dict)

    else:
	context_dict = {'gas_goals': gas_goals_list, 'patient': patient}
        return render(request, 'followup_goal_selection.html', context_dict)

# ______________________________________________   Follow Up Meeting Goal Planning (old) ___________________________________
@user_passes_test(is_physician)
def followup_goal_planning_forward_old(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_goal_planning_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_goal_planning_old(request, user_id):
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
	    selected_goal.action = question_data['action']
	    selected_goal.scorepos2 = question_data['scorepos2']
	    selected_goal.scorepos1 = question_data['scorepos1']
	    selected_goal.scoreneg1 = question_data['scoreneg1']
	    selected_goal.scoreneg2 = question_data['scoreneg2']
	
	    selected_goal.save()

        return render(request, 'followup_goal_summary_forward.html', context_dict)

    return render(request, 'followup_goal_planning.html', context_dict)

#__________________________________________ Follow Up Goal planning **NEW**___________________________________________
def followup_goal_planning_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_goal_planning_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_goal_planning(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))

    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    
    for tempGASGoals in gas_goals_list:
	print tempGASGoals.goal1
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
    found_strategy_yes = 'noneavailable'
    type_selected_strategy = 'nothing'
    #Find flagged (needsplanning) strategies and finish them 1 by 1
    #Start with Prequestions then questions. (Therefore check prequestions last)
    #Check Questions
    #Check FreeForm First
    freeform_strategy_list = FreeForm.objects.filter(gasgoal=selected_goal, isgoalplanningdata = '1')
    for tempstrategy in freeform_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'freeform'
	    found_strategy_yes = 'yes'
    #Check Boolean
    boolean_strategy_list = Boolean.objects.filter(gasgoal=selected_goal, isgoalplanningdata = '1')
    for tempstrategy in boolean_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'boolean'
	    found_strategy_yes = 'yes'
    #Check slider
    slider_strategy_list = Slider.objects.filter(gasgoal=selected_goal, isgoalplanningdata = '1')
    for tempstrategy in slider_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'slider'
	    found_strategy_yes = 'yes'

    if found_strategy_yes == 'noneavailable':
	print 'Couldnt find question for goal, please create one'
	type_selected_strategy = 'noneavailable'
	context_dict = {'patient': patient, 'selected_goal': selected_goal, 'type_selected_strategy': type_selected_strategy }
    else:
        #Create dict
        context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_strategy': selected_strategy, 'type_selected_strategy': type_selected_strategy }

    #print request.POST
    if request.method == 'POST':
	if found_strategy_yes == 'yes':
	    #unflag needsplanning for strategy submitted.
	    selected_strategy.needsplanning = 0
	    selected_strategy.activated = 1
	    selected_strategy.save()

        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
            question_data[str(k)] = v.pop()

	#might have to move this
	selected_goal.goal1=question_data['title']
	selected_goal.environmentalassessment1=question_data['environmentalassessment1']
	selected_goal.save()

	if question_data['text'] == '':
	    print 'These is no followup strategy planning data.'
	elif type_selected_strategy == 'freeform':
	    print 'Updating Freeform strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.units=question_data['units']
	    selected_strategy.baseline=question_data['baseline']
	    #selected_strategy.action=question_data['action'] #Action is not applicable to goals
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.isgoalplanningdata=1
	    selected_strategy.save()

	elif type_selected_strategy == 'boolean':
	    print 'Updating Boolean strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.baseline=question_data['baseline']
	    #selected_strategy.action=question_data['action'] #Action is not applicable to goals
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.isgoalplanningdata=1
	    selected_strategy.save()

	elif type_selected_strategy == 'slider':
	    print 'Updating Slider strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.baseline=question_data['baseline']
	    #selected_strategy.action=question_data['action']  #Action is not applicable to goals
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.min_value=question_data['min_value']
	    selected_strategy.max_value=question_data['max_value']
	    selected_strategy.increment=question_data['increment']
	    selected_strategy.isgoalplanningdata=1
	    selected_strategy.save()

	else:
            if t == "[u'boolean']": # new question is boolean
                boolean = Boolean(title=question_data['title'],
				  text=question_data['text'],
                                  description=question_data['description'],
                                  target=int(question_data['goal']),
                                  patient=patient,
				  gasgoal=selected_goal,
				  #importance=selected_strategy.importance,
				  #difficulty=selected_strategy.difficulty,
				  baseline=question_data['baseline'],
				  #action=question_data['action'], #Action is not applicable to goals
				  timeline=question_data['timeline'],
				  indicator=question_data['indicator'],
				  scorepos2=question_data['scorepos2'],
				  scorepos1=question_data['scorepos1'],
				  scoreneg1=question_data['scoreneg1'],
				  scoreneg2=question_data['scoreneg2'],
				  activated=1,
				  needsplanning=0,
			          isgoalplanningdata=1)
                boolean.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()


            elif t == "[u'category']": # new question is categorical
                category_list = []

                i = 1
                while 'cat' + str(i) in question_data:
                    category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                    category_list.append(question_data['cat'+ str(i)].lower())
                    i = i + 1

                categorical = Categorical(title=selected_strategy.title,
					    text=question_data['text'],
                                            description=question_data['description'],
                                            categories=category_list,
                                            patient=patient)

                if question_data['goal'].lower() in category_list: # check for numerical or text goal
                    categorical.target = category_list.index(question_data['goal'].lower())
                else:
                    categorical.target = int(question_data['goal'])

                categorical.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

            elif t == "[u'integer']": # new question is free form
		#selected_strategy.text = question_data['text']
		#selected_strategy.description = question_data['description']
		#selected_strategy.target = question_data['target']
		#selected_strategy.text = question_data['units']

                free_form = FreeForm(title=question_data['title'],
				     text=question_data['text'],
                                     description=question_data['description'],
                                     target = int(question_data['goal']),
                                     patient=patient,
                                     units=question_data['units'],
				     gasgoal=selected_goal,
				     #importance=selected_strategy.importance,
				     #difficulty=selected_strategy.difficulty,
				     baseline=question_data['baseline'],
				     #action=question_data['action'], #Action is not applicable to goals
				     timeline=question_data['timeline'],
				     indicator=question_data['indicator'],
				     scorepos2=question_data['scorepos2'],
				     scorepos1=question_data['scorepos1'],
				     scoreneg1=question_data['scoreneg1'],
				     scoreneg2=question_data['scoreneg2'],
				     activated=1,
				     needsplanning=0,
				     isgoalplanningdata=1)
		print 'Saved the freeform'
                free_form.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()
            elif t == "[u'slider']": # new question is slider
                slider = Slider(title=question_data['title'],
				text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                max_value=question_data['max_value'],
                                min_value=question_data['min_value'],
                                increment=question_data['increment'],
				gasgoal=selected_goal,
				#importance=selected_strategy.importance,
				#difficulty=selected_strategy.difficulty,
				baseline=question_data['baseline'],
				#action=question_data['action'], #Action is not applicable to goals
				timeline=question_data['timeline'],
				indicator=question_data['indicator'],
				scorepos2=question_data['scorepos2'],
				scorepos1=question_data['scorepos1'],
				scoreneg1=question_data['scoreneg1'],
				scoreneg2=question_data['scoreneg2'],
				activated=1,
				needsplanning=0,
				isgoalplanningdata=1)
                slider.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

	#check if anymore strategies need planning, if so repeat strategy planning page
	#if not, continue to overall summary page.
	
	for tempstrategy in freeform_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_goal_planning_forward.html', context_dict)
	for tempstrategy in boolean_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_goal_planning_forward.html', context_dict)
	for tempstrategy in slider_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_goal_planning_forward.html', context_dict)
	else:
	    return render(request, 'followup_goaledit_forward.html', context_dict)
    
    return render(request, 'followup_goal_planning.html', context_dict)

# ______________________________________________   Follow Up Meeting Goal Summary ______________________________
@user_passes_test(is_physician)
def followup_goal_summary_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'follow_goal_summary_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_goal_summary(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    context_dict = {'patient': patient, 'selected_goal': selected_goal}
    return render(request, 'followup_goal_summary.html', context_dict)


## ______________________________________________   Follow Up Meeting Strategyedit ______________________________________________
@user_passes_test(is_physician)
def followup_strategyedit_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_strategyedit_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_strategyedit(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    #Reset all needsplanning flags for questions and prequestions (so no multiple edits on strategy planning page
    all_strategy_list = Question.objects.filter(patient=patient, gasgoal=selected_goal, isgoalplanningdata = '0')
    for each_strategy in all_strategy_list:
	each_strategy.needsplanning = 0
	each_strategy.save()
    all_prequestion_list = PreQuestion.objects.filter(patient=patient, gasgoal=selected_goal)
    for each_strategy in all_prequestion_list:
	each_strategy.needsplanning = 0
	each_strategy.save()

    #Need to find all strategies so I guess we need to check every type of question?... no we dont yeah!
    #Note: selected_freeform_strategy_list wouldnt have freeform in it since its all selected strategies ---- please update!!!!
    #Find all selected freeform strategies
    selected_freeform_strategy_list = Question.objects.filter(patient=patient, gasgoal=selected_goal, activated='1', isgoalplanningdata = '0')
	    
    #Find all non activated freeform strategies
    nonactive_freeform_strategy_list = Question.objects.filter(patient=patient, gasgoal=selected_goal, activated='0', isgoalplanningdata = '0')

    #Find all prequestion strategies
    prequestion_strategy_list = PreQuestion.objects.filter(patient=patient, gasgoal=selected_goal, activated='0')

    #Find all active strategies
    #active_strategy_list = Question.objects.filter(gasgoal=selected_goal, activated='1')
    #for astrat in active_strategy_list:
	#print astrat.title
    navselecterror = 'good'
    pageforward = 'unknown'
    #print request.POST
    if request.method == 'POST':
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
	navselecterror = 'error'
        for k, v in response.items():

	    #Determine which Button was Pressed then forward to required page.
	    #checking for "deactivate" button pressed for selected_freeform_strategy_list
	    if str(v) == "[u'Deactivate']":
	        for selected_strategy in selected_freeform_strategy_list:
		    if str(k) == 'deactivate' + str(selected_strategy.id):
			#print 'deactivated' + selected_strategy.id
			print 'Deactivate button was pressed for:'+selected_strategy.title+'(id:' + str(selected_strategy.id)+')'
			#Deactive strategy and return to followup_strategyedit page
			selected_strategy.activated = 0
			selected_strategy.save()
			pageforward = 'forward_followup_strategyedit'
	    #Done - checking for "deactivate" pressed for selected_freeform_strategy_list

	    #checking for "activate" button pressed for nonactive_freeform_strategy_list
	    if str(v) == "[u'Activate']":
	        for nonactive_strategy in nonactive_freeform_strategy_list:
		    if str(k) == 'activate' + str(nonactive_strategy.id):
			print 'Activate button was pressed for:'+nonactive_strategy.title+'(id:' + str(nonactive_strategy.id)+')'
			#Activate strategy and return to followup_strategyedit page
			nonactive_strategy.activated = 1
			nonactive_strategy.save()
			pageforward = 'forward_followup_strategyedit'
	    #Done - checking for "deactivate" pressed for selected_freeform_strategy_list

	    #checking for "edit+activate" button pressed for prequestion_strategy_list
	    if str(v) == "[u'Edit + Activate']":
	        for each_prequestion in prequestion_strategy_list:
		    if str(k) == 'preedit' + str(each_prequestion.id):
			print 'EditActivate button was pressed for:'+each_prequestion.title+'(id:' + str(each_prequestion.id)+')'
			#Flag Strategy for needsplanning and forward to strategy planning page
			each_prequestion.needsplanning = 1
			each_prequestion.save()
			pageforward = 'forward_followup_strategy_planning'
	    #Done - checking for "edit+activate" button pressed for prequestion_strategy_list

	    #checking for "edit" button pressed for selected_freeform_strategy_list and nonactive_freeform_strategy_list
	    if str(v) == "[u'Edit']":
	        for nonactive_strategy in nonactive_freeform_strategy_list:
		    if str(k) == 'edit' + str(nonactive_strategy.id):
			print 'Edit button was pressed for:'+nonactive_strategy.title+'(id:' + str(nonactive_strategy.id)+')'
			#Flag Strategy for needsplanning and forward to strategy planning page
			nonactive_strategy.needsplanning = 1
			nonactive_strategy.save()
			pageforward = 'forward_followup_strategy_planning'
		for selected_strategy in selected_freeform_strategy_list:
		    if str(k) == 'edit' + str(selected_strategy.id):
			print 'Edit button was pressed for:'+selected_strategy.title+'(id:' + str(selected_strategy.id)+')'
			#Flag Strategy for needsplanning and forward to strategy planning page
			selected_strategy.needsplanning = 1
			selected_strategy.save()
			pageforward = 'forward_followup_strategy_planning'
	    #Done - checking for "edit" button pressed for prequestion_strategy_list

	    #checking for "Graph" button pressed
	    if str(v) == "[u'Graph']":
		pageforward = 'graph_forward.html'
	    #Done - checking for "finish" button pressed

	    #checking for "Create New Strategy" button pressed
	    if str(v) == "[u'Create New Strategy']":
		pageforward = 'followup_strategy_create_forward.html'
	    #Done - checking for "finish" button pressed

            question_data[str(k)] = v.pop()
	    if k == 'navselect':
		navselecterror = 'good'
		
	

	context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_freeform_strategy_list': selected_freeform_strategy_list, 'nonactive_freeform_strategy_list': nonactive_freeform_strategy_list, 'prequestion_strategy_list': prequestion_strategy_list, 'navselecterror' : navselecterror}

	#Next Page logic 
	if pageforward == 'forward_followup_strategyedit':
	    return render(request, 'followup_strategyedit_forward.html', context_dict)
	if pageforward == 'graph_forward.html':
	    return render(request, 'graph_forward.html', context_dict)
	if pageforward == 'forward_followup_strategy_planning':
	    return render(request, 'followup_strategy_planning_forward.html', context_dict)
	if pageforward == 'followup_strategy_create_forward.html':
	    return render(request, 'followup_strategy_create_forward.html', context_dict)
	#done Next Page Logic

	#Old code-----If user didnt select option., Return to page with error notification
	if navselecterror == 'error':
	    return render(request, 'followup_strategyedit.html', context_dict)

	if question_data['navselect'] == 'keep':
	    return render(request, 'followup_overall_summary_forward.html', context_dict)
	if question_data['navselect'] == 'select':
	    return render(request, 'followup_strategy_selection_forward.html', context_dict)
	if question_data['navselect'] == 'create':
	    return render(request, 'followup_strategy_create_forward.html', context_dict)

    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_freeform_strategy_list': selected_freeform_strategy_list, 'nonactive_freeform_strategy_list': nonactive_freeform_strategy_list, 'prequestion_strategy_list': prequestion_strategy_list, 'navselecterror' : navselecterror}
    return render(request, 'followup_strategyedit.html', context_dict)

## ______________________________________________   Follow Up strategy create ______________________________________________
@user_passes_test(is_physician)
def followup_strategy_create_forward_old(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_strategy_create_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_strategy_create_old(request, user_id):
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
	    #Save Question Title, Importance, and Difficulty to PreQuestion for further planning
	    newstrategy = PreQuestion(title=question_data['title'], 
			         importance=question_data['importance'],
			         difficulty=question_data['difficulty'],
			         gasgoal=selected_goal, 
			         patient=patient)
            newstrategy.save()
	#Check if user would like to create another strategy or move to next step
	if question_data['createanotherstrategy'] == 'yes':
	    return render(request, 'followup_strategy_create.html', context_dict)
	else:
	    return render(request, 'followup_strategy_selection_forward.html', context_dict)
    else:

        return render(request, 'followup_strategy_create.html', context_dict)

## ______________________________________________   Follow Up strategy create **NEW**_____________________________________
@user_passes_test(is_physician)
def followup_strategy_create_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_strategy_create_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_strategy_create(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    #Create dict
    context_dict = {'patient': patient, 'selected_goal': selected_goal}
    print 'New strategy create page'
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
	    #Save Question Title, Importance, and Difficulty to PreQuestion for further planning
	    if t == "[u'boolean']": # new question is boolean
                boolean = Boolean(title=question_data['title'],
				  text=question_data['text'],
                                  description=question_data['description'],
                                  target=int(question_data['goal']),
                                  patient=patient,
				  gasgoal=selected_goal,
				  importance=question_data['importance'],
				  difficulty=question_data['difficulty'],
				  baseline=question_data['baseline'],
				  action=question_data['action'],
				  timeline=question_data['timeline'],
				  indicator=question_data['indicator'],
				  scorepos2=question_data['scorepos2'],
				  scorepos1=question_data['scorepos1'],
				  scoreneg1=question_data['scoreneg1'],
				  scoreneg2=question_data['scoreneg2'],
				  activated=1,
				  needsplanning=0)
                boolean.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()


            elif t == "[u'category']": # new question is categorical
                category_list = []

                i = 1
                while 'cat' + str(i) in question_data:
                    category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                    category_list.append(question_data['cat'+ str(i)].lower())
                    i = i + 1

                categorical = Categorical(title=selected_strategy.title,
					    text=question_data['text'],
                                            description=question_data['description'],
                                            categories=category_list,
                                            patient=patient)

                if question_data['goal'].lower() in category_list: # check for numerical or text goal
                    categorical.target = category_list.index(question_data['goal'].lower())
                else:
                    categorical.target = int(question_data['goal'])

                categorical.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

            elif t == "[u'integer']": # new question is free form
		#selected_strategy.text = question_data['text']
		#selected_strategy.description = question_data['description']
		#selected_strategy.target = question_data['target']
		#selected_strategy.text = question_data['units']

                free_form = FreeForm(title=question_data['title'],
				     text=question_data['text'],
                                     description=question_data['description'],
                                     target = int(question_data['goal']),
                                     patient=patient,
                                     units=question_data['units'],
				     gasgoal=selected_goal,
				     importance=question_data['importance'],
				     difficulty=question_data['difficulty'],
				     baseline=question_data['baseline'],
				     action=question_data['action'],
				     timeline=question_data['timeline'],
				     indicator=question_data['indicator'],
				     scorepos2=question_data['scorepos2'],
				     scorepos1=question_data['scorepos1'],
				     scoreneg1=question_data['scoreneg1'],
				     scoreneg2=question_data['scoreneg2'],
				     activated=1,
				     needsplanning=0)
		#print 'Saved the freeform'
                free_form.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()
            elif t == "[u'slider']": # new question is slider
                slider = Slider(title=question_data['title'],
				text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                max_value=question_data['max_value'],
                                min_value=question_data['min_value'],
                                increment=question_data['increment'],
				gasgoal=selected_goal,
				importance=question_data['importance'],
				difficulty=question_data['difficulty'],
				baseline=question_data['baseline'],
				action=question_data['action'],
				timeline=question_data['timeline'],
				indicator=question_data['indicator'],
				scorepos2=question_data['scorepos2'],
				scorepos1=question_data['scorepos1'],
				scoreneg1=question_data['scoreneg1'],
				scoreneg2=question_data['scoreneg2'],
				activated=1,
				needsplanning=0)
                slider.save()
	return render(request, 'followup_strategyedit_forward.html', context_dict)
    else:

        return render(request, 'followup_strategy_create.html', context_dict)
## ______________________________________________   Follow Up strategy selection ______________________________________________
def followup_strategy_selection_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_strategy_selection_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_strategy_selection(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    #Find all strategies
    #Find all non active prequestions
    prequestion_strategy_list = PreQuestion.objects.filter(gasgoal=selected_goal, activated='0')
    #Find all active and non active questions
    question_strategy_list = Question.objects.filter(gasgoal=selected_goal)
    #--End Find all strategies

    for strat in question_strategy_list:
	print strat.title
	
    #Create dict
    context_dict = {'prequestion_strategy_list' : prequestion_strategy_list, 'question_strategy_list' : question_strategy_list, 'patient': patient, 'selected_goal': selected_goal}

    #print request.POST
    if request.method == 'POST':
	#Reset flag (needsplanning) to 0 then update.
	#for stratcheck in strategy_list:
	    #stratcheck.needsplanning = 0
	    #stratcheck.activated = 0
	    #stratcheck.save()
	
	#reset all activated flag to 0 then update (later on, look below) activated flag 
	#only if some of at least one strategy is selected... or there will be problems
	#add some code

	#Reset needsplanning for all strategies because user will decide what strategies to use
	#Reset needsplanning PreQuestions
        for tempstrat in prequestion_strategy_list:
	    tempstrat.needsplanning = 0
	    tempstrat.save()
	#Reset needsplanning Questions
        for tempstrat in question_strategy_list:
	    tempstrat.needsplanning = 0
	    tempstrat.save()

	#Reset activated for all strategies
	#Reset activated PreQuestions
        for tempstrat in prequestion_strategy_list:
	    tempstrat.activated = 0
	    tempstrat.save()
	#Reset activated Questions
        for tempstrat in question_strategy_list:
	    tempstrat.activated = 0
	    tempstrat.save()

        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
	    for stratcheck in prequestion_strategy_list:
                if str(k) == str(stratcheck.id):
		    if v.pop() == 'selected':
	                print stratcheck.title
			stratcheck.needsplanning = 1
			stratcheck.activated = 0
			stratcheck.save()
	    for stratcheck1 in question_strategy_list:
                if str(k) == str(stratcheck1.id):
		    if v.pop() == 'selected':
	                print stratcheck1.title
			stratcheck1.needsplanning = 1
			stratcheck1.activated = 0
			stratcheck1.save()

	
	return render(request, 'followup_strategy_planning_forward.html', context_dict)

    else:
        
        return render(request, 'followup_strategy_selection.html', context_dict)
#__________________________________________ Follow Up strategy planning ___________________________________________
def followup_strategy_planning_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_strategy_planning_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_strategy_planning(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))

    #Find selected goal to create new strategy linked to selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals

    type_selected_strategy = 'nothing'
    #Find flagged (needsplanning) strategies and finish them 1 by 1
    #Start with Prequestions then questions. (Therefore check prequestions last)
    #Check Questions
    #Check FreeForm First
    freeform_strategy_list = FreeForm.objects.filter(gasgoal=selected_goal)
    for tempstrategy in freeform_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'freeform'
    #Check Boolean
    boolean_strategy_list = Boolean.objects.filter(gasgoal=selected_goal)
    for tempstrategy in boolean_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'boolean'
    #Check slider
    slider_strategy_list = Slider.objects.filter(gasgoal=selected_goal)
    for tempstrategy in slider_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'slider'
    #Check Prequestions
    prequestion_strategy_list = PreQuestion.objects.filter(gasgoal=selected_goal)
    for tempstrategy in prequestion_strategy_list:
	if tempstrategy.needsplanning == 1:
	    selected_strategy = tempstrategy
	    type_selected_strategy = 'prequestion'

    #Create dict
    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'selected_strategy': selected_strategy, 'type_selected_strategy': type_selected_strategy }

    #print request.POST
    if request.method == 'POST':
	#unflag needsplanning for strategy submitted.
	selected_strategy.needsplanning = 0
	selected_strategy.activated = 1
	selected_strategy.save()

        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        question_data = {}
        for k, v in response.items():
            question_data[str(k)] = v.pop()

	
	if question_data['text'] == '':
	    print 'These is no followup strategy planning data.'
	elif type_selected_strategy == 'freeform':
	    print 'Updating Freeform strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.units=question_data['units']
	    selected_strategy.baseline=question_data['baseline']
	    selected_strategy.action=question_data['action']
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.save()

	elif type_selected_strategy == 'boolean':
	    print 'Updating Boolean strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.baseline=question_data['baseline']
	    selected_strategy.action=question_data['action']
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.save()

	elif type_selected_strategy == 'slider':
	    print 'Updating Slider strategy'
	    selected_strategy.title=question_data['title']
	    selected_strategy.text=question_data['text']
	    selected_strategy.description=question_data['description']
	    selected_strategy.target = int(question_data['goal'])
	    selected_strategy.baseline=question_data['baseline']
	    selected_strategy.action=question_data['action']
	    selected_strategy.timeline=question_data['timeline']
	    selected_strategy.indicator=question_data['indicator']
	    selected_strategy.scorepos2=question_data['scorepos2']
	    selected_strategy.scorepos1=question_data['scorepos1']
	    selected_strategy.scoreneg1=question_data['scoreneg1']
	    selected_strategy.scoreneg2=question_data['scoreneg2']
	    selected_strategy.activated=1
	    selected_strategy.needsplanning=0
	    selected_strategy.min_value=question_data['min_value']
	    selected_strategy.max_value=question_data['max_value']
	    selected_strategy.increment=question_data['increment']
	    selected_strategy.save()

	else:
            if t == "[u'boolean']": # new question is boolean
                boolean = Boolean(title=question_data['title'],
				  text=question_data['text'],
                                  description=question_data['description'],
                                  target=int(question_data['goal']),
                                  patient=patient,
				  gasgoal=selected_strategy.gasgoal,
				  importance=selected_strategy.importance,
				  difficulty=selected_strategy.difficulty,
				  baseline=question_data['baseline'],
				  action=question_data['action'],
				  timeline=question_data['timeline'],
				  indicator=question_data['indicator'],
				  scorepos2=question_data['scorepos2'],
				  scorepos1=question_data['scorepos1'],
				  scoreneg1=question_data['scoreneg1'],
				  scoreneg2=question_data['scoreneg2'],
				  activated=1,
				  needsplanning=0)
                boolean.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()


            elif t == "[u'category']": # new question is categorical
                category_list = []

                i = 1
                while 'cat' + str(i) in question_data:
                    category = Category(name=question_data['cat' + str(i)].lower(), value=i-1)
                    category_list.append(question_data['cat'+ str(i)].lower())
                    i = i + 1

                categorical = Categorical(title=selected_strategy.title,
					    text=question_data['text'],
                                            description=question_data['description'],
                                            categories=category_list,
                                            patient=patient)

                if question_data['goal'].lower() in category_list: # check for numerical or text goal
                    categorical.target = category_list.index(question_data['goal'].lower())
                else:
                    categorical.target = int(question_data['goal'])

                categorical.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

            elif t == "[u'integer']": # new question is free form
		#selected_strategy.text = question_data['text']
		#selected_strategy.description = question_data['description']
		#selected_strategy.target = question_data['target']
		#selected_strategy.text = question_data['units']

                free_form = FreeForm(title=question_data['title'],
				     text=question_data['text'],
                                     description=question_data['description'],
                                     target = int(question_data['goal']),
                                     patient=patient,
                                     units=question_data['units'],
				     gasgoal=selected_strategy.gasgoal,
				     importance=selected_strategy.importance,
				     difficulty=selected_strategy.difficulty,
				     baseline=question_data['baseline'],
				     action=question_data['action'],
				     timeline=question_data['timeline'],
				     indicator=question_data['indicator'],
				     scorepos2=question_data['scorepos2'],
				     scorepos1=question_data['scorepos1'],
				     scoreneg1=question_data['scoreneg1'],
				     scoreneg2=question_data['scoreneg2'],
				     activated=1,
				     needsplanning=0)
		print 'Saved the freeform'
                free_form.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()
            elif t == "[u'slider']": # new question is slider
                slider = Slider(title=question_data['title'],
				text=question_data['text'],
                                description=question_data['description'],
                                target = int(question_data['goal']),
                                patient=patient,
                                max_value=question_data['max_value'],
                                min_value=question_data['min_value'],
                                increment=question_data['increment'],
				gasgoal=selected_strategy.gasgoal,
				importance=selected_strategy.importance,
				difficulty=selected_strategy.difficulty,
				baseline=question_data['baseline'],
				action=question_data['action'],
				timeline=question_data['timeline'],
				indicator=question_data['indicator'],
				scorepos2=question_data['scorepos2'],
				scorepos1=question_data['scorepos1'],
				scoreneg1=question_data['scoreneg1'],
				scoreneg2=question_data['scoreneg2'],
				activated=1,
				needsplanning=0)
                slider.save()
		#delete selected_strategy since it has been replaced. this is not so good (NEED TO CHANGE)
		#selected_strategy.delete()

	#check if anymore strategies need planning, if so repeat strategy planning page
	#if not, continue to overall summary page.
	for tempstrategy in prequestion_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_strategy_planning_forward.html', context_dict)
	for tempstrategy in freeform_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_strategy_planning_forward.html', context_dict)
	for tempstrategy in boolean_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_strategy_planning_forward.html', context_dict)
	for tempstrategy in slider_strategy_list:
	    if tempstrategy.needsplanning == 1: 
                return render(request, 'followup_strategy_planning_forward.html', context_dict)
	else:
	    return render(request, 'followup_strategyedit_forward.html', context_dict)
    
    return render(request, 'followup_strategy_planning.html', context_dict)

# ______________________________________________   Follow Up Meeting Overall Summary __________________________
@user_passes_test(is_physician)
def followup_overall_summary_forward(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #print request.POST
    return render(request, 'followup_overall_summary_forward.html', {'patient': patient})

@user_passes_test(is_physician)
def followup_overall_summary(request, user_id):
    patient = get_object_or_404(User, pk=int(user_id))
    #Find selected goal
    gas_goals_list = GASGoals.objects.filter(patient=patient)
    for tempGASGoals in gas_goals_list:
	#print tempGASGoals.select
        if tempGASGoals.activated == 1:
	    selected_goal = tempGASGoals
	    print tempGASGoals.goal1
    #Find all active strategies
    active_strategy_list = Question.objects.filter(gasgoal=selected_goal, activated='1')
    for astrat in active_strategy_list:
	print astrat.title

    context_dict = {'patient': patient, 'selected_goal': selected_goal, 'active_strategy_list': active_strategy_list}
    return render(request, 'followup_overall_summary.html', context_dict)

#__________________________________________ Password Change ___________________________________________
# This view handles the password change.
def profile(request):
    user = request.user
    errors_dictionary = {} # a dictionary to hold errors that will be passed to the template

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PasswordForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            confirm_new_password = form.cleaned_data['confirm_new_password']
            
            #Validate that the old_password field is correct.
            if user.check_password(old_password):
                #print " * Old password is correct"
                errors_dictionary['old_pass_flag'] = False
                if new_password == confirm_new_password:
                    #print " * New passwords match YAY"
                    errors_dictionary['new_pass_flag'] = False
                    user.set_password(new_password)
                    user.save()

                    update_success = {}
                    update_success['flag'] = True
                    empty_form = PasswordForm() # return an empty form to prevent displaying password data
                    # render a template for successful password update:
                    return render(request, 'profile.html', {'form': empty_form, 'profile_user': user,
                                                            'any_errors': errors_dictionary,
                                                            'update_success': update_success })
                else:
                    #print " * New passwords do not match"
                    errors_dictionary['new_pass_flag'] = True
            else:
                #print " * Old password is not correct"
                errors_dictionary['old_pass_flag'] = True
                if new_password != confirm_new_password:
                    #print ' * New passwords do not match'
                    errors_dictionary['new_pass_flag'] = True

            # render a template with form, user data, and errors dictionaries:
            return render(request, 'profile.html', {'form': form, 'profile_user': user, 'any_errors': errors_dictionary})

    # if a GET (or any other method), create a blank form
    else:
        form = PasswordForm()
    
    #print " * Rendering the bottom-most return statement"
    return render(request, 'profile.html', {'form': form, 'profile_user': user})


# Add a significant other
@user_passes_test(is_physician)
def create_so(request):
    # Retrieve patients
    patients = Patient.objects.filter(physicians=Physician.objects.get(user=request.user))
    status_dictionary={}
    if request.method == 'POST':
        # Retrieve a list of patients IDs that were selected via checkboxes
        patients_ids = request.POST.getlist('chk_patients')
        # Retrieve response data
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        so_data = {}
        for k, v in response.items():
            so_data[str(k)] = v.pop()
        
        # Check that chk_patients exists in the response data.
        # It wouldn't exist, if user did not check any checkboxes.
        # If it does, then add it, because it is missing from the call to getlist()
        if 'chk_patients' in so_data:
            patients_ids.append(so_data['chk_patients'])
        else:
            status_dictionary['no_patient'] = True
            if so_data['userid'] == "" or so_data['useremail'] == "" or so_data['password'] == "":
                status_dictionary['missing_info'] = True
            return render(request, 'create_so.html', {'patients': patients, 'status': status_dictionary})
        
        # Retrieve selected patients by their IDs, and add them to a dictionary
        selected_patients = []
        for item in patients_ids:
            temp_patient_user = get_object_or_404(User, pk=int(item))
            patient = Patient.objects.get(user=temp_patient_user)
            selected_patients.append(patient)
        #---------------------------------------------------------------
        status_dictionary['missing_info'] = False # Remove this line when form validation is done.
        status_dictionary['duplicate_username'] = False # default
        status_dictionary['so_created'] = False # default
        status_dictionary['no_patient'] = False # default
        status_dictionary['smtp_error'] = False # default
        
        # Check for empty stings in forms
        if so_data['userid'] == "" or so_data['useremail'] == "" or so_data['password'] == "":
            status_dictionary['missing_info'] = True
            return render(request, 'create_so.html', {'patients': patients, 'status': status_dictionary})
        
        # Create a new user object
        try:
            tempuser = User.objects.create_user(so_data['userid'],
					    so_data['useremail'],
					    so_data['password'])
        except IntegrityError as e:
            print e
            status_dictionary['duplicate_username'] = True
            return render(request, 'create_so.html', {'patients': patients, 'status': status_dictionary})
            
        # At this point, tempuser is a User object that has already been saved
        # to the database. You can continue to change its attributes if you want.
        
        # get the current physician's object
        doctor = Physician.objects.get(user=request.user)
        # create Significant Other (SO)
        newSigOther = SignificantOther(user = tempuser)
        # save SO
        newSigOther.save()
        # add doctor and patient
        # Note: the corresponding SignificantOther object has to be created and saved by this point
        newSigOther.physicians.add(doctor)
        # add patient(s)
        for eachpatient in selected_patients:
            newSigOther.patients.add(eachpatient)
        # update SO
        newSigOther.save()

        status_dictionary['so_created'] = True #set the flag to True if SO is successfully created

        email_flag = True
        if (email_flag):
            # Send an email
            #email = EmailMessage('Django Subject', 'Body goes here', 'wtdev.testing@gmail.com', ['capstone59.wt@gmail.com'] )
            email = EmailMessage('Wellness Tracker -- Your New Account',
                'Dear ' + so_data['userid'] + '\n\nThis is a message from Wellness Tracker. You have been signed up for the Wellness Tracker as a significant other. Here are the details of you account:\n\nYour username: ' + so_data['userid'] + '\nYour password: ' + so_data['password'] + '\n\nSincerely,\nWellness Tracker Team',
                'wtdev.testing@gmail.com',
                [so_data['useremail']] )
            try:
                email.send()
            except SMTPException as e:
                #print ' * Error when sending email'
                print e
                status_dictionary['smtp_error'] = True
                return render(request, 'create_so.html', {'patients': patients, 'status': status_dictionary})
    
    return render(request, 'create_so.html', {'patients': patients, 'status': status_dictionary})

@user_passes_test(is_physician)
def manage_surveys(request):
    surveys = PreSurvey.objects.all()
    return render (request, 'manage_surveys.html', {'surveys': surveys})

@user_passes_test(is_physician)
def create_survey(request):
    status_dictionary={}
    status_dictionary['no_title'] = False # default
    # Retrieve patients of the current physician
    patients = Patient.objects.filter(physicians=Physician.objects.get(user=request.user))
    
    if request.method == 'POST':
        # retrieve a list of selected checkboxes with patients IDs
        patients_ids = request.POST.getlist('chk_patients')
        
        response = dict(request.POST)
        response.pop('csrfmiddlewaretoken')
        t = str(response.get('type'))
        pre_survey_data = {}
        for k, v in response.items():
            pre_survey_data[str(k)] = v.pop()
            print str(k)
            print pre_survey_data[str(k)]
        print ' * Done'

        if pre_survey_data['surveytitle'] == "":
            status_dictionary['surveytitle'] = True
            print ' * No survey title provided'
            return render (request, 'create_survey.html', {'patients': patients, 'status': status_dictionary})
        
        pre_survey = PreSurvey(title=pre_survey_data['surveytitle']) 
        pre_survey.save()
        print ' * Created a PreSurvey with title'
        print pre_survey_data['surveytitle']
        
        
        # Check that chk_patients exists in the response data.
        # It wouldn't exist, if user did not check any checkboxes.
        # If it does, that add it, because it is missing from the call to getlist()
        if 'chk_patients' in pre_survey_data:
            patients_ids.append(pre_survey_data['chk_patients'])
        else:
            print ' * No patients for the survey were selected'
        
        
        # add another checkbox value, because it is missing from the call to getlist() 
        #patients_ids.append(pre_survey_data['chk_patients'])
        
        print ' * Patients ids from checkboxes:'
        for item in patients_ids:
            print item
        print ' * Done'
        
        
        # --------------------------------------------------------------
        if t == "[u'boolean']": # new question is boolean
            print ' * You chose boolean question'
            boolean = Sboolean(title=pre_survey_data['title'],
                              text=pre_survey_data['text'],
                              description=pre_survey_data['description'],
                              target=int(pre_survey_data['goal']))
            boolean.save()
            # add to the presurvey
            pre_survey.squestions.add(boolean)
            # update the presurvey
            pre_survey.save()
            print ' * Added a boolean Q to presurvey'

        elif t == "[u'category']": # new question is categorical
            print ' * You chose categorical question'
            category_list = []

            i = 1
            while 'cat' + str(i) in question_data:
                category = Scategory(name=pre_survey_data['cat' + str(i)].lower(), value=i-1)
                category_list.append(pre_survey_data['cat'+ str(i)].lower())
                i = i + 1

            categorical = Scategorical(title=pre_survey_data['title'],
                                        text=pre_survey_data['text'],
                                        description=pre_survey_data['description'],
                                        categories=pre_survey_data)

            if pre_survey_data['goal'].lower() in category_list: # check for numerical or text goal
                categorical.target = category_list.index(pre_survey_data['goal'].lower())
            else:
                categorical.target = int(pre_survey_data['goal'])

            categorical.save()

        elif t == "[u'integer']": # new question is free form
            print ' * You chose free form question'
            free_form = SfreeForm(title=pre_survey_data['title'],
                                text=pre_survey_data['text'],
                                description=pre_survey_data['description'],
                                target = int(pre_survey_data['goal']),
                                units=pre_survey_data['units'])
            free_form.save()

        elif t == "[u'slider']": # new question is slider
            print ' * You chose slider question'
            slider = Sslider(title=pre_survey_data['title'],
                            text=pre_survey_data['text'],
                            description=pre_survey_data['description'],
                            target = int(pre_survey_data['goal']),
                            max_value=pre_survey_data['max_value'],
                            min_value=pre_survey_data['min_value'],
                            increment=pre_survey_data['increment'])
            slider.save()
        # --------------------------------------------------------------
        
        # get patients from IDs
        patients_users = []
        patients_instances = []
        
        # Retrieve users and add them to a dictionary
        for item in patients_ids:
            print item
            temp_patient_user = get_object_or_404(User, pk=int(item))
            patients_users.append(temp_patient_user)
            patient = Patient.objects.get(user=temp_patient_user)
            patients_instances.append(patient)
            # add to the presurvey
            pre_survey.spatients.add(patient)
            # update
            pre_survey.save()
        
        '''
        print ' * Usernames of patients:'
        presurvey_patients = pre_survey.spatients.all()
        for item in presurvey_patients:
            print item.user.username
        
        print ' * Retrieved patients are as follows:'
        for pat in patients_instances:
            print pat.user.username
        '''
    return render (request, 'create_survey.html', {'patients': patients, 'status': status_dictionary})

@user_passes_test(is_physician)
def edit_survey(request):
    return render (request, 'edit_survey.html')

@user_passes_test(is_physician)
def survey_overview(request, survey_id):
    survey = get_object_or_404(PreSurvey, pk=int(survey_id))
    
    #print ' * You choose survey titled'
    print survey.title
    
    #print ' * Usernames of patients:'
    presurvey_patients = survey.spatients.all()
    #for item in presurvey_patients:
        #print item.user.username
    presurvey_questions = survey.squestions.all()
    
    return render (request, 'survey_overview.html', {'survey': survey, 'patients': presurvey_patients, 'questions': presurvey_questions})

@user_passes_test(is_physician)
def s_new_question(request):
    return render (request, 's_new_question.html')

@user_passes_test(is_physician)
def new_survey_question(request):
    return render (request, 'new_survey_question.html')
    
