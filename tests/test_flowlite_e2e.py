from pathlib import Path

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.daily_generation_report_page import DailyGenerationReportPage
from pages.operational_expenses_page import OperationalExpensesPage
from pages.dsm_page import DSMPage
from pages.dgr_overview_page import DGROverviewPage
from pages.export_reports_page import ExportReportsPage

DOWNLOAD_DIR = Path.cwd() / "downloads"


def test_successful_login(page, base_url, credentials):
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)

    login_page.open(base_url)
    login_page.login(credentials["username"], credentials["password"])

    dashboard_page.is_loaded()
    assert "flowlite.trugreen.ai" in page.url


def test_flowlite_end_to_end(auth_page, base_url):
    dashboard_page = DashboardPage(auth_page)
    dgr_page = DailyGenerationReportPage(auth_page)

    # Navigate through the requested plant-data save flow.
    dashboard_page.open_data_upload()

    daily_generation_tab = auth_page.locator("button, [role='tab'], a").filter(has_text="Daily Generation")
    if daily_generation_tab.count():
        # The sidebar's expand animation leaves the "Data Upload" toggle
        # button overlapping this link, so a positional click (even forced)
        # can hit the button instead - dispatch the click on the DOM node.
        daily_generation_tab.first.evaluate("el => el.click()")

    dgr_page.is_loaded()
    dgr_page.open_plant_data_tab()
    dgr_page.fill_plant_data_random()
    dgr_page.assert_plant_data_saved()


def test_full_user_journey(auth_page, base_url):
    login_page = LoginPage(auth_page)
    dashboard_page = DashboardPage(auth_page)
    dgr_page = DailyGenerationReportPage(auth_page)
    operational_expenses_page = OperationalExpensesPage(auth_page)
    dsm_page = DSMPage(auth_page)
    dgr_overview_page = DGROverviewPage(auth_page)
    export_reports_page = ExportReportsPage(auth_page)

    download_dir = DOWNLOAD_DIR / "journey"
    download_dir.mkdir(parents=True, exist_ok=True)

    dashboard_page.is_loaded()

    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_plant_data_tab()
    dgr_page.fill_plant_data_random()
    dgr_page.assert_plant_data_saved()

    # Saving plant data redirects back to the Dashboard, so return to the
    # Daily Generation Reports page before switching to the Inverter tab.
    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_inverter_tab()
    dgr_page.fill_inverter_data_random()

    dashboard_page.open_operational_expenses()
    operational_expenses_page.is_loaded()

    dashboard_page.open_dsm()
    dsm_page.is_loaded()

    dashboard_page.open_dgr_overview()
    dgr_overview_page.is_loaded()
    dgr_overview_path = dgr_overview_page.export_report(download_dir, "dgr_overview_export.csv")
    assert dgr_overview_path.exists()

    dashboard_page.open_export_reports()
    export_reports_page.is_loaded()
    export_reports_page.select_first_plant()
    export_reports_page.set_start_date("01 Apr 2026")
    export_reports_page.set_end_date_to_today()
    exported_report_path = export_reports_page.generate_report(download_dir, "generated_report.xlsx")
    assert exported_report_path.exists()

    dashboard_page.logout()
    assert login_page.is_login_page_visible()
