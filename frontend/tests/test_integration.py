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
        result_alert = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))

        # success message
        assert result_alert.is_displayed()
        alert_text = result_alert.text
        assert "Scan" in alert_text and domain in alert_text
