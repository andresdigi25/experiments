import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    # Start tracing before creating / navigating a page.
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.goto("https://integrichain-admin.integrichain.net/login")

    page.get_by_label("Email").click()
    page.get_by_label("Email").fill("afc@integrichain.com")
    page.get_by_label("Email").press("Tab")
    page.get_by_label("Password").fill("Ab_12345678")
    page.get_by_role("button", name="login Sign in").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Integrichain Monitor").click()
    page1 = page1_info.value
    page1.get_by_role("button", name="Last 12 months").click()
    page1.get_by_test_id("contributions").click()
    page1.get_by_test_id("percent-by-groups").click()
    page1.get_by_role("row", name="More than 1000 11 4%").locator("div").click()
    expect(page1.get_by_role("row", name="More than 1000 11 4%").locator("div")).to_be_visible()
    expect(page1.locator("h3")).to_contain_text("Number of Members by contributions: last year")
    page1.get_by_label("Close modal").click()
    page1.get_by_role("button", name="2023").click()
    page1.get_by_test_id("contributions").click()
    page1.get_by_test_id("percent-by-groups").click()
    expect(page1.get_by_role("dialog")).to_contain_text("Range contributions")
    page1.get_by_role("button", name="Radar chart").click()

    # ---------------------
    context.tracing.stop(path = "trace.zip")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
