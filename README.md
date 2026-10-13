# Milk Tea & Beverage Shop — PHP POS

IT415 practical exam, Scenario 3. A desktop-friendly web POS built with PHP,
HTML, and CSS only. No JavaScript, framework, database, external assets, or
application dependencies. Money is calculated in integer centavos.

## Run locally

Install PHP 8.0 or newer. From the repository directory:

```sh
cd public
php -S localhost:8000
```

Open **http://localhost:8000** in a browser. Stop the server with Ctrl+C.
If PHP is not on PATH, use your PHP executable, for example on this workstation:

```powershell
cd public
D:\xampp\php\php.exe -S localhost:8000
```

Run the server inside `public` so source code, tests, and documentation are outside
the web root. PHP needs a writable session storage directory. The built-in server
is intended for local development and the exam demonstration.

## Transaction flow — Section IV

1. Browse the six product buttons showing exact names and prices.
2. Add products. Repeated clicks increase quantity; use **+**, **−**, or **Remove**.
   Decreasing quantity from one removes that item.
3. Review quantities, unit prices, subtotals, and total after each form submission.
4. Enter cash using digits and up to two decimal places, such as `200.50`.
   Blank, non-numeric, negative, and insufficient cash show clear error alerts.
5. Select **Validate & Compute** to calculate change and open payment review.
6. Review the order, total, cash, and change; select **Confirm Payment** to finalize.
   **Edit Cash** or **Cancel Confirmation** clears validation and returns to editing.
7. Read the digital receipt. **New Transaction** clears cart, cash, validation,
   and receipt for the next sale; it can also reset an unfinished order.

## Project structure

```text
public/
  index.php          Session setup, POST handling, forms, and receipt display
  styles.css         Responsive desktop layout and print styling
src/
  pos.php            Catalog, cart actions, cash validation, and receipt snapshot
tests/               PHP regression tests
legacy/              Archived Python/Tkinter application, tests, and old README
AI_USAGE.md          Historical AI-use documentation
README.md            Current web application instructions
```

The active web application requires only PHP. Archived Python files are retained
for reference and are outside the web root; they are not loaded by the POS.

## Payment and data security

- Prices come only from the server's hard-coded catalog. All calculations and
  displayed money formatting use integer centavos, without float arithmetic.
- Quantity is limited to 99 per product; maximum cash is ₱1,000,000.00. Cash
  rejects exponents, currency symbols, commas, more than two decimal places,
  arrays, and oversized values. Surrounding whitespace is accepted.
- Every POST checks a session CSRF token and the current order ID/revision.
  Stale tabs, old confirmation forms, and forms from previous transactions fail.
- Cart edits, payment cancellation, cash editing, and failed cash validation
  invalidate earlier validation. Confirmation additionally checks a single-use
  payment token and the current total. A completed order is locked.
- Validated cash is displayed read-only. Use **Edit Cash** to invalidate payment
  before editing. Without JavaScript, PHP observes changes only on submission;
  there is no editable cash input beside the confirmation button.
- PHP's session lock serializes requests; POST/Redirect/GET prevents ordinary
  refresh from repeating actions. Output is escaped and unexpected request errors
  show a generic alert. Cookies use HttpOnly and SameSite=Strict; Secure is enabled
  when served over HTTPS. Responses disable caching and restrict scripts/frames.
- Transactions are temporary session data. There is no durable sales ledger,
  authentication, stock management, or multi-register account system. Browser
  tabs in the same session share one order. New Transaction discards the receipt;
  use the browser's Print command to save it first if needed.

## Version control

This local folder initially had no `.git` directory. Real metadata was recovered
from the existing GitHub repository without overwriting files or rewriting history.
The starting commit was `975ed8d`, which includes the original development commits
and the merge of the previous `work` branch into `main`.

Conversion commits build on that history. See `git log --oneline` for actual hashes.
The repository is
`https://github.com/christan-dave-castillo/Abdullah-Castillo-Practical-Exam-Scenario-3.git`.
Synchronization status is reported after the final commit and remote verification.

## Automated checks

From the repository root, run:

```sh
php tests/run.php
php -l src/pos.php
php -l public/index.php
```

With the server still running in a separate terminal, run:

```sh
php tests/http.php
```

The HTTP suite creates its own test sessions and fake sales; it does not use your
browser's session. PHP's built-in HTTP streams must be enabled (`allow_url_fopen`).
An optional alternate server port can be supplied as a localhost URL:
`php tests/http.php http://localhost:8001`.

Verified on 2026-10-13 with PHP 8.3.13: **36 logic tests** and **100 HTTP checks**
passed. These cover catalog/cart calculations, cash errors, payment invalidation,
confirmation and receipts, duplicate/stale requests, reset, separate sessions,
CSRF, escaped cash output, response headers, and public-directory isolation.
Both application PHP files and the HTTP test passed syntax checks.

Browser inspection was blocked because browser access to localhost was declined.
Automated HTTP checks verify returned HTML and server behavior, but do not verify
rendering, physical keyboard/mouse use, browser history behavior, or print layout.

## Testing checklist — Section V

Use these categories for manual screenshots. The feature names follow the twelve
features recorded in the original project README.

| # | Required feature | Manual check / screenshot |
| --- | --- | --- |
| 1 | Product names and prices | Show all six buttons: Classic ₱59, Wintermelon ₱65, Taro ₱65, Lychee ₱55, Brown Sugar ₱69, Water ₱20; verify full names |
| 2 | Add through buttons | Add Classic twice, Lychee once, Water once; Classic has quantity 2 |
| 3 | Increase/decrease quantities | Use + and −; decreasing from quantity 1 removes the row |
| 4 | Remove an item | Remove Water, then add it again |
| 5 | Automatic subtotals/total | Sample order subtotals are ₱118.00, ₱55.00, ₱20.00; total is ₱193.00 |
| 6 | Clear order summary | Read names, quantities, unit prices, subtotals, and total in the cart table |
| 7 | Cash input | Enter `200.00`; select Validate & Compute (also try Enter in the field) |
| 8 | Invalid cash alerts | Try blank, `abc`, `-1`, and `192.99`; verify clear error messages and no confirmation |
| 9 | Correct change | Cash `200.00` gives ₱7.00; `193.00` gives ₱0.00; `200.50` gives ₱7.50 |
| 10 | Successful confirmation | Cancel first and check no receipt; validate again, then Confirm Payment; verify success message |
| 11 | Digital receipt | Check transaction number, item names, quantities, unit prices, subtotals, total, cash, and change |
| 12 | New Transaction | Clear completed sale; cart is empty, cash is blank, receipt is gone; second sale has a different number |

Additional manual checks:

- Validate cash, then change the cart; review closes and validation is required
  again. Restore the cart and validate; select Edit Cash, change cash, and check
  that validation is required again. Cancelling also revokes validation.
- Keep an older tab open, update the cart in another tab, and submit the older
  form. Check the outdated-form alert. Use Back after confirmation and resubmit;
  check that only the existing receipt remains. Refresh must not add items again.
- Check the page at 1366×768 and a narrow mobile width, keyboard Tab/Enter use,
  and horizontal scrolling of tables on small screens. Print the receipt and
  check that cart controls are omitted. These visual checks remain manual.

## GitHub synchronization evidence

After committing/pushing, capture:

```sh
git log -8 --oneline
git status --short --branch
git remote -v
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Local HEAD and the remote `main` SHA must match. The first conversion commit is
`6a19724` — **Convert Tkinter POS to session-based PHP web application**. A
subsequent commit adds automated HTTP/security verification and the exam testing
checklist. Use the live Git log for that commit's actual hash; no hashes or push
results are fabricated in this guide. Capture the GitHub `main` branch, its
Commits page, test results, and the app screenshot categories above.
