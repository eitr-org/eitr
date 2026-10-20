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

// Qt rich text has no padding or background on <pre>, so code blocks sit in a tinted one-cell table.
function readableHtml(html, accent, shortcuts, codeBackground) {
    html = html.replace(/<table>/g, '<table width="100%" cellspacing="0" cellpadding="6">');
    if (codeBackground) html = html.replace(/<pre>([\s\S]*?)<\/pre>/g,
        '<table width="100%" cellspacing="0" cellpadding="12" bgcolor="' + codeBackground + '"><tr><td><pre>$1</pre></td></tr></table>');
    if (shortcuts) html = html.replace(/(<tr>\s*)<(th|td)(\s[^>]*)?>/g, '$1<$2 width="45%"$3>');
    return '<style>h1 { font-size:24px; margin-top:0px; margin-bottom:18px; }'
        + 'h2 { font-size:20px; margin-top:24px; margin-bottom:10px; }'
        + 'h3,h4,h5,h6 { margin-top:20px; margin-bottom:10px; }'
        + 'p { margin-top:0px; margin-bottom:14px; }'
        + 'ul,ol { margin-top:8px; margin-bottom:16px; }'
        + 'li { margin-top:4px; margin-bottom:6px; }'
        + 'pre { margin-top:0px; margin-bottom:0px; white-space:pre-wrap; }'
        + 'table { margin-top:4px; margin-bottom:14px; }'
        + 'th,td { text-align:left; vertical-align:top; }'
        + 'a { color:' + accent + '; }</style>' + html;
}
