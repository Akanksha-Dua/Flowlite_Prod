from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class OperationalExpensesPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.assert_text_visible("Operational Expenses", exact=True)

    def export_report(self, save_dir, file_name="operational_expenses_export.xlsx"):
        self.ensure_monthly_value_entered()
        export_btn = self.page.get_by_role("button", name="Export", exact=True)
        export_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        return self.download_via(export_btn.first, save_dir, file_name)
