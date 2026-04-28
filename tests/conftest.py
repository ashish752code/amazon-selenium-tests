"""
tests/conftest.py
─────────────────
Shared pytest fixtures available to every test module.

The ``driver`` fixture spins up a fresh Chrome session before each test
and tears it down (with a screenshot on failure) after each test.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime

import pytest

from utils.helpers import create_driver

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Browser fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def driver(request):
    """
    Pytest fixture – yields a configured Chrome WebDriver.

    * scope="function"  → each test gets its own isolated browser session
    * On test FAILURE   → saves a PNG screenshot to  reports/screenshots/
    """
    browser = create_driver(headless=True)
    logger.info("Browser started for test: %s", request.node.name)

    yield browser   # ← test runs here

    # ── teardown ─────────────────────────────────────────────────────────────
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        _take_screenshot(browser, request.node.name)

    browser.quit()
    logger.info("Browser closed for test: %s", request.node.name)


# ─────────────────────────────────────────────────────────────────────────────
#  Hook – capture test result so the fixture can access it
# ─────────────────────────────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the call-phase report to the test node for use in fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _take_screenshot(browser, test_name: str) -> None:
    """Save a PNG screenshot to reports/screenshots/ on test failure."""
    screenshots_dir = os.path.join("reports", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name  = "".join(c if c.isalnum() else "_" for c in test_name)
    path       = os.path.join(screenshots_dir, f"{safe_name}_{timestamp}.png")

    try:
        browser.save_screenshot(path)
        logger.info("Screenshot saved → %s", path)
    except Exception as exc:
        logger.warning("Could not save screenshot: %s", exc)
