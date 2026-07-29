from playwright.sync_api import sync_playwright
import re

base_url='https://flowlite.trugreen.ai/'
username='automation_dashboard'
password='Password@123456'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(base_url, wait_until='domcontentloaded')
    page.fill('#username', username)
    page.fill('#password', password)
    page.click('#loginButton')
    page.wait_for_load_state('networkidle', timeout=30000)
    print('URL after login:', page.url)
    page.mouse.move(0, 300)
    page.wait_for_timeout(2000)
    data_upload = page.get_by_role('button', name=re.compile('Data Upload', re.I))
    print('data_upload count', data_upload.count())
    if data_upload.count():
        data_upload.first.click(timeout=5000)
    page.wait_for_timeout(2000)
    buttons = page.locator('button, [role="button"], a')
    for i in range(min(buttons.count(), 60)):
        loc = buttons.nth(i)
        try:
            text = loc.inner_text()
        except Exception:
            text = ''
        if text and text.strip() and any(k.lower() in text.lower() for k in ['data','generation','plant','report','upload']):
            print('IDX', i, 'TEXT:', repr(text.strip()))
            try:
                print('HTML:', loc.evaluate('el => el.outerHTML').replace('\n',' ')[:1400])
            except Exception as e:
                print('HTML ERR', e)
    print('--- body text ---')
    body = page.locator('body').inner_text()
    print(body[:30000])
    browser.close()
