import re
from pathlib import Path

from playwright.sync_api import Page, Locator, expect


class BasePage:
    DEFAULT_TIMEOUT = 30_000

    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str):
        # "load" (Playwright's default) waits for every last resource on the
        # page and can hang well past its timeout if anything keeps a
        # connection open (e.g. a websocket/long-poll) - domcontentloaded is
        # enough for interacting with the page, and Playwright's own
        # actionability waits handle the rest per-element.
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_for_url_contains(self, fragment: str):
        # This app navigates client-side (SPA route changes), which never
        # fires another "load" event (Playwright's wait_until default) -
        # "commit" only waits for the URL itself to change, which is all we
        # need here; actual content readiness is checked separately.
        self.page.wait_for_url(re.compile(re.escape(fragment)), timeout=self.DEFAULT_TIMEOUT, wait_until="commit")

    def click_text(self, text: str, exact: bool = True):
        locator = self.page.get_by_text(text, exact=exact).first
        try:
            expect(locator).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
            locator.scroll_into_view_if_needed()
            locator.click(timeout=self.DEFAULT_TIMEOUT)
        except Exception:
            locator.click(force=True, timeout=self.DEFAULT_TIMEOUT * 2)

    def click_button(self, name: str, exact: bool = True):
        self.page.get_by_role("button", name=name, exact=exact).first.click()

    def fill_by_label(self, label: str, value: str):
        self.page.get_by_label(label, exact=False).first.fill(value)

    def fill_by_placeholder(self, placeholder: str, value: str, index: int = 0):
        self.page.get_by_placeholder(placeholder).nth(index).fill(value)

    def assert_text_visible(self, text: str, exact: bool = False):
        expect(self.page.get_by_text(text, exact=exact).first).to_be_visible(
            timeout=self.DEFAULT_TIMEOUT
        )

    def download_via(self, trigger: Locator, save_dir: Path, file_name: str) -> Path:
        save_dir.mkdir(parents=True, exist_ok=True)
        target = save_dir / file_name
        if target.exists():
            target.unlink()

        with self.page.expect_download(timeout=self.DEFAULT_TIMEOUT * 2) as download_info:
            trigger.scroll_into_view_if_needed()
            trigger.click(force=True)

        download = download_info.value
        download.save_as(target)
        return target

    def ensure_monthly_value_entered(self, site_text: str = "Automation Site 1", value: int = 50000) -> bool:
        """Fill in the month's value via Edit if it's showing as missing.

        Operational Expenses/DSM show a dash placeholder until a value is
        entered for the current month, and exporting then produces nothing
        since there's no data. Returns True if a value was entered, False
        if data already existed for this month.
        """
        row = self.page.locator("tr", has_text=site_text)
        row.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        if "—" not in row.first.inner_text():
            return False

        self.page.get_by_role("button", name="Edit", exact=True).first.click(force=True)

        cell = row.first.locator('td[data-x="1"]')
        cell.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        cell.first.click(force=True)
        self.page.keyboard.type(str(value))
        self.page.keyboard.press("Tab")

        self.page.get_by_role("button", name="Save", exact=True).first.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    def fill_all_visible_table_inputs(self, value_provider, row_locator: Locator = None):
        target = row_locator if row_locator is not None else self.page.locator("table")
        inputs = target.locator("input")
        filled = 0
        for i in range(inputs.count()):
            cell = inputs.nth(i)
            try:
                if cell.is_visible() and cell.is_enabled():
                    cell.fill(str(value_provider()))
                    filled += 1
            except Exception:
                continue
        return filled
