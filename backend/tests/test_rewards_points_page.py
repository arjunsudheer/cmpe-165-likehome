from playwright.sync_api import Page, expect

import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("CI") == "true", reason="Requires live servers")

BASE_URL = "http://127.0.0.1:5173/rewards"


def test_rewards_balance_label(page: Page):
    page.goto(BASE_URL)

    label = page.locator(".balance-label")
    expect(label).to_have_text("Your Balance")


def test_points_format(page: Page):
    page.goto(BASE_URL)

    number_text = page.locator(".balance-number").inner_text()
    points_text = page.locator(".balance-unit").inner_text()

    # number should be digits with optional commas
    assert number_text.strip().replace(",", "").isdigit()
    assert points_text == "pts"


def test_dollar_value_format(page: Page):
    page.goto(BASE_URL)

    value_text = page.locator(".balance-value").inner_text().strip()

    import re

    assert re.match(r"^Worth \$\d+\.\d{2}", value_text)
