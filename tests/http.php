<?php
declare(strict_types=1);

// Start php -S localhost:8000 -t public separately, then run php tests/http.php.
// Only PHP's built-in HTTP streams are used; no cURL or packages are required.
$base = $argv[1] ?? 'http://localhost:8000';
if (!preg_match('#^http://(?:localhost|127\.0\.0\.1):[0-9]+$#D', $base)) {
    fwrite(STDERR, "Use a localhost HTTP URL with a port.\n");
    exit(1);
}
$checks = 0;
function verify(bool $condition, string $message): void
{
    global $checks;
    if (!$condition) { throw new RuntimeException($message); }
    $checks++;
}
function request(string $method, string $path, string &$cookie, array $post = []): array
{
    global $base;
    $headers = 'Content-Type: application/x-www-form-urlencoded' . "\r\n";
    if ($cookie !== '') { $headers .= 'Cookie: ' . $cookie . "\r\n"; }
    $options = ['method' => $method, 'header' => $headers, 'ignore_errors' => true, 'follow_location' => 0, 'timeout' => 10];
    if ($method === 'POST') { $options['content'] = http_build_query($post); }
    $html = file_get_contents($base . $path, false, stream_context_create(['http' => $options]));
    if ($html === false) { throw new RuntimeException('HTTP request failed. Start the PHP server first.'); }
    foreach ($http_response_header as $header) {
        if (preg_match('/^Set-Cookie: ([^;]+)/i', $header, $match)) { $cookie = $match[1]; }
    }
    preg_match('/\s([0-9]{3})\s/', $http_response_header[0], $status);
    return ['html' => $html, 'status' => (int) $status[1], 'headers' => implode("\n", $http_response_header)];
}
function hidden(string $html): array
{
    preg_match_all('/<input type="hidden" name="([^"]+)" value="([^"]*)">/', $html, $matches, PREG_SET_ORDER);
    $fields = [];
    foreach ($matches as $match) { $fields[$match[1]] = html_entity_decode($match[2], ENT_QUOTES, 'UTF-8'); }
    unset($fields['product']);
    return $fields;
}
function post_form(string &$cookie, string $html, string $action, array $extra = []): string
{
    $response = request('POST', '/', $cookie, $extra + ['action' => $action] + hidden($html));
    verify($response['status'] === 303, 'POST did not redirect');
    $response = request('GET', '/', $cookie);
    verify($response['status'] === 200, 'Redirect destination failed');
    return $response['html'];
}

try {
    $cookie = '';
    $initial = request('GET', '/', $cookie);
    verify($initial['status'] === 200, 'Initial page failed');
    verify(str_contains($initial['headers'], 'HttpOnly') && str_contains($initial['headers'], 'SameSite=Strict'), 'Session cookie protections missing');
    verify(str_contains($initial['headers'], 'Content-Security-Policy:') && str_contains($initial['headers'], 'Cache-Control: no-store'), 'Security headers missing');
    verify(substr_count($initial['html'], 'class="product"') === 6, 'Catalog does not show six products');
    verify(!str_contains($initial['html'], '<script'), 'Unexpected JavaScript');
    $html = post_form($cookie, $initial['html'], 'add', ['product' => 'water', 'csrf' => 'wrong']);
    verify(str_contains($html, 'Security check failed') && str_contains($html, 'Your cart is empty'), 'Bad CSRF token altered cart');
    $response = request('POST', '/', $cookie, ['action' => 'add', 'product' => 'water']);
    verify($response['status'] === 303, 'Missing CSRF request failed unexpectedly');
    $html = request('GET', '/', $cookie)['html'];
    verify(str_contains($html, 'Invalid or missing form field: csrf') && str_contains($html, 'Your cart is empty'), 'Missing CSRF bypassed');
    $otherCookie = '';
    $other = request('GET', '/', $otherCookie)['html'];
    $html = post_form($cookie, $html, 'add', ['product' => 'water', 'csrf' => hidden($other)['csrf']]);
    verify(str_contains($html, 'Security check failed'), 'Cross-session token accepted');
    $stale = $html;
    foreach (['classic', 'classic', 'lychee', 'water'] as $id) { $html = post_form($cookie, $html, 'add', ['product' => $id]); }
    verify(str_contains($html, '₱118.00') && str_contains($html, '₱193.00'), 'Sample cart totals failed');
    $html = post_form($cookie, $stale, 'add', ['product' => 'water']);
    verify(str_contains($html, 'outdated') && str_contains($html, '₱193.00'), 'Stale cart request accepted');
    $html = post_form($cookie, $html, 'increase', ['product' => 'water']);
    verify(str_contains($html, '₱213.00'), 'Increase failed over HTTP');
    $html = post_form($cookie, $html, 'decrease', ['product' => 'water']);
    $html = post_form($cookie, $html, 'remove', ['product' => 'water']);
    verify(str_contains($html, '₱173.00'), 'Remove failed over HTTP');
    $html = post_form($cookie, $html, 'add', ['product' => 'water']);
    foreach (['' => 'blank', 'abc' => 'numeric', '-1' => 'negative', '192.99' => 'Insufficient'] as $cash => $message) {
        $html = post_form($cookie, $html, 'validate', ['cash' => (string) $cash]);
        verify(str_contains($html, $message) && str_contains($html, 'role="alert"') && !isset(hidden($html)['payment_token']), 'Invalid cash not rejected: ' . $message);
    }
    $html = post_form($cookie, $html, 'validate', ['cash' => '"><script>alert(1)</script>']);
    verify(str_contains($html, '&lt;script&gt;') && !str_contains($html, '<script>'), 'Cash output not escaped');
    $html = post_form($cookie, $html, 'validate', ['cash' => ['200']]);
    verify(str_contains($html, 'Invalid or missing form field: cash'), 'Malformed POST cash not handled');
    $html = post_form($cookie, $html, 'validate', ['cash' => '200']);
    verify(str_contains($html, '₱7.00') && str_contains($html, 'Confirm this payment?') && !str_contains($html, 'id="cash"'), 'Payment review failed');
    $oldConfirmation = $html;
    $html = post_form($cookie, $html, 'edit_cash');
    verify(str_contains($html, 'id="cash"') && !isset(hidden($html)['payment_token']), 'Edit Cash did not revoke validation');
    $html = post_form($cookie, $oldConfirmation, 'confirm');
    verify(str_contains($html, 'outdated') && !str_contains($html, 'Digital receipt'), 'Old confirmation finalized');
    $html = post_form($cookie, $html, 'validate', ['cash' => '200']);
    $html = post_form($cookie, $html, 'cancel');
    verify(!str_contains($html, 'Digital receipt'), 'Cancel finalized payment');
    $html = post_form($cookie, $html, 'validate', ['cash' => '200']);
    $oldConfirmation = $html;
    $html = post_form($cookie, $html, 'confirm');
    verify(str_contains($html, 'Payment successful') && str_contains($html, 'Digital receipt') && str_contains($html, '₱200.00') && str_contains($html, '₱7.00'), 'Receipt or success message missing');
    preg_match('/MT-[A-F0-9]{16}/', $html, $number);
    verify(isset($number[0]), 'Transaction number missing');
    $html = post_form($cookie, $oldConfirmation, 'confirm');
    verify(str_contains($html, 'outdated') && str_contains($html, $number[0]), 'Duplicate confirmation changed receipt');
    $html = post_form($cookie, $html, 'add', ['product' => 'water']);
    verify(str_contains($html, 'already confirmed'), 'Completed order editable');
    $html = post_form($cookie, $html, 'new');
    verify(str_contains($html, 'Your cart is empty') && str_contains($html, 'value=""') && !str_contains($html, 'Digital receipt'), 'New Transaction failed');
    $html = post_form($cookie, $oldConfirmation, 'confirm');
    verify(str_contains($html, 'outdated') && !str_contains($html, 'Digital receipt'), 'Old transaction confirmation reused');
    $html = post_form($cookie, $html, 'add', ['product' => 'water']);
    $html = post_form($cookie, $html, 'validate', ['cash' => '20']);
    $html = post_form($cookie, $html, 'confirm');
    preg_match('/MT-[A-F0-9]{16}/', $html, $secondNumber);
    verify(isset($secondNumber[0]) && $number[0] !== $secondNumber[0], 'Second sale reference reused');
    verify(str_contains(request('GET', '/', $otherCookie)['html'], 'Your cart is empty'), 'Session data leaked to another browser');
    verify(request('GET', '/styles.css', $cookie)['status'] === 200, 'Stylesheet unavailable');
    foreach (['/src/pos.php', '/tests/run.php', '/legacy/main.py', '/README.md', '/.git/config'] as $path) {
        verify(request('GET', $path, $cookie)['status'] === 404, 'File exposed outside public directory: ' . $path);
    }
    verify(request('PUT', '/', $cookie)['status'] === 405, 'Unsupported method accepted');
    echo "PASS: $checks HTTP checks, including forms, sessions, CSRF, payment, receipts, reset, and web-root isolation.\n";
} catch (Throwable $error) {
    fwrite(STDERR, 'FAIL: ' . $error->getMessage() . "\n");
    exit(1);
}
