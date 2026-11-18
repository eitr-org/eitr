// Verification code and HTTP link detection for notification cards.
// Adapted from Omarchy (shell/plugins/notifications/Detect.js & Security.js), MIT License.
// Copyright (c) David Heinemeier Hansson
.pragma library

var MAX_BODY = 32768;
var MAX_URL = 4096;
var MAX_CODES = 8;
var NEAR_BEFORE = 36;
var NEAR_AFTER = 72;

// Code/OTP/PIN/verification keywords in all 8 UI languages (en, pt_BR, es, de, fr, ja, zh_CN, ko).
var LATIN_CODE_WORDS = [
    "code", "otp", "one[\\s-]?time", "passcode", "pin", "2fa", "two[\\s-]?factor", "mfa", "totp",
    "verification", "verify", "security[\\s-]+key",
    "c[oó]digo", "verifica[cç][aã]o", "verificar", "autentica[cç][aã]o", "dois[\\s-]+fatores",
    "senha[\\s-]+(?:[uú]nica|de[\\s-]+uso[\\s-]+[uú]nico)",
    "verificaci[oó]n", "autenticaci[oó]n", "dos[\\s-]+factores",
    "contrase[nñ]a[\\s-]+de[\\s-]+un[\\s-]+solo[\\s-]+uso",
    "clave[\\s-]+(?:de[\\s-]+verificaci[oó]n|[uú]nica)",
    "best[aä]tigungscode", "verifizierungscode", "sicherheitscode", "pr[uü]fcode", "einmalcode",
    "zugangscode", "freischaltcode", "aktivierungscode", "anmeldecode", "autorisierungscode",
    "authentifizierungscode", "pin-?code", "verifizierung", "verifizieren", "einmal-?passwort",
    "einmalkennwort", "zwei-?faktor", "authentifizierung", "pr[uü]fziffer",
    "v[eé]rification", "v[eé]rifier", "deux[\\s-]+facteurs", "usage[\\s-]+unique"
];
var LATIN_BOUNDARY = "[^A-Za-z0-9_\\u00C0-\\u024F]";
var LATIN_RE = new RegExp("(?:^|" + LATIN_BOUNDARY + ")(" + LATIN_CODE_WORDS.join("|") + ")(?=$|" + LATIN_BOUNDARY + ")", "gi");

var CJK_CODE_WORDS = [
    "認証コード", "確認コード", "セキュリティコード", "ワンタイムコード", "パスコード", "確認用コード",
    "認証番号", "確認番号", "暗証番号", "ワンタイムパスワード", "ワンタイム", "二要素", "二段階認証", "認証", "コード",
    "验证码", "校验码", "确认码", "安全码", "动态码", "动态口令", "一次性密码", "一次性验证码",
    "通行码", "授权码", "登录码", "激活码", "验证",
    "인증\\s*번호", "인증\\s*코드", "확인\\s*코드", "확인\\s*번호", "보안\\s*코드",
    "일회용\\s*비밀번호", "일회용\\s*코드", "2단계\\s*인증", "이중\\s*인증", "코드", "인증"
];
var CJK_RE = new RegExp("(" + CJK_CODE_WORDS.join("|") + ")", "g");

// Grouped or plain 4-8 digit codes, optionally with a single-letter prefix ("G-482913").
var CODE_SHAPE = /(?:^|[^\w-])((?:[A-Za-z]-)?\d{2,4}(?:[ \t-]\d{2,4}){1,3}|(?:[A-Za-z]-)?\d{4,8})(?![\w-])/g;

function bounded(value, max) {
    return typeof value === "string" ? value.slice(0, max) : "";
}

function maskUrls(text) {
    return text.replace(/https?:\/\/[^\s<>"']+/gi, function(match) {
        return new Array(match.length + 1).join(" ");
    });
}

// "Claude Code", "VS Code": a capitalized word before capitalized "Code" is a product name.
function isProductName(text, at, word) {
    if (String(word).toLowerCase() !== "code" || word.charAt(0) !== "C") return false;
    var before = text.slice(Math.max(0, at - 24), at).match(/([A-Za-z][\w.]*)[ \t]+$/);
    if (!before || !/^([A-Z][a-z]+|[A-Z]{2,})$/.test(before[1])) return false;
    return !/^(?:Verification|Security|Auth|Authentication|Authorization|Login|Access|Confirm|Confirmation|One|Two|Pass|Backup|Recovery|PIN|OTP|2FA|MFA|TOTP)$/i.test(before[1]);
}

function isNonAuthKeyword(text, at, word) {
    var lower = String(word).toLowerCase();
    var before = text.slice(Math.max(0, at - 24), at);
    var after = text.slice(at + word.length, Math.min(text.length, at + word.length + 20));
    if (lower === "code" || lower === "código" || lower === "codigo") {
        if (/(?:zip|postal|post|area|country|dialing|error|status|exit|return|http|qr|bar|source|promo|coupon|discount|voucher|referral|invite|color|hex|tracking|order|fehler)[ \t]+$/i.test(before)) return true;
        if (/^[ \t]*(?:postal|de[ \t]+error|de[ \t]+erro|de[ \t]+barras|d'erreur|erreur)(?=$|[^A-Za-z])/i.test(after)) return true;
    }
    if (lower === "pin" && /(?:map|push|bowling)[ \t]+$/i.test(before)) return true;
    if (word === "コード" && /(?:エラー|郵便|ソース|プロモ|クーポン|割引|バー|QR)$/.test(before)) return true;
    if (/^코드$/.test(word) && /(?:오류|에러|소스|할인|프로모션|우편|바|QR)[ \t]*$/.test(before)) return true;
    return false;
}

function clampWindow(text, kwStart, kwEnd) {
    var start = Math.max(0, kwStart - NEAR_BEFORE);
    var end = Math.min(text.length, kwEnd + NEAR_AFTER);
    var left = text.slice(start, kwStart);
    var breakRe = /[.!?][ \t]+|[。！？]/g;
    var match;
    while ((match = breakRe.exec(left)) !== null) {
        start = Math.max(start, Math.max(0, kwStart - NEAR_BEFORE) + match.index + match[0].length);
    }
    var right = text.slice(kwEnd, end);
    var rightBreak = right.search(/[.!?][ \t]+|[。！？]/);
    if (rightBreak !== -1) end = kwEnd + rightBreak;
    return [start, end, kwStart, kwEnd];
}

function keywordWindows(text) {
    var spans = [];
    var match;
    LATIN_RE.lastIndex = 0;
    while ((match = LATIN_RE.exec(text)) !== null) {
        var at = match.index + match[0].length - match[1].length;
        if (!isProductName(text, at, match[1]) && !isNonAuthKeyword(text, at, match[1])) {
            spans.push(clampWindow(text, at, at + match[1].length));
        }
        if (LATIN_RE.lastIndex === match.index) LATIN_RE.lastIndex++;
    }
    CJK_RE.lastIndex = 0;
    while ((match = CJK_RE.exec(text)) !== null) {
        if (!isNonAuthKeyword(text, match.index, match[1])) {
            spans.push(clampWindow(text, match.index, match.index + match[1].length));
        }
        if (CJK_RE.lastIndex === match.index) CJK_RE.lastIndex++;
    }
    return spans.slice(0, MAX_CODES * 2);
}

function isRejectedNumber(text, numStart, numEnd, raw, digits, spans) {
    if (digits.length < 4 || digits.length > 8) return true;
    var plain = raw.replace(/^[A-Za-z]-/, "");
    if (!/[ \t-]/.test(plain) && /^(19|20)\d\d$/.test(digits)) return true;
    if (/^(19|20)\d\d-(19|20)\d\d$/.test(plain)) return true;
    var before = text.slice(Math.max(0, numStart - 32), numStart);
    var after = text.slice(numEnd, Math.min(text.length, numEnd + 20));
    // Prices and currency amounts.
    if (/[$€£¥₩₹][ \t]*$/.test(before)) return true;
    if (/(?:^|[^A-Za-z])(?:USD|EUR|GBP|JPY|CNY|KRW|BRL|CAD|AUD|CHF|R\$)[ \t]*$/i.test(before)) return true;
    if (/\d[.,]$/.test(before) || /^[.,]\d/.test(after)) return true;
    if (/^[ \t]*(?:USD|EUR|GBP|JPY|CNY|KRW|BRL|CAD|AUD|CHF|[€£¥₩₹])(?=$|[^A-Za-z])/i.test(after)) return true;
    // Order, invoice, ticket, and tracking numbers.
    if (/#[ \t]*$/.test(before)) return true;
    if (/(?:order|pedido|commande|bestellung|auftragsnummer|bestellnummer|invoice|rechnung|fatura|factura|ticket|issue|tracking|shipment|env[ií]o|rastreio|lieferung|注文(?:番号)?|订单(?:号)?|주문(?:번호)?)[ \t]*(?:#|no\.?|n[úu]m(?:ero)?\.?|nr\.?|number)?[: \t]*$/i.test(before)) return true;
    // Ports, times, IP addresses, and version strings.
    if (/(?:^|[^A-Za-z])port[ \t]*[: \t]?[ \t]*$/i.test(before)) return true;
    if (/\d:$/.test(before) || /^:\d/.test(after)) return true;
    if (/:$/.test(before)) {
        var endsAtColonKeyword = spans.some(function(span) { return span[3] === numStart - 1; });
        if (!endsAtColonKeyword) return true;
    }
    if (/\d\.$/.test(before) || /^\.\d/.test(after) || /(?:^|[^A-Za-z])v\d+\.$/i.test(before)) return true;
    if (/^[ \t]*(?:am|pm|hrs?|hours?|mins?|minutes?|secs?|seconds?)(?=$|[^A-Za-z])/i.test(after)) return true;
    // Phone numbers.
    if (/\+[ \t]*$/.test(before) || /\+\d{1,3}[ \t-]+$/.test(before)) return true;
    if (/\(\d{2,4}\)[ \t]*$/.test(before)) return true;
    if (/\($/.test(before) && /^\)[ \t-]*\d/.test(after)) return true;
    if (/(?:tel(?:ephone|éfono|efone|efon)?|phone|call|fax|llamar|ligar|anrufen|appeler|電話|电话|전화)[ \t]*[: \t]*$/i.test(before)) return true;
    return false;
}

function detectCode(text) {
    var clean = maskUrls(bounded(text, MAX_BODY));
    var spans = keywordWindows(clean);
    if (!spans.length) return "";
    var best = null;
    var match;
    CODE_SHAPE.lastIndex = 0;
    while ((match = CODE_SHAPE.exec(clean)) !== null) {
        var raw = match[1];
        var numStart = match.index + match[0].length - raw.length;
        var numEnd = numStart + raw.length;
        var matching = spans.filter(function(span) { return numStart >= span[0] && numStart < span[1]; });
        if (!matching.length) continue;
        var digits = raw.replace(/^[A-Za-z]-/, "").replace(/[ \t-]/g, "");
        if (isRejectedNumber(clean, numStart, numEnd, raw, digits, spans)) continue;
        var score = Infinity;
        for (var index = 0; index < matching.length; index++) {
            var span = matching[index];
            var afterKeyword = numStart >= span[3];
            var distance = afterKeyword ? numStart - span[3] : span[2] - numEnd;
            score = Math.min(score, (afterKeyword ? 0 : 1000) + Math.max(0, distance));
        }
        if (!best || score < best.score) best = {digits: digits, score: score};
    }
    return best ? best.digits : "";
}

function canonicalHostname(raw) {
    if (typeof raw !== "string" || raw.length > 253) return "";
    var host = raw.toLowerCase().replace(/\.$/, "");
    if (host === "localhost") return host;
    if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
        var octets = host.split(".");
        for (var index = 0; index < octets.length; index++) {
            if (/^0\d/.test(octets[index]) || Number(octets[index]) > 255) return "";
        }
        return host;
    }
    if (!/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/.test(host)) return "";
    if (/^(?:0x[0-9a-f]*|[0-9]+)$/i.test(host.split(".").pop())) return "";
    return host;
}

function safeHttpUrl(raw) {
    if (typeof raw !== "string" || raw.length > MAX_URL || /[\x00-\x20\x7f-\x9f\\]/.test(raw)) return "";
    if (/%(?:0[0-9a-f]|1[0-9a-f]|7f|25|5c)/i.test(raw) || /[<>"']/.test(raw)) return "";
    if (/^[a-z]+:\/\/[^/?#]*@/i.test(raw)) return "";
    var match = raw.match(/^(https?):\/\/([^/?#]+)([^]*)$/i);
    if (!match) return "";
    var authority = match[2].match(/^([^:%@]+)(?::([0-9]{1,5}))?$/);
    if (!authority) return "";
    var host = canonicalHostname(authority[1]);
    if (!host || (authority[2] && (+authority[2] < 1 || +authority[2] > 65535))) return "";
    if (/%(?![0-9a-f]{2})/i.test(match[3])) return "";
    return match[1].toLowerCase() + "://" + host + (authority[2] ? ":" + String(+authority[2]) : "") + (match[3] || "/");
}

function trimTrailingPunctuation(raw) {
    var trimmed = raw.replace(/[.,;:!?\]}'"]+$/, "");
    while (trimmed.slice(-1) === ")") {
        var opens = (trimmed.match(/\(/g) || []).length;
        var closes = (trimmed.match(/\)/g) || []).length;
        if (closes <= opens) break;
        trimmed = trimmed.slice(0, -1).replace(/[.,;:!?\]}'"]+$/, "");
    }
    return trimmed;
}

function detectLink(body) {
    var text = bounded(body, MAX_BODY);
    var re = /(?:^|[\s(\[<"'])(https?:\/\/[^\s<>"']+)/gi;
    var match;
    while ((match = re.exec(text)) !== null) {
        var url = safeHttpUrl(trimTrailingPunctuation(match[1]));
        if (url) return url;
    }
    return "";
}

function scan(summary, body) {
    var combined = String(summary || "") + "\n" + String(body || "");
    return {
        code: detectCode(combined),
        link: detectLink(body || "")
    };
}

if (typeof module !== "undefined") {
    module.exports = {detectCode: detectCode, detectLink: detectLink, scan: scan, safeHttpUrl: safeHttpUrl};
}
