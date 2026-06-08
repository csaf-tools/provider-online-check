# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for frontend-backend

Does not include tests for the backend alone (see backend tests)
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Mark all tests in this module as nondestructive
pytestmark = pytest.mark.nondestructive


class TestScanIntegration:
    """Integration tests"""

    def test_scan_via_ui(self, firefox_driver, base_url):
        """Test scan submission"""
        firefox_driver.get(base_url)

        # Enter domain
        domain = "example.net"
        domain_input = firefox_driver.find_element(By.ID, "domainInput")
        domain_input.send_keys(domain)
        # Submit form
        submit_button = firefox_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait
        wait = WebDriverWait(firefox_driver, 5)
        result_alert = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h3")))

        # success message
        assert result_alert.is_displayed()
        alert_text = result_alert.text
        assert "Scan" in alert_text

    def test_scan_with_invalid_domain(self, firefox_driver, base_url):
        """Test scan submission with invalid domain"""
        firefox_driver.get(base_url)

        # Enter domain
        domain = "example..com"
        domain_input = firefox_driver.find_element(By.ID, "domainInput")
        domain_input.send_keys(domain)

        # Submit form
        submit_button = firefox_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait
        wait = WebDriverWait(firefox_driver, 5)
        result_alert = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))

        # error message
        assert result_alert.is_displayed()
        alert_text = result_alert.text
        assert "Error" in alert_text and "Invalid domain format" in alert_text

    def test_scan_with_small_valid_domain(self, firefox_driver, base_url):
        """Test scan submission with small valid domain"""
        firefox_driver.get(base_url)

        # Enter domain
        domain = "intevation.de"
        domain_input = firefox_driver.find_element(By.ID, "domainInput")
        domain_input.send_keys(domain)

        # Submit form
        submit_button = firefox_driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait and get body
        wait = WebDriverWait(firefox_driver, 5)
        header3 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h3")))

        # success message
        assert header3.is_displayed()
        assert "Scan Done" in header3.text or "Scan found in cache" in header3.text
        header4 = firefox_driver.find_element(By.TAG_NAME, "h4")
        assert "CSAF trusted provider" in header4.text
