const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(`${__dirname}/../DockModel.js`, 'utf8').replace(/^\.pragma.*$/m, ''), context);
const site = 'music.youtube.com__-default';
for (const windowClass of ['chrome-music.youtube.com__-Default', 'chromium-music.youtube.com__-Default',
    'brave-browser-music.youtube.com__-Default', 'msedge-music.youtube.com__-Default'])
    assert.equal(context.webAppKey(windowClass), site, windowClass);
for (const ordinary of ['google-chrome', 'kitty', 'org.gnome.Nautilus', 'eitr-menu-terminal'])
    assert.equal(context.webAppKey(ordinary), '', ordinary);
const dock = fs.readFileSync(`${__dirname}/../EdgeDockContent.qml`, 'utf8');
assert.ok(dock.includes('DockModel.webAppKey(entry.startupClass) === webApp'));
console.log('Dock web app matching passed');
