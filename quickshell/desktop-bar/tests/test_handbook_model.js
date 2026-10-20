const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../HandbookModel.js"), "utf8").replace(/^\.pragma library\s*/, ""), context);
const chapters = [
    {id: "start", title: "Getting Started", summary: "Basics", markdown: "WiFi and Bluetooth"},
    {id: "wifi", title: "WiFi", summary: "Networks", markdown: "Enterprise credentials"},
];
assert.deepStrictEqual(Array.from(context.matches(chapters, "wifi"), item => item.id), ["wifi", "start"]);
assert.deepStrictEqual(Array.from(context.matches(chapters, "enterprise credentials"), item => item.id), ["wifi"]);
assert.equal(context.matches(chapters, "unmatched").length, 0);
assert.equal(context.linkTarget("handbook:wifi", chapters).chapter, "wifi");
assert.equal(context.linkTarget("https://example.org", chapters).external, "https://example.org");
for (const link of ["file:///etc/shadow", "javascript:alert(1)", "exec:reboot", "handbook:missing"])
    assert.equal(Object.keys(context.linkTarget(link, chapters)).length, 0);
console.log("Handbook search and read-only link policy passed");
const html = context.readableHtml('<h2>Title</h2><p><a>Link</a></p>', "#85a1dc");
assert(html.includes("margin-top:24px"));
assert(html.includes("margin-bottom:14px"));
assert(html.includes("color:#85a1dc"));
const table = context.readableHtml('<table><tr><th style="text-align:left">Shortcut</th><th>Action</th></tr><tr><td>Key</td><td>Action</td></tr></table>', "#85a1dc", true);
assert(table.includes('<table width="100%"'));
assert.equal((table.match(/width="45%"/g) || []).length, 2);
const code = context.readableHtml('<p>Run</p><pre><code class="language-sh">sudo true\n</code></pre>', "#85a1dc", false, "#14ffffff");
assert(code.includes('bgcolor="#14ffffff"><tr><td><pre><code class="language-sh">sudo true\n</code></pre></td></tr></table>'));
assert(!context.readableHtml('<pre><code>x</code></pre>', "#85a1dc").includes("bgcolor"));
