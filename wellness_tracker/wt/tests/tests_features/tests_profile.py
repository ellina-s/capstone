# ----------------------------------------------------
# Phase 2 of Wellness Tracker
# Tests for changing the password in the profile page
# How to run these tests with unittest:
# python -m unittest discover -v
# ----------------------------------------------------

import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class WTProfileTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000"

    # Test a successful change of password
    def test_change_password_success(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctorwho")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("who")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Profile").click()
        # Check that status messages are not present
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source
        assert "Password updated successfully" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("who")
        driver.find_element_by_id("id_new_password").clear()
        driver.find_element_by_id("id_new_password").send_keys("new8pwd")
        driver.find_element_by_id("id_confirm_new_password").clear()
        driver.find_element_by_id("id_confirm_new_password").send_keys("new8pwd")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        # Upon successful change of the password, assert:
        assert "Password updated successfully" in driver.page_source
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source
        driver.find_element_by_link_text("logout").click()
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctorwho")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("new8pwd")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        # Change the password back to the original one
        driver.find_element_by_link_text("Profile").click()
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("new8pwd")
        driver.find_element_by_id("id_new_password").clear()
        driver.find_element_by_id("id_new_password").send_keys("who")
        driver.find_element_by_id("id_confirm_new_password").clear()
        driver.find_element_by_id("id_confirm_new_password").send_keys("who")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        assert "Password updated successfully" in driver.page_source
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source

    # Test for incorrect current password
    def test_incorrect_current_password(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctorwho")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("who")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Profile").click()
        # Check that status messages are not present
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source
        assert "Password updated successfully" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("new8pwd")
        driver.find_element_by_id("id_new_password").clear()
        driver.find_element_by_id("id_new_password").send_keys("pwd")
        driver.find_element_by_id("id_confirm_new_password").clear()
        driver.find_element_by_id("id_confirm_new_password").send_keys("pwd")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        # Check that the incorrect current password has been caught
        assert "Incorrect current password" in driver.page_source
        assert "Password updated successfully" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source

    # Test for mismatching new passwords
    def test_mismatching_new_passwords(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctorwho")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("who")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Profile").click()
        # Check that status messages are not present
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source
        assert "Password updated successfully" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("who")
        driver.find_element_by_id("id_new_password").clear()
        driver.find_element_by_id("id_new_password").send_keys("pwd7tyh")
        driver.find_element_by_id("id_confirm_new_password").clear()
        driver.find_element_by_id("id_confirm_new_password").send_keys("pwd9ugh")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        # Check that the passwords didn't match
        assert "New passwords do not macth" in driver.page_source
        assert "Incorrect current password" not in driver.page_source
        assert "Password updated successfully" not in driver.page_source

    # Test that old password is incorrect, and new passwords do not match.
    def test_incorrect_old_and_new_passwords(self):
        driver = self.driver
        driver.get(self.base_url + "/login/")
        self.assertIn("WellnessTracker - Login", driver.title)
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys("doctorwho")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("who")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        driver.find_element_by_link_text("Profile").click()
        # Check that status messages are not present
        assert "Incorrect current password" not in driver.page_source
        assert "New passwords do not macth" not in driver.page_source
        assert "Password updated successfully" not in driver.page_source
        # Fill in the data and submit
        driver.find_element_by_id("id_old_password").clear()
        driver.find_element_by_id("id_old_password").send_keys("umkgd")
        driver.find_element_by_id("id_new_password").clear()
        driver.find_element_by_id("id_new_password").send_keys("ljxfl4")
        driver.find_element_by_id("id_confirm_new_password").clear()
        driver.find_element_by_id("id_confirm_new_password").send_keys("pwd9ugh")
        driver.find_element_by_xpath("//input[@type='submit']").click()
        assert "New passwords do not macth" in driver.page_source
        assert "Incorrect current password" in driver.page_source
        assert "Password updated successfully" not in driver.page_source

    def tearDown(self):
        self.driver.close()
        
if __name__ == "__main__":
    unittest.main()
