from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://flowlite.trugreen.ai/', wait_until='networkidle', timeout=120000)
    print('URL:', page.url)
    print('TITLE:', page.title())
    print('BODY HTML SNIPPET:')
    print(page.locator('body').inner_html()[:10000])
    browser.close()
