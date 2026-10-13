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
