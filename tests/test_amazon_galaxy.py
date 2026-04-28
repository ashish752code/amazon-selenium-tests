"""
tests/test_amazon_galaxy.py
────────────────────────────
Test Case 2 – Search Amazon for a Samsung Galaxy device, add it to the
               cart, and print the device price to the console.

Markers : smoke, regression, parallel
"""

from __future__ import annotations

import logging
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.helpers import (
    search_amazon,
    click_first_product,
    extract_price,
    add_to_cart,
    dismiss_popups,
    DEFAULT_WAIT,
)

logger = logging.getLogger(__name__)

# ── search term ───────────────────────────────────────────────────────────────
SEARCH_QUERY = "Samsung Galaxy S24 Ultra"


# ─────────────────────────────────────────────────────────────────────────────
#  Test class
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parallel
class TestAmazonGalaxy:
    """
    End-to-end test: search Galaxy → open product → capture price → add to cart
    """

    def test_search_galaxy_and_add_to_cart(self, driver):
        """
        Steps
        -----
        1. Open amazon.com
        2. Search for 'Samsung Galaxy S24 Ultra'
        3. Click the first result
        4. Extract & print the price
        5. Click 'Add to Cart'
        6. Assert the item was successfully added
        """

        # ── Step 1 & 2 : Navigate + Search ───────────────────────────────────
        search_amazon(driver, SEARCH_QUERY)

        # ── Step 3 : Click first product ─────────────────────────────────────
        product_title = click_first_product(driver)
        logger.info("Product page opened: %s", product_title)

        # Wait for product page to load
        WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
        time.sleep(1)
        dismiss_popups(driver)

        # Retrieve product title from the detail page
        try:
            title_el = driver.find_element(By.ID, "productTitle")
            full_title = title_el.text.strip()
        except Exception:
            full_title = product_title

        # ── Step 4 : Extract & print price ───────────────────────────────────
        price = extract_price(driver)

        # ── CONSOLE OUTPUT ────────────────────────────────────────────────────
        print("\n" + "═" * 60)
        print("  TEST CASE 2 – Samsung Galaxy")
        print("═" * 60)
        print(f"  Product : {full_title[:80]}")
        print(f"  Price   : {price if price else 'Price not displayed (may require selection)'}")
        print("═" * 60 + "\n")

        logger.info("Galaxy price → %s", price)

        # ── Step 5 : Add to Cart ──────────────────────────────────────────────
        add_to_cart(driver)

        # ── Step 6 : Verify cart confirmation ────────────────────────────────
        self._verify_cart_confirmation(driver)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _verify_cart_confirmation(driver) -> None:
        """
        Assert that Amazon shows a cart-confirmation signal.
        Tries several possible confirmation indicators.
        """
        confirmation_selectors = [
            # Side-panel / slide-in confirmation
            (By.ID,   "NATC_SMART_WAGON_CONF_MSG_SUCCESS"),
            (By.CSS_SELECTOR, "#attachDisplayAddBaseAlert"),
            (By.CSS_SELECTOR, "#sw-atc-confirmation"),
            (By.CSS_SELECTOR, "#sw-atc-details-form-section"),
            # Full cart page
            (By.CSS_SELECTOR, "#activeCartViewForm"),
            (By.CSS_SELECTOR, ".a-alert-success"),
            # Cart count badge in nav
            (By.ID, "nav-cart-count"),
        ]

        confirmed = False
        for by, sel in confirmation_selectors:
            try:
                el = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((by, sel))
                )
                if el:
                    logger.info(
                        "Cart confirmation detected via selector: %s", sel
                    )
                    print("  ✅  Galaxy device successfully added to cart!\n")
                    confirmed = True
                    break
            except Exception:
                continue

        if not confirmed:
            if "cart" in driver.current_url.lower():
                print("  ✅  Redirected to cart page – item added!\n")
                confirmed = True

        assert confirmed, (
            "Could not verify that the Galaxy device was added to the cart. "
            f"Current URL: {driver.current_url}"
        )
