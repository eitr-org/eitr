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
const style = {body: "Body Sans", mono: "Site Mono", carved: "Site Carved", fg: "#e4dcd2", gold: "#b08d57", raised: "#1e1a1a", line: "#3a3634"};
const styled = context.readableHtml('<h1>Title</h1><h2>Part</h2><h3>Section</h3><table><tr><th>Key</th></tr></table><pre><code>&lt;disk&gt;\n</code></pre>', "#d4545c", false, "", style);
assert(styled.includes('font-family:"Site Carved"; font-size:20px'), "level 2 headings are carved");
assert(styled.includes('color:#b08d57; font-variant:small-caps'), "level 3 headings are gold small caps");
assert(styled.includes('font-family:"Site Mono"'));
assert(styled.includes('font-family:"Body Sans"'));
assert(styled.includes('border="1" bordercolor="#3a3634"'));
assert(styled.includes('<th bgcolor="#1e1a1a">Key'));
assert(styled.includes('&lt;disk&gt;</code></pre>'), "code keeps entities and drops its trailing newline");
assert(!styled.includes('bgcolor="#14'), "QML owns the code card");
assert(styled.includes('a { color:#d4545c; }'), "links use the accent");
const book = [
    {id: "start", title: "Start", group: "Begin", blocks: ["<h1>Welcome</h1>", "<p>Text</p>"]},
    {id: "bar", title: "Bar", group: "Desktop", blocks: ["<p>Bar</p>"]},
    {id: "focus", title: "Focus", group: "Desktop", blocks: []},
];
assert.deepStrictEqual(Array.from(context.articleBlocks(book[0])), ["<p>Text</p>"], "the page header replaces the leading title");
assert.deepStrictEqual(Array.from(context.articleBlocks(book[1])), ["<p>Bar</p>"]);
assert.equal(context.articleBlocks(null).length, 0);
const rows = context.sidebarEntries(book, book, "");
assert.deepStrictEqual(Array.from(rows, row => row.group), ["Begin", "Desktop", "Desktop"]);
assert.equal(rows[1].groupRune, rows[2].groupRune, "a group shares one rune");
assert.notEqual(rows[0].groupRune, rows[1].groupRune);
assert.notEqual(rows[1].rune, rows[2].rune, "each chapter has its own rune");
const results = context.sidebarEntries(book, [book[2], book[0]], "Results");
assert.deepStrictEqual(Array.from(results, row => row.id), ["focus", "start"], "search keeps its ranking");
assert(results.every(row => row.group === "Results"));
assert.equal(context.groupOf(book, book[2]).name, "Desktop");
console.log("Handbook rendering and sidebar grouping passed");
