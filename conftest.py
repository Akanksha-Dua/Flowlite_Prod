import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def credentials():
    return {
        "username": os.environ.get("FLOWLITE_USERNAME", "automation_dashboard"),
        "password": os.environ.get("FLOWLITE_PASSWORD", "Password@123456"),
    }


@pytest.fixture(scope="session")
def authenticated_storage(pytestconfig, playwright, credentials):
    """Create a session-scoped storage state with an authenticated user.

    This logs in once (using a Playwright browser) and returns the path to
    the `storage_state.json` file containing cookies/localStorage so tests
    can create contexts from it without re-logging in.
    """
    from pages.login_page import LoginPage

    base_url = pytestconfig.getini("base_url")
    out_dir = Path(pytestconfig.rootpath) / "tmp_auth"
    out_dir.mkdir(parents=True, exist_ok=True)
    storage_path = out_dir / "storage_state.json"

    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.login(credentials["username"], credentials["password"])

    # give the app a moment to settle before saving state
    context.storage_state(path=str(storage_path))
    context.close()
    browser.close()
    return str(storage_path)


@pytest.fixture
def auth_page(browser, authenticated_storage, pytestconfig):
    """Provide a `page` that's already authenticated using saved storage state."""
    context = browser.new_context(storage_state=authenticated_storage)
    page = context.new_page()
    page.goto(pytestconfig.getini("base_url"))
    yield page
    context.close()
