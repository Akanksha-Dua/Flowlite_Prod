import os
import pytest
import allure
from pathlib import Path
from playwright.sync_api import Page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    # Attach a screenshot here (rather than in a fixture) so it runs before
    # any fixture teardown closes the page/context.
    if rep.when == "call" and rep.failed:
        for value in item.funcargs.values():
            if isinstance(value, Page):
                try:
                    allure.attach(
                        value.screenshot(full_page=True),
                        name="failure-screenshot",
                        attachment_type=allure.attachment_type.PNG,
                    )
                except Exception:
                    pass
                break


def pytest_sessionfinish(session, exitstatus):
    alluredir = session.config.getoption("--alluredir", default=None)
    if not alluredir:
        return
    env_dir = Path(alluredir)
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / "environment.properties").write_text(
        f"Base.URL={session.config.getini('base_url')}\nBrowser=Chromium\n"
    )


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
