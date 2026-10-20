const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const context = vm.createContext({});
const source = fs.readFileSync(path.join(__dirname, '../../Eitr/Locale.js'), 'utf8').replace(/^\.pragma library\s*/, '');
vm.runInContext(source, context);
const supported = {en: {}, pt_BR: {}, es: {}, de: {}, fr: {}};
for (const [environment, expected] of [
    [{LANG: 'pt_BR.UTF-8'}, 'pt_BR'], [{LANG: 'pt_PT.UTF-8'}, 'pt_BR'], [{LANG: 'pt'}, 'pt_BR'], [{LANG: 'es_MX.UTF-8'}, 'es'],
    [{LANG: 'fr', LC_MESSAGES: 'de_DE.UTF-8'}, 'de'],
    [{LANG: 'fr', LC_ALL: 'C.UTF-8'}, 'en'], [{LANG: '../../de'}, 'en'],
]) assert.equal(context.select(context.systemLocale(environment), supported), expected);
assert.equal(context.translate('Hello %1, %2', {'Hello %1, %2': 'Hallo %2, %1'}, {}, ['%2', 'Erick']), 'Hallo Erick, %2');
assert.equal(context.translate('Missing', {}, {}, []), 'Missing');
assert.equal(context.translate('Fallback', {Fallback: ''}, {Fallback: 'Base'}, []), 'Base');
console.log('QML locale precedence, regional fallback and one-pass placeholders passed.');

assert.equal(context.translate('{current} of {total}', {}, {}, {current: '{total}', total: '%1'}), '{total} of %1');
assert.equal(context.translate('{missing}', {}, {}, {}), '{missing}');
