from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class DSMPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.assert_text_visible("DSM", exact=True)
