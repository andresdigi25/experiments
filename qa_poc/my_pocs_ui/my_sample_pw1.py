from playwright.sync_api import sync_playwright

def main():
    print('RUNNING PLAYWRIGHT')
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.amazon.in/")
        page.get_by_role("textbox", name="Search").click()
        page.get_by_role("textbox", name="Search").fill("legion 5i pro")
        page.get_by_role("textbox", name="Search").press("Enter")

if __name__ == '__main__':
    main()