from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional


def init_driver(headless: bool = True):
    options = Options()
    if headless:
        try:
            options.add_argument("--headless=new")
        except Exception:
            options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    chromedriver_path = ChromeDriverManager().install()
    service = Service(chromedriver_path, log_path=None)
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass
    return driver


def fetch_page(driver, url: str, wait_for_tag: Optional[str] = "body", timeout: int = 10) -> str:
    """Navigate to url and return page_source, waiting for a tag (default: body)."""
    driver.get(url)
    if wait_for_tag:
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, wait_for_tag)))
        except Exception:
            # best-effort, continue
            pass
    return driver.page_source