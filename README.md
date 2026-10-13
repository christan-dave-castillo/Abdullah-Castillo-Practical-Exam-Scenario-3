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

`POS` keeps the current cart as product IDs and integer quantities. Its `items`
property provides the order summary, and `total` sums the item subtotals.
`validate_payment` checks cash and saves the validated amount. `confirm_payment`
requires that validation, generates a reference/receipt, and locks the transaction.

## Automated tests

From the repository directory, run:

```sh
python -m unittest discover -s tests -v
```

Tests do not import the GUI or need a display. They cover the catalog, cart CRUD,
totals, exact payment, change including cents, invalid/unsafe inputs, validation
invalidation, required validation, completed-transaction locks, duplicate
confirmation, receipt details, and transaction reset.

## Local GUI verification

This cloud environment has Tkinter but no desktop display. Headless logic tests
can run here; widget appearance, mouse/keyboard behavior, and dialogs must be
verified on a desktop/laptop. Use this manual check:

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

For exam submission, Sections VIII–X of the supplied PDF additionally request
your actual AI prompts and personal evaluation, desktop screenshots, and GitHub
commit/push evidence. Keep those records yourself; automated test results do not
replace your explanation of the code or local GUI checks.
