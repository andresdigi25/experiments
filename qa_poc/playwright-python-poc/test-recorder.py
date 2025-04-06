import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.google.com/search?q=meristation&oq=meristation&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCDQwMjFqMGoyqAIAsAIA&sourceid=chrome&ie=UTF-8")
    page.get_by_role("link", name="MeriStation: Noticias, guías").click()
    page.locator("#acceptationCMPWall div").click()
    page.get_by_label("Agree and close: Agree to our").click()
    page.goto("https://as.com/meristation/")
    page.get_by_role("link", name="PlayStation convierte tu PS5 en una PS4, PS3, PS2 y PSX con el mejor homenaje que vas a ver por su 30 aniversario", exact=True).click()
    page.get_by_role("heading", name="Una actualización de PS5 te").click()
    page.get_by_role("img", name="PlayStation 30 aniversario").click()
    page.get_by_role("link", name="canal de MeriStation en").click(button="right")
    page1 = context.new_page()
    page1.goto("https://x.com/MeriStation?s=20")
    page1.goto("https://x.com/MeriStation?s=20")
    page.goto("https://www.google.com/search?q=meristation&oq=meristation&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCDQwMjFqMGoyqAIAsAIA&sourceid=chrome&ie=UTF-8")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
