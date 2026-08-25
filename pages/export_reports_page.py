from datetime import datetime

from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class ExportReportsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.assert_text_visible("Export DGR Report", exact=True)

    def select_first_plant(self):
        self.page.wait_for_load_state("networkidle")
        combobox = self.page.get_by_placeholder("Select option", exact=True)
        combobox.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        combobox.first.click(force=True)

        option = self.page.get_by_role("option").first
        option.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        option.click(force=True)

    def set_start_date(self, date_str="01 Apr 2026"):
        target = datetime.strptime(date_str, "%d %b %Y")
        field = self.page.locator("#input-start-date")
        field.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        field.fill(target.strftime("%Y-%m-%d"))

    def set_end_date_to_today(self):
        field = self.page.locator("#input-end-date")
        field.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        # The field's own "max" attribute is the app's notion of today, which
        # avoids any clock skew between this machine and the server.
        today_value = field.get_attribute("max")
        field.fill(today_value)

    def generate_report(self, save_dir, file_name="generated_report.xlsx"):
        btn = self.page.get_by_role("button", name="Generate Report", exact=True)
        btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        return self.download_via(btn.first, save_dir, file_name)
