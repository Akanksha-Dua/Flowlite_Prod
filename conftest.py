import os
import pytest
import allure
from pathlib import Path
from playwright.sync_api import Page, expect


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
    # An unset GitHub Actions secret still sets the env var - just to an
    # empty string - so `or` is needed here, not `os.environ.get(key, default)`,
    # to actually fall back to the default in that case.
    return {
        "username": os.environ.get("FLOWLITE_USERNAME") or "automation_dashboard",
        "password": os.environ.get("FLOWLITE_PASSWORD") or "Password@123456",
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

    try:
        # The dashboard heading used to be a single "Automation Dashboard"
        # text node; the app now renders it as a two-part breadcrumb, so
        # check for a stable, unambiguous dashboard-only element instead.
        expect(page.get_by_role("button", name="Yearly View", exact=True)).to_be_visible(timeout=15_000)
    except Exception:
        failure_url = page.url
        failure_text = ""
        try:
            allure.attach(
                page.screenshot(full_page=True),
                name="login-failure-screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
            failure_text = page.locator("body").inner_text()
            allure.attach(
                failure_text,
                name="login-failure-page-text",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass
        context.close()
        browser.close()
        pytest.fail(
            "Login did not reach the Dashboard for user "
            f"'{credentials['username']}' - check that the FLOWLITE_USERNAME/"
            f"FLOWLITE_PASSWORD secrets (or defaults) are correct. "
            f"Landed on: {failure_url}\nPage text: {failure_text[:500]}"
        )

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
    page.goto(pytestconfig.getini("base_url"), wait_until="domcontentloaded")
    yield page
    context.close()
