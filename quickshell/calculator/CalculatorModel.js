.pragma library
// Arithmetic for Eitr's calculator: + − × ÷, ^, %, √ and parentheses, parsed
// here rather than run as code. evaluate() returns {value} or {error}.

const SYMBOLS = {"×": "*", "·": "*", "÷": "/", "−": "-", "–": "-", ",": "."};

function tokens(text) {
    const source = Array.from(String(text)).map(character => SYMBOLS[character] || character).join("");
    const list = [];
    let index = 0;
    while (index < source.length) {
        const character = source[index];
        if (/\s/.test(character)) { index += 1; continue; }
        const number = /^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?/.exec(source.slice(index));
        if (number) { list.push({type: "number", value: Number(number[0])}); index += number[0].length; continue; }
        if (source.startsWith("sqrt", index)) { list.push({type: "op", value: "√"}); index += 4; continue; }
        if ("+-*/^%()√".includes(character)) { list.push({type: "op", value: character}); index += 1; continue; }
        throw new Error(`'${character}' is not something the calculator understands`);
    }
    return list;
}

function evaluate(text) {
    let list;
    try {
        list = tokens(text);
    } catch (error) {
        return {error: error.message};
    }
    if (!list.length) return {value: 0};
    let position = 0;
    const peek = () => list[position];
    const isOp = value => peek() && peek().type === "op" && peek().value === value;
    const fail = message => { throw new Error(message); };

    function expression() {
        let value = term();
        while (isOp("+") || isOp("-")) {
            const op = list[position++].value;
            const right = term();
            value = op === "+" ? value + right : value - right;
        }
        return value;
    }
    function term() {
        let value = unary();
        while (isOp("*") || isOp("/") || (peek() && (peek().type === "number" || isOp("(") || isOp("√")))) {
            // A number or bracket right after a value multiplies: 2(3+4), 2√9.
            const op = isOp("*") || isOp("/") ? list[position++].value : "*";
            const right = unary();
            if (op === "/" && right === 0) fail("Cannot divide by zero");
            value = op === "*" ? value * right : value / right;
        }
        return value;
    }
    function unary() {
        if (isOp("-")) { position += 1; return -unary(); }
        if (isOp("+")) { position += 1; return unary(); }
        return power();
    }
    function power() {
        const base = postfix();
        if (isOp("^")) { position += 1; return Math.pow(base, unary()); }
        return base;
    }
    function postfix() {
        let value = primary();
        while (isOp("%")) { position += 1; value /= 100; }
        return value;
    }
    function primary() {
        const token = peek();
        if (!token) fail("The calculation is not finished");
        if (token.type === "number") { position += 1; return token.value; }
        if (isOp("√")) {
            position += 1;
            const value = unary();
            if (value < 0) fail("No square root of a negative number");
            return Math.sqrt(value);
        }
        if (isOp("(")) {
            position += 1;
            const value = expression();
            if (!isOp(")")) fail("A bracket is not closed");
            position += 1;
            return value;
        }
        fail(`'${token.value}' is in the wrong place`);
    }

    try {
        const value = expression();
        if (position < list.length) fail(isOp(")") ? "A bracket closes without opening" : "The calculation has an extra part");
        if (!Number.isFinite(value)) fail("The result is too large");
        return {value};
    } catch (error) {
        return {error: error.message};
    }
}

// Twelve significant digits hide floating-point noise (0.1 + 0.2 shows 0.3).
function format(value) {
    if (value === 0) return "0";
    const rounded = Number(value.toPrecision(12));
    if (Math.abs(rounded) >= 1e15 || Math.abs(rounded) < 1e-9) return rounded.toExponential(6).replace(/\.?0+e/, "e");
    const [whole, fraction] = String(rounded).split(".");
    const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return fraction ? `${grouped}.${fraction}` : grouped;
}
