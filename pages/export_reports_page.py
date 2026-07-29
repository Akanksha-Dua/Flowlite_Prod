import re
from datetime import datetime

from playwright.sync_api import Page

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class ExportReportsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        self.assert_text_visible("Export DGR Report", exact=True)

    def select_first_plant(self):
        self.page.wait_for_load_state("networkidle")

        placeholder = self.page.get_by_text("Select an option", exact=False)
        if placeholder.count():
            placeholder.first.click(force=True)
            option = self.page.get_by_role("option").first
            option.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
            option.click(force=True)
            return

        select_els = self.page.locator("select")
        if select_els.count() > 0:
            select_els.first.select_option(index=0)

    def _open_date_picker(self, label_text: str):
        # The trigger button's own text is a placeholder only until a date is
        # picked, after which it shows the chosen date instead - so locate it
        # relative to its (stable) field label rather than by its own text.
        label = self.page.get_by_text(label_text, exact=True)
        label.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        trigger = label.first.locator("xpath=following::button[1]")
        trigger.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        trigger.first.click(force=True)
        self.page.locator(".react-calendar").first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)

    def _navigate_calendar_to(self, target_month: int, target_year: int):
        label = self.page.locator(".react-calendar__navigation__label")
        for _ in range(36):
            match = re.match(r"([A-Za-z]+)\s+(\d{4})", label.first.inner_text().strip())
            if not match:
                raise AssertionError("Could not read the calendar's current month/year")

            current_month = MONTH_NAMES.index(match.group(1)) + 1
            current_year = int(match.group(2))
            diff = (target_year - current_year) * 12 + (target_month - current_month)
            if diff == 0:
                return

            nav_class = ".react-calendar__navigation__next-button" if diff > 0 else ".react-calendar__navigation__prev-button"
            self.page.locator(nav_class).first.click(force=True)
            self.page.wait_for_timeout(150)

        raise AssertionError("Could not navigate the calendar to the target month/year")

    def _click_calendar_day(self, day: int):
        cells = self.page.locator(
            ".react-calendar__tile.react-calendar__month-view__days__day"
            ":not(.react-calendar__month-view__days__day--neighboringMonth)"
        ).filter(has_text=re.compile(rf"^{day}$"))
        cells.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        cells.first.click(force=True)

    def set_start_date(self, date_str="01 Apr 2026"):
        target = datetime.strptime(date_str, "%d %b %Y")
        self._open_date_picker("Start Date")
        self._navigate_calendar_to(target.month, target.year)
        self._click_calendar_day(target.day)

    def set_end_date_to_today(self):
        self._open_date_picker("End Date")
        today_cell = self.page.locator(".react-calendar__tile--now")
        today_cell.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        today_cell.first.click(force=True)

    def generate_report(self, save_dir, file_name="generated_report.xlsx"):
        btn = self.page.get_by_role("button", name="Generate Report", exact=True)
        btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        return self.download_via(btn.first, save_dir, file_name)
