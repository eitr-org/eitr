.pragma library

function matches(chapters, query) {
    var words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    return chapters.filter(chapter => {
        var text = (chapter.title + " " + chapter.summary + " " + chapter.markdown).toLowerCase();
        return words.every(word => text.indexOf(word) !== -1);
    }).sort((first, second) => {
        var titleMatch = chapter => words.length && words.every(word => chapter.title.toLowerCase().indexOf(word) !== -1) ? 0 : 1;
        return titleMatch(first) - titleMatch(second) || chapters.indexOf(first) - chapters.indexOf(second);
    });
}

function linkTarget(link, chapters) {
    if (link.indexOf("handbook:") === 0) {
        var id = link.slice(9).split("#")[0];
        return chapters.some(chapter => chapter.id === id) ? {chapter: id} : {};
    }
    return /^https?:\/\//i.test(link) ? {external: link} : {};
}

var runes = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ", "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛜ", "ᛞ", "ᛟ"];
var resultsRune = "ᛉ";

// Chapters keep their catalog order; each group takes the next rune, as Settings' groups do.
function groupOf(chapters, chapter) {
    var names = [];
    chapters.forEach(entry => { if (names.indexOf(entry.group || "") < 0) names.push(entry.group || ""); });
    var index = Math.max(0, names.indexOf(chapter ? chapter.group || "" : ""));
    return {name: chapter ? chapter.group || "" : "", rune: runes[index % runes.length]};
}

// Sidebar rows for FamilySidebar; search results keep their ranking under one caption.
function sidebarEntries(chapters, results, resultsLabel) {
    return results.map(chapter => {
        var group = groupOf(chapters, chapter);
        return {id: chapter.id, title: chapter.title, rune: runes[Math.max(0, chapters.indexOf(chapter)) % runes.length],
            group: resultsLabel || group.name, groupRune: resultsLabel ? resultsRune : group.rune};
    });
}

// The page header already shows the chapter title, so a leading <h1> is not repeated.
function articleBlocks(chapter) {
    var blocks = chapter ? chapter.blocks || [] : [];
    return blocks.length && /^<h1>/.test(blocks[0]) ? blocks.slice(1) : blocks;
}

// The reader frames code and table blocks as cards in QML; the plain renderer uses a one-cell code table.
// `style` carries the Settings palette and fonts: body, mono, carved, fg, gold, raised and line.
function readableHtml(html, accent, shortcuts, codeBackground, style) {
    html = html.replace(/<table>/g, '<table width="100%" cellspacing="0" cellpadding="' + (style ? 9 : 6) + '"'
        + (style ? ' border="1" bordercolor="' + style.line + '" style="border-collapse:collapse; border-style:solid"' : '') + '>');
    if (style) html = html.replace(/<th(\s|>)/g, '<th bgcolor="' + style.raised + '"$1').replace(/\n<\/code><\/pre>/g, '</code></pre>');
    if (codeBackground && !style) html = html.replace(/<pre>([\s\S]*?)<\/pre>/g,
        '<table width="100%" cellspacing="0" cellpadding="12" bgcolor="' + codeBackground + '"><tr><td><pre>$1</pre></td></tr></table>');
    if (shortcuts) html = html.replace(/(<tr>\s*)<(th|td)(\s[^>]*)?>/g, '$1<$2 width="45%"$3>');
    if (style) html = html.replace(/<h([1-6])>/g, function(tag, level) {
        var size = level === "1" ? 24 : level === "2" ? 20 : 14;
        return '<h' + level + ' style=\'font-family:"' + style.carved + '"; font-size:' + size + 'px; font-weight:500; color:'
            + (Number(level) >= 3 ? style.gold + '; font-variant:small-caps; letter-spacing:1px' : style.fg) + ';\'>';
    });
    var styleCss = style ? 'body,p,li { font-family:"' + style.body + '"; color:' + style.fg + '; } strong,b { color:' + style.fg + '; }'
        + 'h1,h2 { font-family:"' + style.carved + '"; color:' + style.fg + '; font-weight:500; }'
        + 'h1 { font-size:24px; } h2 { font-size:20px; }'
        + 'h3,h4,h5,h6 { font-family:"' + style.carved + '"; color:' + style.gold + '; font-weight:500; font-variant:small-caps; }'
        + 'code,pre { font-family:"' + style.mono + '"; color:' + style.fg + '; }'
        + 'td,th { border:1px solid ' + style.line + '; padding:9px; }'
        + 'th { color:' + style.gold + '; }' : "";
    return '<style>h1 { font-size:24px; margin-top:0px; margin-bottom:18px; }'
        + 'h2 { font-size:20px; margin-top:24px; margin-bottom:10px; }'
        + 'h3,h4,h5,h6 { margin-top:20px; margin-bottom:10px; }'
        + 'p { margin-top:0px; margin-bottom:14px; }'
        + 'ul,ol { margin-top:8px; margin-bottom:16px; }'
        + 'li { margin-top:4px; margin-bottom:6px; }'
        + 'pre { margin-top:0px; margin-bottom:0px; white-space:pre-wrap; }'
        + 'table { margin-top:4px; margin-bottom:14px; }'
        + 'th,td { text-align:left; vertical-align:top; }'
        + 'a { color:' + accent + '; }' + styleCss + '</style>' + html;
}
