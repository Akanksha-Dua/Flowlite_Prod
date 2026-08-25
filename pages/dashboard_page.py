import re

import allure
from playwright.sync_api import Page, expect

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage


class DashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.wait_for_url_contains("flowlite.trugreen.ai")
        # The dashboard heading used to be a single "Automation Dashboard"
        # text node; the app now renders it as a two-part breadcrumb, so
        # check for a stable, unambiguous dashboard-only element instead.
        expect(self.page.get_by_role("button", name="Yearly View", exact=True)).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

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

        # "Daily Generation Reports" is a plain text label (not a link/button)
        # that's always in the DOM twice (a visible/hidden pair for responsive
        # layout) and only visible once "Data Upload" - a toggle - is
        # expanded, so only click it when not already expanded.
        report_items = self.page.get_by_text("Daily Generation Reports", exact=True)
        visible_item = next(
            (report_items.nth(i) for i in range(report_items.count()) if report_items.nth(i).is_visible()),
            None,
        )
        if visible_item is None:
            data_upload = self.page.get_by_role("button", name=re.compile("Data Upload", re.IGNORECASE))
            if data_upload.count():
                data_upload.first.click(timeout=5000, force=True)
            self.page.wait_for_timeout(1000)
            report_items = self.page.get_by_text("Daily Generation Reports", exact=True)
            visible_item = next(
                (report_items.nth(i) for i in range(report_items.count()) if report_items.nth(i).is_visible()),
                None,
            )

        if visible_item is not None:
            # A positional/force click can still land on an overlapping
            # element mid-animation - dispatch directly on the DOM node.
            visible_item.evaluate("el => el.click()")
        else:
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

    def _snapshot(self, name):
        try:
            allure.attach(
                self.page.screenshot(full_page=True),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        except Exception:
            pass

    def logout(self):
        # The profile row's log-out icon opens an in-app confirmation button;
        # confirming that redirects to the identity provider's own logout
        # page, which requires a second confirmation before the session ends.
        # This row sits at the bottom of the sidebar and can land outside the
        # viewport depending on page height, so dispatch on the DOM node
        # directly instead of a positional click.
        dispatch_click = "el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))"
        icon = self.page.locator("svg.lucide-log-out")
        icon_count = icon.count()
        if icon_count:
            icon.first.evaluate(dispatch_click)
        else:
            self.page.get_by_text("AD", exact=True).first.evaluate(dispatch_click)
        self.page.wait_for_timeout(500)
        self._snapshot(f"logout-1-after-icon-click (icon_count={icon_count})")

        logout_pattern = re.compile("logout|log out", re.IGNORECASE)

        confirm_btn = self.page.get_by_role("button", name=logout_pattern)
        confirm_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        confirm_btn_count = confirm_btn.count()
        confirm_btn.first.click(force=True)
        self.page.wait_for_timeout(500)
        self._snapshot(f"logout-2-after-confirm-click (matches={confirm_btn_count}, url={self.page.url})")

        idp_confirm_btn = self.page.get_by_role("button", name=logout_pattern)
        idp_confirm_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        idp_confirm_btn_count = idp_confirm_btn.count()
        idp_confirm_btn.first.click(force=True)
        self.page.wait_for_timeout(500)
        self._snapshot(f"logout-3-after-idp-click (matches={idp_confirm_btn_count}, url={self.page.url})")

        # Confirming on the identity provider lands on an intermediate
        # "/logout" page that then redirects to the actual login page.
        self.page.wait_for_load_state("networkidle")
        self._snapshot(f"logout-4-final (url={self.page.url})")
