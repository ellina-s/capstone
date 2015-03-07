# Tests for Phase 2 of Wellness Tracker

import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class WTBaseTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000"

    # Generic test to walk through the website
    def test_generic(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctoraj")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("ajp")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Mary").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Sam").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Rainy").click()
        driver.find_element_by_link_text("Follow Up Meeting").click()
        driver.find_element_by_link_text("Patients").click()
        driver.find_element_by_link_text("Mary").click()
        driver.find_element_by_link_text("Goal Attainment Wizard").click()
        driver.find_element_by_link_text("logout").click()

    # Test for creating a new patient
    def test_create_patient_success(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctoraj")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("ajp")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Create Patient").click()
        # Check that status messages are not present
        assert "Patient has been created successfully" not in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Email error" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("userid").clear()
        driver.find_element_by_id("userid").send_keys("Jannis")
        driver.find_element_by_id("useremail").clear()
        driver.find_element_by_id("useremail").send_keys("jannis@example.com")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("jannisp")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        # Upon successful creation of a new patient
        assert "Patient has been created successfully" in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Email error" not in driver.page_source
        driver.find_element_by_link_text("Back to Patient's List").click()
        driver.find_element_by_link_text("Add Patient").click()
        # Fill in the data and submit
        driver.find_element_by_id("userid").clear()
        driver.find_element_by_id("userid").send_keys("Jonn")
        driver.find_element_by_id("useremail").clear()
        driver.find_element_by_id("useremail").send_keys("jonn@example.com")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("jonnp")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        # Upon successful creation of a new patient
        assert "Patient has been created successfully" in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Email error" not in driver.page_source
        driver.find_element_by_link_text("Goal Attainment Wizard").click()
        self.assertIn("WellnessTracker - GAS Step1", driver.title)

    #Test for creating a patient with duplicate username
    def test_create_duplicate_patient(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctoraj")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("ajp")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Add Patient").click()
        # Check that status messages are not present
        assert "Patient has been created successfully" not in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Email error" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("userid").clear()
        driver.find_element_by_id("userid").send_keys("Jannis")
        driver.find_element_by_id("useremail").clear()
        driver.find_element_by_id("useremail").send_keys("jannis@example.com")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("jannisp")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        #Check that duplicate username is caught
        assert "Duplicate username. Please select another username." in driver.page_source
        assert "Patient has been created successfully" not in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Email error" not in driver.page_source

    # Test for missing information in the create patient form 
    def test_create_patient_missing_info(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctoraj")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("ajp")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Add Patient").click()
        # Check that status messages are not present
        assert "Patient has been created successfully" not in driver.page_source
        assert "Missing a username, password, or email." not in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Email error" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("userid").clear()
        driver.find_element_by_id("userid").send_keys("")
        driver.find_element_by_id("useremail").clear()
        driver.find_element_by_id("useremail").send_keys("")
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        #Check that the missing info error is caught
        assert "Missing a username, password, or email." in driver.page_source
        assert "Duplicate username. Please select another username." not in driver.page_source
        assert "Patient has been created successfully" not in driver.page_source
        assert "Email error" not in driver.page_source

    def tearDown(self):
        self.driver.close()
        
    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
