# Milk Tea and Beverage Shop POS

Scenario 3 of the IT415 practical exam. A small desktop POS using Python standard
libraries and Tkinter only. Products and transaction data are held in memory;
closing the app discards them. There is no database, login, or inventory system.

## Run locally

Use Python 3.10 or newer with Tkinter installed. Open a terminal in this repository
and run (use `python3` instead of `python` if that is your Python command):

```sh
python main.py
```

No pip dependencies are required. Check Tkinter with `python -m tkinter`; it
should open a small test window. If Tkinter is missing on Debian/Ubuntu, install
the `python3-tk` package for your system Python. On Windows/macOS, use a Python
installation that includes Tcl/Tk. A desktop display is required to run the GUI.

## Transaction flow (exam Section IV)

1. Browse the six product buttons, showing the exact Scenario 3 names and peso prices.
2. Click a product to add it. Repeated clicks increase its quantity. Select a
   cart row and use **+ Quantity**, **− Quantity**, or **Remove**. Decreasing a
   quantity from one removes the item.
3. Review the cart's items, quantities, unit prices, subtotals, and total. Every
   cart edit automatically updates these amounts.
4. Enter cash using digits and an optional decimal point with one or two decimal
   places, such as `200` or `200.50`. Surrounding whitespace is accepted. Currency
   symbols, thousands separators, exponents, and inputs longer than 16 characters
   are rejected. Negative, blank, non-numeric, and insufficient amounts show alerts.
5. Click **Validate & Compute** (or press Enter in the cash field). A valid
   payment displays change and enables **Confirm Payment**.
6. Click **Confirm Payment** and review the item details, total, cash, and change
   in the confirmation dialog. Choose Yes to complete the transaction or No to
   return to the order. A success message appears after completion.
7. Read the digital receipt, including its transaction reference, items,
   quantities, subtotals, total, cash, and change. **New Transaction** clears the
   cart, payment, validation, reference, and receipt for the next customer.

This flow covers all 12 features in Section V. Cart or cash changes invalidate
payment validation, including changing values and then changing them back.
Completed transactions cannot be edited or confirmed twice; start a new
transaction to continue. New Transaction also resets an unfinished order.

## Code organization

- `main.py`: Tkinter layout, cart selection, callbacks, dialogs, and receipt display.
- `pos_logic.py`: six hard-coded products, cart operations, payment validation,
  confirmation, and receipt generation. All money uses `Decimal`, constructed
  from strings. Input is parsed as data and never evaluated as Python code.
- `tests/test_pos_logic.py`: automated tests using the standard-library `unittest`.
- `tests/test_gui.py`: tests of real Tkinter widgets and keyboard events; these
  skip when a display is unavailable. Dialog responses are mocked.

`POS` keeps the current cart as product IDs and integer quantities. Its `items`
property provides the order summary, and `total` sums the item subtotals.
`validate_payment` checks cash and saves the validated amount. `confirm_payment`
requires that validation, generates a reference/receipt, and locks the transaction.

## Automated tests

From the repository directory, run:

```sh
python -m unittest discover -s tests -v
```

The 26 logic tests do not need Tkinter or a display. They cover the catalog, cart
CRUD, totals, exact payment, change including cents, invalid/unsafe inputs,
validation invalidation, required validation, completed-transaction locks,
duplicate confirmation, receipt details, and transaction reset. Without a
display, the GUI test class is reported as skipped. With a display, all 40 tests
run (26 logic tests and 14 GUI tests). The GUI tests check button callbacks,
displayed values, cash alerts, confirmation/cancellation, receipt/reset, disabled
controls, Enter-key payment validation, and cart keyboard navigation.

On Linux with Xvfb installed, an optional virtual-display test command is:

```sh
xvfb-run -a python3 -m unittest discover -s tests -v
```

Xvfb is a testing aid, not an application dependency.

## Second-stage validation results — 2026-10-13

- Baseline: all 26 existing logic tests passed.
- A real-widget regression test failed: refreshing the cart after a quantity edit
  cleared the focused row, disrupting keyboard navigation. `main.py` now restores
  the focused row along with selection, and focuses the row when adding a product.
- After the fix, **all 40 tests passed** under a temporary Xvfb display, including
  the focused-row regression and a generated Down-arrow event. The actual cloud
  command was `python3 /tmp/pos-run-display.py -m unittest discover -s tests -v`;
  the helper/extracted Xvfb were temporary files outside this repository.
- A separate run without a display passed **26 logic tests**, with the GUI class
  explicitly skipped (`OK (skipped=1)`). No calculation or payment-validation
  defects were found in the tested cases.
- `python3 -m py_compile main.py pos_logic.py tests/test_gui.py tests/test_pos_logic.py`
  and `git diff --check` passed.

### Section V coverage

| # | Required feature | Verification |
| --- | --- | --- |
| 1 | Product names and prices | Exact six-product catalog; product buttons constructed and exercised |
| 2 | Add through buttons | Real button callbacks merge repeated products into cart rows |
| 3 | Increase/decrease quantities | Logic and GUI button tests; decreasing the last unit removes it |
| 4 | Remove an item | Logic and GUI tests show an empty cart and zero total after removal |
| 5 | Automatic subtotals/total | Decimal calculations and displayed cart values checked after edits |
| 6 | Clear order summary | Treeview names, quantities, unit prices, and subtotals verified |
| 7 | Cash input | Entry text and Enter-key validation exercised |
| 8 | Invalid cash alerts | Blank, non-numeric, negative, insufficient, and unsafe forms rejected; alert content checked |
| 9 | Correct change | Exact payment, cent amounts, and ₱200 − ₱193 = ₱7 tested |
| 10 | Successful confirmation | Confirmation details, cancellation, success message request, and locked controls checked |
| 11 | Digital receipt | Reference, items, quantities, subtotals, total, cash, and change checked in model and widget |
| 12 | New Transaction | Cart, cash, validation, receipt, and reference reset; a second sale succeeds |

The GUI end-to-end test exercises the seven Section IV stages described above.
Dialog contents and requested responses are tested using mocks; native dialog
rendering and human desktop interaction are still manual checks.

## Local GUI verification

This cloud environment has no human desktop display. Real widgets were tested
using a virtual display, with dialog responses mocked. Actual Windows/macOS/Linux
appearance, native dialogs, mouse interaction, and physical keyboard behavior
must still be checked on your desktop/laptop. Use this manual check:

1. Add two Classic Milk Teas, one Lychee Fruit Tea, and one Bottled Water.
   Check subtotals of ₱118.00, ₱55.00, and ₱20.00, and a total of **₱193.00**.
2. Exercise + Quantity, − Quantity, and Remove, then restore the order above.
3. Try blank cash, `abc`, `-1`, and `192.99`; each should show an error and keep
   confirmation disabled. Enter `200.00` and validate; change should be **₱7.00**.
4. Edit the cart or cash after validation; confirmation should become disabled.
   Restore the order and cash, then validate again.
5. Choose No in the confirmation dialog and check that no receipt appears. Confirm
   again and choose Yes; check the success message and all receipt details.
6. Confirm that cart/payment controls are disabled after success. Click New
   Transaction and check that the cart, cash, change, and receipt are cleared.
   Complete a second sale and check that its reference differs.

## Git history and GitHub evidence (Section IX)

The real commits at the start of this second stage were:

| Commit | Purpose |
| --- | --- |
| `b786663` | Original README-only repository commit |
| `0102751` | Initial Tkinter interface and six-product catalog |
| `ddc384d` | Cart, Decimal payment validation/computation, confirmation, and receipts |
| `653872a` | Initial headless regression tests and execution/verification guide |

This stage adds a new commit for the keyboard-focus fix, GUI tests, and evidence
documentation. Use `git log --oneline` for its actual hash; no history is rewritten.
The working branch is `work`, and the origin is
`https://github.com/christan-dave-castillo/Abdullah-Castillo-Practical-Exam-Scenario-3.git`.
At the initial second-stage read-only check, GitHub `main` was still `b786663`;
local commits were not synchronized. Publication/verification happens after the
final commit. This historical observation is not the final synchronization status.

Capture these commands in a terminal screenshot after the final push:

```sh
git log --oneline
git status
git remote -v
git rev-parse HEAD
git ls-remote origin refs/heads/work
```

The full SHA from `git rev-parse HEAD` must match the remote `work` SHA. A clean
working tree alone does not prove synchronization. Capture the successful push
output too. To push later changes on this branch without rewriting history, use
`git push -u origin work`, then check the remote SHA again.

On GitHub, select **work** in the branch selector before taking screenshots of
the source files and **Commits** page. The default `main` branch may still show
the initial README; pushing `work` does not merge it into `main`. Submit the branch
link with your evidence, or merge it using your normal workflow if your instructor
specifically requires the application on `main`.

## Screenshot/documentation checklist (Sections VIII, IX, and X)

- **VIII — two AI uses:** capture each exact development prompt and the AI
  response, or use the response summaries in [AI_USAGE.md](AI_USAGE.md). Add your
  own evaluation (correct/partially correct/incorrect and why) and any changes you
  personally made. The two prompts are recorded; your evaluation is left for you.
- **IX — local version control:** capture `git log --oneline`, clean `git status`,
  `git remote -v`, successful push output, and matching local/remote hashes.
- **IX — GitHub:** capture the repository's **work** branch and its Commits page,
  showing interface, core functionality, and final debugging/improvement commits.
- **Working app:** capture all six products and the ₱193 sample cart; capture
  invalid-cash alerts, the validated ₱200 payment/₱7 change, the confirmation
  dialog, the success message/full receipt, and the cleared New Transaction state.
- **Tests:** capture the test command and final result. Report GUI skips honestly
  if testing without a display; do not label mocked dialogs as visual verification.

These records support your submission. Complete the local GUI checks and your
personal AI evaluation, and be ready to explain the cart, Decimal calculations,
validation invalidation, and confirmation guard in your own words.
