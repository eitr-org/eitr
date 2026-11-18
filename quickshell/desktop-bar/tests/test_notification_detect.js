const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const detect = {};
vm.createContext(detect);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../NotificationDetect.js'), 'utf8').replace(/^\.pragma library\s*/m, ''), detect);

// Positives across all 8 UI languages (en, pt_BR, es, de, fr, ja, zh_CN, ko).
const positiveCodes = [
    ['Your code is 482913', '482913'],
    ['verification code: 12-34-56', '123456'],
    ['OTP 5521', '5521'],
    ['código 123456', '123456'],
    ['482 913 is your one-time passcode', '482913'],
    ['G-482913 is your Google verification code', '482913'],
    ['Your 2FA code is 99887766', '99887766'],
    ['PIN: 4321', '4321'],
    ['482913 is your Instagram verification code', '482913'],
    ['Order #123456 shipped. Verification code: 482913', '482913'],
    ['Your code is 482913. Support: 555-019-2834', '482913'],
    // pt_BR
    ['Seu código é 123456', '123456'],
    ['Código de verificação: 98-76-54', '987654'],
    ['Autenticação em dois fatores: 445566', '445566'],
    ['Senha única: 7788', '7788'],
    // es
    ['Tu código de verificación es 654-321', '654321'],
    ['Clave de verificación: 112233', '112233'],
    // de
    ['Ihr Bestätigungscode lautet 654321', '654321'],
    ['Verifizierungscode: 12 34 56', '123456'],
    ['Einmalpasswort: 889900', '889900'],
    ['Sicherheitscode 443322', '443322'],
    ['Prüfziffer: 5566', '5566'],
    // fr
    ['Votre code de vérification : 77-88-99', '778899'],
    ['Code à usage unique 334455', '334455'],
    ['Authentification à deux facteurs : 667788', '667788'],
    // ja
    ['認証コード: 482913', '482913'],
    ['確認コードは123456です', '123456'],
    ['ワンタイムパスワード 998877', '998877'],
    ['暗証番号：4321', '4321'],
    // zh_CN
    ['您的验证码是123456', '123456'],
    ['校验码：65-43-21', '654321'],
    ['动态口令 889900', '889900'],
    // ko
    ['인증번호는 482913입니다', '482913'],
    ['보안 코드: 12 34 56', '123456'],
    ['일회용 비밀번호 5521', '5521'],
];
for (const [text, expected] of positiveCodes) {
    assert.equal(detect.detectCode(text), expected, text);
}

// Summary + body scan combines for code, uses body only for links.
const combined = detect.scan('Verification code', '482913\nSign in at https://example.com/auth');
assert.equal(combined.code, '482913');
assert.equal(combined.link, 'https://example.com/auth');
assert.equal(detect.scan('Visit https://summary.example', 'No link here').link, '');

// Negatives: non-code prose, order numbers, ports, times, prices, years, phone numbers, URL numbers.
const negativeCodes = [
    'Build 482913 passed',
    '412 passed',
    'Order #482913 confirmed',
    'Order 482913 shipped',
    'Verify order #482913',
    'Pedido #987654 confirmado',
    'Bestellung 123456 bestätigt',
    'Listening on port 8080',
    'Verification server listening on port 8080',
    'Auth service at localhost:8080',
    'Verify http://127.0.0.1:8080/login',
    'Visit https://example.com/verify/482913',
    'Claude Code 2.1.4000',
    'VS Code 18500',
    'Error code 4004',
    'ZIP code 90210',
    'Postal code 12345',
    'Meeting at 14:30',
    'Verification expires at 14:30',
    'Code expires at 14:30:00',
    'Verification scheduled 1430 hrs',
    'Total: $1234',
    'Verification fee: $49.99',
    'Verification fee: $1234',
    'Verify payment of 1234 EUR',
    'Verify payment of R$ 1500',
    'Copyright 2026',
    'Verification 2026',
    'Code valid 2024-2026',
    'Call +1 555-019-2834',
    'Verification call +1 555-1234',
    'Verification support: (555) 123-4567',
    'Call 555-1234 for verification',
    'Phone: 555-1234 for your code',
];
for (const text of negativeCodes) {
    assert.equal(detect.detectCode(text), '', text);
}

// Link detection: first http(s) URL only, non-http and unsafe URLs rejected.
const positiveLinks = [
    ['Sign in at https://example.com/auth?t=1', 'https://example.com/auth?t=1'],
    ['First https://first.example/a then https://second.example/b', 'https://first.example/a'],
    ['Open (https://example.com/docs).', 'https://example.com/docs'],
    ['Wiki https://en.wikipedia.org/wiki/Foo_(bar).', 'https://en.wikipedia.org/wiki/Foo_(bar)'],
    ['Server at http://localhost:3000/status', 'http://localhost:3000/status'],
    ['Device at http://192.168.1.10:8080/', 'http://192.168.1.10:8080/'],
];
for (const [text, expected] of positiveLinks) {
    assert.equal(detect.detectLink(text), expected, text);
}

const negativeLinks = [
    'Open file:///etc/passwd',
    'Run javascript:alert(1)',
    'Load data:text/html,<script>alert(1)</script>',
    'Download ftp://files.example.com/a.tar.gz',
    'Email mailto:user@example.com',
    'Connect ssh://host.example.com',
    'Auth https://user:pass@example.com/path',
    'Hex http://0x7f.0x0.0x0.0x1/',
    'Nested javascript:https://example.com',
];
for (const text of negativeLinks) {
    assert.equal(detect.detectLink(text), '', text);
}

console.log('Notification detection checks passed');
