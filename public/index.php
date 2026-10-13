<?php
declare(strict_types=1);
require dirname(__DIR__) . '/src/pos.php';

ini_set('session.use_strict_mode', '1');
ini_set('session.use_only_cookies', '1');
session_name('milk_tea_pos');
session_set_cookie_params([
    'httponly' => true, 'samesite' => 'Strict',
    'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
    'path' => '/',
]);
header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
header("Content-Security-Policy: default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
if (!session_start()) {
    http_response_code(503);
    exit('Unable to start a secure session. Check PHP session storage and reload.');
}
$_SESSION['order'] ??= new_order();
$_SESSION['csrf'] ??= bin2hex(random_bytes(32));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $token = field($_POST, 'csrf');
        if (!hash_equals($_SESSION['csrf'], $token)) {
            throw new InvalidArgumentException('Security check failed. Reload the page and try again.');
        }
        $message = handle_action($_SESSION['order'], $_POST);
        $_SESSION['flash'] = ['type' => 'success', 'message' => $message];
    } catch (InvalidArgumentException $error) {
        $_SESSION['flash'] = ['type' => 'error', 'message' => $error->getMessage()];
    } catch (Throwable $error) {
        error_log('POS request failed: ' . get_class($error));
        $_SESSION['flash'] = ['type' => 'error', 'message' => 'Unable to process this request. Review the order and try again.'];
    }
    session_write_close();
    header('Location: /', true, 303);
    exit;
}
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    header('Allow: GET, POST');
    http_response_code(405);
    exit('Method not allowed.');
}
$order = $_SESSION['order'];
$csrf = $_SESSION['csrf'];
$flash = $_SESSION['flash'] ?? null;
unset($_SESSION['flash']);
session_write_close();
$closed = $order['receipt'] !== null;
$payment = $order['payment'];

function form_fields(): void
{
    global $order, $csrf;
    echo '<input type="hidden" name="csrf" value="' . escape($csrf) . '">';
    echo '<input type="hidden" name="order_id" value="' . escape($order['id']) . '">';
    echo '<input type="hidden" name="revision" value="' . $order['revision'] . '">';
}
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Milk Tea &amp; Beverage Shop POS</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
<main>
    <header class="topbar">
        <div><p class="eyebrow">IT415 · Scenario 3</p><h1>Milk Tea &amp; Beverage Shop</h1><p>Choose products, review the order, and accept cash.</p></div>
        <form method="post" action="/">
            <?php form_fields(); ?>
            <button name="action" value="new" class="secondary">New Transaction</button>
        </form>
    </header>
    <?php if ($flash): ?>
        <div class="notice <?= escape($flash['type']) ?>" role="<?= $flash['type'] === 'error' ? 'alert' : 'status' ?>"><?= escape($flash['message']) ?></div>
    <?php endif; ?>
    <div class="layout">
        <section class="panel" aria-labelledby="products-heading">
            <h2 id="products-heading">1. Choose products</h2>
            <div class="products">
                <?php foreach (PRODUCTS as $id => $product): ?>
                    <form method="post" action="/">
                        <?php form_fields(); ?>
                        <input type="hidden" name="product" value="<?= escape($id) ?>">
                        <button class="product" name="action" value="add" <?= $closed ? 'disabled' : '' ?>>
                            <span><?= escape($product['name']) ?></span><strong><?= money($product['price']) ?></strong><small>Add to cart</small>
                        </button>
                    </form>
                <?php endforeach; ?>
            </div>
        </section>
        <section class="panel" aria-labelledby="cart-heading">
            <h2 id="cart-heading">2. Review order</h2>
            <div class="table-wrap"><table>
                <thead><tr><th scope="col">Item</th><th scope="col">Qty</th><th scope="col">Price</th><th scope="col">Subtotal</th><th scope="col">Actions</th></tr></thead>
                <tbody>
                <?php if (!$order['cart']): ?><tr><td colspan="5" class="empty">Your cart is empty. Choose a product to begin.</td></tr><?php endif; ?>
                <?php foreach ($order['cart'] as $id => $quantity): $product = PRODUCTS[$id]; ?>
                    <tr><td><?= escape($product['name']) ?></td><td><?= $quantity ?></td><td class="amount"><?= money($product['price']) ?></td><td class="amount"><?= money($product['price'] * $quantity) ?></td>
                        <td><form class="cart-actions" method="post" action="/">
                            <?php form_fields(); ?>
                            <input type="hidden" name="product" value="<?= escape($id) ?>">
                            <button name="action" value="decrease" aria-label="Decrease <?= escape($product['name']) ?> quantity" <?= $closed ? 'disabled' : '' ?>>−</button>
                            <button name="action" value="increase" aria-label="Increase <?= escape($product['name']) ?> quantity" <?= $closed ? 'disabled' : '' ?>>+</button>
                            <button name="action" value="remove" class="remove" aria-label="Remove <?= escape($product['name']) ?>" <?= $closed ? 'disabled' : '' ?>>Remove</button>
                        </form></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table></div>
            <p class="total"><span>Total</span><strong><?= money(cart_total($order['cart'])) ?></strong></p>
            <h2>3. Cash payment</h2>
            <?php if ($closed): ?>
                <p>Payment confirmed. Start a New Transaction for the next customer.</p>
            <?php elseif ($payment !== null): ?>
                <div class="confirmation">
                    <h3>Confirm this payment?</h3>
                    <p>Review the items above before finalizing.</p>
                    <dl><dt>Total</dt><dd><?= money($payment['total']) ?></dd><dt>Cash paid</dt><dd><?= money($payment['cash']) ?></dd><dt>Change</dt><dd><?= money($payment['change']) ?></dd></dl>
                    <form method="post" action="/" class="confirmation-actions">
                        <?php form_fields(); ?>
                        <input type="hidden" name="payment_token" value="<?= escape($payment['token']) ?>">
                        <button name="action" value="confirm">Confirm Payment</button>
                        <button name="action" value="edit_cash" class="secondary">Edit Cash</button>
                        <button name="action" value="cancel" class="secondary">Cancel Confirmation</button>
                    </form>
                </div>
            <?php else: ?>
                <form method="post" action="/" class="payment-form">
                    <?php form_fields(); ?>
                    <label for="cash">Cash received (₱)</label>
                    <p id="cash-help">Use digits and up to two decimal places, e.g. 200.50. Maximum ₱1,000,000.00.</p>
                    <div class="cash-controls"><input id="cash" name="cash" type="text" inputmode="decimal" maxlength="32" autocomplete="off" aria-describedby="cash-help" value="<?= escape($order['cash_text']) ?>">
                    <button name="action" value="validate">Validate &amp; Compute</button></div>
                </form>
            <?php endif; ?>
        </section>
    </div>
    <?php if ($closed): $receipt = $order['receipt']; ?>
        <section class="panel receipt" aria-labelledby="receipt-heading">
            <h2 id="receipt-heading">Digital receipt</h2><p>Milk Tea &amp; Beverage Shop</p>
            <p><strong>Transaction number:</strong> <?= escape($receipt['number']) ?></p>
            <div class="table-wrap"><table>
                <thead><tr><th scope="col">Item</th><th scope="col">Qty</th><th scope="col">Unit price</th><th scope="col">Subtotal</th></tr></thead>
                <tbody><?php foreach ($receipt['items'] as $item): ?>
                    <tr><td><?= escape($item['name']) ?></td><td><?= $item['quantity'] ?></td><td><?= money($item['price']) ?></td><td><?= money($item['subtotal']) ?></td></tr>
                <?php endforeach; ?></tbody>
            </table></div>
            <dl><dt>Total</dt><dd><?= money($receipt['total']) ?></dd><dt>Cash paid</dt><dd><?= money($receipt['cash']) ?></dd><dt>Change</dt><dd><?= money($receipt['change']) ?></dd></dl>
            <p>Payment confirmed. Thank you!</p>
        </section>
    <?php endif; ?>
    <footer>Session-only transactions · No sales database · Start a New Transaction to clear this order.</footer>
</main>
</body>
</html>
