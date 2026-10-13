<?php
declare(strict_types=1);
require dirname(__DIR__) . '/src/pos.php';

$passed = 0;
function check(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}
function rejects(callable $operation, string $message): void
{
    try {
        $operation();
    } catch (InvalidArgumentException $error) {
        check(str_contains($error->getMessage(), $message), 'Unexpected error: ' . $error->getMessage());
        return;
    }
    throw new RuntimeException('Expected rejection: ' . $message);
}
function submit(array &$order, string $action, array $fields = []): string
{
    return handle_action($order, $fields + [
        'order_id' => $order['id'], 'revision' => (string) $order['revision'], 'action' => $action,
    ]);
}
function sample_order(): array
{
    $order = new_order();
    foreach (['classic', 'classic', 'lychee', 'water'] as $id) {
        submit($order, 'add', ['product' => $id]);
    }
    return $order;
}
function test(string $name, callable $operation): void
{
    global $passed;
    $operation();
    $passed++;
    echo "PASS $name\n";
}

try {
    test('Exact six-product exam catalog', function () {
        check(array_column(PRODUCTS, 'name') === [
            'Classic Milk Tea (Regular)', 'Wintermelon Milk Tea (Regular)', 'Taro Milk Tea (Regular)',
            'Fruit Tea — Lychee (Regular)', 'Brown Sugar Milk Tea (Regular)', 'Bottled Water',
        ], 'Product names differ');
        check(array_column(PRODUCTS, 'price') === [5900, 6500, 6500, 5500, 6900, 2000], 'Prices differ');
    });
    test('Cart CRUD and automatic subtotals', function () {
        $order = new_order();
        submit($order, 'add', ['product' => 'classic']);
        submit($order, 'increase', ['product' => 'classic']);
        check(cart_items($order['cart'])[0]['subtotal'] === 11800, 'Incorrect subtotal');
        submit($order, 'decrease', ['product' => 'classic']);
        check(cart_total($order['cart']) === 5900, 'Incorrect total');
        submit($order, 'remove', ['product' => 'classic']);
        check($order['cart'] === [] && cart_total($order['cart']) === 0, 'Remove failed');
        submit($order, 'add', ['product' => 'water']);
        submit($order, 'decrease', ['product' => 'water']);
        check($order['cart'] === [], 'Decrease at one must remove');
    });
    test('All products and server-controlled prices', function () {
        $order = new_order();
        foreach (array_keys(PRODUCTS) as $id) {
            submit($order, 'add', ['product' => $id, 'price' => '1']);
        }
        check(cart_total($order['cart']) === 33300, 'Client-supplied price accepted');
    });
    test('Invalid products, missing rows, malformed fields, and unknown actions', function () {
        $order = new_order();
        rejects(function () use (&$order) { submit($order, 'add', ['product' => 'unknown']); }, 'Unknown product');
        rejects(function () use (&$order) { submit($order, 'remove', ['product' => 'water']); }, 'no longer');
        rejects(function () use (&$order) { submit($order, 'add', ['product' => ['water']]); }, 'Invalid or missing');
        rejects(function () use (&$order) { submit($order, 'bad_action'); }, 'Unknown action');
        check($order['cart'] === [], 'Invalid actions changed cart');
    });
    test('Quantity limit', function () {
        $order = new_order();
        for ($i = 0; $i < 99; $i++) { submit($order, 'add', ['product' => 'water']); }
        rejects(function () use (&$order) { submit($order, 'increase', ['product' => 'water']); }, 'Maximum quantity');
        check($order['cart']['water'] === 99, 'Limit bypassed');
    });
    test('Empty cart cannot be paid or confirmed', function () {
        $order = new_order();
        rejects(function () use (&$order) { submit($order, 'validate', ['cash' => '200']); }, 'Add at least');
        rejects(function () use (&$order) { submit($order, 'confirm'); }, 'Validate the current');
    });
    foreach (['' => 'blank', ' ' => 'blank', 'abc' => 'numeric', '-1' => 'negative', '-0.01' => 'negative',
        '0' => 'Insufficient', '192.99' => 'Insufficient', 'NaN' => 'numeric', 'Infinity' => 'numeric',
        '1e3' => 'numeric', '₱200' => 'numeric', '1,000' => 'numeric', '200.001' => 'numeric',
        '２００' => 'numeric', '<script>' => 'numeric', str_repeat('9', 30) => 'too long',
        '1000000.01' => 'Maximum cash', '1000001' => 'Maximum cash'] as $text => $message) {
        test('Reject invalid cash ' . json_encode((string) $text), function () use ($text, $message) {
            $order = sample_order();
            submit($order, 'validate', ['cash' => '200']);
            rejects(function () use (&$order, $text) { submit($order, 'validate', ['cash' => (string) $text]); }, $message);
            check($order['payment'] === null && $order['receipt'] === null, 'Old validation survived');
        });
    }
    test('Malformed cash clears prior validation', function () {
        $order = sample_order();
        submit($order, 'validate', ['cash' => '200']);
        rejects(function () use (&$order) { submit($order, 'validate', ['cash' => ['200']]); }, 'Invalid or missing');
        check($order['payment'] === null, 'Malformed input preserved validation');
    });
    test('Integer centavos, spaces, exact payment, and maximum cash', function () {
        check(parse_cash(' 200.5 ') === 20050, 'Fraction or whitespace parsed incorrectly');
        check(parse_cash('1000000.00') === 100000000, 'Maximum amount failed');
        check(money(123456789) === '₱1,234,567.89', 'Money formatting failed');
        $order = sample_order();
        submit($order, 'validate', ['cash' => '193']);
        check($order['payment']['change'] === 0, 'Exact payment should have zero change');
        submit($order, 'validate', ['cash' => '200.50']);
        check($order['payment']['change'] === 750, 'Centavo change failed');
    });
    foreach (['add', 'increase', 'decrease', 'remove'] as $action) {
        test("$action invalidates payment even if total is restored", function () use ($action) {
            $order = sample_order();
            $originalCart = $order['cart'];
            submit($order, 'validate', ['cash' => '200']);
            $oldConfirmation = ['order_id' => $order['id'], 'revision' => (string) $order['revision'], 'action' => 'confirm', 'payment_token' => $order['payment']['token']];
            submit($order, $action, ['product' => 'classic']);
            if ($action === 'remove') {
                submit($order, 'add', ['product' => 'classic']);
                submit($order, 'add', ['product' => 'classic']);
            } else {
                $reverse = ($action === 'decrease') ? 'increase' : 'decrease';
                submit($order, $reverse, ['product' => 'classic']);
            }
            // Removing and adding can change insertion order; quantities must match.
            check($order['cart'] == $originalCart, 'Cart was not restored');
            check($order['payment'] === null, 'Cart change preserved payment');
            rejects(function () use (&$order, $oldConfirmation) { handle_action($order, $oldConfirmation); }, 'outdated');
            rejects(function () use (&$order) { submit($order, 'confirm'); }, 'Validate the current');
        });
    }
    foreach (['edit_cash', 'cancel'] as $action) {
        test("$action revokes confirmation", function () use ($action) {
            $order = sample_order();
            submit($order, 'validate', ['cash' => '200']);
            $oldToken = $order['payment']['token'];
            submit($order, $action);
            check($order['payment'] === null, 'Payment not revoked');
            submit($order, 'validate', ['cash' => '200']);
            rejects(function () use (&$order, $oldToken) { submit($order, 'confirm', ['payment_token' => $oldToken]); }, 'Validate the current');
        });
    }
    test('Stale form cannot edit a newer cart', function () {
        $order = sample_order();
        $stale = ['order_id' => $order['id'], 'revision' => (string) $order['revision'], 'action' => 'add', 'product' => 'water'];
        submit($order, 'add', ['product' => 'water']);
        rejects(function () use (&$order, $stale) { handle_action($order, $stale); }, 'outdated');
        check($order['cart']['water'] === 2, 'Stale form duplicated item');
    });
    test('Complete seven-step sale, receipt snapshot, duplicate and locked order guards', function () {
        $order = sample_order();
        check(cart_total($order['cart']) === 19300, 'Sample order total failed');
        submit($order, 'validate', ['cash' => '200']);
        check($order['payment']['change'] === 700 && $order['receipt'] === null, 'Validation finalized early');
        $confirmation = ['order_id' => $order['id'], 'revision' => (string) $order['revision'], 'action' => 'confirm', 'payment_token' => $order['payment']['token']];
        handle_action($order, $confirmation);
        $receipt = $order['receipt'];
        check((bool) preg_match('/^MT-[A-F0-9]{16}$/D', $receipt['number']), 'Missing transaction number');
        check($receipt['items'][0]['quantity'] === 2 && $receipt['items'][0]['subtotal'] === 11800, 'Incorrect receipt items');
        check(count($receipt['items']) === 3 && $receipt['total'] === 19300 && $receipt['cash'] === 20000 && $receipt['change'] === 700, 'Incorrect receipt totals');
        rejects(function () use (&$order, $confirmation) { handle_action($order, $confirmation); }, 'outdated');
        foreach (['add', 'validate', 'edit_cash', 'confirm'] as $action) {
            rejects(function () use (&$order, $action) { submit($order, $action); }, 'already confirmed');
        }
        check($order['receipt'] === $receipt, 'Receipt changed after completion');
        submit($order, 'new');
        check($order['cart'] === [] && $order['cash_text'] === '' && $order['payment'] === null && $order['receipt'] === null, 'New transaction did not clear all data');
        rejects(function () use (&$order, $confirmation) { handle_action($order, $confirmation); }, 'outdated');
        submit($order, 'add', ['product' => 'water']);
        submit($order, 'validate', ['cash' => '20']);
        submit($order, 'confirm', ['payment_token' => $order['payment']['token']]);
        check($order['receipt']['number'] !== $receipt['number'], 'Transaction number reused');
    });
    test('New Transaction clears unfinished payment', function () {
        $order = sample_order();
        submit($order, 'validate', ['cash' => '200']);
        submit($order, 'new');
        check($order['payment'] === null && $order['cash_text'] === '' && $order['cart'] === [], 'Reset failed');
    });
    test('Escape HTML in user-supplied strings', function () {
        check(escape('<script>"&\'') === '&lt;script&gt;&quot;&amp;&#039;', 'HTML escaping failed');
    });
    echo "\n$passed tests passed.\n";
} catch (Throwable $error) {
    fwrite(STDERR, "FAIL: {$error->getMessage()}\n");
    exit(1);
}
