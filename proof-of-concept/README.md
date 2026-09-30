# Read-only live proof — page candidate

This folder is a branch-only candidate. It is not wired to a live API or merged to the GitHub Pages main branch. With no mock query, it displays DOWN and no account data. Adding ?mock=1 fetches mock.json, which contains only synthetic PREVIEW-/DEMO identities and an unmissable preview banner.

Run python -m http.server 8787 --bind 127.0.0.1 at the site repository root, then open http://127.0.0.1:8787/proof-of-concept/?mock=1. Run node proof-of-concept/test_dashboard.mjs for the static guards. Browser-checked captures are screenshots/preview-1400.png and screenshots/preview-375.png.

Before any live connection, the director must review the deployed Worker's exact HTTPS origin and masking/auth tests. Pin that origin in API_BASE inside index.html, add the same exact origin to connect-src, regenerate the inline-script SHA-256 CSP hash, and rerun tests. No URL, query parameter, local storage item, or user input may choose the API destination. The password and bearer token stay only in tab memory. Logout and 401/403 clear private DOM and state. The storefront and its zero-JavaScript contract remain unchanged.

The two disclaimer paragraphs are copied verbatim from terms.html; they are not live-performance claims. The synthetic fixture is not broker evidence.
