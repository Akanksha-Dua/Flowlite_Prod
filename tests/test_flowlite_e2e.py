from pathlib import Path

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.daily_generation_report_page import DailyGenerationReportPage
from pages.operational_expenses_page import OperationalExpensesPage
from pages.dsm_page import DSMPage
from pages.dgr_overview_page import DGROverviewPage
from pages.export_reports_page import ExportReportsPage

DOWNLOAD_DIR = Path.cwd() / "downloads"


def test_full_user_journey(auth_page):
    login_page = LoginPage(auth_page)
    dashboard_page = DashboardPage(auth_page)
    dgr_page = DailyGenerationReportPage(auth_page)
    operational_expenses_page = OperationalExpensesPage(auth_page)
    dsm_page = DSMPage(auth_page)
    dgr_overview_page = DGROverviewPage(auth_page)
    export_reports_page = ExportReportsPage(auth_page)

    download_dir = DOWNLOAD_DIR / "journey"
    download_dir.mkdir(parents=True, exist_ok=True)

    # User lands on the Dashboard after the (single, shared) login.
    dashboard_page.is_loaded()

    # Data Upload -> Daily Generation Reports -> Plant Data: fixed operating
    # hours, random capacity/availability figures, then Save.
    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_plant_data_tab()
    saved = dgr_page.fill_plant_data(up_time="08:00", down_time="18:00")
    dgr_page.assert_plant_data_saved(saved)

    # Saving plant data redirects back to the Dashboard, so return to the
    # Daily Generation Reports page before switching to the Inverter tab.
    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_inverter_tab()
    dgr_page.fill_inverter_data_random()

    # Edit the historical Plant Data row.
    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_plant_data_tab()
    dgr_page.edit_historical_plant_data()

    # Edit the historical Inverter row.
    dashboard_page.open_daily_generation_reports()
    dgr_page.is_loaded()
    dgr_page.open_inverter_tab()
    dgr_page.edit_historical_inverter_data()

    # Operational Expenses: export should download successfully.
    dashboard_page.open_operational_expenses()
    operational_expenses_page.is_loaded()
    opex_path = operational_expenses_page.export_report(download_dir, "operational_expenses_export.xlsx")
    assert opex_path.exists()

    # DSM: export should download successfully.
    dashboard_page.open_dsm()
    dsm_page.is_loaded()
    dsm_path = dsm_page.export_report(download_dir, "dsm_export.xlsx")
    assert dsm_path.exists()

    # DGR Overview: export should download successfully.
    dashboard_page.open_dgr_overview()
    dgr_overview_page.is_loaded()
    dgr_overview_path = dgr_overview_page.export_report(download_dir, "dgr_overview_export.csv")
    assert dgr_overview_path.exists()

    # Export Reports: first plant, fixed start date, end date today, then
    # Generate Report should download successfully.
    dashboard_page.open_export_reports()
    export_reports_page.is_loaded()
    export_reports_page.select_first_plant()
    export_reports_page.set_start_date("01 Apr 2026")
    export_reports_page.set_end_date_to_today()
    exported_report_path = export_reports_page.generate_report(download_dir, "generated_report.xlsx")
    assert exported_report_path.exists()

    # Logout should land back on the login page.
    dashboard_page.logout()
    assert login_page.is_login_page_visible()
