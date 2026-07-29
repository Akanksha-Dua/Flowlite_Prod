from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class DGROverviewPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.assert_text_visible("DGR Overview", exact=True)

    def export_report(self, save_dir, file_name="dgr_overview_export.csv"):
        # "Export Report" opens a filter modal that has its own, identically
        # named submit button - the actual download only fires from that one.
        open_btn = self.page.get_by_role("button", name="Export Report", exact=True)
        open_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        open_btn.first.click(force=True)

        submit_btn = self.page.get_by_role("button", name="Export Report", exact=True).last
        submit_btn.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        return self.download_via(submit_btn, save_dir, file_name)
