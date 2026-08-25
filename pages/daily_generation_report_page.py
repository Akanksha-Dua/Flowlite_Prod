import re

from playwright.sync_api import Page, expect

try:
    from .base_page import BasePage
except ImportError:
    from base_page import BasePage

from utils.data_generator import random_number


class DailyGenerationReportPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def is_loaded(self):
        # Match on the URL and a label from the page body - checking sidebar
        # link text alone gives a false pass, since it's attached on every page.
        self.wait_for_url_contains("/upload/page-1")
        self.page.wait_for_load_state("networkidle")
        # The historical data table loads asynchronously after networkidle
        # and re-renders the page when it arrives, which can swallow clicks
        # made on other controls while that's in flight.
        self.page.wait_for_timeout(2000)
        for text in ["Plant Data", "Daily Generation Data"]:
            locator = self.page.get_by_text(text, exact=False)
            if locator.count():
                try:
                    expect(locator.first).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
                    return
                except Exception:
                    continue
        raise AssertionError("The Daily Generation Reports page did not load")

    def open_plant_data_tab(self):
        self.page.wait_for_load_state("networkidle")
        clicked = False
        for label in ["Plant Data", "Plant data", "Plant Data "]:
            for locator in [
                self.page.get_by_text(label, exact=False),
                self.page.get_by_role("tab", name=re.compile(label, re.IGNORECASE)),
                self.page.locator("button, [role='button'], a").filter(has_text=re.compile(label, re.IGNORECASE)),
                self.page.locator(f'a[title="{label}"]'),
            ]:
                if locator.count():
                    try:
                        locator.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
                        locator.first.click(timeout=5000, force=True)
                        clicked = True
                        break
                    except Exception:
                        continue
            if clicked:
                break

        if not clicked:
            if self.page.get_by_text("Plant Data", exact=False).count():
                self.page.get_by_text("Plant Data", exact=False).first.click(timeout=5000, force=True)
            else:
                self.page.goto("https://flowlite.trugreen.ai/upload/page-1")

        # Switching tabs triggers its own async data load, which can
        # swallow clicks made on other controls while it's in flight.
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def _set_time(self, field_label, time_str):
        # Plant Up/Down Time are buttons that open a popup with separate
        # hour/minute inputs - not plain text fields, so they can't be
        # filled directly.
        hour, minute = time_str.split(":")
        trigger = self.page.get_by_text(field_label, exact=False).locator("xpath=following::button[1]")
        trigger.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        # A lingering toast/banner can overlap this button, intercepting a
        # positional click even with force=True - dispatch on the DOM node.
        trigger.first.evaluate("el => el.click()")

        time_inputs = self.page.locator("input[maxlength='2']")
        time_inputs.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        time_inputs.nth(0).fill(hour)
        time_inputs.nth(1).fill(minute)
        self.page.get_by_role("button", name="Set Time", exact=True).evaluate("el => el.click()")
        # Give the popup's confirm action a moment to commit before the next
        # field's popup opens - back-to-back calls can otherwise clobber it.
        self.page.wait_for_timeout(500)

    def fill_plant_data(self, up_time="08:00", down_time="18:00"):
        self.page.wait_for_load_state("networkidle")

        self._set_time("Plant Up Time", up_time)
        self._set_time("Plant Down Time", down_time)

        for placeholder in [
            "Enter DC Capacity",
            "Enter AC Capacity",
            "Enter Plant Availability (%)",
            "Enter Grid Availability (%)",
        ]:
            field = self.page.get_by_placeholder(placeholder)
            if field.count() and field.first.is_visible() and field.first.is_enabled():
                field.first.fill(str(random_number(1, 99)))

        save_btn = self.page.get_by_role("button", name="Save", exact=True)
        save_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        if save_btn.first.get_attribute("disabled") is not None:
            # This form only supports first-time entry for a date - once
            # data already exists, Save is permanently disabled and further
            # edits must go through the Historical Data section instead.
            return False
        save_btn.first.click(force=True)
        return True

    def assert_plant_data_saved(self, saved=True):
        if not saved:
            return
        self.page.wait_for_timeout(1000)
        body_text = self.page.locator("body").inner_text().lower()
        assert "success" in body_text, f"Plant data save was not confirmed. Body contains: {body_text[:300]}"

    def _edit_first_historical_row(self, heading_text, value_provider):
        # The page always has a "Save" button for the top data-entry form,
        # so the Edit/Save controls for this section must be located
        # relative to its own heading, not looked up globally.
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        heading = self.page.get_by_text(heading_text, exact=True)
        heading.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)

        edit_btn = heading.locator("xpath=following::button[1]")
        edit_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        edit_btn.first.click(force=True)

        row = heading.locator("xpath=following::table[1]").locator("tbody tr").first
        field = row.locator('input[type="number"]').first
        field.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        field.fill(str(value_provider()))

        save_btn = heading.locator("xpath=following::button").filter(has_text=re.compile(r"^Save$", re.IGNORECASE))
        save_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        save_btn.first.click(force=True)

    def edit_historical_plant_data(self):
        self._edit_first_historical_row("Historical Data - Plant Information", lambda: random_number(1, 99))

    def export_plant_data(self, save_dir, file_name="plant_data_export.xlsx"):
        save_dir.mkdir(parents=True, exist_ok=True)
        export_btn = self.page.locator("button, [role='button'], a").filter(has_text="Export")
        if export_btn.count():
            try:
                export_btn.first.click(timeout=5000)
            except Exception:
                pass
        return save_dir / file_name

    def open_inverter_tab(self):
        self.page.wait_for_load_state("networkidle")
        self.click_text("Inverter", exact=True)
        # The Form/Table toggle is a plain <span>, not a real button.
        self.click_text("Table", exact=True)

        # Switching tabs triggers its own async data load, which can
        # swallow clicks made on other controls while it's in flight.
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def fill_inverter_data_random(self):
        # This is a spreadsheet-style grid (no <input> elements) - a cell
        # only becomes editable via click, then type-to-edit + Tab commits it.
        data_row = self.page.locator('tr[data-y="0"]')
        data_row.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
        column_count = data_row.first.locator("td[data-x]").count()

        for x in range(1, column_count):
            cell = self.page.locator(f'td[data-x="{x}"][data-y="0"]')
            cell.click(force=True)
            self.page.wait_for_timeout(150)
            self.page.keyboard.type(str(random_number(100, 5000)))
            self.page.wait_for_timeout(150)
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(150)

        save_data_btn = self.page.get_by_role("button", name=re.compile("Save Data|Save", re.IGNORECASE))
        if save_data_btn.count():
            save_data_btn.first.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
            save_data_btn.first.click(force=True)

    def edit_historical_inverter_data(self):
        self._edit_first_historical_row("Historical Data - Inverter Data", lambda: random_number(100, 5000))

    def export_inverter_data(self, save_dir, file_name="inverter_data_export.xlsx"):
        export_btn = self.page.get_by_role("button", name="Export", exact=True).first
        return self.download_via(export_btn, save_dir, file_name)
