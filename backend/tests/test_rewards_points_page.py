from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5173/rewards"


def test_rewards_balance_label(page: Page):
    page.goto(BASE_URL)

    label = page.locator(".balance-label")
    expect(label).to_have_text("Rewards Balance")


def test_points_format(page: Page):
    page.goto(BASE_URL)

    number_text = page.locator(".balance-number").inner_text()
    points_text = page.locator(".balance-points").inner_text()

    # number should be digits with optional commas
    assert number_text.strip().replace(",", "").isdigit()
    assert points_text == "points"


def test_dollar_value_format(page: Page):
    page.goto(BASE_URL)

    value_text = page.locator(".balance-info").inner_text().strip()

    # Should match: $xx.xx value
    # Example: "$48.20 value"
    import re

    assert re.match(r"^\$\d+\.\d{2} value$", value_text)
