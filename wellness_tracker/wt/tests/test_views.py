import datetime
from django.test import TestCase
from wt.models import *
from django.contrib.auth.models import User, Group
from django.core.management import call_command

class WTViewsTestCase(TestCase):
	
	def setUp(self):
		call_command('loaddata', 'wt/fixtures/groups.json', verbosity=0)
		self.docUser = User.objects.create_user('doc', 'doctest@test.com', 'pw')
		self.patUser = User.objects.create_user('pat', 'pattest@test.com', 'pw')
		self.docGroup = Group.objects.get(name='Doctors')
		self.patGroup = Group.objects.get(name='Patients')
		self.docGroup.user_set.add(self.docUser)
		self.patGroup.user_set.add(self.patUser)
		self.boolean_question = Boolean.objects.create(patient=self.patUser, 
													   goal=1, 
													   title='bool test', 
													   text='yes or no', 
													   description='test')  
	
	def tearDown(self):
		del self.docUser
		del self.docGroup
		del self.patGroup
		del self.patUser

	def doc_login(self):	
		self.client.login(username='doc', password='pw')

	def pat_login(self):	
		self.client.login(username='pat', password='pw')

	# Graph
	def test_graph_patient(self):
		self.pat_login()
		resp = self.client.get('/graph/')
		self.assertEquals(resp.status_code,200)
		self.assertTrue('symptoms' in resp.context)
		self.assertTrue('data' in resp.context)
		self.assertTrue('graph_user' in resp.context)
		self.assertTrue(resp.context['graph_user'] == self.patUser)
		self.assertTrue(len(resp.context['symptoms']) != 0)
		
	def test_graph_doctor(self):
		self.doc_login()
		resp = self.client.get('/graph/2/')
		self.assertEquals(resp.status_code, 200)
		self.assertTrue('symptoms' in resp.context)
		self.assertTrue('data' in resp.context)
		self.assertTrue('graph_user' in resp.context)
		self.assertTrue(resp.context['graph_user'] != self.docUser)
		self.assertTrue(len(resp.context['symptoms']) != 0)
	
	# Questions	
	def test_questions(self):
		self.pat_login()
		resp = self.client.get('/questions/')
		self.assertEquals(resp.status_code, 200)
		self.assertTrue('questions' in resp.context)
	
	# New Question
	def test_new_question(self):
		self.doc_login()
		resp = self.client.get('/new_question/2/')
		self.assertEquals(resp.status_code, 200)
	
	def test_new_question_invalid(self):
		self.pat_login()
		resp = self.client.get('/new_question/2/')
		self.assertEquals(resp.status_code, 302)
	
	# Patient List
	def test_pat_list(self):
		self.doc_login()
		resp = self.client.get('/patients/')
		self.assertEquals(resp.status_code, 200)
		self.assertTrue('patients' in resp.context)
		self.assertTrue(self.patUser in list(resp.context['patients']))
		
	def test_pat_list_invalid(self):
		self.pat_login()
		resp = self.client.get('/patients/')
		self.assertEquals(resp.status_code, 302)

	
		
		