import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://demo.playwright.dev/todomvc/#/")
    await page.get_by_placeholder("What needs to be done?").click()
    await page.get_by_placeholder("What needs to be done?").fill("read books")
    await page.get_by_placeholder("What needs to be done?").press("Enter")
    await page.get_by_placeholder("What needs to be done?").fill("eat")
    await page.get_by_placeholder("What needs to be done?").press("Enter")
    await page.get_by_role("link", name="Active").click()
    await page.get_by_role("link", name="Completed").click()
    await expect(page.get_by_placeholder("What needs to be done?")).to_be_visible()
    await page.get_by_role("link", name="All").click()
    await page.locator("li").filter(has_text="read books").get_by_label("Toggle Todo").check()
    await expect(page.locator("body")).to_contain_text("eat")
    await page.get_by_role("link", name="Completed").click()
    await expect(page.get_by_test_id("todo-title")).to_be_visible()
    # ---------------------
    await context.close()
    await browser.close()


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


asyncio.run(main())