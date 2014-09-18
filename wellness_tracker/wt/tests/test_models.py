from django.test import TestCase
from wt.models import *
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

#### model forms tests ####
class SimpleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category_1 = Category.objects.create(name='cat1', value=0)
        self.category_2 = Category.objects.create(name='cat2', value=1)
      	self.category_3 = Category.objects.create(name='cat3', value=2)
        self.categorical_question = Categorical.objects.create(patient=self.user, goal=1, categories=[self.category_1,self.category_2,self.category_3])
        self.boolean_question = Boolean.objects.create(patient=self.user, goal=1)  
        self.freeform_question = FreeForm.objects.create(patient=self.user, goal=1, units="kg")
        self.slider_question = Slider.objects.create(patient=self.user, goal=1, max_value=100, min_value=0, increment=1) 
        self.question = Question.objects.create(patient=self.user, goal=1, title = 'how happy are you today?', text = 'how happy are you today?', description ='how happy are you today?' )
	## selenium
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8023"
        self.verificationErrors = []
        self.accept_next_alert = True
   
    def tearDown(self):
        del self.user
        del self.boolean_question
        del self.freeform_question
        del self.slider_question
        del self.question
	
	# CATEGORY
    def test_category_length(self):
        self.assertEqual(len(self.categorical_question.categories.all()), 3)
        
    def test_category_types(self):
        for category in self.categorical_question.categories.all():
            self.assertEqual(category.__class__.__name__,'Category')
            
    def test_category_name(self):
    	self.assertEqual(self.category_1.name, 'cat1')
    
    def test_category_value(self):
    	self.assertTrue(type(self.category_1.value) is int)
    	self.assertEqual(self.category_1.value, 0)
    	self.assertTrue(type(self.category_2.value) is int)
    	self.assertEqual(self.category_2.value, 1)
    	self.assertTrue(type(self.category_3.value) is int)
    	self.assertEqual(self.category_3.value, 2)

    # CATEGORICAL
    def test_categorical_type(self):
    	self.assertEqual(self.categorical_question.__class__.__name__, 'Categorical')
    	
    def test_categorical_goal(self):
    	self.assertEqual(self.categorical_question.goal, 1)
    	
    def test_categorical_user(self):
    	self.assertEqual(self.categorical_question.patient, self.user)	
    	
    	
	# BOOLEAN
    def test_boolean(self):
        self.boolean_question
        
    def test_boolean_type(self):
        self.assertEqual(self.boolean_question.__class__.__name__,'Boolean')
    
    def test_boolean_goal(self):
    	self.assertEqual(self.boolean_question.goal, 1)

	# FREEFORM
    def test_freeform_units(self):
        self.assertMultiLineEqual(str(self.freeform_question.units), 'kg')
        
    def test_freeform_length(self):
        self.assertLessEqual(len(self.freeform_question.units), 32)
        
    def test_freeform_types(self):
        self.assertEqual(self.freeform_question.__class__.__name__, 'FreeForm')

	# SLIDER
    def test_slider_type(self):
       self.assertEqual(self.slider_question.__class__.__name__, 'Slider')
       
    def test_slider_max_value(self):
          self.assertLessEqual(self.slider_question.max_value,100)
          
    def test_slider_min_value(self):
          self.assertGreaterEqual(self.slider_question.min_value,0)
          
    def test_slider_increment(self):
         self.assertGreaterEqual(self.slider_question.increment,1)

	# QUESTION
    def test_question_title(self):
        self.assertLessEqual(len(self.question.title),32)
        self.assertEqual(self.question.title, 'how happy are you today?')
        
    def test_question_text(self):
        self.assertLessEqual(len(self.question.text),128)
        self.assertEqual(self.question.text, 'how happy are you today?')
        
    def test_question_description_length(self):
        self.assertLessEqual(len(self.question.description),512)
        self.assertEqual(self.question.description, 'how happy are you today?')

#### generic page test ####
    def test_1test_python(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("andrew")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("a")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_id("oneMonth").click()
        driver.find_element_by_id("sixMonth").click()
        driver.find_element_by_id("oneYear").click()
        driver.find_element_by_id("allTime").click()
        driver.find_element_by_id("average").click()
        driver.find_element_by_id("best-fit").click()
        driver.find_element_by_id("goal").click()
        driver.find_element_by_id("stdev").click()
        driver.find_element_by_id("stdev").click()
        driver.find_element_by_id("goal").click()
        driver.find_element_by_id("best-fit").click()
        driver.find_element_by_id("average").click()
        driver.find_element_by_link_text("[ andrew ]").click()
        driver.find_element_by_link_text("WellnessTracker").click()
        driver.find_element_by_link_text("Graph").click()
        driver.find_element_by_link_text("logout").click()

#### admin test ####
    def test_3admin_tour(self):
        driver = self.driver
        driver.get(self.base_url + "/login/?next=/admin/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("adiemer")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("andrew")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Users").click()
        driver.find_element_by_link_text("adiemer").click()
        driver.find_element_by_id("id_first_name").clear()
        driver.find_element_by_id("id_first_name").send_keys("Andrew")
        driver.find_element_by_id("id_last_name").clear()
        driver.find_element_by_id("id_last_name").send_keys("Diemer")
        driver.find_element_by_id("id_user_permissions_remove_all_link").click()
        driver.find_element_by_id("id_user_permissions_add_all_link").click()
        driver.find_element_by_css_selector("option[value=\"9\"]").click()
        driver.find_element_by_css_selector("option[value=\"1\"]").click()
        driver.find_element_by_css_selector("option[value=\"8\"]").click()
        driver.find_element_by_id("id_user_permissions_remove_all_link").click()
        driver.find_element_by_id("id_user_permissions_add_all_link").click()
        driver.find_element_by_name("_save").click()
        driver.find_element_by_link_text("Yes").click()
        driver.find_element_by_link_text("No").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Yes')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'No')])[2]").click()
        driver.find_element_by_link_text("All").click()
        driver.find_element_by_xpath("(//a[contains(text(),'All')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Yes')])[3]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'No')])[3]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'All')])[3]").click()
        driver.find_element_by_link_text("Auth").click()
        driver.find_element_by_link_text("Groups").click()
        driver.find_element_by_id("searchbar").clear()
        driver.find_element_by_id("searchbar").send_keys("doctors")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        driver.find_element_by_link_text("Auth").click()
        driver.find_element_by_link_text("Home").click()

#### doctor to patients test page ####s
    def test_5_doctor_patients(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("adiemer")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("andrew")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("James").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Nigel").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Ryan").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Nikola").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Haleh").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("James").click()
        driver.find_element_by_link_text("Add Symptom").click()
        driver.find_element_by_id("question").clear()
        driver.find_element_by_id("question").send_keys("Tiredness")
        driver.find_element_by_name("text").clear()
        driver.find_element_by_name("text").send_keys("How tired are you today?")
        driver.find_element_by_id("description").clear()
        driver.find_element_by_id("description").send_keys("On Scale 1-10")
        driver.find_element_by_id("goal").clear()
        driver.find_element_by_id("goal").send_keys("3")
        Select(driver.find_element_by_id("type")).select_by_visible_text("Slider")
        Select(driver.find_element_by_id("type")).select_by_visible_text("Category")
        driver.find_element_by_link_text("Add Category").click()
        driver.find_element_by_link_text("Add Category").click()
        Select(driver.find_element_by_id("type")).select_by_visible_text("Yes / No")
        Select(driver.find_element_by_id("type")).select_by_visible_text("Numerical")
        Select(driver.find_element_by_id("type")).select_by_visible_text("Slider")
        driver.find_element_by_id("slider-increment").clear()
        driver.find_element_by_id("slider-increment").send_keys("10")
        driver.find_element_by_id("slider-max_value").clear()
        driver.find_element_by_id("slider-max_value").send_keys("10")
        driver.find_element_by_id("slider-min_value").clear()
        driver.find_element_by_id("slider-min_value").send_keys("1")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("James").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_link_text("logout").click()
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("James")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("a")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_link_text("Questions").click()
        driver.find_element_by_xpath("//input[@type='submit']").click()
        driver.find_element_by_link_text("Graph").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_id("Tiredness0").click()
    
#### graph test ####
    def test_4_testgraph(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("andrew")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("a")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_link_text("Hunger").click()
        driver.find_element_by_link_text("Hunger").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_link_text("Weight").click()
        driver.find_element_by_link_text("Weight").click()
        driver.find_element_by_id("Tiredness1").click()
        driver.find_element_by_id("Tiredness2").click()
        driver.find_element_by_id("Tiredness0").click()
        driver.find_element_by_link_text("Sleep time").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[2]").click()
        driver.find_element_by_link_text("Sleep time").click()
        driver.find_element_by_link_text("Weight").click()
        driver.find_element_by_link_text("Weight").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Weight')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Weight')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Sleep time')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[3]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Sleep time')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[3]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[4]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[5]").click()
        driver.find_element_by_link_text("Hello").click()
        driver.find_element_by_link_text("Hello").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Tiredness')])[3]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Sleep time')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Weight')])[2]").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Weight')])[2]").click()
        driver.find_element_by_id("Sleep-time1").click()
        driver.find_element_by_id("reset").click()
        driver.find_element_by_id("selectAll").click()
        driver.find_element_by_id("reset").click()
        driver.find_element_by_id("oneMonth").click()
        driver.find_element_by_id("sixMonth").click()
        driver.find_element_by_id("oneYear").click()
        driver.find_element_by_id("allTime").click()
        driver.find_element_by_id("oneMonth").click()
        driver.find_element_by_id("Sleep-time0").click()
        driver.find_element_by_link_text("Questions").click()
        driver.find_element_by_name("q-3").clear()
        driver.find_element_by_name("q-3").send_keys("180")
        driver.find_element_by_name("q-7").clear()
        driver.find_element_by_name("q-7").send_keys("140")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        driver.find_element_by_link_text("Graph").click()
        driver.find_element_by_link_text("Tiredness").click()
        driver.find_element_by_id("oneMonth").click()
        driver.find_element_by_id("Tiredness2").click()
        driver.find_element_by_link_text("logout").click()

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
