"""
utils/helpers.py
────────────────
Shared browser-factory and helper utilities used by every test module.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


# ── constants ─────────────────────────────────────────────────────────────────
AMAZON_URL    = "https://www.amazon.com"
DEFAULT_WAIT  = 15          # seconds for explicit waits
IMPLICIT_WAIT = 5           # seconds for implicit waits
PAGE_LOAD_TMO = 30          # seconds for page-load timeout


# ─────────────────────────────────────────────────────────────────────────────
#  Browser factory
# ─────────────────────────────────────────────────────────────────────────────

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Build and return a Chrome WebDriver instance.

    Parameters
    ----------
    headless : bool
        Run Chrome without a GUI when True (default).
        Set ``HEADLESS=false`` as an env variable to see the browser.

    Returns
    -------
    webdriver.Chrome
    """
    headless_env = os.getenv("HEADLESS", "true").lower()
    run_headless = headless if headless_env == "true" else False

    options = ChromeOptions()

    if run_headless:
        options.add_argument("--headless=new")          # new headless mode (Chrome ≥ 112)

    # ── stability / sandbox flags (required in Docker / CI) ──────────────────
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # ── avoid bot-detection ──────────────────────────────────────────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )

    service = ChromeService(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.set_page_load_timeout(PAGE_LOAD_TMO)

    logger.info("Chrome WebDriver created  (headless=%s)", run_headless)
    return driver


# ─────────────────────────────────────────────────────────────────────────────
#  Amazon helpers
# ─────────────────────────────────────────────────────────────────────────────

def wait_for(driver: webdriver.Chrome, by: str, value: str,
             timeout: int = DEFAULT_WAIT):
    """Return element once it is visible, or raise TimeoutException."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


def wait_clickable(driver: webdriver.Chrome, by: str, value: str,
                   timeout: int = DEFAULT_WAIT):
    """Return element once it is clickable, or raise TimeoutException."""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def dismiss_popups(driver: webdriver.Chrome) -> None:
    """
    Silently close common Amazon overlays / sign-in prompts.
    Does nothing if no popup is present.
    """
    selectors = [
        (By.ID,   "sp-cc-accept"),               # cookie banner
        (By.CSS_SELECTOR, "[data-action='a-popover-close']"),
        (By.CSS_SELECTOR, ".a-popover-closebutton"),
        (By.XPATH, "//button[contains(text(),'No thanks')]"),
        (By.XPATH, "//button[contains(text(),'Decline')]"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((by, sel))
            )
            btn.click()
            logger.info("Dismissed popup: %s", sel)
            time.sleep(0.5)
        except (TimeoutException, NoSuchElementException):
            pass


def search_amazon(driver: webdriver.Chrome, query: str) -> None:
    """
    Navigate to Amazon homepage and perform a product search.

    Parameters
    ----------
    query : str  e.g. "iPhone 15 Pro"
    """
    logger.info("Navigating to Amazon …")
    driver.get(AMAZON_URL)
    time.sleep(2)
    dismiss_popups(driver)

    search_box = wait_clickable(driver, By.ID, "twotabsearchtextbox")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    logger.info("Searched for: %s", query)
    time.sleep(2)


def extract_price(driver: webdriver.Chrome) -> Optional[str]:
    """
    Try several CSS / XPath selectors to extract a price string
    from the current product page.

    Returns
    -------
    str  –  price text like "$999.00"  or  None if not found
    """
    price_selectors = [
        (By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div "
                          ".a-price-whole"),
        (By.CSS_SELECTOR, "#price_inside_buybox"),
        (By.CSS_SELECTOR, "#priceblock_ourprice"),
        (By.CSS_SELECTOR, "#priceblock_dealprice"),
        (By.CSS_SELECTOR, ".a-price .a-offscreen"),
        (By.CSS_SELECTOR, "#apex_offerDisplay_desktop .a-price .a-offscreen"),
        (By.XPATH,        "//span[@data-a-color='price']//span[@class='a-offscreen']"),
    ]
    for by, sel in price_selectors:
        try:
            el = driver.find_element(by, sel)
            price = el.get_attribute("textContent") or el.text
            price = price.strip()
            if price:
                logger.info("Price found via selector '%s': %s", sel, price)
                return price
        except NoSuchElementException:
            continue
    logger.warning("Could not locate price on page.")
    return None


def click_first_product(driver: webdriver.Chrome) -> str:
    """
    Click the first sponsored or organic product result on the SERP.

    Returns
    -------
    str – the product title
    """
    # Try to grab the first product card link
    product_selectors = [
        (By.CSS_SELECTOR, "div[data-component-type='s-search-result'] "
                          "h2 a.a-link-normal"),
        (By.CSS_SELECTOR, ".s-result-item h2 a"),
        (By.XPATH,        "(//div[@data-component-type='s-search-result']"
                          "//h2//a)[1]"),
    ]
    for by, sel in product_selectors:
        try:
            link = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.element_to_be_clickable((by, sel))
            )
            title = link.text.strip() or link.get_attribute("aria-label") or "Unknown"
            logger.info("Clicking product: %s", title[:80])
            # Scroll into view then click
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            time.sleep(0.5)
            link.click()
            return title
        except (TimeoutException, NoSuchElementException,
                ElementClickInterceptedException):
            continue

    raise RuntimeError("Could not find any product link on the search results page.")


def add_to_cart(driver: webdriver.Chrome) -> None:
    """
    Click the 'Add to Cart' button on a product detail page.
    Handles both standard and variant-selection flows.
    """
    add_to_cart_selectors = [
        (By.ID,           "add-to-cart-button"),
        (By.CSS_SELECTOR, "#addToCart input[type='submit']"),
        (By.XPATH,        "//input[@id='add-to-cart-button']"),
        (By.XPATH,        "//input[contains(@value,'Add to Cart')]"),
        (By.XPATH,        "//button[contains(@name,'submit.add-to-cart')]"),
    ]
    for by, sel in add_to_cart_selectors:
        try:
            btn = WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.element_to_be_clickable((by, sel))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.4)
            btn.click()
            logger.info("'Add to Cart' clicked.")
            time.sleep(2)
            dismiss_popups(driver)
            return
        except (TimeoutException, NoSuchElementException,
                ElementClickInterceptedException):
            continue

    raise RuntimeError("'Add to Cart' button not found on this page.")
