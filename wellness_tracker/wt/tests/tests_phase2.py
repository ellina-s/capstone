# Tests for Phase 2 of Wellness Tracker

import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class WTBaseTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000"

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

    def tearDown(self):
        self.driver.close()
        
    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
