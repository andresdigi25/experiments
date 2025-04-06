import re
import time
from playwright.sync_api import Page, expect

def test_example(page: Page) -> None:
    page.goto("https://demo.playwright.dev/todomvc/#/")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").click()
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").fill("read books")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").press("Enter")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").fill("eat")
    time.sleep(1)  # Add delay
    page.get_by_placeholder("What needs to be done?").press("Enter")
    time.sleep(1)  # Add delay
    page.get_by_role("link", name="Active").click()
    time.sleep(1)  # Add delay
    page.get_by_role("link", name="Completed").click()
    time.sleep(1)  # Add delay
    expect(page.get_by_placeholder("What needs to be done?")).to_be_visible()
    time.sleep(1)  # Add delay
    page.get_by_role("link", name="All").click()
    time.sleep(1)  # Add delay
    page.locator("li").filter(has_text="read books").get_by_label("Toggle Todo").check()
    time.sleep(1)  # Add delay
    expect(page.locator("body")).to_contain_text("eat")
    time.sleep(1)  # Add delay
    page.get_by_role("link", name="Completed").click()
    time.sleep(1)  # Add delay
    expect(page.get_by_test_id("todo-title")).to_be_visible()
    time.sleep(1)  # Add delay