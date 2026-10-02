# Offline proof-page tests

All accounts, balances and comparison values in these fixtures are synthetic. Every browser network request is fulfilled locally. Screenshots carry a synthetic label.

Run `node --test proof-of-concept/tests/session-binding.cjs`. To enable exact backend integration, set FTB_SESSION_MODULE_ROOT to the reviewed backend's _work/ftb_live directory (PR26 head c643ecdac).

Run `node proof-of-concept/tests/browser.cjs` with Playwright available. PLAYWRIGHT_MODULE can point to an existing Playwright installation; CHROMIUM_PATH can specify an existing Chromium browser. No package installation or production credentials are required. Results and screenshots go to tests/artifacts (ignored).

The browser suite covers current legacy API null behavior, verified ny-18-17-v1 projection, source freshness, partial coverage, pending-response expiration/rollover, DST, Today sorting, privacy, authentication boundaries, fixed origin/CSP, health dots and desktop/mobile layout. This is a UI contract test, not evidence that real financial records exist.
