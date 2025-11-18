"""UI tests for the CSAF Provider Scanner frontend."""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Mark all tests in this module as nondestructive
pytestmark = pytest.mark.nondestructive


class TestHomePage:
    """Test basic UI elements"""

    def test_page_title(self, firefox_driver, base_url):
        """Test for page title"""
        firefox_driver.get(base_url)
        assert "CSAF Provider Scan" in firefox_driver.title

    def test_scan_form_elements(self, firefox_driver, base_url):
        """Form elements"""
        firefox_driver.get(base_url)

        # domain input field
        domain_input = firefox_driver.find_element(By.ID, "domainInput")
        assert domain_input.is_displayed()
        assert domain_input.get_attribute("placeholder") == "example.com"

        # submit button
        submit_button = firefox_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        assert submit_button.is_displayed()
        assert "Start" in submit_button.text

    def test_about(self, firefox_driver, base_url):
        """About section and meta information"""
        firefox_driver.get(base_url)

        about_heading = firefox_driver.find_element(By.XPATH, "//h5[contains(text(), 'About')]")
        assert about_heading.is_displayed()

        # CSAF-Link
        csaf_link = firefox_driver.find_element(By.LINK_TEXT, "CSAF")
        assert csaf_link.get_attribute("href") == "https://www.csaf.io/"

        # Apache-2.0 license
        page_text = firefox_driver.find_element(By.TAG_NAME, "body").text
        assert "Apache-2.0" in page_text


class TestScanForm:
    """Test scan form"""

    def test_empty_form_validation(self, firefox_driver, base_url):
        """Empty form submission should show error message."""
        firefox_driver.get(base_url)

        submit_button = firefox_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        domain_input = firefox_driver.find_element(By.ID, "domainInput")
        validation_message = domain_input.get_attribute("validationMessage")
        assert validation_message == 'Please fill out this field.'


class TestAccessibility:
    """Accessibility tests"""

    def test_form_labels(self, firefox_driver, base_url):
        """Test that all form inputs have a label"""
        firefox_driver.get(base_url)

        # Find all input elements in the form
        inputs = firefox_driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")

        for input_element in inputs:
            input_id = input_element.get_attribute("id")
            if input_id:
                # Each input should have a corresponding label
                labels = firefox_driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                assert len(labels) > 0, f"Input with id '{input_id}' does not have a label"
                assert labels[0].is_displayed(), f"Label for '{input_id}' is not visible"
