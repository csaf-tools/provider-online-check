"""Pytest configuration for Selenium tests."""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="function")
def chrome_driver():
    """Create a Chrome WebDriver instance for testing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture(scope="function")
def firefox_driver():
    """Create a Firefox WebDriver instance for testing."""
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--width=1920")
    firefox_options.add_argument("--height=1080")

    driver = webdriver.Firefox(options=firefox_options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the frontend application."""
    return "http://localhost:48091"


@pytest.fixture(scope="session")
def backend_url():
    """Base URL for the backend API."""
    return "http://localhost:48090"


@pytest.fixture(scope="session")
def sensitive_url():
    """Allow localhost URLs to be tested."""
    return r"^https?://localhost(:\d+)?(/.*)?$"
