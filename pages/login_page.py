from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def open(self, url: str):
        self.goto(url)

    def login(self, username: str = "automation_dashboard", password: str = "Password@123456"):
        username_field = self.page.locator("#username")
        username_field.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        username_field.fill(username)
        password_field = self.page.locator("#password")
        password_field.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        password_field.fill(password)

        self.page.locator("#loginButton").click()

    def is_login_page_visible(self) -> bool:
        return self.page.get_by_role("button", name="Login", exact=True).is_visible()
