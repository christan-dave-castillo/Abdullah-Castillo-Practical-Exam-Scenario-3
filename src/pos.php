<?php
declare(strict_types=1);

// All prices and calculations use integer centavos, never floating point.
const PRODUCTS = [
    'classic' => ['name' => 'Classic Milk Tea (Regular)', 'price' => 5900],
    'wintermelon' => ['name' => 'Wintermelon Milk Tea (Regular)', 'price' => 6500],
    'taro' => ['name' => 'Taro Milk Tea (Regular)', 'price' => 6500],
    'lychee' => ['name' => 'Fruit Tea — Lychee (Regular)', 'price' => 5500],
    'brown_sugar' => ['name' => 'Brown Sugar Milk Tea (Regular)', 'price' => 6900],
    'water' => ['name' => 'Bottled Water', 'price' => 2000],
];

function money(int $centavos): string
{
    $pesos = (string) intdiv($centavos, 100);
    $pesos = preg_replace('/\B(?=(\d{3})+(?!\d))/', ',', $pesos);
    return '₱' . $pesos . '.' . str_pad((string) ($centavos % 100), 2, '0', STR_PAD_LEFT);
}

function escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function new_order(): array
{
    return [
        'id' => bin2hex(random_bytes(16)), 'revision' => 0, 'cart' => [],
        'cash_text' => '', 'payment' => null, 'receipt' => null,
    ];
}

function cart_items(array $cart): array
{
    $items = [];
    foreach ($cart as $id => $quantity) {
        $product = PRODUCTS[$id];
        $items[] = $product + ['quantity' => $quantity, 'subtotal' => $product['price'] * $quantity];
    }
    return $items;
}

function cart_total(array $cart): int
{
    return array_sum(array_column(cart_items($cart), 'subtotal'));
}

function field(array $post, string $name): string
{
    if (!isset($post[$name]) || !is_string($post[$name])) {
        throw new InvalidArgumentException('Invalid or missing form field: ' . $name . '. Reload and try again.');
    }
    return $post[$name];
}

function parse_cash(string $text): int
{
    $text = trim($text);
    if ($text === '') {
        throw new InvalidArgumentException('Cash is blank. Please enter a cash amount.');
    }
    // A bounded amount is safe even on a 32-bit PHP installation.
    if (strlen($text) > 12) {
        throw new InvalidArgumentException('Cash amount is too long. Maximum cash is ₱1,000,000.00.');
    }
    if (preg_match('/^-[0-9]+(?:\.[0-9]+)?$/D', $text)) {
        throw new InvalidArgumentException('Cash cannot be negative. Enter a non-negative amount.');
    }
    if (!preg_match('/^[0-9]+(?:\.[0-9]{1,2})?$/D', $text)) {
        throw new InvalidArgumentException('Cash must be numeric: use digits and up to two decimal places.');
    }
    [$whole, $fraction] = array_pad(explode('.', $text, 2), 2, '');
    if ((int) $whole > 1000000) {
        throw new InvalidArgumentException('Maximum cash is ₱1,000,000.00.');
    }
    $cash = (int) $whole * 100 + (int) str_pad($fraction, 2, '0');
    if ($cash > 100000000) {
        throw new InvalidArgumentException('Maximum cash is ₱1,000,000.00.');
    }
    return $cash;
}

// The session lock serializes requests. The order ID and revision reject stale tabs.
function handle_action(array &$order, array $post): string
{
    if (!hash_equals($order['id'], field($post, 'order_id'))
        || (string) $order['revision'] !== field($post, 'revision')) {
        throw new InvalidArgumentException('This form is outdated. Review the current order and try again.');
    }
    $action = field($post, 'action');
    if ($action === 'new') {
        $order = new_order();
        return 'New transaction started. Cart, cash, and receipt cleared.';
    }
    if ($order['receipt'] !== null) {
        throw new InvalidArgumentException('Payment is already confirmed. Start a New Transaction.');
    }
    if (in_array($action, ['add', 'increase', 'decrease', 'remove'], true)) {
        $id = field($post, 'product');
        if (!isset(PRODUCTS[$id])) {
            throw new InvalidArgumentException('Unknown product. Choose a listed product.');
        }
        if ($action !== 'add' && !isset($order['cart'][$id])) {
            throw new InvalidArgumentException('That item is no longer in the cart.');
        }
        $quantity = $order['cart'][$id] ?? 0;
        if ($action === 'add' || $action === 'increase') {
            if ($quantity >= 99) {
                throw new InvalidArgumentException('Maximum quantity is 99 per product.');
            }
            $order['cart'][$id] = $quantity + 1;
        } elseif ($action === 'remove' || $quantity === 1) {
            unset($order['cart'][$id]);
        } else {
            $order['cart'][$id] = $quantity - 1;
        }
        $order['payment'] = null;
        $order['revision']++;
        return 'Cart updated. Validate cash again before confirming payment.';
    }
    if ($action === 'edit_cash' || $action === 'cancel') {
        $order['payment'] = null;
        $order['revision']++;
        return 'Payment confirmation cancelled. Edit the order or cash and validate again.';
    }
    if ($action === 'validate') {
        // Clear earlier validation even when this attempt fails or is malformed.
        $order['payment'] = null;
        $order['revision']++;
        $order['cash_text'] = '';
        $cashText = field($post, 'cash');
        $order['cash_text'] = substr($cashText, 0, 32);
        if (!$order['cart']) {
            throw new InvalidArgumentException('Add at least one product before entering payment.');
        }
        $cash = parse_cash($cashText);
        $total = cart_total($order['cart']);
        if ($cash < $total) {
            throw new InvalidArgumentException('Insufficient payment. Please enter at least ' . money($total) . '.');
        }
        $order['payment'] = [
            'cash' => $cash, 'total' => $total, 'change' => $cash - $total,
            'token' => bin2hex(random_bytes(32)),
        ];
        return 'Cash validated. Review the order, cash, and change, then confirm payment.';
    }
    if ($action === 'confirm') {
        $payment = $order['payment'];
        if ($payment === null || !hash_equals($payment['token'], field($post, 'payment_token'))
            || $payment['total'] !== cart_total($order['cart'])) {
            throw new InvalidArgumentException('Validate the current cart and cash before confirming payment.');
        }
        // Build the full snapshot before locking the transaction.
        $receipt = [
            'number' => 'MT-' . strtoupper(bin2hex(random_bytes(8))),
            'items' => cart_items($order['cart']), 'total' => $payment['total'],
            'cash' => $payment['cash'], 'change' => $payment['change'],
        ];
        $order['receipt'] = $receipt;
        $order['payment'] = null;
        $order['revision']++;
        return 'Payment successful. Transaction confirmed and receipt generated.';
    }
    throw new InvalidArgumentException('Unknown action. Use the buttons on this page.');
}
