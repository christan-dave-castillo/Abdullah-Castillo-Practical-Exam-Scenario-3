# AI-assisted development record — IT415 Section VIII

The first two records below are historical Python/Tkinter development evidence.
The active application is now PHP; see **Use 3** and the current README.

Tool: Codex in the GitHub-connected cloud environment.

The two development request texts below are copied from this conversation.
Upload metadata and earlier environment-onboarding messages are omitted. Purpose
and response summaries describe work actually performed. The student's personal
evaluation and personal modifications must be completed by the student after
reviewing/testing; this document does not invent them.

## Use 1 — initial application development

Purpose: build a minimal Scenario 3 Python/Tkinter POS with testable logic and
meaningful interface/core commits.

Exact development prompt:

```text
### 1. CONTEXT

I am building Scenario 3: Milk Tea and Beverage Shop POS for a 150-minute IT415 practical exam. You are working in my GitHub-connected Codex Cloud environment. The application must run on a desktop/laptop using Python and Tkinter.

### 2. OBJECTIVE

Create a simple, functional, beginner-friendly POS following the examination's Section IV (7-step transaction flow) and Section V (12 required features).

### 3. REQUIREMENTS

- Display six products: Classic Milk Tea (Regular) ₱59, Wintermelon Milk Tea (Regular) ₱65, Taro Milk Tea (Regular) ₱65, Fruit Tea — Lychee (Regular) ₱55, Brown Sugar Milk Tea (Regular) ₱69, and Bottled Water ₱20.
- Product buttons add items to the cart.
- Support cart CRUD: add, view, increase/decrease quantity, and remove.
- Automatically update item subtotals and total.
- Accept cash input; reject blank, non-numeric, negative, and insufficient amounts with clear alerts.
- Calculate change, validate payment, then allow payment confirmation.
- Show a success message and digital receipt containing transaction reference, items, quantities, subtotals, total, cash paid, and change.
- New Transaction must clear the cart, payment, and receipt.
- Prevent duplicate confirmations and invalidate payment validation when cart or cash changes.
- Include basic input security and error handling.

### 4. CONSTRAINTS

- Use Python standard libraries and Tkinter only.
- Keep the application minimal, readable, and easy to explain.
- Use hard-coded products and in-memory transaction data. No database, login, inventory, or unnecessary features.
- Use Decimal for money calculations.
- Separate testable POS logic from GUI code if helpful.
- Cloud environments may not support displaying Tkinter windows. Perform headless logic tests and clearly report any GUI testing limitations.
- Work in the existing GitHub repository. Do not overwrite unrelated files or initialize a nested repository.

### 5. EXPECTED OUTPUT

- Working desktop POS source code.
- Simple, organized interface.
- README with local execution and testing instructions.
- Automated tests for the core calculations and validation.
- Meaningful Git commits during implementation: initial interface, then core functionality.
- Brief summary of implemented features, tests performed, and anything requiring local verification.
```

AI response summary: created `main.py`, `pos_logic.py`, 26 headless tests, a
README, and `.gitignore`. Implemented six products, cart CRUD, Decimal totals and
change, strict cash parsing, validation invalidation, confirmation guards,
receipt generation, and transaction reset. Created actual commits `0102751`,
`ddc384d`, and `653872a`. All 26 tests passed. Reported the missing display and
that the commits had not been pushed. GUI interaction was not verified in this
first stage.

Student's evaluation: **[Complete: correct, partially correct, or incorrect;
explain your own test results and what you understand about the code.]**

Modifications you personally made: **[Record actual changes, or state that you
made none. Do not describe Codex's changes as your own manual changes.]**

## Use 2 — testing, debugging, and finalization

Purpose: verify the existing POS and exam requirements, debug real failures,
inspect Git/GitHub state, and provide evidence instructions.

Exact development prompt:

```text
### 1. CONTEXT

The first development prompt for my IT415 Milk Tea POS has already been executed in this GitHub-connected Codex Cloud environment. This is my second AI-assisted development stage.

### 2. OBJECTIVE

Test, debug, and finalize the existing application while ensuring compliance with Sections IV, V, VIII, and IX of my practical exam.

### 3. REQUIREMENTS

- Verify all 12 required POS features and the 7-step transaction flow.
- Test cart CRUD, automatic totals, cash validation, change calculation, payment confirmation, receipt, and transaction reset.
- Fix discovered bugs, handle invalid inputs securely, and provide clear alerts.
- Inspect actual Git history using `git log --oneline`, `git status`, and `git remote -v`.
- Verify that the repository contains meaningful commits for initial interface, core functionality, and final validation/improvements.
- Update the README and provide test results.
- Explain how to capture evidence of the commits, GitHub synchronization, and working application for my documentation.

### 4. CONSTRAINTS

- Preserve the existing Python/Tkinter application.
- Do not rebuild unnecessarily or introduce advanced features.
- Do not fabricate commits, rewrite history, or claim GitHub synchronization without verification.
- Make a genuine final debugging/improvement commit after implementing changes.
- Report any GUI features that cannot be tested in the cloud environment.

### 5. EXPECTED OUTPUT

- Tested and corrected POS application.
- Actual Git history and commit hashes.
- GitHub synchronization status.
- Summary of bugs fixed and tests performed.
- Screenshot checklist for Parts VIII and IX.
- Any remaining steps I must perform manually.
```

AI response summary: reran the 26 logic tests and inspected the actual Git
history/status/remotes and GitHub refs. Added 14 tests of real Tkinter widgets
using a temporary virtual display. Found a failing keyboard-focus test after
cart quantity edits, then preserved the focused cart row during refresh and
focused newly added rows. All 40 tests passed after the fix. A separate run
without a display passed the 26 logic tests and explicitly skipped the GUI class.
Updated README coverage, test results, and screenshot instructions. Final Git
commit and synchronization evidence must be taken from the actual terminal/GitHub
output described in the README; this record does not assume a successful push.

Student's evaluation: **[Complete after checking the fix, running tests, and
performing the local GUI checklist. Explain why you accept or reject the output.]**

Modifications you personally made: **[Record actual changes, or state that you
made none. Identify any adjustments made after this second response.]**

## Evidence to attach

- The two prompts and responses/screenshots, plus your completed evaluations.
- Test output showing the command, counts, and any skips.
- Desktop screenshots from the README checklist, especially validation and receipt.
- Actual final commit history, push output, and matching local/remote branch SHA.

Be prepared to explain `POS.add`, `total`, `validate_payment`, and
`confirm_payment`, and why changing the cart/cash requires revalidation.

## Use 3 — PHP web conversion (2026-10-13)

Tool: Codex desktop in the existing local project folder. PHP 8.3.13 was available.

### Prompt screenshot categories

Capture the actual five-part conversion request and response in the chat manually.
These categories summarize the request; they are not a verbatim prompt transcript.

- **Context:** existing Milk Tea POS; IT415 practical exam, Scenario 3.
- **Objective:** convert the desktop application to a simple PHP web POS.
- **Requirements:** six exact products; cart CRUD; total/cash/change; confirmation,
  receipt/reset; alerts, validation, sessions, CSRF, escaped output, duplicate guards.
- **Constraints:** PHP/HTML/CSS only; no JavaScript, database, framework, or external
  dependencies; integer centavos; preserve Git history and make genuine commits.
- **Expected Output:** working app, local setup, test checklist, actual commit
  history, synchronization status, and remaining manual browser checks.

### Actual response and test evidence

Recovered the folder's missing Git metadata from the original GitHub repository,
starting at `975ed8d`; the downloaded files matched the recovered HEAD. Preserved
the original Python files in `legacy/`. Added the PHP catalog/cart/payment logic,
session forms, responsive CSS, confirmation review, digital receipt, and reset.
The first conversion commit is `6a19724`; subsequent verification history is
available in the actual Git log.

Added **36 passing PHP logic tests** and **100 passing HTTP checks**. These include
the ₱193 sample sale, ₱200 cash and ₱7 change; invalid cash; failed/revoked payment
validation; stale and duplicate requests; receipts/reset; separate sessions; CSRF;
escaped input; and web-root isolation. Browser inspection was declined, so visual
rendering, keyboard/mouse behavior, and print layout remain manual checks. Final
GitHub synchronization evidence must come from actual push and matching SHA output.

### Student evaluation and screenshots

Student's evaluation: **[Complete after running the PHP tests and manual browser
checklist. Explain what you verified and any limitations.]**

Personal changes: **[Record only changes you actually made.]**

Screenshot categories: **products/cart**, **invalid cash alerts**, **validated
payment and confirmation**, **successful receipt**, **New Transaction**, **PHP test
results**, and **Git history/GitHub synchronization**. See the current README for
the twelve-feature checklist. Be ready to explain integer centavos, PHP sessions,
CSRF, order revisions, and why Edit Cash revokes payment validation.
