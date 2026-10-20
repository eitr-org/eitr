const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const model = {};
vm.createContext(model);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'calculator', 'CalculatorModel.js'), 'utf8')
    .replace(/^\.pragma library\s*/, ''), model);

const value = text => {
    const result = model.evaluate(text);
    assert.equal(result.error, undefined, `${text}: ${result.error}`);
    return result.value;
};
const error = text => {
    const result = model.evaluate(text);
    assert.ok(result.error, `${text} should fail`);
    return result.error;
};

assert.equal(value('2+3×4'), 14, 'multiplication before addition');
assert.equal(value('(2+3)×4'), 20);
assert.equal(value('10÷4'), 2.5);
assert.equal(value('7−10'), -3, 'the minus sign from the keypad');
assert.equal(value('-3^2'), -9, 'powers before the sign');
assert.equal(value('2^3^2'), 512, 'powers group to the right');
assert.equal(value('50%'), 0.5);
assert.equal(value('200×15%'), 30);
assert.equal(value('√16+1'), 5);
assert.equal(value('sqrt(2)^2').toFixed(10), '2.0000000000');
assert.equal(value('2(3+4)'), 14, 'a bracket after a number multiplies');
assert.equal(value('2√9'), 6);
assert.equal(value('1,5+1'), 2.5, 'a decimal comma');
assert.equal(value('1e3'), 1000);
assert.equal(value(''), 0);

assert.equal(error('1/0'), 'Cannot divide by zero');
assert.equal(error('(1+2'), 'A bracket is not closed');
assert.equal(error('1+2)'), 'A bracket closes without opening');
assert.equal(error('3+'), 'The calculation is not finished');
assert.equal(error('√-4'), 'No square root of a negative number');
assert.match(error('2 & 3'), /'&' is not something/);
assert.match(error('alert(1)'), /is not something/, 'nothing is run as code');
assert.equal(error('10^400'), 'The result is too large');

assert.equal(model.format(0.1 + 0.2), '0.3', 'floating-point noise is hidden');
assert.equal(model.format(1234567.5), '1 234 567.5');
assert.equal(model.format(-42), '-42');
assert.equal(model.format(1e20), '1e+20');
assert.equal(model.format(0), '0');
console.log('Calculator arithmetic, errors and formatting checks passed');
