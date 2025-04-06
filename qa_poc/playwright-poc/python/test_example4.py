import time
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()  # Create a new page 
    page.goto("https://demo.playwright.dev/todomvc/#/")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").click()
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").fill("learn")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").press("Enter")
    time.sleep(1)  # Add delay
    page.get_by_label("Toggle Todo").check()
    time.sleep(1)  # Add delay
    page.goto("https://demo.playwright.dev/todomvc/#/completed")
    time.sleep(1)  # Add delay
    page.get_by_test_id("todo-title").click(button="right")
    time.sleep(1)  # Add delay
    page.get_by_test_id("todo-title").click()
    time.sleep(1)  # Add delay
    expect(page.get_by_test_id("todo-title")).to_contain_text("learn")
    time.sleep(1)  # Add delay
    page.get_by_role("button", name="Clear completed").click()
    time.sleep(1)  # Add delay

    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)