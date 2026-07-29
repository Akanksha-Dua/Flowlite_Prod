import re

from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class DashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.wait_for_url_contains("flowlite.trugreen.ai")
        self.assert_text_visible("Automation Dashboard")

    def _open_sidebar(self):
        nav = self.page.locator("nav").first
        box = nav.bounding_box(timeout=self.DEFAULT_TIMEOUT)
        if box:
            self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + 20)
        else:
            self.page.mouse.move(28, 60)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

    def open_data_upload(self):
        self._open_sidebar()
        data_upload = self.page.get_by_text("Data Upload", exact=True)
        data_upload.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        data_upload.first.click(force=True)

    def open_daily_generation_reports(self):
        self._open_sidebar()

        report_link = self.page.locator('a[title="Daily Generation Reports"]')

        # The "Data Upload" button only opens the submenu - it's a toggle,
        # so only click it when the submenu isn't already expanded.
        if not (report_link.count() and report_link.first.is_visible()):
            data_upload = self.page.get_by_role("button", name=re.compile("Data Upload", re.IGNORECASE))
            if data_upload.count():
                data_upload.first.click(timeout=5000, force=True)
            self.page.wait_for_timeout(1000)

        if report_link.count():
            try:
                report_link.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
                # The "Data Upload" toggle button visually overlaps this link
                # while the submenu is expanding, so a positional click (even
                # forced) can land on the button instead - dispatch on the DOM node.
                report_link.first.evaluate("el => el.click()")
                return
            except Exception:
                pass

        self.goto("https://flowlite.trugreen.ai/upload/page-1")

    def _click_sidebar_link(self, href: str, fallback_url: str):
        """Navigate via the sidebar link's client-side routing.

        A plain `page.goto()` to these deep links forces a full page
        reload, which re-triggers the OAuth flow and always lands back
        on the dashboard root instead of the requested page.
        """
        self._open_sidebar()
        link = self.page.locator(f'a[href="{href}"]')
        if link.count():
            link.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
            link.first.evaluate("el => el.click()")
            return
        self.goto(fallback_url)

    def open_operational_expenses(self):
        self._click_sidebar_link("/monthly-budget/opex", "https://flowlite.trugreen.ai/monthly-budget/opex")

    def open_dsm(self):
        self._click_sidebar_link("/monthly-budget/dsm", "https://flowlite.trugreen.ai/monthly-budget/dsm")

    def open_dgr_overview(self):
        self._click_sidebar_link("/settings/metric-calculations", "https://flowlite.trugreen.ai/settings/metric-calculations")

    def open_export_reports(self):
        self._click_sidebar_link("/reports", "https://flowlite.trugreen.ai/reports")

    def logout(self):
        # The profile row's log-out icon opens an in-app confirmation button;
        # confirming that redirects to the identity provider's own logout
        # page, which requires a second confirmation before the session ends.
        # This row sits at the bottom of the sidebar and can land outside the
        # viewport depending on page height, so dispatch on the DOM node
        # directly instead of a positional click.
        dispatch_click = "el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))"
        icon = self.page.locator("svg.lucide-log-out")
        if icon.count():
            icon.first.evaluate(dispatch_click)
        else:
            self.page.get_by_text("AD", exact=True).first.evaluate(dispatch_click)

        logout_pattern = re.compile("logout|log out", re.IGNORECASE)

        confirm_btn = self.page.get_by_role("button", name=logout_pattern)
        confirm_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        confirm_btn.first.click(force=True)

        idp_confirm_btn = self.page.get_by_role("button", name=logout_pattern)
        idp_confirm_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        idp_confirm_btn.first.click(force=True)

        # Confirming on the identity provider lands on an intermediate
        # "/logout" page that then redirects to the actual login page.
        self.page.wait_for_load_state("networkidle")
