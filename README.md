# Flowlite Automation

[![Daily Flowlite E2E Tests](https://github.com/Akanksha-Dua/Flowlite_Prod/actions/workflows/daily-tests.yml/badge.svg)](https://github.com/Akanksha-Dua/Flowlite_Prod/actions/workflows/daily-tests.yml)

Playwright + pytest end-to-end test suite for [Flowlite](https://flowlite.trugreen.ai/).

## Daily run

Tests run automatically every day at 08:00 AM IST via GitHub Actions, and can also be triggered manually from the [Actions tab](https://github.com/Akanksha-Dua/Flowlite_Prod/actions/workflows/daily-tests.yml) ("Run workflow").

- **Latest Allure report (with trend history):** https://akanksha-dua.github.io/Flowlite_Prod/
- **Workflow run history:** https://github.com/Akanksha-Dua/Flowlite_Prod/actions/workflows/daily-tests.yml
- A pass/fail summary is emailed to akanksha@truboardpartners.com after every run.

## Running locally

```
pip install -r requirements.txt
playwright install chromium
pytest
```

Run headed (to watch the browser) with:

```
pytest --headed
```

Credentials default to the built-in automation account; override with the `FLOWLITE_USERNAME`/`FLOWLITE_PASSWORD` environment variables if needed.
